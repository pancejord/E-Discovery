from datetime import datetime

from pydantic import BaseModel, Field


class MatterRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    client_name: str | None = None
    matter_number: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustodianRead(BaseModel):
    id: int
    full_name: str
    email: str | None = None
    organization: str | None = None
    role: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentSummary(BaseModel):
    id: int
    matter_id: int | None = None
    custodian_id: int | None = None
    original_filename: str
    file_type: str
    document_type: str | None = None
    subject: str | None = None
    document_date: datetime | None = None
    processing_status: str
    risk_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentSummary):
    stored_file_path: str
    extracted_text: str | None = None
    text_hash: str | None = None
    sender: str | None = None
    recipients: str | None = None
    cc: str | None = None
    bcc: str | None = None


class ChunkRead(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    token_count: int
    vector_id: str | None = None
    embedding_model: str | None = None

    model_config = {"from_attributes": True}


class DocumentIngestionResult(BaseModel):
    id: int
    original_filename: str
    stored_file_path: str
    file_type: str
    content_type: str | None
    size_bytes: int
    processing_status: str = "uploaded"


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    matter_id: int | None = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    document_id: int
    chunk_id: int
    title: str
    snippet: str
    score: float
    citation: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class EntitySummary(BaseModel):
    id: int
    matter_id: int | None = None
    name: str
    entity_type: str
    normalized_name: str
    mention_count: int = 0


class EntityMentionRead(BaseModel):
    id: int
    document_id: int
    chunk_id: int | None = None
    mention_text: str
    char_start: int
    char_end: int
    citation: str

    model_config = {"from_attributes": True}


class EntityDetail(EntitySummary):
    mentions: list[EntityMentionRead] = Field(default_factory=list)


class RelationshipSummary(BaseModel):
    id: int
    matter_id: int | None = None
    source_entity_id: int
    source_entity_name: str
    relationship_type: str
    target_entity_id: int
    target_entity_name: str
    document_id: int | None = None
    confidence: float
    evidence: str | None = None


class AnalyticsSnapshot(BaseModel):
    document_count: int
    entity_count: int
    relationship_count: int
    file_type_counts: dict[str, int]
    custodian_counts: dict[str, int]


class EvaluationMetric(BaseModel):
    task_type: str
    metric_name: str
    metric_value: float
    created_at: datetime
