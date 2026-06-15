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

export async function getKnowledgeGraph(relationshipType?: string): Promise<KnowledgeGraph> {
  const params = new URLSearchParams();
  if (relationshipType) {
    params.set("relationship_type", relationshipType);
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

export async function getAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  const response = await fetch(`${apiBaseUrl}/api/analytics/dashboard`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Analytics dashboard request failed");
  }
  return response.json();
}

export async function askAssistant(question: string, limit = 5): Promise<AIAnswer> {
  const response = await fetch(`${apiBaseUrl}/api/ai/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  });
  if (!response.ok) {
    throw new Error("AI answer request failed");
  }
  return response.json();
}
