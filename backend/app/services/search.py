import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.schemas import SearchResult
from app.services.embeddings import cosine_similarity, embed_text
from app.services.vector_store import citation_for_chunk, query_chunks

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']*")


def search_chunks(db: Session, query: str, matter_id: int | None = None, limit: int = 10) -> list[SearchResult]:
    query_vector = embed_text(query)
    query_terms = {token.lower() for token in TOKEN_PATTERN.findall(query)}
    qdrant_results = _search_qdrant(db, query_vector, query_terms, matter_id=matter_id, limit=limit)
    if qdrant_results:
        return qdrant_results

    return _search_local(db, query_vector, query_terms, matter_id=matter_id, limit=limit)


def _search_qdrant(
    db: Session,
    query_vector: list[float],
    query_terms: set[str],
    matter_id: int | None,
    limit: int,
) -> list[SearchResult]:
    try:
        hits = query_chunks(query_vector, matter_id=matter_id, limit=limit)
    except Exception:
        return []

    results = []
    for hit in hits:
        statement = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id).where(
            DocumentChunk.id == hit["chunk_id"]
        )
        row = db.execute(statement).first()
        if row is None:
            continue
        chunk, document = row
        results.append(
            SearchResult(
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.subject or document.original_filename,
                snippet=_snippet(chunk.text, query_terms),
                score=round(hit["score"], 4),
                citation=citation_for_chunk(document, chunk),
                source="qdrant",
            )
        )
    return results


def _search_local(
    db: Session,
    query_vector: list[float],
    query_terms: set[str],
    matter_id: int | None,
    limit: int,
) -> list[SearchResult]:
    statement = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
    if matter_id is not None:
        statement = statement.where(Document.matter_id == matter_id)

    scored_results = []
    for chunk, document in db.execute(statement).all():
        vector_score = cosine_similarity(chunk.embedding, query_vector)
        keyword_score = _keyword_score(chunk.text, query_terms)
        score = (0.75 * vector_score) + (0.25 * keyword_score)
        if score <= 0:
            continue
        scored_results.append((score, chunk, document))

    scored_results.sort(key=lambda item: item[0], reverse=True)
    return [
        SearchResult(
            document_id=document.id,
            chunk_id=chunk.id,
            title=document.subject or document.original_filename,
            snippet=_snippet(chunk.text, query_terms),
            score=round(score, 4),
            citation=citation_for_chunk(document, chunk),
            source="local",
        )
        for score, chunk, document in scored_results[:limit]
    ]


def _keyword_score(text: str, query_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    text_terms = {token.lower() for token in TOKEN_PATTERN.findall(text)}
    return len(query_terms & text_terms) / len(query_terms)


def _snippet(text: str, query_terms: set[str], max_length: int = 300) -> str:
    lowered = text.lower()
    first_match = min(
        (lowered.find(term) for term in query_terms if lowered.find(term) >= 0),
        default=0,
    )
    start = max(first_match - 80, 0)
    end = min(start + max_length, len(text))
    snippet = text[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(text):
        snippet = f"{snippet}..."
    return snippet
