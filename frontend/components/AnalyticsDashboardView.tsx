"use client";

import dynamic from "next/dynamic";
import { Activity, BarChart3, Download, RefreshCw, Users } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  getAnalyticsDashboard,
  analyticsExportUrl,
  getCustodians,
  getMatters,
  type AnalyticsBucket,
  type AnalyticsDashboard,
  type CommunicationMetric,
  type Custodian,
  type Matter,
} from "../lib/api";
import { Alert, EmptyState, MetricTile, PageHeader, Panel } from "./ui";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const plotConfig = {
  displayModeBar: false,
  responsive: true,
};

export function AnalyticsDashboardView() {
  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [custodians, setCustodians] = useState<Custodian[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [custodianId, setCustodianId] = useState<number | undefined>();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard(nextMatterId = matterId) {
    setIsLoading(true);
    setError(null);
    try {
      setDashboard(await getAnalyticsDashboard({ matterId: nextMatterId, custodianId, dateFrom, dateTo }));
    } catch {
      setError("Unable to load analytics data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void Promise.all([getMatters(), getCustodians()])
      .then(([matterRows, custodianRows]) => {
        setMatters(matterRows);
        setCustodians(custodianRows);
        if (matterRows.length > 0) {
          setMatterId(matterRows[0].id);
          void loadDashboard(matterRows[0].id);
          return;
        }
        void loadDashboard();
      })
      .catch(() => void loadDashboard());
  }, []);

  const communicationPairs = dashboard?.communication_pairs ?? [];
  const timeline = dashboard?.document_timeline ?? [];
  const exportUrl = analyticsExportUrl({ matterId, custodianId, dateFrom, dateTo });
  const headerActions = (
    <>
      <select
        className="form-field mt-0 w-auto min-w-44"
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
      <select
        className="form-field mt-0 w-auto min-w-44"
        value={custodianId ?? ""}
        onChange={(event) => {
          const nextCustodianId = event.target.value ? Number(event.target.value) : undefined;
          setCustodianId(nextCustodianId);
        }}
        aria-label="Custodian"
      >
        <option value="">All custodians</option>
        {custodians.map((custodian) => (
          <option key={custodian.id} value={custodian.id}>
            {custodian.full_name}
          </option>
        ))}
      </select>
      <input className="form-field mt-0 w-auto" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} aria-label="Date from" />
      <input className="form-field mt-0 w-auto" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} aria-label="Date to" />
      <button className="primary-button w-auto" onClick={() => void loadDashboard()} type="button">
        <RefreshCw size={17} />
        Refresh
      </button>
      <a className="nav-button" href={exportUrl}>
        <Download size={17} />
        Export
      </a>
    </>
  );

  const timelineData = useMemo(
    () => [
      {
        x: timeline.map((point) => point.date),
        y: timeline.map((point) => point.document_count),
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#0F766E", width: 3 },
        marker: { color: "#0F766E", size: 7 },
        name: "Documents",
      },
    ],
    [timeline],
  );

  return (
    <main className="min-h-screen bg-panel">
      <PageHeader
        eyebrow="LegalSight Analytics"
        title="Matter activity and communication signals"
        description="Filter the dashboard by matter, custodian, and date range, then export the visible analytics as CSV."
        actions={headerActions}
      />

      <section className="mx-auto max-w-7xl px-6 py-5">
        {error && <Alert tone="danger">{error}</Alert>}

        <div className="grid gap-3 md:grid-cols-4">
          <MetricTile label="Documents" value={dashboard?.snapshot.document_count ?? 0} icon={<BarChart3 size={18} />} />
          <MetricTile label="Entities" value={dashboard?.snapshot.entity_count ?? 0} icon={<Users size={18} />} />
          <MetricTile
            label="Relationships"
            value={dashboard?.snapshot.relationship_count ?? 0}
            icon={<Activity size={18} />}
          />
          <MetricTile label="Communications" value={communicationPairs.length} icon={<Users size={18} />} />
        </div>

        {isLoading ? (
          <div className="mt-4">
            <EmptyState message="Loading analytics" />
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
              <BucketBarChart buckets={dashboard?.file_type_distribution ?? []} color="#0F766E" />
            </ChartPanel>

            <ChartPanel title="Document Classes">
              <BucketBarChart buckets={dashboard?.document_type_distribution ?? []} color="#6D5BD0" />
            </ChartPanel>

            <ChartPanel title="Entity Types">
              <BucketBarChart buckets={dashboard?.entity_type_distribution ?? []} color="#B7791F" />
            </ChartPanel>

            <ChartPanel title="Relationship Types">
              <BucketBarChart buckets={dashboard?.relationship_type_distribution ?? []} color="#BE123C" />
            </ChartPanel>

            <ChartPanel title="Top Custodians">
              <BucketBarChart buckets={dashboard?.top_custodians ?? []} color="#2563EB" />
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
  return <EmptyState message={message} />;
}

function CommunicationTable({ pairs }: { pairs: CommunicationMetric[] }) {
  const [sortConfig, setSortConfig] = useState<{ key: "source" | "target" | "messages"; direction: "asc" | "desc" }>({
    key: "messages",
    direction: "desc",
  });
  const [pageIndex, setPageIndex] = useState(0);
  const pageSize = 8;
  const sortedPairs = useMemo(() => {
    const rows = [...pairs];
    rows.sort((left, right) => {
      const direction = sortConfig.direction === "asc" ? 1 : -1;
      if (sortConfig.key === "messages") {
        return (left.message_count - right.message_count) * direction;
      }
      const leftValue = sortConfig.key === "source" ? left.source_entity_name : left.target_entity_name;
      const rightValue = sortConfig.key === "source" ? right.source_entity_name : right.target_entity_name;
      return leftValue.localeCompare(rightValue) * direction;
    });
    return rows;
  }, [pairs, sortConfig]);
  const pageCount = Math.max(1, Math.ceil(sortedPairs.length / pageSize));
  const visiblePairs = sortedPairs.slice(pageIndex * pageSize, pageIndex * pageSize + pageSize);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  function sortBy(key: typeof sortConfig.key) {
    setPageIndex(0);
    setSortConfig((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  return (
    <div className="mt-4">
      <Panel
        title="Communication Analysis"
        actions={<span className="status-pill">{pairs.length} pairs</span>}
      >
        <div className="table-shell">
          <table className="data-table">
            <thead>
            <tr>
              <th><button type="button" onClick={() => sortBy("source")}>Sender</button></th>
              <th><button type="button" onClick={() => sortBy("target")}>Recipient</button></th>
              <th><button type="button" onClick={() => sortBy("messages")}>Messages</button></th>
              <th>Documents</th>
            </tr>
          </thead>
          <tbody>
            {pairs.length === 0 ? (
              <tr>
                <td className="text-slate-600" colSpan={4}>
                  No communication relationships found
                </td>
              </tr>
            ) : (
              visiblePairs.map((pair) => (
                <tr key={`${pair.source_entity_id}:${pair.target_entity_id}`} className="border-b border-line">
                  <td className="font-medium text-ink">{pair.source_entity_name}</td>
                  <td className="text-slate-700">{pair.target_entity_name}</td>
                  <td className="text-slate-700">{pair.message_count}</td>
                  <td className="text-slate-700">{pair.document_ids.join(", ") || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-600">
          <span>Page {pageIndex + 1} of {pageCount}</span>
          <div className="flex gap-2">
            <button className="nav-button" disabled={pageIndex === 0} onClick={() => setPageIndex((page) => Math.max(0, page - 1))} type="button">
              Previous
            </button>
            <button className="nav-button" disabled={pageIndex >= pageCount - 1} onClick={() => setPageIndex((page) => Math.min(pageCount - 1, page + 1))} type="button">
              Next
            </button>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function ChartPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Panel title={title}>
      <div className="p-0">{children}</div>
    </Panel>
  );
}

function chartLayout(title: string) {
  return {
    title: { text: title, font: { size: 13 } },
    margin: { t: 34, r: 18, b: 56, l: 46 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#fbfdff",
    font: { family: "Arial, Helvetica, sans-serif", color: "#17202A" },
    xaxis: { tickangle: -25, automargin: true },
    yaxis: { rangemode: "tozero", gridcolor: "#E6EBF0" },
  };
}
