export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth() {
  const response = await fetch(`${apiBaseUrl}/health`);
  if (!response.ok) {
    throw new Error("API health check failed");
  }
  return response.json();
}

export type GraphNode = {
  id: number;
  label: string;
  entity_type: string;
  mention_count: number;
  degree: number;
};

export type GraphEdge = {
  id: string;
  source: number;
  target: number;
  relationship_type: string;
  weight: number;
  confidence: number;
  document_ids: number[];
  evidence: string[];
  confidence_explanations: string[];
};

export type GraphMetrics = {
  node_count: number;
  edge_count: number;
  connected_component_count: number;
  density: number;
  top_entities: GraphNode[];
};

export type KnowledgeGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metrics: GraphMetrics;
};

export type AnalyticsSnapshot = {
  document_count: number;
  entity_count: number;
  relationship_count: number;
  file_type_counts: Record<string, number>;
  custodian_counts: Record<string, number>;
};

export type Matter = {
  id: number;
  name: string;
  description: string | null;
  client_name: string | null;
  matter_number: string | null;
  ai_external_allowed: boolean;
  ai_redaction_required: boolean;
  ai_allowed_modes: string[];
  created_at: string;
};

export type Custodian = {
  id: number;
  full_name: string;
  email: string | null;
  organization: string | null;
  role: string | null;
  created_at: string;
};

export type DocumentSummary = {
  id: number;
  matter_id: number | null;
  custodian_id: number | null;
  parent_document_id: number | null;
  attachment_filename: string | null;
  original_filename: string;
  file_type: string;
  document_type: string | null;
  subject: string | null;
  document_date: string | null;
  processing_status: string;
  tags: string[];
  issue_codes: string[];
  privilege_flag: boolean;
  review_status: string;
  processing_stages: Record<string, string>;
  processing_error: string | null;
  risk_score: number;
  created_at: string;
};

export type DocumentChunk = {
  id: number;
  document_id: number;
  chunk_index: number;
  text: string;
  char_start: number;
  char_end: number;
  token_count: number;
  vector_id: string | null;
  embedding_model: string | null;
};

export type DocumentEntityMention = {
  id: number;
  entity_id: number;
  entity_name: string;
  entity_type: string;
  chunk_id: number | null;
  mention_text: string;
  char_start: number;
  char_end: number;
  citation: string;
};

export type RelationshipSummary = {
  id: number;
  matter_id: number | null;
  source_entity_id: number;
  source_entity_name: string;
  relationship_type: string;
  target_entity_id: number;
  target_entity_name: string;
  document_id: number | null;
  confidence: number;
  evidence: string | null;
  confidence_explanation: string | null;
};

export type DocumentDetail = DocumentSummary & {
  stored_file_path: string;
  extracted_text: string | null;
  text_hash: string | null;
  extraction_warnings: string[];
  attachment_names: string[];
  ocr_status: string | null;
  sender: string | null;
  recipients: string | null;
  cc: string | null;
  bcc: string | null;
  notes: string | null;
  child_documents: DocumentSummary[];
  chunks: DocumentChunk[];
  entity_mentions: DocumentEntityMention[];
  relationships: RelationshipSummary[];
};

export type DocumentUploadResult = {
  id: number;
  original_filename: string;
  stored_file_path: string;
  file_type: string;
  content_type: string | null;
  size_bytes: number;
  processing_status: string;
};

export type SearchResult = {
  document_id: number;
  chunk_id: number;
  title: string;
  snippet: string;
  score: number;
  citation: string | null;
  source: string;
  diagnostics: {
    keyword_score: number;
    vector_score: number;
    metadata_score: number;
    phrase_matches: string[];
    required_terms: string[];
    excluded_terms: string[];
  };
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
  source: string;
};

export type SearchFilters = {
  matterId?: number;
  custodianId?: number;
  documentType?: string;
  fileType?: string;
  processingStatus?: string;
  tag?: string;
  issueCode?: string;
  privilegeFlag?: boolean;
  reviewStatus?: string;
  sender?: string;
  recipient?: string;
  sortBy?: "relevance" | "date" | "custodian" | "document_type";
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
};

export type SavedSearch = {
  id: number;
  matter_id: number | null;
  name: string;
  query: string;
  filters: Record<string, unknown> | null;
  created_by: string | null;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
};

