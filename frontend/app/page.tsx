"use client";

import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  ChevronDown,
  FileSearch,
  FlaskConical,
  GitBranch,
  LayoutDashboard,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Upload,
  Users,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { ChangeEvent, useEffect, useMemo, useState } from "react";

import {
  createCustodian,
  createMatter,
  createSavedSearch,
  deleteSavedSearch,
  getAnalyticsDashboard,
  getCustodians,
  getDocuments,
  getMatters,
  getSavedSearches,
  runSavedSearch,
  searchDocuments,
  updateSavedSearch,
  uploadDocument,
  type AnalyticsSnapshot,
  type Custodian,
  type DocumentSummary,
  type Matter,
  type SavedSearch,
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
  const [searchCustodianId, setSearchCustodianId] = useState<number | undefined>();
  const [documentTypeFilter, setDocumentTypeFilter] = useState("");
  const [fileTypeFilter, setFileTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [issueCodeFilter, setIssueCodeFilter] = useState("");
  const [reviewStatusFilter, setReviewStatusFilter] = useState("");
  const [privilegeFilter, setPrivilegeFilter] = useState("");
  const [senderFilter, setSenderFilter] = useState("");
  const [recipientFilter, setRecipientFilter] = useState("");
  const [sortBy, setSortBy] = useState<"relevance" | "date" | "custodian" | "document_type">("relevance");
  const [dateFromFilter, setDateFromFilter] = useState("");
  const [dateToFilter, setDateToFilter] = useState("");
  const [savedSearchName, setSavedSearchName] = useState("");
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
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
      const [matterRows, custodianRows, documentRows, dashboard, savedRows] = await Promise.all([
        getMatters(),
        getCustodians(),
        getDocuments(nextMatterId),
        getAnalyticsDashboard({ matterId: nextMatterId }),
        getSavedSearches(nextMatterId),
      ]);
      setMatters(matterRows);
      setCustodians(custodianRows);
      setDocuments(documentRows);
      setSnapshot(dashboard.snapshot);
      setSavedSearches(savedRows);
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
      setFieldErrors({ matterName: "Matter name is required." });
      return;
    }
    setFieldErrors({});
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
      setFieldErrors({ custodianName: "Custodian name is required." });
      return;
    }
    if (custodianEmail.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(custodianEmail.trim())) {
      setFieldErrors({ custodianEmail: "Enter a valid email address." });
      return;
    }
    setFieldErrors({});
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
      setFieldErrors({ upload: "Choose a file before uploading." });
      setStatus("Choose a file to upload");
      return;
    }
    setFieldErrors({});
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
      setFieldErrors({ query: "Search query is required." });
      return;
    }
    setFieldErrors({});
    setIsBusy(true);
    setStatus(null);
    setHasSearched(true);
    try {
      setSearchResponse(await searchDocuments({ query: trimmed, ...currentSearchFilters() }));
    } catch {
      setStatus("Unable to search documents");
    } finally {
      setIsBusy(false);
    }
  }

  function currentSearchFilters() {
    return {
      matterId: selectedMatterId,
      custodianId: searchCustodianId,
      documentType: documentTypeFilter.trim() || undefined,
      fileType: fileTypeFilter.trim() || undefined,
      processingStatus: statusFilter || undefined,
      tag: tagFilter.trim() || undefined,
      issueCode: issueCodeFilter.trim() || undefined,
      reviewStatus: reviewStatusFilter || undefined,
      privilegeFlag: privilegeFilter ? privilegeFilter === "true" : undefined,
      sender: senderFilter.trim() || undefined,
      recipient: recipientFilter.trim() || undefined,
      sortBy,
      dateFrom: dateFromFilter ? `${dateFromFilter}T00:00:00` : undefined,
      dateTo: dateToFilter ? `${dateToFilter}T23:59:59` : undefined,
      limit: 10,
    };
  }

  async function saveCurrentSearch() {
    const trimmedName = savedSearchName.trim();
    const trimmedQuery = query.trim();
    if (!trimmedName || !trimmedQuery) {
      setFieldErrors({
        savedSearchName: !trimmedName ? "Saved search name is required." : "",
        query: !trimmedQuery ? "Search query is required." : "",
      });
      setStatus("Name the search before saving");
      return;
    }
    setFieldErrors({});
    setIsBusy(true);
    setStatus(null);
    try {
      await createSavedSearch({
        name: trimmedName,
        query: trimmedQuery,
        ...currentSearchFilters(),
      });
      setSavedSearchName("");
      setSavedSearches(await getSavedSearches(selectedMatterId));
      setStatus(`Saved search ${trimmedName}`);
    } catch {
      setStatus("Unable to save search");
    } finally {
      setIsBusy(false);
    }
  }

  async function runSaved(savedSearch: SavedSearch) {
    setIsBusy(true);
    setStatus(null);
    setHasSearched(true);
    try {
      setQuery(savedSearch.query);
      const filters = savedSearch.filters ?? {};
      setSearchCustodianId(typeof filters.custodian_id === "number" ? filters.custodian_id : undefined);
      setDocumentTypeFilter(typeof filters.document_type === "string" ? filters.document_type : "");
      setFileTypeFilter(typeof filters.file_type === "string" ? filters.file_type : "");
      setStatusFilter(typeof filters.processing_status === "string" ? filters.processing_status : "");
      setTagFilter(typeof filters.tag === "string" ? filters.tag : "");
      setIssueCodeFilter(typeof filters.issue_code === "string" ? filters.issue_code : "");
      setReviewStatusFilter(typeof filters.review_status === "string" ? filters.review_status : "");
      setPrivilegeFilter(typeof filters.privilege_flag === "boolean" ? String(filters.privilege_flag) : "");
      setSenderFilter(typeof filters.sender === "string" ? filters.sender : "");
      setRecipientFilter(typeof filters.recipient === "string" ? filters.recipient : "");
      const savedSort = typeof filters.sort_by === "string" ? filters.sort_by : "";
      setSortBy(savedSort === "date" || savedSort === "custodian" || savedSort === "document_type" ? savedSort : "relevance");
      setDateFromFilter(typeof filters.date_from === "string" ? filters.date_from.slice(0, 10) : "");
      setDateToFilter(typeof filters.date_to === "string" ? filters.date_to.slice(0, 10) : "");
      setSearchResponse(await runSavedSearch(savedSearch.id));
      setStatus(`Ran saved search ${savedSearch.name}`);
    } catch {
      setStatus("Unable to run saved search");
    } finally {
      setIsBusy(false);
    }
  }

  async function updateSaved(savedSearch: SavedSearch) {
    setIsBusy(true);
    setStatus(null);
    try {
      await updateSavedSearch(savedSearch.id, {
        name: savedSearch.name,
        query,
        ...currentSearchFilters(),
      });
      setSavedSearches(await getSavedSearches(selectedMatterId));
      setStatus(`Updated saved search ${savedSearch.name}`);
    } catch {
      setStatus("Unable to update saved search");
    } finally {
      setIsBusy(false);
    }
  }

  async function toggleSavedShare(savedSearch: SavedSearch) {
    setIsBusy(true);
    setStatus(null);
    try {
      await updateSavedSearch(savedSearch.id, { is_shared: !savedSearch.is_shared });
      setSavedSearches(await getSavedSearches(selectedMatterId));
      setStatus(`${savedSearch.is_shared ? "Unshared" : "Shared"} ${savedSearch.name}`);
    } catch {
      setStatus("Unable to update saved search sharing");
    } finally {
      setIsBusy(false);
    }
  }

  async function removeSaved(savedSearch: SavedSearch) {
    setIsBusy(true);
    setStatus(null);
    try {
      await deleteSavedSearch(savedSearch.id);
      setSavedSearches(await getSavedSearches(selectedMatterId));
      setStatus(`Deleted saved search ${savedSearch.name}`);
    } catch {
      setStatus("Unable to delete saved search");
    } finally {
      setIsBusy(false);
    }
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  return (
    <main className="workspace-shell min-h-screen">
      <aside className="workspace-sidebar">
        <Link className="sidebar-brand" href="/" aria-label="LegalSight home">
          <Image
            src="/legalsight-logo.png"
            alt="LegalSight"
            width={1154}
            height={456}
            priority
            className="sidebar-logo"
          />
        </Link>
        <nav className="sidebar-nav" aria-label="Primary navigation">
          <Link href="/" className="sidebar-link sidebar-link-active">
            <LayoutDashboard size={19} />
            <span>Workspace</span>
          </Link>
          <Link href="/assistant" className="sidebar-link">
            <Bot size={19} />
            <span>AI Assistant</span>
          </Link>
          <Link href="/dashboard" className="sidebar-link">
            <BarChart3 size={19} />
            <span>Analytics</span>
          </Link>
          <Link href="/graph" className="sidebar-link">
            <GitBranch size={19} />
            <span>Knowledge Graph</span>
          </Link>
          <Link href="/audit" className="sidebar-link">
            <ShieldCheck size={19} />
            <span>Audit Trail</span>
          </Link>
          <Link href="/evaluation" className="sidebar-link">
            <FlaskConical size={19} />
            <span>Evaluation</span>
          </Link>
        </nav>
        <div className="sidebar-footer">
          <Link href="/admin" className="sidebar-link">
            <Users size={19} />
            <span>Administration</span>
          </Link>
          <button className="sidebar-link" onClick={() => void refresh()} type="button">
            <RefreshCw size={19} />
            <span>Refresh data</span>
          </button>
          <Link href="/admin" className="sidebar-link">
            <Settings size={19} />
            <span>Settings</span>
          </Link>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <div>
            <p className="workspace-kicker">Litigation intelligence</p>
            <h1>Evidence workspace</h1>
          </div>
          <div className="topbar-actions">
            <label className="matter-switcher">
              <span className="sr-only">Active matter</span>
              <select
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
              <ChevronDown size={15} aria-hidden="true" />
            </label>
            <button className="icon-button" type="button" title="Notifications" aria-label="Notifications">
              <Bell size={19} />
              <span className="notification-dot" />
            </button>
            <div className="user-avatar" title="LegalSight user">LS</div>
          </div>
        </header>

        <div className="workspace-content">
          <section className="dashboard-intro">
            <div>
              <p className="workspace-kicker">Overview</p>
              <h2>{selectedMatter ? selectedMatter.name : "All active matters"}</h2>
              <p>Review evidence, investigate relationships, and monitor discovery progress.</p>
            </div>
            <Link href="/assistant" className="assistant-cta">
              <Bot size={18} />
              Ask LegalSight
            </Link>
          </section>

          <section className="dashboard-grid" aria-label="Matter overview">
            <div className="metric-stack">
              <Metric label="Documents" value={snapshot?.document_count ?? documents.length} />
              <Metric label="Entities" value={snapshot?.entity_count ?? 0} />
              <Metric label="Relationships" value={snapshot?.relationship_count ?? 0} />
              <Metric label="File types" value={Object.keys(snapshot?.file_type_counts ?? {}).length} />
            </div>
            <div className="activity-card">
              <div className="activity-card-header">
                <div>
                  <p className="workspace-kicker">Review activity</p>
                  <h3>Evidence processing</h3>
                </div>
                <span className="status-pill"><Activity size={14} /> Live matter data</span>
              </div>
              <EvidenceChart total={snapshot?.document_count ?? documents.length} />
            </div>
          </section>

          <div className="workspace-alerts">
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
        </div>

      <section className="workspace-tools">
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
              {fieldErrors.matterName && <span className="field-error">{fieldErrors.matterName}</span>}
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
              {fieldErrors.custodianName && <span className="field-error">{fieldErrors.custodianName}</span>}
            </label>
            <label className="block">
              <span className="form-label">Email</span>
              <input
                className="form-field"
                value={custodianEmail}
                onChange={(event) => setCustodianEmail(event.target.value)}
              />
              {fieldErrors.custodianEmail && <span className="field-error">{fieldErrors.custodianEmail}</span>}
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
            {fieldErrors.upload && <span className="field-error">{fieldErrors.upload}</span>}
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
            {fieldErrors.query && <span className="field-error">{fieldErrors.query}</span>}
            <div className="grid gap-3 md:grid-cols-3">
              <label className="block">
                <span className="form-label">Custodian</span>
                <select
                  className="form-field"
                  value={searchCustodianId ?? ""}
                  onChange={(event) =>
                    setSearchCustodianId(event.target.value ? Number(event.target.value) : undefined)
                  }
                >
                  <option value="">Any custodian</option>
                  {custodians.map((custodian) => (
                    <option key={custodian.id} value={custodian.id}>
                      {custodian.full_name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="form-label">Document type</span>
                <input
                  className="form-field"
                  value={documentTypeFilter}
                  onChange={(event) => setDocumentTypeFilter(event.target.value)}
                  placeholder="contract"
                />
              </label>
              <label className="block">
                <span className="form-label">File type</span>
                <input
                  className="form-field"
                  value={fileTypeFilter}
                  onChange={(event) => setFileTypeFilter(event.target.value)}
                  placeholder="pdf"
                />
              </label>
              <label className="block">
                <span className="form-label">Status</span>
                <select className="form-field" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">Any status</option>
                  <option value="parsed">Parsed</option>
                  <option value="uploaded">Uploaded</option>
                  <option value="needs_ocr">Needs OCR</option>
                </select>
              </label>
              <label className="block">
                <span className="form-label">Review status</span>
                <select className="form-field" value={reviewStatusFilter} onChange={(event) => setReviewStatusFilter(event.target.value)}>
                  <option value="">Any review status</option>
                  <option value="unreviewed">Unreviewed</option>
                  <option value="in_review">In review</option>
                  <option value="responsive">Responsive</option>
                  <option value="non_responsive">Non-responsive</option>
                  <option value="privileged">Privileged</option>
                  <option value="needs_follow_up">Needs follow-up</option>
                </select>
              </label>
              <label className="block">
                <span className="form-label">Privilege</span>
                <select className="form-field" value={privilegeFilter} onChange={(event) => setPrivilegeFilter(event.target.value)}>
                  <option value="">Any privilege state</option>
                  <option value="true">Flagged</option>
                  <option value="false">Not flagged</option>
                </select>
              </label>
              <label className="block">
                <span className="form-label">Tag</span>
                <input className="form-field" value={tagFilter} onChange={(event) => setTagFilter(event.target.value)} placeholder="hot" />
              </label>
              <label className="block">
                <span className="form-label">Issue code</span>
                <input
                  className="form-field"
                  value={issueCodeFilter}
                  onChange={(event) => setIssueCodeFilter(event.target.value)}
                  placeholder="privilege"
                />
              </label>
              <label className="block">
                <span className="form-label">Sender</span>
                <input className="form-field" value={senderFilter} onChange={(event) => setSenderFilter(event.target.value)} />
              </label>
              <label className="block">
                <span className="form-label">Recipient</span>
                <input className="form-field" value={recipientFilter} onChange={(event) => setRecipientFilter(event.target.value)} />
              </label>
              <label className="block">
                <span className="form-label">Sort</span>
                <select className="form-field" value={sortBy} onChange={(event) => setSortBy(event.target.value as typeof sortBy)}>
                  <option value="relevance">Relevance</option>
                  <option value="date">Date</option>
                  <option value="custodian">Custodian</option>
                  <option value="document_type">Document type</option>
                </select>
              </label>
              <label className="block">
                <span className="form-label">From date</span>
                <input className="form-field" type="date" value={dateFromFilter} onChange={(event) => setDateFromFilter(event.target.value)} />
              </label>
              <label className="block">
                <span className="form-label">To date</span>
                <input className="form-field" type="date" value={dateToFilter} onChange={(event) => setDateToFilter(event.target.value)} />
              </label>
            </div>
            <div className="flex flex-col gap-3 md:flex-row md:items-end">
              <label className="block flex-1">
                <span className="form-label">Saved search name</span>
                <input
                  className="form-field"
                  value={savedSearchName}
                  onChange={(event) => setSavedSearchName(event.target.value)}
                  placeholder="Privilege review set"
                />
                {fieldErrors.savedSearchName && <span className="field-error">{fieldErrors.savedSearchName}</span>}
              </label>
              <button className="secondary-button md:w-auto" disabled={isBusy} onClick={() => void saveCurrentSearch()} type="button">
                Save Search
              </button>
            </div>
            {savedSearches.length > 0 && (
              <div className="soft-panel p-3">
                <h3 className="text-sm font-semibold text-ink">Saved Searches</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {savedSearches.map((savedSearch) => (
                    <div className="saved-search-card flex flex-wrap items-center gap-2 p-2" key={savedSearch.id}>
                      <button
                        className="rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-ink"
                        disabled={isBusy}
                        onClick={() => void runSaved(savedSearch)}
                        type="button"
                      >
                        {savedSearch.name}
                      </button>
                      <button className="nav-button" disabled={isBusy} onClick={() => void updateSaved(savedSearch)} type="button">
                        Update
                      </button>
                      <button className="nav-button" disabled={isBusy} onClick={() => void toggleSavedShare(savedSearch)} type="button">
                        {savedSearch.is_shared ? "Unshare" : "Share"}
                      </button>
                      <button className="nav-button" disabled={isBusy} onClick={() => void removeSaved(savedSearch)} type="button">
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {searchResponse && (
              <div className="mt-4 space-y-2">
                <p className="text-sm text-slate-600">
                  {searchResponse.results.length} result(s), source: {searchResponse.source}
                </p>
                {searchResponse.results.map((result) => (
                  <article key={`${result.document_id}-${result.chunk_id}`} className="result-card p-3">
                    <Link
                      className="font-semibold text-ink"
                      href={`/documents/${result.document_id}?chunk=${result.chunk_id}&q=${encodeURIComponent(query)}`}
                    >
                      {result.title}
                    </Link>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{result.snippet}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>score {result.score}</span>
                      <span>{result.source}</span>
                      <span>keyword {result.diagnostics.keyword_score}</span>
                      <span>vector {result.diagnostics.vector_score}</span>
                      <span>{result.citation}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
            {hasSearched && searchResponse?.results.length === 0 && (
              <p className="soft-panel mt-4 p-3 text-sm text-slate-600">
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
                    className="document-card p-3"
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
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function EvidenceChart({ total }: { total: number }) {
  const bars = [28, 42, 38, 55, 48, 68, 62, 79, 73, 88, 82, 96];

  return (
    <div className="evidence-chart">
      <div className="chart-summary">
        <strong>{total}</strong>
        <span>documents in scope</span>
      </div>
      <div className="chart-bars" aria-label="Evidence processing activity trend">
        {bars.map((height, index) => (
          <span key={index} style={{ height: `${height}%` }} />
        ))}
      </div>
      <div className="chart-axis">
        <span>Collection</span>
        <span>Review</span>
        <span>Production</span>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="app-card">
      <div className="border-b border-line px-4 py-3">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
      </div>
      <div className="space-y-3 p-4">{children}</div>
    </section>
  );
}
