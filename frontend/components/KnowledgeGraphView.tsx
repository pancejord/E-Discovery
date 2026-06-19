"use client";

import { RefreshCw, Share2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  getKnowledgeGraph,
  getMatters,
  type GraphEdge,
  type GraphNode,
  type KnowledgeGraph,
  type Matter,
} from "../lib/api";

const relationshipOptions = [
  { label: "All", value: "" },
  { label: "Mentioned With", value: "mentioned_with" },
  { label: "Communicated With", value: "communicated_with" },
];

const entityColors: Record<string, string> = {
  PERSON: "#1D6F6B",
  ORGANIZATION: "#6D5BD0",
  EMAIL_ADDRESS: "#2F80ED",
  DATE: "#B7791F",
  MONEY: "#0F766E",
  LEGAL_REFERENCE: "#9F1239",
  LOCATION: "#047857",
};

type PositionedNode = GraphNode & {
  x: number;
  y: number;
};

export function KnowledgeGraphView() {
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [relationshipType, setRelationshipType] = useState("");
  const [entityType, setEntityType] = useState("");
  const [entityQuery, setEntityQuery] = useState("");
  const [minConfidence, setMinConfidence] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadGraph(
    nextRelationshipType = relationshipType,
    nextMatterId = matterId,
    nextMinConfidence = minConfidence,
  ) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getKnowledgeGraph(nextRelationshipType || undefined, nextMatterId, nextMinConfidence);
      setGraph(data);
      setSelectedNodeId(data.nodes[0]?.id ?? null);
    } catch {
      setError("Unable to load graph data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void getMatters()
      .then((rows) => {
        setMatters(rows);
        if (rows.length > 0) {
          setMatterId(rows[0].id);
          void loadGraph("", rows[0].id);
          return;
        }
        void loadGraph("");
      })
      .catch(() => void loadGraph(""));
  }, []);

  const positionedNodes = useMemo(() => positionNodes(graph?.nodes ?? []), [graph]);
  const entityTypes = useMemo(
    () => Array.from(new Set((graph?.nodes ?? []).map((node) => node.entity_type))).sort(),
    [graph],
  );
  const filteredNodes = useMemo(
    () =>
      positionedNodes.filter((node) => {
        const matchesType = !entityType || node.entity_type === entityType;
        const matchesQuery = !entityQuery || node.label.toLowerCase().includes(entityQuery.toLowerCase());
        return matchesType && matchesQuery;
      }),
    [positionedNodes, entityQuery, entityType],
  );
  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((node) => node.id)), [filteredNodes]);
  const filteredEdges = useMemo(
    () =>
      (graph?.edges ?? []).filter(
        (edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target),
      ),
    [graph, filteredNodeIds],
  );
  const nodeById = useMemo(
    () => new Map(filteredNodes.map((node) => [node.id, node])),
    [filteredNodes],
  );
  const selectedNode = selectedNodeId ? nodeById.get(selectedNodeId) : null;
  const selectedEdges = useMemo(
    () =>
      selectedNodeId && selectedNode
        ? (graph?.edges ?? []).filter((edge) => edge.source === selectedNodeId || edge.target === selectedNodeId)
        : [],
    [graph, selectedNode, selectedNodeId],
  );

  function handleRelationshipChange(value: string) {
    setRelationshipType(value);
    void loadGraph(value, matterId, minConfidence);
  }

  return (
    <main className="min-h-screen bg-panel">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">Knowledge Graph</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Entity relationships</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={matterId ?? ""}
              onChange={(event) => {
                const nextMatterId = event.target.value ? Number(event.target.value) : undefined;
                setMatterId(nextMatterId);
                void loadGraph(relationshipType, nextMatterId, minConfidence);
              }}
              aria-label="Matter"
            >
              <option value="">All matters</option>
              {matters.map((matter) => (
                <option key={matter.id} value={matter.id}>
                  {matter.name}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={relationshipType}
              onChange={(event) => handleRelationshipChange(event.target.value)}
              aria-label="Relationship type"
            >
              {relationshipOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={entityType}
              onChange={(event) => setEntityType(event.target.value)}
              aria-label="Entity type"
            >
              <option value="">All entity types</option>
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <input
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={entityQuery}
              onChange={(event) => setEntityQuery(event.target.value)}
              placeholder="Find entity"
              aria-label="Find entity"
            />
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={minConfidence}
              onChange={(event) => {
                const nextConfidence = Number(event.target.value);
                setMinConfidence(nextConfidence);
                void loadGraph(relationshipType, matterId, nextConfidence);
              }}
              aria-label="Minimum confidence"
            >
              <option value={0}>Any confidence</option>
              <option value={0.5}>0.5+</option>
              <option value={0.75}>0.75+</option>
              <option value={0.9}>0.9+</option>
            </select>
            <button
              className="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-semibold text-white"
              onClick={() => void loadGraph()}
              type="button"
              title="Refresh graph"
            >
              <RefreshCw size={17} />
              Refresh
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-5 lg:grid-cols-[1fr_320px]">
        <div className="min-h-[640px] rounded-md border border-line bg-white">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Share2 size={17} />
              Network
            </div>
            {graph && (
              <div className="text-sm text-slate-600">
                {filteredNodes.length} nodes / {filteredEdges.length} edges
              </div>
            )}
          </div>
          <GraphCanvas
            edges={filteredEdges}
            nodes={filteredNodes}
            nodeById={nodeById}
            selectedNodeId={selectedNodeId}
            isLoading={isLoading}
            error={error}
            onSelectNode={setSelectedNodeId}
          />
        </div>

        <aside className="rounded-md border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Graph Metrics</h2>
          </div>
          <div className="grid grid-cols-2 gap-3 p-4">
            <Metric label="Nodes" value={graph?.metrics.node_count ?? 0} />
            <Metric label="Edges" value={graph?.metrics.edge_count ?? 0} />
            <Metric label="Components" value={graph?.metrics.connected_component_count ?? 0} />
            <Metric label="Density" value={graph?.metrics.density ?? 0} />
          </div>

          <div className="border-t border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Selected Entity</h2>
            {selectedNode ? (
              <div className="mt-3 space-y-2 text-sm text-slate-700">
                <p className="font-semibold text-ink">{selectedNode.label}</p>
                <p>{selectedNode.entity_type}</p>
                <p>{selectedNode.mention_count} mentions</p>
                <p>{selectedNode.degree} connections</p>
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-600">No entity selected</p>
            )}
          </div>

          <div className="border-t border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Selected Relationships</h2>
            <div className="mt-3 space-y-2">
              {selectedEdges.length === 0 ? (
                <p className="text-sm text-slate-600">No relationships selected</p>
              ) : (
                selectedEdges.slice(0, 8).map((edge) => {
                  const source = (graph?.nodes ?? []).find((node) => node.id === edge.source);
                  const target = (graph?.nodes ?? []).find((node) => node.id === edge.target);
                  return (
                    <article key={edge.id} className="rounded-md border border-line bg-panel p-3 text-sm">
                      <p className="font-semibold text-ink">
                        {source?.label ?? edge.source} {edge.relationship_type.replaceAll("_", " ")}{" "}
                        {target?.label ?? edge.target}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
                        <span>weight {edge.weight}</span>
                        <span>confidence {edge.confidence}</span>
                        {edge.document_ids.slice(0, 4).map((documentId) => (
                          <Link key={documentId} className="font-semibold text-accent" href={`/documents/${documentId}`}>
                            doc {documentId}
                          </Link>
                        ))}
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>

          <div className="border-t border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Top Entities</h2>
            <div className="mt-3 space-y-2">
              {filteredNodes
                .slice()
                .sort((left, right) => right.degree - left.degree || right.mention_count - left.mention_count)
                .slice(0, 6)
                .map((node) => (
                  <button
                    key={node.id}
                    className="flex w-full items-center justify-between rounded-md border border-line px-3 py-2 text-left text-sm hover:bg-panel"
                    onClick={() => setSelectedNodeId(node.id)}
                    type="button"
                  >
                    <span className="font-medium text-ink">{node.label}</span>
                    <span className="text-slate-500">{node.degree}</span>
                  </button>
                ))}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}

function GraphCanvas({
  edges,
  nodes,
  nodeById,
  selectedNodeId,
  isLoading,
  error,
  onSelectNode,
}: {
  edges: GraphEdge[];
  nodes: PositionedNode[];
  nodeById: Map<number, PositionedNode>;
  selectedNodeId: number | null;
  isLoading: boolean;
  error: string | null;
  onSelectNode: (nodeId: number) => void;
}) {
  if (isLoading) {
    return <div className="flex h-[584px] items-center justify-center text-sm text-slate-600">Loading graph</div>;
  }

  if (error) {
    return <div className="flex h-[584px] items-center justify-center text-sm text-rose-700">{error}</div>;
  }

  if (nodes.length === 0) {
    return <div className="flex h-[584px] items-center justify-center text-sm text-slate-600">No graph data</div>;
  }

  return (
    <svg className="h-[584px] w-full" viewBox="0 0 900 584" role="img" aria-label="Knowledge graph">
      <rect width="900" height="584" fill="#ffffff" />
      {edges.map((edge) => {
        const source = nodeById.get(edge.source);
        const target = nodeById.get(edge.target);
        if (!source || !target) {
          return null;
        }
        const isSelected = selectedNodeId === source.id || selectedNodeId === target.id;
        return (
          <line
            key={edge.id}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            stroke={isSelected ? "#17202A" : "#AAB4C0"}
            strokeWidth={Math.min(5, 1 + edge.weight)}
            opacity={isSelected ? 0.9 : 0.55}
          />
        );
      })}
      {nodes.map((node) => {
        const radius = Math.min(28, 12 + node.degree * 2);
        const isSelected = selectedNodeId === node.id;
        return (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            role="button"
            tabIndex={0}
            aria-label={node.label}
            onClick={() => onSelectNode(node.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                onSelectNode(node.id);
              }
            }}
          >
            <circle
              r={radius}
              fill={entityColors[node.entity_type] ?? "#64748B"}
              stroke={isSelected ? "#17202A" : "#ffffff"}
              strokeWidth={isSelected ? 4 : 2}
            />
            <text
              y={radius + 16}
              textAnchor="middle"
              className="fill-ink text-[12px] font-semibold"
            >
              {shortLabel(node.label)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-panel p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function positionNodes(nodes: GraphNode[]): PositionedNode[] {
  const centerX = 450;
  const centerY = 292;
  const radius = 210;
  return nodes.map((node, index) => {
    const angle = nodes.length === 1 ? 0 : (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
    const degreeOffset = Math.min(50, node.degree * 6);
    return {
      ...node,
      x: centerX + Math.cos(angle) * (radius - degreeOffset),
      y: centerY + Math.sin(angle) * (radius - degreeOffset),
    };
  });
}

function shortLabel(label: string) {
  if (label.length <= 18) {
    return label;
  }
  return `${label.slice(0, 16)}...`;
}