export type AnalyticsBucket = {
  label: string;
  count: number;
};

export type TimelinePoint = {
  date: string;
  document_count: number;
};

export type CommunicationMetric = {
  source_entity_id: number;
  source_entity_name: string;
  target_entity_id: number;
  target_entity_name: string;
  message_count: number;
  document_ids: number[];
};

export type AnalyticsDashboard = {
  snapshot: AnalyticsSnapshot;
  document_timeline: TimelinePoint[];
  file_type_distribution: AnalyticsBucket[];
  document_type_distribution: AnalyticsBucket[];
  entity_type_distribution: AnalyticsBucket[];
  relationship_type_distribution: AnalyticsBucket[];
  top_custodians: AnalyticsBucket[];
  communication_pairs: CommunicationMetric[];
};

export type AISource = {
  document_id: number;
  chunk_id: number;
  title: string;
  snippet: string;
  score: number;
  citation: string;
};

export type GroundingSignal = {
  supported_terms: string[];
  unsupported_terms: string[];
  citation_count: number;
  valid_citation_count: number;
  unsupported_term_rate: number;
  hallucination_risk_score: number;
};

export type AIAnswer = {
  question: string;
  answer: string;
  answer_mode: string;
  provider: string;
  model: string | null;
  provider_enabled: boolean;
  redactions_applied: boolean;
  redaction_count: number;
  policy: Record<string, unknown>;
  citations: string[];
  sources: AISource[];
  grounding: GroundingSignal;
};

export type BenchmarkCase = {
  id: string;
  dataset_name: string;
  task_type: string;
  query: string;
  expected_terms: string[];
  minimum_citation_count: number;
  owner: string | null;
  triage_notes: string | null;
  expected_document_type: string | null;
  expected_document_date: string | null;
  expected_entities: string[];
  expected_relationships: string[];
  expected_ocr_terms: string[];
};

export type EvaluationMetric = {
  id: number | null;
  matter_id: number | null;
  dataset_name: string | null;
  case_id: string | null;
  task_type: string;
  metric_name: string;
  metric_value: number;
  details: Record<string, unknown> | null;
  created_at: string;
};

export type EvaluationRunResponse = {
  dataset_name: string;
  matter_id: number | null;
  metrics: EvaluationMetric[];
};

export type EvaluationSummary = {
  dataset_name: string | null;
  task_type: string | null;
  metric_name: string;
  run_count: number;
  latest_value: number;
  average_value: number;
  latest_created_at: string;
};

export type EvaluationTrendPoint = {
  metric_name: string;
  created_at: string;
  metric_value: number;
  dataset_name: string | null;
  case_id: string | null;
};

export type AuditLog = {
  id: number;
  actor: string | null;
  action: string;
  matter_id: number | null;
  document_id: number | null;
  entity_id: number | null;
  request_id: string | null;
  client_ip: string | null;
  user_agent: string | null;
  route: string | null;
  method: string | null;
  response_status: number | null;
  summary: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
};

export type AdminRole = {
  id: number;
  name: string;
  description: string | null;
  is_admin: boolean;
  created_at: string;
};

export type AdminUser = {
  id: number;
  email: string;
  display_name: string;
  role_id: number | null;
  role_name: string | null;
  organization: string | null;
  tenant_id: string | null;
  is_active: boolean;
  created_at: string;
};

export type AdminUserCreateResponse = {
  user: AdminUser;
  api_key: string;
};

export type AdminMembership = {
  id: number;
  user_id: number;
  user_email: string;
  matter_id: number;
  matter_name: string;
  role: string;
  created_at: string;
};

export type GraphFilters = {
  relationshipType?: string;
  matterId?: number;
  minConfidence?: number;
  entityLimit?: number;
  entityOffset?: number;
};

