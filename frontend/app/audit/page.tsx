"use client";

import { Download, Filter, RefreshCw, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  apiBaseUrl,
  auditQueryString,
  getAuditLogs,
  getMatters,
  type AuditFilters,
  type AuditLog,
  type Matter,
} from "../../lib/api";

export default function AuditPage() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [events, setEvents] = useState<AuditLog[]>([]);
  const [filters, setFilters] = useState<AuditFilters>({ limit: 100 });
  const [documentId, setDocumentId] = useState("");
  const [responseStatus, setResponseStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const exportBase = useMemo(() => auditQueryString(filters), [filters]);
  const csvUrl = `${apiBaseUrl}/api/audit/export?${exportBase ? `${exportBase}&` : ""}format=csv`;
  const jsonUrl = `${apiBaseUrl}/api/audit/export?${exportBase ? `${exportBase}&` : ""}format=json`;

  async function refresh(nextFilters = filters) {
    setIsLoading(true);
    setError(null);
    try {
      const [matterRows, eventRows] = await Promise.all([getMatters(), getAuditLogs(nextFilters)]);
      setMatters(matterRows);
      setEvents(eventRows);
    } catch {
      setError("Unable to load audit events");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  function applyFilters() {
    const nextFilters = {
      ...filters,
      documentId: documentId ? Number(documentId) : undefined,
      responseStatus: responseStatus ? Number(responseStatus) : undefined,
    };
    setFilters(nextFilters);
    void refresh(nextFilters);
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Audit</p>
              <h1 className="mt-2 text-3xl font-semibold text-ink">Activity history</h1>
              <p className="mt-2 text-sm text-slate-600">
                Review matter activity, permission denials, ingestion failures, searches, AI answers, and exports.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/" className="nav-button">
                Workspace
              </Link>
              <a className="nav-button" href={csvUrl}>
                <Download size={18} />
                CSV
              </a>
              <a className="nav-button" href={jsonUrl}>
                <Download size={18} />
                JSON
              </a>
              <button className="nav-button" onClick={() => void refresh()} type="button">
                <RefreshCw size={18} />
                Refresh
              </button>
            </div>
          </div>
          {error && <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-md border border-line bg-white p-4">
          <div className="flex items-center gap-2">
            <Filter className="text-accent" size={18} />
            <h2 className="text-base font-semibold text-ink">Filters</h2>
          </div>
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="form-label">Matter</span>
              <select
                className="form-field"
                value={filters.matterId ?? ""}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    matterId: event.target.value ? Number(event.target.value) : undefined,
                  }))
                }
              >
                <option value="">Visible matters</option>
                {matters.map((matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">Actor</span>
              <input
                className="form-field"
                value={filters.actor ?? ""}
                onChange={(event) => setFilters((current) => ({ ...current, actor: event.target.value || undefined }))}
                placeholder="reviewer@example.com"
              />
            </label>
            <label className="block">
              <span className="form-label">Action</span>
              <input
                className="form-field"
                value={filters.action ?? ""}
                onChange={(event) => setFilters((current) => ({ ...current, action: event.target.value || undefined }))}
                placeholder="document.upload"
              />
            </label>
            <label className="block">
              <span className="form-label">Document ID</span>
              <input className="form-field" value={documentId} onChange={(event) => setDocumentId(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Request ID</span>
              <input
                className="form-field"
                value={filters.requestId ?? ""}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, requestId: event.target.value || undefined }))
                }
              />
            </label>
            <label className="block">
              <span className="form-label">Method</span>
              <select
                className="form-field"
                value={filters.method ?? ""}
                onChange={(event) => setFilters((current) => ({ ...current, method: event.target.value || undefined }))}
              >
                <option value="">Any method</option>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
            </label>
            <label className="block">
              <span className="form-label">Route</span>
              <input
                className="form-field"
                value={filters.route ?? ""}
                onChange={(event) => setFilters((current) => ({ ...current, route: event.target.value || undefined }))}
                placeholder="/api/search"
              />
            </label>
            <label className="block">
              <span className="form-label">Status</span>
              <input className="form-field" value={responseStatus} onChange={(event) => setResponseStatus(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">From</span>
              <input
                className="form-field"
                type="datetime-local"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, createdFrom: event.target.value || undefined }))
                }
              />
            </label>
            <label className="block">
              <span className="form-label">To</span>
              <input
                className="form-field"
                type="datetime-local"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, createdTo: event.target.value || undefined }))
                }
              />
            </label>
            <button className="primary-button" onClick={applyFilters} type="button">
              Apply Filters
            </button>
          </div>
        </aside>

        <section className="rounded-md border border-line bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="text-accent" size={18} />
              <h2 className="text-base font-semibold text-ink">Events</h2>
            </div>
            <p className="text-sm text-slate-600">{isLoading ? "Loading..." : `${events.length} event(s)`}</p>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[1120px] border-collapse text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="py-2 pr-3">Time</th>
                  <th className="py-2 pr-3">Actor</th>
                  <th className="py-2 pr-3">Action</th>
                  <th className="py-2 pr-3">Request</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Matter</th>
                  <th className="py-2 pr-3">Document</th>
                  <th className="py-2 pr-3">Summary</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} className="border-b border-line align-top">
                    <td className="py-3 pr-3 text-slate-600">{new Date(event.created_at).toLocaleString()}</td>
                    <td className="py-3 pr-3">{event.actor ?? "unknown"}</td>
                    <td className="py-3 pr-3 font-semibold text-ink">{event.action}</td>
                    <td className="py-3 pr-3">
                      <p>{[event.method, event.route].filter(Boolean).join(" ") || "-"}</p>
                      <p className="mt-1 text-xs text-slate-500">{event.request_id ?? "-"}</p>
                    </td>
                    <td className="py-3 pr-3">{event.response_status ?? "-"}</td>
                    <td className="py-3 pr-3">{event.matter_id ?? "-"}</td>
                    <td className="py-3 pr-3">{event.document_id ?? "-"}</td>
                    <td className="py-3 pr-3 text-slate-700">{event.summary ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!isLoading && events.length === 0 && (
              <p className="rounded-md border border-line bg-panel p-3 text-sm text-slate-600">
                No audit events match the current filters.
              </p>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
