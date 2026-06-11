"use client";

import { RefreshCw, Share2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getKnowledgeGraph, type GraphEdge, type GraphNode, type KnowledgeGraph } from "../lib/api";

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
  const [relationshipType, setRelationshipType] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadGraph(nextRelationshipType = relationshipType) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getKnowledgeGraph(nextRelationshipType || undefined);
      setGraph(data);
      setSelectedNodeId(data.nodes[0]?.id ?? null);
    } catch {
      setError("Unable to load graph data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadGraph("");
  }, []);

  const positionedNodes = useMemo(() => positionNodes(graph?.nodes ?? []), [graph]);
  const nodeById = useMemo(
    () => new Map(positionedNodes.map((node) => [node.id, node])),
    [positionedNodes],
  );
  const selectedNode = selectedNodeId ? nodeById.get(selectedNodeId) : null;

  function handleRelationshipChange(value: string) {
    setRelationshipType(value);
    void loadGraph(value);
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
                {graph.metrics.node_count} nodes / {graph.metrics.edge_count} edges
              </div>
            )}
          </div>
          <GraphCanvas
            edges={graph?.edges ?? []}
            nodes={positionedNodes}
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
            <h2 className="text-base font-semibold text-ink">Top Entities</h2>
            <div className="mt-3 space-y-2">
              {(graph?.metrics.top_entities ?? []).slice(0, 6).map((node) => (
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