export async function getKnowledgeGraph(filters: GraphFilters = {}): Promise<KnowledgeGraph> {
  const params = new URLSearchParams();
  if (filters.relationshipType) {
    params.set("relationship_type", filters.relationshipType);
  }
  if (filters.matterId) {
    params.set("matter_id", String(filters.matterId));
  }
  if (filters.minConfidence !== undefined && filters.minConfidence > 0) {
    params.set("min_confidence", String(filters.minConfidence));
  }
  if (filters.entityLimit) {
    params.set("entity_limit", String(filters.entityLimit));
  }
  if (filters.entityOffset) {
    params.set("entity_offset", String(filters.entityOffset));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/graph${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Graph request failed");
  }
  return response.json();
}

export type AnalyticsFilters = {
  matterId?: number;
  custodianId?: number;
  dateFrom?: string;
  dateTo?: string;
};

export function analyticsExportUrl(filters: AnalyticsFilters = {}) {
  const params = analyticsParams(filters);
  const query = params.toString();
  return `${apiBaseUrl}/api/analytics/export.csv${query ? `?${query}` : ""}`;
}

export async function getAnalyticsDashboard(filters: AnalyticsFilters = {}): Promise<AnalyticsDashboard> {
  const params = analyticsParams(filters);
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/analytics/dashboard${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Analytics dashboard request failed");
  }
  return response.json();
}

function analyticsParams(filters: AnalyticsFilters) {
  const params = new URLSearchParams();
  if (filters.matterId) {
    params.set("matter_id", String(filters.matterId));
  }
  if (filters.custodianId) {
    params.set("custodian_id", String(filters.custodianId));
  }
  if (filters.dateFrom) {
    params.set("date_from", filters.dateFrom);
  }
  if (filters.dateTo) {
    params.set("date_to", filters.dateTo);
  }
  return params;
}

export async function getMatters(): Promise<Matter[]> {
  const response = await fetch(`${apiBaseUrl}/api/matters`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Matters request failed");
  }
  return response.json();
}

export async function createMatter(input: {
  name: string;
  description?: string;
  client_name?: string;
  matter_number?: string;
}): Promise<Matter> {
  const response = await fetch(`${apiBaseUrl}/api/matters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Matter creation failed");
  }
  return response.json();
}

export async function getCustodians(): Promise<Custodian[]> {
  const response = await fetch(`${apiBaseUrl}/api/custodians`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Custodians request failed");
  }
  return response.json();
}

export async function createCustodian(input: {
  full_name: string;
  email?: string;
  organization?: string;
  role?: string;
}): Promise<Custodian> {
  const response = await fetch(`${apiBaseUrl}/api/custodians`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Custodian creation failed");
  }
  return response.json();
}

export async function getDocuments(matterId?: number): Promise<DocumentSummary[]> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/documents${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Documents request failed");
  }
  return response.json();
}

export async function getDocument(documentId: number): Promise<DocumentDetail> {
  const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Document request failed");
  }
  return response.json();
}

export async function updateDocumentCoding(
  documentId: number,
  input: {
    tags?: string[];
    notes?: string | null;
    issue_codes?: string[];
    privilege_flag?: boolean;
    review_status?: string;
  },
): Promise<DocumentDetail> {
  const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/coding`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Document coding update failed");
  }
  return response.json();
}

export async function reprocessDocument(documentId: number, stage = "all"): Promise<DocumentDetail> {
  const path = stage === "all" ? "reprocess" : `retry/${stage}`;
  const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/${path}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Document reprocess failed");
  }
  return response.json();
}

export async function uploadDocument(input: {
  file: File;
  matterId?: number;
  custodianId?: number;
}): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.set("file", input.file);
  if (input.matterId) {
    formData.set("matter_id", String(input.matterId));
  }
  if (input.custodianId) {
    formData.set("custodian_id", String(input.custodianId));
  }
  const response = await fetch(`${apiBaseUrl}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error("Document upload failed");
  }
  return response.json();
}

export async function searchDocuments(input: {
  query: string;
} & SearchFilters): Promise<SearchResponse> {
  const body = {
    query: input.query,
    matter_id: input.matterId,
    custodian_id: input.custodianId,
    document_type: input.documentType || undefined,
    file_type: input.fileType || undefined,
    processing_status: input.processingStatus || undefined,
    tag: input.tag || undefined,
    issue_code: input.issueCode || undefined,
    privilege_flag: input.privilegeFlag,
    review_status: input.reviewStatus || undefined,
    sender: input.sender || undefined,
    recipient: input.recipient || undefined,
    sort_by: input.sortBy || "relevance",
    date_from: input.dateFrom || undefined,
    date_to: input.dateTo || undefined,
    limit: input.limit ?? 10,
  };
  const response = await fetch(`${apiBaseUrl}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Search request failed");
  }
  return response.json();
}

