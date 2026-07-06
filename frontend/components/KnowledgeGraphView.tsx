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

const graphWidth = 900;
const graphHeight = 584;
const graphPadding = 70;

export function KnowledgeGraphView() {
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [relationshipType, setRelationshipType] = useState("");
  const [entityType, setEntityType] = useState("");
  const [entityQuery, setEntityQuery] = useState("");
  const [minConfidence, setMinConfidence] = useState(0);
  const [entityLimit, setEntityLimit] = useState(250);
  const [entityOffset, setEntityOffset] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadGraph(
    nextRelationshipType = relationshipType,
    nextMatterId = matterId,
    nextMinConfidence = minConfidence,
    nextEntityOffset = entityOffset,
  ) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getKnowledgeGraph({
        relationshipType: nextRelationshipType || undefined,
        matterId: nextMatterId,
        minConfidence: nextMinConfidence,
        entityLimit,
        entityOffset: nextEntityOffset,
      });
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

  const positionedNodes = useMemo(() => positionNodes(graph?.nodes ?? [], graph?.edges ?? []), [graph]);
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
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Graph</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Entity relationships</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={matterId ?? ""}
              onChange={(event) => {
                const nextMatterId = event.target.value ? Number(event.target.value) : undefined;
                setMatterId(nextMatterId);
                setEntityOffset(0);
                void loadGraph(relationshipType, nextMatterId, minConfidence, 0);
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
                setEntityOffset(0);
                void loadGraph(relationshipType, matterId, nextConfidence, 0);
              }}
              aria-label="Minimum confidence"
            >
              <option value={0}>Any confidence</option>
              <option value={0.5}>0.5+</option>
              <option value={0.75}>0.75+</option>
              <option value={0.9}>0.9+</option>
            </select>
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={entityLimit}
              onChange={(event) => {
                const nextLimit = Number(event.target.value);
                setEntityLimit(nextLimit);
                setEntityOffset(0);
                void loadGraph(relationshipType, matterId, minConfidence, 0);
              }}
              aria-label="Entity page size"
            >
              <option value={100}>100 nodes</option>
              <option value={250}>250 nodes</option>
              <option value={500}>500 nodes</option>
            </select>
            <button
              className="nav-button"
              onClick={() => {
                const nextOffset = Math.max(0, entityOffset - entityLimit);
                setEntityOffset(nextOffset);
                void loadGraph(relationshipType, matterId, minConfidence, nextOffset);
              }}
              type="button"
              disabled={entityOffset === 0}
            >
              Prev
            </button>
            <button
              className="nav-button"
              onClick={() => {
                const nextOffset = entityOffset + entityLimit;
                setEntityOffset(nextOffset);
                void loadGraph(relationshipType, matterId, minConfidence, nextOffset);
              }}
              type="button"
            >
              Next
            </button>
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
                {filteredNodes.length} nodes / {filteredEdges.length} edges / offset {entityOffset}
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
                      {edge.confidence_explanations[0] && (
                        <p className="mt-2 text-xs leading-5 text-slate-600">{edge.confidence_explanations[0]}</p>
                      )}
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
    <svg className="h-[584px] w-full" viewBox={`0 0 ${graphWidth} ${graphHeight}`} role="img" aria-label="Knowledge graph">
      <rect width={graphWidth} height={graphHeight} fill="#ffffff" />
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
        const radius = nodeRadius(node);
        const isSelected = selectedNodeId === node.id;
        const connectedToSelection = edges.some(
          (edge) =>
            selectedNodeId !== null &&
            ((edge.source === selectedNodeId && edge.target === node.id) ||
              (edge.target === selectedNodeId && edge.source === node.id)),
        );
        const dimmed = selectedNodeId !== null && !isSelected && !connectedToSelection;
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
              opacity={dimmed ? 0.45 : 1}
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

function positionNodes(nodes: GraphNode[], edges: GraphEdge[]): PositionedNode[] {
  if (nodes.length === 0) {
    return [];
  }
  if (nodes.length === 1) {
    return [{ ...nodes[0], x: graphWidth / 2, y: graphHeight / 2 }];
  }

  const typeCenters = clusterCenters(nodes);
  const simulation = nodes.map((node, index) => {
    const center = typeCenters.get(node.entity_type) ?? { x: graphWidth / 2, y: graphHeight / 2 };
    const angle = seededAngle(node.id, index);
    const spread = 34 + (index % 5) * 10;
    return {
      ...node,
      x: center.x + Math.cos(angle) * spread,
      y: center.y + Math.sin(angle) * spread,
      vx: 0,
      vy: 0,
    };
  });
  const byId = new Map(simulation.map((node) => [node.id, node]));

  for (let tick = 0; tick < 150; tick += 1) {
    const cooling = 1 - tick / 180;

    for (const node of simulation) {
      const center = typeCenters.get(node.entity_type) ?? { x: graphWidth / 2, y: graphHeight / 2 };
      node.vx += (center.x - node.x) * 0.004 * cooling;
      node.vy += (center.y - node.y) * 0.004 * cooling;
      node.vx += (graphWidth / 2 - node.x) * 0.001;
      node.vy += (graphHeight / 2 - node.y) * 0.001;
    }

    for (const edge of edges) {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) {
        continue;
      }
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const desired = 118 - Math.min(edge.weight, 8) * 5;
      const force = (distance - desired) * 0.006 * cooling;
      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;
      source.vx += fx;
      source.vy += fy;
      target.vx -= fx;
      target.vy -= fy;
    }

    for (let leftIndex = 0; leftIndex < simulation.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < simulation.length; rightIndex += 1) {
        const left = simulation[leftIndex];
        const right = simulation[rightIndex];
        const dx = right.x - left.x || 0.01;
        const dy = right.y - left.y || 0.01;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const minDistance = nodeRadius(left) + nodeRadius(right) + 24;
        if (distance < minDistance) {
          const force = ((minDistance - distance) / distance) * 0.035 * cooling;
          const fx = dx * force;
          const fy = dy * force;
          left.vx -= fx;
          left.vy -= fy;
          right.vx += fx;
          right.vy += fy;
        } else {
          const repel = 16 / (distance * distance);
          left.vx -= dx * repel;
          left.vy -= dy * repel;
          right.vx += dx * repel;
          right.vy += dy * repel;
        }
      }
    }

    for (const node of simulation) {
      node.vx *= 0.82;
      node.vy *= 0.82;
      node.x = clamp(node.x + node.vx, graphPadding, graphWidth - graphPadding);
      node.y = clamp(node.y + node.vy, graphPadding, graphHeight - graphPadding - 24);
    }
  }

  return simulation.map(({ vx, vy, ...node }) => node);
}

function shortLabel(label: string) {
  if (label.length <= 18) {
    return label;
  }
  return `${label.slice(0, 16)}...`;
}

function nodeRadius(node: GraphNode) {
  return Math.min(30, 12 + Math.sqrt(Math.max(node.degree, node.mention_count)) * 4);
}

function clusterCenters(nodes: GraphNode[]) {
  const types = Array.from(new Set(nodes.map((node) => node.entity_type))).sort();
  const centers = new Map<string, { x: number; y: number }>();
  const ringRadius = Math.min(graphWidth, graphHeight) * 0.32;
  for (const [index, type] of types.entries()) {
    const angle = types.length === 1 ? -Math.PI / 2 : (Math.PI * 2 * index) / types.length - Math.PI / 2;
    centers.set(type, {
      x: graphWidth / 2 + Math.cos(angle) * ringRadius,
      y: graphHeight / 2 + Math.sin(angle) * ringRadius * 0.72,
    });
  }
  return centers;
}

function seededAngle(id: number, index: number) {
  const seed = Math.sin(id * 12.9898 + index * 78.233) * 43758.5453;
  return (seed - Math.floor(seed)) * Math.PI * 2;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
