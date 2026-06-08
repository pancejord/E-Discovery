from datetime import datetime

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    custodian: str | None = None
    classification: str | None = None
    created_at: datetime


class DocumentIngestionResult(BaseModel):
    filename: str
    content_type: str | None
    size_bytes: int
    status: str = "received"
    next_step: str = "Add parser, metadata extraction, and persistence."


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    matter_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    document_id: str
    title: str
    snippet: str
    score: float
    citation: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class EntitySummary(BaseModel):
    id: str
    name: str
    entity_type: str
    mention_count: int = 0


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