export async function getSavedSearches(matterId?: number): Promise<SavedSearch[]> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/search/saved${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Saved searches request failed");
  }
  return response.json();
}

export async function createSavedSearch(input: {
  name: string;
  query: string;
} & SearchFilters): Promise<SavedSearch> {
  const response = await fetch(`${apiBaseUrl}/api/search/saved`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      query: input.query,
      matter_id: input.matterId,
      custodian_id: input.custodianId,
      document_type: input.documentType || undefined,
      file_type: input.fileType || undefined,
      processing_status: input.processingStatus || undefined,
      tag: input.tag || undefined,
      issue_code: input.issueCode || undefined,
      privilege_flag: input.privilegeFlag,
      review_status: input.reviewStatus || undefined,
      sender: input.sender || undefined,
      recipient: input.recipient || undefined,
      sort_by: input.sortBy || "relevance",
      is_shared: false,
      date_from: input.dateFrom || undefined,
      date_to: input.dateTo || undefined,
      limit: input.limit ?? 10,
    }),
  });
  if (!response.ok) {
    throw new Error("Saved search creation failed");
  }
  return response.json();
}

export async function updateSavedSearch(
  savedSearchId: number,
  input: {
    name?: string;
    query?: string;
    is_shared?: boolean;
  } & SearchFilters,
): Promise<SavedSearch> {
  const response = await fetch(`${apiBaseUrl}/api/search/saved/${savedSearchId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      query: input.query,
      matter_id: input.matterId,
      custodian_id: input.custodianId,
      document_type: input.documentType || undefined,
      file_type: input.fileType || undefined,
      processing_status: input.processingStatus || undefined,
      tag: input.tag || undefined,
      issue_code: input.issueCode || undefined,
      privilege_flag: input.privilegeFlag,
      review_status: input.reviewStatus || undefined,
      sender: input.sender || undefined,
      recipient: input.recipient || undefined,
      sort_by: input.sortBy,
      is_shared: input.is_shared,
      date_from: input.dateFrom || undefined,
      date_to: input.dateTo || undefined,
      limit: input.limit,
    }),
  });
  if (!response.ok) {
    throw new Error("Saved search update failed");
  }
  return response.json();
}

export async function deleteSavedSearch(savedSearchId: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/search/saved/${savedSearchId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Saved search deletion failed");
  }
}

export async function runSavedSearch(savedSearchId: number): Promise<SearchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/search/saved/${savedSearchId}/run`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Saved search run failed");
  }
  return response.json();
}

export async function askAssistant(input: {
  question: string;
  limit?: number;
  matterId?: number;
  answerMode?: string;
  applyRedactions?: boolean;
}): Promise<AIAnswer> {
  const response = await fetch(`${apiBaseUrl}/api/ai/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: input.question,
      limit: input.limit ?? 5,
      matter_id: input.matterId,
      answer_mode: input.answerMode ?? "summary",
      apply_redactions: input.applyRedactions ?? true,
    }),
  });
  if (!response.ok) {
    throw new Error("AI answer request failed");
  }
  return response.json();
}

export async function getBenchmarks(datasetName?: string): Promise<BenchmarkCase[]> {
  const params = new URLSearchParams();
  if (datasetName) {
    params.set("dataset_name", datasetName);
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/evaluation/benchmarks${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Benchmark request failed");
  }
  return response.json();
}

export async function getEvaluationMetrics(matterId?: number): Promise<EvaluationMetric[]> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/evaluation/metrics${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Evaluation metrics request failed");
  }
  return response.json();
}

export async function getEvaluationSummaries(matterId?: number): Promise<EvaluationSummary[]> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/evaluation/summaries${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Evaluation summaries request failed");
  }
  return response.json();
}

export async function getEvaluationTrends(metricName?: string, matterId?: number): Promise<EvaluationTrendPoint[]> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  if (metricName) {
    params.set("metric_name", metricName);
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/evaluation/trends${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Evaluation trends request failed");
  }
  return response.json();
}

export async function runEvaluation(input: {
  matterId?: number;
  datasetName: string;
  taskType: "retrieval" | "answer" | "extraction" | "all";
  limit: number;
}): Promise<EvaluationRunResponse> {
  const response = await fetch(`${apiBaseUrl}/api/evaluation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      matter_id: input.matterId,
      dataset_name: input.datasetName,
      task_type: input.taskType,
      limit: input.limit,
    }),
  });
  if (!response.ok) {
    throw new Error("Evaluation run failed");
  }
  return response.json();
}

