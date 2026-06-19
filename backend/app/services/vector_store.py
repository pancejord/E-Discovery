from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document


def index_chunk(document: Document, chunk: DocumentChunk) -> None:
    if not settings.qdrant_enabled or not chunk.embedding or not chunk.vector_id:
        return

    client = QdrantClient(url=settings.qdrant_url, timeout=2)
    _ensure_collection(client)
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            models.PointStruct(
                id=chunk.vector_id,
                vector=chunk.embedding,
                payload={
                    "document_id": document.id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "matter_id": document.matter_id,
                    "filename": document.original_filename,
                    "citation": citation_for_chunk(document, chunk),
                },
            )
        ],
    )


def query_chunks(query_vector: list[float], matter_id: int | None = None, limit: int = 10) -> list[dict]:
    if not settings.qdrant_enabled:
        return []

    client = QdrantClient(url=settings.qdrant_url, timeout=2)
    _ensure_collection(client)
    query_filter = None
    if matter_id is not None:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="matter_id",
                    match=models.MatchValue(value=matter_id),
                )
            ]
        )

    if hasattr(client, "query_points"):
        result = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        points = getattr(result, "points", result)
    else:
        points = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

    hydrated = []
    for point in points:
        payload = getattr(point, "payload", {}) or {}
        chunk_id = payload.get("chunk_id")
        if chunk_id is None:
            continue
        hydrated.append(
            {
                "chunk_id": int(chunk_id),
                "score": float(getattr(point, "score", 0.0) or 0.0),
            }
        )
    return hydrated


def citation_for_chunk(document: Document, chunk: DocumentChunk) -> str:
    return f"{document.original_filename}#chunk-{chunk.chunk_index + 1}:{chunk.char_start}-{chunk.char_end}"


def _ensure_collection(client: QdrantClient) -> None:
    collections = client.get_collections().collections
    if any(collection.name == settings.qdrant_collection for collection in collections):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=models.VectorParams(
            size=settings.embedding_dimension,
            distance=models.Distance.COSINE,
        ),
    )
