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
  original_filename: string;
  file_type: string;
  document_type: string | null;
  subject: string | null;
  document_date: string | null;
  processing_status: string;
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
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
  source: string;
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
  provider: string;
  model: string | null;
  provider_enabled: boolean;
  citations: string[];
  sources: AISource[];
  grounding: GroundingSignal;
};

export async function getKnowledgeGraph(
  relationshipType?: string,
  matterId?: number,
  minConfidence?: number,
): Promise<KnowledgeGraph> {
  const params = new URLSearchParams();
  if (relationshipType) {
    params.set("relationship_type", relationshipType);
  }
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  if (minConfidence !== undefined && minConfidence > 0) {
    params.set("min_confidence", String(minConfidence));
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

export async function getAnalyticsDashboard(matterId?: number): Promise<AnalyticsDashboard> {
  const params = new URLSearchParams();
  if (matterId) {
    params.set("matter_id", String(matterId));
  }
  const query = params.toString();
  const response = await fetch(`${apiBaseUrl}/api/analytics/dashboard${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Analytics dashboard request failed");
  }
  return response.json();
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
  matterId?: number;
  limit?: number;
}): Promise<SearchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: input.query,
      matter_id: input.matterId,
      limit: input.limit ?? 10,
    }),
  });
  if (!response.ok) {
    throw new Error("Search request failed");
  }
  return response.json();
}

export async function askAssistant(question: string, limit = 5, matterId?: number): Promise<AIAnswer> {
  const response = await fetch(`${apiBaseUrl}/api/ai/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit, matter_id: matterId }),
  });
  if (!response.ok) {
    throw new Error("AI answer request failed");
  }
  return response.json();
}
