import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.schemas import SearchDiagnostics, SearchResult
from app.services.embeddings import cosine_similarity, embed_text
from app.services.vector_store import citation_for_chunk, query_chunks

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']*")
PHRASE_PATTERN = re.compile(r'"([^"]+)"')


@dataclass(frozen=True)
class QueryPlan:
    raw: str
    terms: set[str]
    required_terms: set[str]
    excluded_terms: set[str]
    phrases: list[str]


def search_chunks(
    db: Session,
    query: str,
    matter_id: int | None = None,
    limit: int = 10,
    matter_ids: list[int] | None = None,
    backend: str = "auto",
    custodian_id: int | None = None,
    document_type: str | None = None,
    file_type: str | None = None,
    processing_status: str | None = None,
    tag: str | None = None,
    issue_code: str | None = None,
    privilege_flag: bool | None = None,
    review_status: str | None = None,
    sender: str | None = None,
    recipient: str | None = None,
    sort_by: str = "relevance",
    date_from=None,
    date_to=None,
) -> list[SearchResult]:
    if matter_ids == []:
        return []
    query_vector = embed_text(query)
    plan = _parse_query(query)
    has_metadata_filters = any(
        [
            custodian_id,
            document_type,
            file_type,
            processing_status,
            tag,
            issue_code,
            privilege_flag is not None,
            review_status,
            sender,
            recipient,
            date_from,
            date_to,
        ]
    )

    if backend in {"auto", "qdrant"}:
        qdrant_results = _search_qdrant(
            db,
            query_vector,
            plan,
            matter_id=matter_id,
            matter_ids=matter_ids,
            limit=limit,
            custodian_id=custodian_id,
            document_type=document_type,
            file_type=file_type,
            processing_status=processing_status,
            tag=tag,
            issue_code=issue_code,
            privilege_flag=privilege_flag,
            review_status=review_status,
            sender=sender,
            recipient=recipient,
            date_from=date_from,
            date_to=date_to,
        )
        if backend == "qdrant":
            return qdrant_results
    else:
        qdrant_results = []

    if backend == "auto" and qdrant_results:
        return qdrant_results

    return _search_local(
        db,
        query_vector,
        plan,
        matter_id=matter_id,
        matter_ids=matter_ids,
        limit=limit,
        custodian_id=custodian_id,
        document_type=document_type,
        file_type=file_type,
        processing_status=processing_status,
        tag=tag,
        issue_code=issue_code,
        privilege_flag=privilege_flag,
        review_status=review_status,
        sender=sender,
        recipient=recipient,
        sort_by=sort_by,
        date_from=date_from,
        date_to=date_to,
    )


def _search_qdrant(
    db: Session,
    query_vector: list[float],
    plan: QueryPlan,
    matter_id: int | None,
    matter_ids: list[int] | None,
    limit: int,
    custodian_id: int | None = None,
    document_type: str | None = None,
    file_type: str | None = None,
    processing_status: str | None = None,
    tag: str | None = None,
    issue_code: str | None = None,
    privilege_flag: bool | None = None,
    review_status: str | None = None,
    sender: str | None = None,
    recipient: str | None = None,
    date_from=None,
    date_to=None,
) -> list[SearchResult]:
    try:
        try:
            hits = query_chunks(
                query_vector,
                matter_id=matter_id,
                matter_ids=matter_ids,
                limit=limit,
                custodian_id=custodian_id,
                document_type=document_type,
                file_type=file_type,
                processing_status=processing_status,
                tag=tag,
                issue_code=issue_code,
                privilege_flag=privilege_flag,
                review_status=review_status,
                sender=sender,
                recipient=recipient,
                date_from=date_from,
                date_to=date_to,
            )
        except TypeError:
            hits = query_chunks(query_vector, matter_id=matter_id, matter_ids=matter_ids, limit=limit)
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
        if not _matches_query(chunk.text, plan):
            continue
        keyword_score = _keyword_score(chunk.text, plan)
        phrase_matches = _phrase_matches(chunk.text, plan.phrases)
        results.append(
            SearchResult(
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.subject or document.original_filename,
                snippet=_snippet(chunk.text, plan.terms | set(plan.phrases)),
                score=round(hit["score"], 4),
                citation=citation_for_chunk(document, chunk),
                source="qdrant",
                diagnostics=SearchDiagnostics(
                    vector_score=round(hit["score"], 4),
                    keyword_score=round(keyword_score, 4),
                    metadata_score=1.0,
                    phrase_matches=phrase_matches,
                    required_terms=sorted(plan.required_terms),
                    excluded_terms=sorted(plan.excluded_terms),
                ),
            )
        )
    return results