export type AuditFilters = {
  matterId?: number;
  documentId?: number;
  actor?: string;
  action?: string;
  requestId?: string;
  method?: string;
  route?: string;
  responseStatus?: number;
  createdFrom?: string;
  createdTo?: string;
  limit?: number;
};

export function auditQueryString(filters: AuditFilters, format?: "csv" | "json") {
  const params = new URLSearchParams();
  if (filters.matterId) {
    params.set("matter_id", String(filters.matterId));
  }
  if (filters.documentId) {
    params.set("document_id", String(filters.documentId));
  }
  if (filters.actor) {
    params.set("event_actor", filters.actor);
  }
  if (filters.action) {
    params.set("action", filters.action);
  }
  if (filters.requestId) {
    params.set("request_id", filters.requestId);
  }
  if (filters.method) {
    params.set("method", filters.method);
  }
  if (filters.route) {
    params.set("route", filters.route);
  }
  if (filters.responseStatus) {
    params.set("response_status", String(filters.responseStatus));
  }
  if (filters.createdFrom) {
    params.set("created_from", filters.createdFrom);
  }
  if (filters.createdTo) {
    params.set("created_to", filters.createdTo);
  }
  if (filters.limit) {
    params.set("limit", String(filters.limit));
  }
  if (format) {
    params.set("format", format);
  }
  return params.toString();
}

export async function getAuditLogs(filters: AuditFilters = {}): Promise<AuditLog[]> {
  const query = auditQueryString(filters);
  const response = await fetch(`${apiBaseUrl}/api/audit${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Audit request failed");
  }
  return response.json();
}

export async function getAdminRoles(): Promise<AdminRole[]> {
  const response = await fetch(`${apiBaseUrl}/api/admin/roles`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Admin roles request failed");
  }
  return response.json();
}

export async function createAdminRole(input: {
  name: string;
  description?: string;
  is_admin: boolean;
}): Promise<AdminRole> {
  const response = await fetch(`${apiBaseUrl}/api/admin/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Admin role creation failed");
  }
  return response.json();
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await fetch(`${apiBaseUrl}/api/admin/users`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Admin users request failed");
  }
  return response.json();
}

export async function createAdminUser(input: {
  email: string;
  display_name: string;
  role_id?: number;
  organization?: string;
  tenant_id?: string;
  is_active: boolean;
}): Promise<AdminUserCreateResponse> {
  const response = await fetch(`${apiBaseUrl}/api/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Admin user creation failed");
  }
  return response.json();
}

export async function updateAdminUser(
  userId: number,
  input: {
    display_name?: string;
    role_id?: number | null;
    organization?: string | null;
    tenant_id?: string | null;
    is_active?: boolean;
  },
): Promise<AdminUser> {
  const response = await fetch(`${apiBaseUrl}/api/admin/users/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Admin user update failed");
  }
  return response.json();
}

export async function rotateAdminUserKey(userId: number): Promise<AdminUserCreateResponse> {
  const response = await fetch(`${apiBaseUrl}/api/admin/users/${userId}/rotate-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    throw new Error("Admin user key rotation failed");
  }
  return response.json();
}

export async function getAdminMemberships(): Promise<AdminMembership[]> {
  const response = await fetch(`${apiBaseUrl}/api/admin/memberships`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Admin memberships request failed");
  }
  return response.json();
}

export async function createAdminMembership(input: {
  user_id: number;
  matter_id: number;
  role: string;
}): Promise<AdminMembership> {
  const response = await fetch(`${apiBaseUrl}/api/admin/memberships`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Admin membership creation failed");
  }
  return response.json();
}

export async function updateAdminMembership(membershipId: number, role: string): Promise<AdminMembership> {
  const response = await fetch(`${apiBaseUrl}/api/admin/memberships/${membershipId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!response.ok) {
    throw new Error("Admin membership update failed");
  }
  return response.json();
}

export async function deleteAdminMembership(membershipId: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/admin/memberships/${membershipId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Admin membership deletion failed");
  }
}
