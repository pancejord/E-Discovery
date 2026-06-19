"use client";

import dynamic from "next/dynamic";
import { Activity, BarChart3, RefreshCw, Users } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  getAnalyticsDashboard,
  getMatters,
  type AnalyticsBucket,
  type AnalyticsDashboard,
  type CommunicationMetric,
  type Matter,
} from "../lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const plotConfig = {
  displayModeBar: false,
  responsive: true,
};

export function AnalyticsDashboardView() {
  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard(nextMatterId = matterId) {
    setIsLoading(true);
    setError(null);
    try {
      setDashboard(await getAnalyticsDashboard(nextMatterId));
    } catch {
      setError("Unable to load analytics data");
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
          void loadDashboard(rows[0].id);
          return;
        }
        void loadDashboard();
      })
      .catch(() => void loadDashboard());
  }, []);

  const communicationPairs = dashboard?.communication_pairs ?? [];
  const timeline = dashboard?.document_timeline ?? [];

  const timelineData = useMemo(
    () => [
      {
        x: timeline.map((point) => point.date),
        y: timeline.map((point) => point.document_count),
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#1D6F6B", width: 3 },
        marker: { color: "#1D6F6B", size: 7 },
        name: "Documents",
      },
    ],
    [timeline],
  );

  return (
    <main className="min-h-screen bg-panel">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">Analytics Dashboard</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Matter activity and communication signals</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink"
              value={matterId ?? ""}
              onChange={(event) => {
                const nextMatterId = event.target.value ? Number(event.target.value) : undefined;
                setMatterId(nextMatterId);
                void loadDashboard(nextMatterId);
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
            <button
              className="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-semibold text-white"
              onClick={() => void loadDashboard()}
              type="button"
            >
              <RefreshCw size={17} />
              Refresh
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-5">
        {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

        <div className="grid gap-3 md:grid-cols-4">
          <MetricCard label="Documents" value={dashboard?.snapshot.document_count ?? 0} icon={<BarChart3 size={18} />} />
          <MetricCard label="Entities" value={dashboard?.snapshot.entity_count ?? 0} icon={<Users size={18} />} />
          <MetricCard
            label="Relationships"
            value={dashboard?.snapshot.relationship_count ?? 0}
            icon={<Activity size={18} />}
          />
          <MetricCard label="Communications" value={communicationPairs.length} icon={<Users size={18} />} />
        </div>

        {isLoading ? (
          <div className="mt-4 rounded-md border border-line bg-white p-8 text-center text-sm text-slate-600">
            Loading analytics
          </div>
        ) : (
          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <ChartPanel title="Document Timeline">
              {timeline.length === 0 ? (
                <EmptyChart message="No dated documents yet" />
              ) : (
                <Plot
                  data={timelineData}
                  layout={chartLayout("Documents over time")}
                  config={plotConfig}
                  className="h-[320px] w-full"
                  style={{ width: "100%", height: "320px" }}
                />
              )}
            </ChartPanel>

            <ChartPanel title="File Types">
              <BucketBarChart buckets={dashboard?.file_type_distribution ?? []} color="#1D6F6B" />
            </ChartPanel>

            <ChartPanel title="Document Classes">
              <BucketBarChart buckets={dashboard?.document_type_distribution ?? []} color="#6D5BD0" />
            </ChartPanel>

            <ChartPanel title="Entity Types">
              <BucketBarChart buckets={dashboard?.entity_type_distribution ?? []} color="#B7791F" />
            </ChartPanel>

            <ChartPanel title="Relationship Types">
              <BucketBarChart buckets={dashboard?.relationship_type_distribution ?? []} color="#9F1239" />
            </ChartPanel>

            <ChartPanel title="Top Custodians">
              <BucketBarChart buckets={dashboard?.top_custodians ?? []} color="#2F80ED" />
            </ChartPanel>
          </div>
        )}

        <CommunicationTable pairs={communicationPairs} />
      </section>
    </main>
  );
}

function BucketBarChart({ buckets, color }: { buckets: AnalyticsBucket[]; color: string }) {
  if (buckets.length === 0) {
    return <EmptyChart message="No data yet" />;
  }
  return (
    <Plot
      data={[
        {
          x: buckets.map((bucket) => bucket.label),
          y: buckets.map((bucket) => bucket.count),
          type: "bar",
          marker: { color },
        },
      ]}
      layout={chartLayout("Counts")}
      config={plotConfig}
      className="h-[320px] w-full"
      style={{ width: "100%", height: "320px" }}
    />
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-[320px] items-center justify-center rounded-md bg-panel text-sm text-slate-600">
      {message}
    </div>
  );
}

function CommunicationTable({ pairs }: { pairs: CommunicationMetric[] }) {
  return (
    <section className="mt-4 rounded-md border border-line bg-white">
      <div className="border-b border-line px-4 py-3">
        <h2 className="text-base font-semibold text-ink">Communication Analysis</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-panel text-left text-slate-600">
            <tr>
              <th className="border-b border-line px-4 py-3 font-semibold">Sender</th>
              <th className="border-b border-line px-4 py-3 font-semibold">Recipient</th>
              <th className="border-b border-line px-4 py-3 font-semibold">Messages</th>
              <th className="border-b border-line px-4 py-3 font-semibold">Documents</th>
            </tr>
          </thead>
          <tbody>
            {pairs.length === 0 ? (
              <tr>
                <td className="px-4 py-5 text-slate-600" colSpan={4}>
                  No communication relationships found
                </td>
              </tr>
            ) : (
              pairs.map((pair) => (
                <tr key={`${pair.source_entity_id}:${pair.target_entity_id}`} className="border-b border-line">
                  <td className="px-4 py-3 font-medium text-ink">{pair.source_entity_name}</td>
                  <td className="px-4 py-3 text-slate-700">{pair.target_entity_name}</td>
                  <td className="px-4 py-3 text-slate-700">{pair.message_count}</td>
                  <td className="px-4 py-3 text-slate-700">{pair.document_ids.join(", ") || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChartPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-line bg-white">
      <div className="border-b border-line px-4 py-3">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
      </div>
      <div className="p-2">{children}</div>
    </section>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="flex items-center justify-between text-slate-600">
        <span className="text-sm">{label}</span>
        <span className="text-accent">{icon}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function chartLayout(title: string) {
  return {
    title: { text: title, font: { size: 13 } },
    margin: { t: 34, r: 18, b: 56, l: 46 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    font: { family: "Arial, Helvetica, sans-serif", color: "#17202A" },
    xaxis: { tickangle: -25, automargin: true },
    yaxis: { rangemode: "tozero", gridcolor: "#E6EBF0" },
  };
}