def _search_local(
    db: Session,
    query_vector: list[float],
    plan: QueryPlan,
    matter_id: int | None,
    matter_ids: list[int] | None,
    limit: int,
    custodian_id: int | None = None,
    document_type: str | None = None,
    file_type: str | None = None,
    processing_status: str | None = None,
    tag: str | None = None,
    issue_code: str | None = None,
    privilege_flag: bool | None = None,
    review_status: str | None = None,
    sender: str | None = None,
    recipient: str | None = None,
    sort_by: str = "relevance",
    date_from=None,
    date_to=None,
) -> list[SearchResult]:
    statement = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
    if matter_id is not None:
        statement = statement.where(Document.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Document.matter_id.in_(matter_ids))
    if custodian_id is not None:
        statement = statement.where(Document.custodian_id == custodian_id)
    if document_type:
        statement = statement.where(Document.document_type == document_type)
    if file_type:
        statement = statement.where(Document.file_type == file_type.lower().lstrip("."))
    if processing_status:
        statement = statement.where(Document.processing_status == processing_status)
    if tag:
        statement = statement.where(Document.tags.ilike(f'%"{tag}"%'))
    if issue_code:
        statement = statement.where(Document.issue_codes.ilike(f'%"{issue_code}"%'))
    if privilege_flag is not None:
        statement = statement.where(Document.privilege_flag.is_(privilege_flag))
    if review_status:
        statement = statement.where(Document.review_status == review_status)
    if sender:
        statement = statement.where(Document.sender.ilike(f"%{sender}%"))
    if recipient:
        recipient_filter = f"%{recipient}%"
        statement = statement.where(
            (Document.recipients.ilike(recipient_filter))
            | (Document.cc.ilike(recipient_filter))
            | (Document.bcc.ilike(recipient_filter))
        )
    if date_from is not None:
        statement = statement.where(Document.document_date >= date_from)
    if date_to is not None:
        statement = statement.where(Document.document_date <= date_to)

    scored_results = []
    for chunk, document in db.execute(statement).all():
        if not _matches_query(chunk.text, plan):
            continue
        vector_score = cosine_similarity(chunk.embedding, query_vector)
        keyword_score = _keyword_score(chunk.text, plan)
        phrase_score = len(_phrase_matches(chunk.text, plan.phrases)) / len(plan.phrases) if plan.phrases else 0.0
        metadata_score = 1.0 if any([tag, issue_code, privilege_flag is not None, review_status, sender, recipient]) else 0.0
        score = (0.65 * vector_score) + (0.25 * keyword_score) + (0.10 * max(phrase_score, metadata_score))
        if score <= 0:
            continue
        scored_results.append((score, vector_score, keyword_score, metadata_score, chunk, document))

    scored_results.sort(key=lambda item: _sort_key(item, sort_by), reverse=sort_by == "relevance")
    return [
        SearchResult(
            document_id=document.id,
            chunk_id=chunk.id,
            title=document.subject or document.original_filename,
            snippet=_snippet(chunk.text, plan.terms | set(plan.phrases)),
            score=round(score, 4),
            citation=citation_for_chunk(document, chunk),
            source="local",
            diagnostics=SearchDiagnostics(
                vector_score=round(vector_score, 4),
                keyword_score=round(keyword_score, 4),
                metadata_score=round(metadata_score, 4),
                phrase_matches=_phrase_matches(chunk.text, plan.phrases),
                required_terms=sorted(plan.required_terms),
                excluded_terms=sorted(plan.excluded_terms),
            ),
        )
        for score, vector_score, keyword_score, metadata_score, chunk, document in scored_results[:limit]
    ]


def _parse_query(query: str) -> QueryPlan:
    phrases = [phrase.strip().lower() for phrase in PHRASE_PATTERN.findall(query) if phrase.strip()]
    without_phrases = PHRASE_PATTERN.sub(" ", query)
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(without_phrases)]
    excluded_terms = {tokens[index + 1] for index, token in enumerate(tokens[:-1]) if token == "not"}
    operator_terms = {"and", "or", "not"}
    terms = {token for token in tokens if token not in operator_terms and token not in excluded_terms}
    required_terms = {token[1:] for token in terms if token.startswith("+") and len(token) > 1}
    terms = {token[1:] if token.startswith("+") else token for token in terms}
    return QueryPlan(
        raw=query,
        terms=terms,
        required_terms=required_terms,
        excluded_terms=excluded_terms,
        phrases=phrases,
    )


def _matches_query(text: str, plan: QueryPlan) -> bool:
    lowered = text.lower()
    text_terms = {token.lower() for token in TOKEN_PATTERN.findall(text)}
    if any(term in text_terms or term in lowered for term in plan.excluded_terms):
        return False
    if plan.required_terms and not plan.required_terms <= text_terms:
        return False
    if plan.phrases and not all(phrase in lowered for phrase in plan.phrases):
        return False
    return True


def _keyword_score(text: str, plan: QueryPlan) -> float:
    query_terms = plan.terms | plan.required_terms
    if not query_terms:
        return 0.0
    text_terms = {token.lower() for token in TOKEN_PATTERN.findall(text)}
    term_score = len(query_terms & text_terms) / len(query_terms)
    phrase_score = len(_phrase_matches(text, plan.phrases)) / len(plan.phrases) if plan.phrases else 0.0
    return max(term_score, phrase_score)


def _snippet(text: str, query_terms: set[str], max_length: int = 300) -> str:
    lowered = text.lower()
    first_match = min(
        (lowered.find(term.lower()) for term in query_terms if lowered.find(term.lower()) >= 0),
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


def _phrase_matches(text: str, phrases: list[str]) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase in lowered]


def _sort_key(item, sort_by: str):
    score, _, _, _, chunk, document = item
    if sort_by == "date":
        return document.document_date or document.created_at
    if sort_by == "custodian":
        return (document.custodian_id or 0, document.created_at)
    if sort_by == "document_type":
        return (document.document_type or "", document.created_at)
    return score
