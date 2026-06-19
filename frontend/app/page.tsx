"use client";

import {
  BarChart3,
  Bot,
  FileSearch,
  GitBranch,
  RefreshCw,
  Search,
  Upload,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { ChangeEvent, useEffect, useMemo, useState } from "react";

import {
  createCustodian,
  createMatter,
  getAnalyticsDashboard,
  getCustodians,
  getDocuments,
  getMatters,
  searchDocuments,
  uploadDocument,
  type AnalyticsSnapshot,
  type Custodian,
  type DocumentSummary,
  type Matter,
  type SearchResponse,
} from "../lib/api";

export default function Home() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [custodians, setCustodians] = useState<Custodian[]>([]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [snapshot, setSnapshot] = useState<AnalyticsSnapshot | null>(null);
  const [selectedMatterId, setSelectedMatterId] = useState<number | undefined>();
  const [matterName, setMatterName] = useState("");
  const [matterNumber, setMatterNumber] = useState("");
  const [custodianName, setCustodianName] = useState("");
  const [custodianEmail, setCustodianEmail] = useState("");
  const [selectedCustodianId, setSelectedCustodianId] = useState<number | undefined>();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [query, setQuery] = useState("contract Rule 26");
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

  const selectedMatter = useMemo(
    () => matters.find((matter) => matter.id === selectedMatterId),
    [matters, selectedMatterId],
  );

  async function refresh(nextMatterId = selectedMatterId) {
    setIsLoadingWorkspace(true);
    setLoadError(null);
    try {
      const [matterRows, custodianRows, documentRows, dashboard] = await Promise.all([
        getMatters(),
        getCustodians(),
        getDocuments(nextMatterId),
        getAnalyticsDashboard(nextMatterId),
      ]);
      setMatters(matterRows);
      setCustodians(custodianRows);
      setDocuments(documentRows);
      setSnapshot(dashboard.snapshot);
    } finally {
      setIsLoadingWorkspace(false);
    }
  }

  useEffect(() => {
    void refresh().catch(() => {
      setIsLoadingWorkspace(false);
      setLoadError("Unable to load workspace data");
    });
  }, [selectedMatterId]);

  async function submitMatter() {
    const trimmed = matterName.trim();
    if (!trimmed) {
      return;
    }
    setIsBusy(true);
    setStatus(null);
    try {
      const matter = await createMatter({
        name: trimmed,
        matter_number: matterNumber.trim() || undefined,
      });
      setSelectedMatterId(matter.id);
      setMatterName("");
      setMatterNumber("");
      await refresh(matter.id);
      setStatus(`Created matter ${matter.name}`);
    } catch {
      setStatus("Unable to create matter");
    } finally {
      setIsBusy(false);
    }
  }

  async function submitCustodian() {
    const trimmed = custodianName.trim();
    if (!trimmed) {
      return;
    }
    setIsBusy(true);
    setStatus(null);
    try {
      const custodian = await createCustodian({
        full_name: trimmed,
        email: custodianEmail.trim() || undefined,
      });
      setSelectedCustodianId(custodian.id);
      setCustodianName("");
      setCustodianEmail("");
      await refresh();
      setStatus(`Created custodian ${custodian.full_name}`);
    } catch {
      setStatus("Unable to create custodian");
    } finally {
      setIsBusy(false);
    }
  }

  async function submitUpload() {
    if (!selectedFile) {
      setStatus("Choose a file to upload");
      return;
    }
    setIsBusy(true);
    setStatus(null);
    try {
      const result = await uploadDocument({
        file: selectedFile,
        matterId: selectedMatterId,
        custodianId: selectedCustodianId,
      });
      setSelectedFile(null);
      await refresh();
      setStatus(`Uploaded ${result.original_filename} (${result.processing_status})`);
    } catch {
      setStatus("Unable to upload document");
    } finally {
      setIsBusy(false);
    }
  }

  async function submitSearch() {
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }
    setIsBusy(true);
    setStatus(null);
    setHasSearched(true);
    try {
      setSearchResponse(await searchDocuments({ query: trimmed, matterId: selectedMatterId }));
    } catch {
      setStatus("Unable to search documents");
    } finally {
      setIsBusy(false);
    }
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">
                Litigation Analytics Workspace
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-ink">eDiscovery investigation dashboard</h1>
              <p className="mt-2 text-sm text-slate-600">
                {selectedMatter ? `Active matter: ${selectedMatter.name}` : "Create or select a matter to begin."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/assistant" className="nav-button">
                <Bot size={18} />
                Assistant
              </Link>
              <Link href="/dashboard" className="nav-button">
                <BarChart3 size={18} />
                Dashboard
              </Link>
              <Link href="/graph" className="nav-button">
                <GitBranch size={18} />
                Graph
              </Link>
              <button className="nav-button" onClick={() => void refresh()} type="button">
                <RefreshCw size={18} />
                Refresh
              </button>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <Metric label="Documents" value={snapshot?.document_count ?? documents.length} />
            <Metric label="Entities" value={snapshot?.entity_count ?? 0} />
            <Metric label="Relationships" value={snapshot?.relationship_count ?? 0} />
            <Metric label="File Types" value={Object.keys(snapshot?.file_type_counts ?? {}).length} />
          </div>
          {isLoadingWorkspace && (
            <p className="rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">
              Loading workspace data...
            </p>
          )}
          {loadError && (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {loadError}
            </p>
          )}
          {status && <p className="rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">{status}</p>}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-4">
          <Panel title="Matter Setup">
            <label className="block">
              <span className="form-label">Active matter</span>
              <select
                className="form-field"
                value={selectedMatterId ?? ""}
                onChange={(event) =>
                  setSelectedMatterId(event.target.value ? Number(event.target.value) : undefined)
                }
              >
                <option value="">All matters</option>
                {matters.map((matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">Matter name</span>
              <input className="form-field" value={matterName} onChange={(event) => setMatterName(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Matter number</span>
              <input
                className="form-field"
                value={matterNumber}
                onChange={(event) => setMatterNumber(event.target.value)}
              />
            </label>
            <button className="primary-button" disabled={isBusy} onClick={() => void submitMatter()} type="button">
              Create Matter
            </button>
          </Panel>

          <Panel title="Custodian">
            <label className="block">
              <span className="form-label">Assign custodian</span>
              <select
                className="form-field"
                value={selectedCustodianId ?? ""}
                onChange={(event) =>
                  setSelectedCustodianId(event.target.value ? Number(event.target.value) : undefined)
                }
              >
                <option value="">Unassigned</option>
                {custodians.map((custodian) => (
                  <option key={custodian.id} value={custodian.id}>
                    {custodian.full_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">New custodian</span>
              <input
                className="form-field"
                value={custodianName}
                onChange={(event) => setCustodianName(event.target.value)}
              />
            </label>
            <label className="block">
              <span className="form-label">Email</span>
              <input
                className="form-field"
                value={custodianEmail}
                onChange={(event) => setCustodianEmail(event.target.value)}
              />
            </label>
            <button className="secondary-button" disabled={isBusy} onClick={() => void submitCustodian()} type="button">
              Create Custodian
            </button>
          </Panel>
        </aside>

        <div className="space-y-5">
          <Panel title="Upload Documents">
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <input className="form-field" onChange={chooseFile} type="file" />
              <button className="primary-button md:w-auto" disabled={isBusy} onClick={() => void submitUpload()} type="button">
                <Upload size={17} />
                {isBusy ? "Working" : "Upload"}
              </button>
            </div>
            {selectedFile && <p className="text-sm text-slate-600">Selected: {selectedFile.name}</p>}
          </Panel>

          <Panel title="Search Evidence">
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <input
                className="form-field"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search parsed document text"
              />
              <button className="primary-button md:w-auto" disabled={isBusy} onClick={() => void submitSearch()} type="button">
                <Search size={17} />
                Search
              </button>
            </div>
            {searchResponse && (
              <div className="mt-4 space-y-2">
                <p className="text-sm text-slate-600">
                  {searchResponse.results.length} result(s), source: {searchResponse.source}
                </p>
                {searchResponse.results.map((result) => (
                  <article key={`${result.document_id}-${result.chunk_id}`} className="rounded-md border border-line bg-panel p-3">
                    <Link className="font-semibold text-ink" href={`/documents/${result.document_id}?chunk=${result.chunk_id}`}>
                      {result.title}
                    </Link>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{result.snippet}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>score {result.score}</span>
                      <span>{result.source}</span>
                      <span>{result.citation}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
            {hasSearched && searchResponse?.results.length === 0 && (
              <p className="mt-4 rounded-md border border-line bg-panel p-3 text-sm text-slate-600">
                No matching chunks found for this query.
              </p>
            )}
          </Panel>

          <Panel title="Recent Documents">
            <div className="grid gap-3 md:grid-cols-2">
              {documents.length === 0 ? (
                <p className="text-sm text-slate-600">No documents uploaded yet.</p>
              ) : (
                documents.map((document) => (
                  <Link
                    key={document.id}
                    className="rounded-md border border-line bg-panel p-3 hover:border-accent"
                    href={`/documents/${document.id}`}
                  >
                    <div className="flex items-start gap-2">
                      <FileSearch className="mt-0.5 text-accent" size={17} />
                      <div>
                        <p className="font-semibold text-ink">{document.subject || document.original_filename}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {document.file_type} / {document.processing_status}
                        </p>
                      </div>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </Panel>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-panel p-4">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}
