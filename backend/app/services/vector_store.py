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
                    "custodian_id": document.custodian_id,
                    "document_type": document.document_type,
                    "file_type": document.file_type,
                    "processing_status": document.processing_status,
                    "tags": _json_list(document.tags),
                    "issue_codes": _json_list(document.issue_codes),
                    "privilege_flag": document.privilege_flag,
                    "review_status": document.review_status,
                    "sender": document.sender,
                    "recipients": document.recipients,
                    "document_date": document.document_date.isoformat() if document.document_date else None,
                    "filename": document.original_filename,
                    "citation": citation_for_chunk(document, chunk),
                },
            )
        ],
    )


def query_chunks(
    query_vector: list[float],
    matter_id: int | None = None,
    matter_ids: list[int] | None = None,
    limit: int = 10,
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
) -> list[dict]:
    if not settings.qdrant_enabled:
        return []

    client = QdrantClient(url=settings.qdrant_url, timeout=2)
    _ensure_collection(client)
    query_filter = _payload_filter(
        matter_id=matter_id,
        matter_ids=matter_ids,
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
    search_limit = limit
    if matter_ids:
        search_limit = max(limit, min(limit * len(matter_ids), 100))

    if hasattr(client, "query_points"):
        result = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            query_filter=query_filter,
            limit=search_limit,
            with_payload=True,
        )
        points = getattr(result, "points", result)
    else:
        points = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=search_limit,
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
    return hydrated[:limit]


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


def _payload_filter(
    matter_id: int | None,
    matter_ids: list[int] | None,
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
) -> models.Filter | None:
    conditions = []
    if matter_id is not None:
        conditions.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)))
    elif matter_ids is not None:
        conditions.append(models.FieldCondition(key="matter_id", match=models.MatchAny(any=matter_ids)))
    if custodian_id is not None:
        conditions.append(models.FieldCondition(key="custodian_id", match=models.MatchValue(value=custodian_id)))
    if document_type:
        conditions.append(models.FieldCondition(key="document_type", match=models.MatchValue(value=document_type)))
    if file_type:
        conditions.append(models.FieldCondition(key="file_type", match=models.MatchValue(value=file_type.lower().lstrip("."))))
    if processing_status:
        conditions.append(models.FieldCondition(key="processing_status", match=models.MatchValue(value=processing_status)))
    if tag:
        conditions.append(models.FieldCondition(key="tags", match=models.MatchAny(any=[tag])))
    if issue_code:
        conditions.append(models.FieldCondition(key="issue_codes", match=models.MatchAny(any=[issue_code])))
    if privilege_flag is not None:
        conditions.append(models.FieldCondition(key="privilege_flag", match=models.MatchValue(value=privilege_flag)))
    if review_status:
        conditions.append(models.FieldCondition(key="review_status", match=models.MatchValue(value=review_status)))
    if sender:
        conditions.append(models.FieldCondition(key="sender", match=models.MatchText(text=sender)))
    if recipient:
        conditions.append(models.FieldCondition(key="recipients", match=models.MatchText(text=recipient)))
    if date_from is not None:
        conditions.append(models.FieldCondition(key="document_date", range=models.DatetimeRange(gte=date_from)))
    if date_to is not None:
        conditions.append(models.FieldCondition(key="document_date", range=models.DatetimeRange(lte=date_to)))
    if not conditions:
        return None
    return models.Filter(must=conditions)


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    import json

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []
