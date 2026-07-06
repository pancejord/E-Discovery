from datetime import datetime
import json

from pydantic import BaseModel, Field, field_validator


class MatterRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    client_name: str | None = None
    matter_number: str | None = None
    ai_external_allowed: bool = False
    ai_redaction_required: bool = True
    ai_allowed_modes: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("ai_allowed_modes", mode="before")
    @classmethod
    def parse_ai_allowed_modes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return []
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        return []


class MatterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    client_name: str | None = Field(default=None, max_length=255)
    matter_number: str | None = Field(default=None, max_length=100)
    ai_external_allowed: bool = False
    ai_redaction_required: bool = True
    ai_allowed_modes: list[str] = Field(default_factory=list)


class MatterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    client_name: str | None = Field(default=None, max_length=255)
    matter_number: str | None = Field(default=None, max_length=100)
    ai_external_allowed: bool | None = None
    ai_redaction_required: bool | None = None
    ai_allowed_modes: list[str] | None = None


class CustodianRead(BaseModel):
    id: int
    full_name: str
    email: str | None = None
    organization: str | None = None
    role: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustodianCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, max_length=255)


class CustodianUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, max_length=255)


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_admin: bool = False


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserRead(BaseModel):
    id: int
    email: str
    display_name: str
    role_id: int | None = None
    role_name: str | None = None
    organization: str | None = None
    tenant_id: str | None = None
    is_active: bool
    created_at: datetime


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    role_id: int | None = None
    organization: str | None = Field(default=None, max_length=255)
    tenant_id: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, min_length=12, max_length=255)
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    role_id: int | None = None
    organization: str | None = Field(default=None, max_length=255)
    tenant_id: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class AdminUserCreateResponse(BaseModel):
    user: AdminUserRead
    api_key: str


class ApiKeyRotationRequest(BaseModel):
    api_key: str | None = Field(default=None, min_length=12, max_length=255)


class ApiKeyRotationResponse(BaseModel):
    user: AdminUserRead
    api_key: str


class MatterMembershipCreate(BaseModel):
    user_id: int
    matter_id: int
    role: str = Field(default="reviewer", min_length=1, max_length=100)


class MatterMembershipUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=100)


class MatterMembershipRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    matter_id: int
    matter_name: str
    role: str
    created_at: datetime


class DocumentSummary(BaseModel):
    id: int
    matter_id: int | None = None
    custodian_id: int | None = None
    parent_document_id: int | None = None
    attachment_filename: str | None = None
    original_filename: str
    file_type: str
    document_type: str | None = None
    subject: str | None = None
    document_date: datetime | None = None
    processing_status: str
    tags: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    privilege_flag: bool = False
    review_status: str = "unreviewed"
    processing_stages: dict[str, str] = Field(default_factory=dict)
    processing_error: str | None = None
    risk_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


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


class DocumentCodingUpdate(BaseModel):
    tags: list[str] | None = None
    notes: str | None = None
    issue_codes: list[str] | None = None
    privilege_flag: bool | None = None
    review_status: str | None = Field(default=None, max_length=100)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    matter_id: int | None = None
    custodian_id: int | None = None
    document_type: str | None = None
    file_type: str | None = None
    processing_status: str | None = None
    tag: str | None = None
    issue_code: str | None = None
    privilege_flag: bool | None = None
    review_status: str | None = None
    sender: str | None = None
    recipient: str | None = None
    saved_search_owner: str | None = None
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|custodian|document_type)$")
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchDiagnostics(BaseModel):
    keyword_score: float = 0
    vector_score: float = 0
    metadata_score: float = 0
    phrase_matches: list[str] = Field(default_factory=list)
    required_terms: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    document_id: int
    chunk_id: int
    title: str
    snippet: str
    score: float
    citation: str | None = None
    source: str = "local"
    diagnostics: SearchDiagnostics = Field(default_factory=SearchDiagnostics)


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    source: str = "local"


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    query: str = Field(min_length=1, max_length=1000)
    matter_id: int | None = None
    custodian_id: int | None = None
    document_type: str | None = None
    file_type: str | None = None
    processing_status: str | None = None
    tag: str | None = None
    issue_code: str | None = None
    privilege_flag: bool | None = None
    review_status: str | None = None
    sender: str | None = None
    recipient: str | None = None
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|custodian|document_type)$")
    is_shared: bool = False
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=10, ge=1, le=100)


class SavedSearchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    query: str | None = Field(default=None, min_length=1, max_length=1000)
    matter_id: int | None = None
    custodian_id: int | None = None
    document_type: str | None = None
    file_type: str | None = None
    processing_status: str | None = None
    tag: str | None = None
    issue_code: str | None = None
    privilege_flag: bool | None = None
    review_status: str | None = None
    sender: str | None = None
    recipient: str | None = None
    sort_by: str | None = Field(default=None, pattern="^(relevance|date|custodian|document_type)$")
    is_shared: bool | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int | None = Field(default=None, ge=1, le=100)


class SavedSearchRead(BaseModel):
    id: int
    matter_id: int | None = None
    name: str
    query: str
    filters: dict | None = None
    created_by: str | None = None
    is_shared: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntitySummary(BaseModel):
    id: int
    matter_id: int | None = None
    name: str
    entity_type: str
    normalized_name: str
    alias_of_entity_id: int | None = None
    review_status: str = "unreviewed"
    extraction_provider: str | None = None
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


class DocumentEntityMention(BaseModel):
    id: int
    entity_id: int
    entity_name: str
    entity_type: str
    chunk_id: int | None = None
    mention_text: str
    char_start: int
    char_end: int
    citation: str


class EntityDetail(EntitySummary):
    mentions: list[EntityMentionRead] = Field(default_factory=list)


class EntityMergeRequest(BaseModel):
    target_entity_id: int


class EntitySplitRequest(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    entity_type: str = Field(min_length=1, max_length=100)
    mention_ids: list[int] = Field(min_length=1)


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
    confidence_explanation: str | None = None


class DocumentDetail(DocumentSummary):
    stored_file_path: str
    extracted_text: str | None = None
    text_hash: str | None = None
    extraction_warnings: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)
    ocr_status: str | None = None
    notes: str | None = None
    sender: str | None = None
    recipients: str | None = None
    cc: str | None = None
    bcc: str | None = None
    child_documents: list[DocumentSummary] = Field(default_factory=list)
    chunks: list[ChunkRead] = Field(default_factory=list)
    entity_mentions: list[DocumentEntityMention] = Field(default_factory=list)
    relationships: list[RelationshipSummary] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: int
    label: str
    entity_type: str
    mention_count: int = 0
    degree: int = 0


class GraphEdge(BaseModel):
    id: str
    source: int
    target: int
    relationship_type: str
    weight: int = 1
    confidence: float
    document_ids: list[int] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence_explanations: list[str] = Field(default_factory=list)


class GraphMetrics(BaseModel):
    node_count: int
    edge_count: int
    connected_component_count: int
    density: float
    top_entities: list[GraphNode] = Field(default_factory=list)


class KnowledgeGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metrics: GraphMetrics


class GraphPathResponse(BaseModel):
    source_entity_id: int
    target_entity_id: int
    paths: list[list[GraphNode]]


class AnalyticsSnapshot(BaseModel):
    document_count: int
    entity_count: int
    relationship_count: int
    file_type_counts: dict[str, int]
    custodian_counts: dict[str, int]


class AnalyticsBucket(BaseModel):
    label: str
    count: int


class TimelinePoint(BaseModel):
    date: str
    document_count: int


class CommunicationMetric(BaseModel):
    source_entity_id: int
    source_entity_name: str
    target_entity_id: int
    target_entity_name: str
    message_count: int
    document_ids: list[int] = Field(default_factory=list)


class AnalyticsDashboard(BaseModel):
    snapshot: AnalyticsSnapshot
    document_timeline: list[TimelinePoint] = Field(default_factory=list)
    file_type_distribution: list[AnalyticsBucket] = Field(default_factory=list)
    document_type_distribution: list[AnalyticsBucket] = Field(default_factory=list)
    entity_type_distribution: list[AnalyticsBucket] = Field(default_factory=list)
    relationship_type_distribution: list[AnalyticsBucket] = Field(default_factory=list)
    top_custodians: list[AnalyticsBucket] = Field(default_factory=list)
    communication_pairs: list[CommunicationMetric] = Field(default_factory=list)


class EvaluationMetric(BaseModel):
    id: int | None = None
    matter_id: int | None = None
    dataset_name: str | None = None
    case_id: str | None = None
    task_type: str
    metric_name: str
    metric_value: float
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BenchmarkCase(BaseModel):
    id: str
    dataset_name: str
    task_type: str
    query: str
    expected_terms: list[str] = Field(default_factory=list)
    minimum_citation_count: int = 1
    owner: str | None = None
    triage_notes: str | None = None
    expected_document_type: str | None = None
    expected_document_date: str | None = None
    expected_entities: list[str] = Field(default_factory=list)
    expected_relationships: list[str] = Field(default_factory=list)
    expected_ocr_terms: list[str] = Field(default_factory=list)


class EvaluationSummary(BaseModel):
    dataset_name: str | None = None
    task_type: str | None = None
    metric_name: str
    run_count: int
    latest_value: float
    average_value: float
    latest_created_at: datetime


class EvaluationTrendPoint(BaseModel):
    metric_name: str
    created_at: datetime
    metric_value: float
    dataset_name: str | None = None
    case_id: str | None = None


class EvaluationRunRequest(BaseModel):
    matter_id: int | None = None
    dataset_name: str = "phase6_synthetic_retrieval"
    task_type: str = Field(default="retrieval", pattern="^(retrieval|answer|extraction|all)$")
    limit: int = Field(default=10, ge=1, le=50)


class EvaluationRunResponse(BaseModel):
    dataset_name: str
    matter_id: int | None = None
    metrics: list[EvaluationMetric] = Field(default_factory=list)


class HallucinationCheckRequest(BaseModel):
    answer: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)


class HallucinationCheckResponse(BaseModel):
    supported_terms: list[str] = Field(default_factory=list)
    unsupported_terms: list[str] = Field(default_factory=list)
    citation_count: int
    valid_citation_count: int
    unsupported_term_rate: float
    hallucination_risk_score: float


class AISource(BaseModel):
    document_id: int
    chunk_id: int
    title: str
    snippet: str
    score: float
    citation: str


class AIAnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    matter_id: int | None = None
    limit: int = Field(default=5, ge=1, le=20)
    answer_mode: str = Field(default="summary", pattern="^(summary|chronology|issues|contradiction|privilege|deposition)$")
    apply_redactions: bool = True


class AIAnswerResponse(BaseModel):
    question: str
    answer: str
    answer_mode: str = "summary"
    provider: str
    model: str | None = None
    provider_enabled: bool
    redactions_applied: bool = False
    redaction_count: int = 0
    policy: dict = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)
    sources: list[AISource] = Field(default_factory=list)
    grounding: HallucinationCheckResponse


class AuditLogRead(BaseModel):
    id: int
    actor: str | None = None
    action: str
    matter_id: int | None = None
    document_id: int | None = None
    entity_id: int | None = None
    request_id: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    route: str | None = None
    method: str | None = None
    response_status: int | None = None
    summary: str | None = None
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
