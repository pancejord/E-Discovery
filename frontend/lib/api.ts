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
