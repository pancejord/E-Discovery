"use client";

import { ArrowLeft, ChevronDown, ChevronUp, FileText, RefreshCw, Save } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { getDocument, reprocessDocument, updateDocumentCoding, type DocumentDetail } from "../../../lib/api";

export default function DocumentDetailPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-5xl px-6 py-8">
          <p className="rounded-md border border-line bg-white p-4 text-sm text-slate-600">Loading document...</p>
        </main>
      }
    >
      <DocumentDetailContent />
    </Suspense>
  );
}

function DocumentDetailContent() {
  const params = useParams<{ documentId: string }>();
  const searchParams = useSearchParams();
  const selectedChunkId = Number(searchParams.get("chunk") ?? 0);
  const highlightQuery = searchParams.get("q") ?? "";
  const documentId = Number(params.documentId);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [tags, setTags] = useState("");
  const [issueCodes, setIssueCodes] = useState("");
  const [notes, setNotes] = useState("");
  const [privilegeFlag, setPrivilegeFlag] = useState(false);
  const [reviewStatus, setReviewStatus] = useState("unreviewed");

  useEffect(() => {
    if (!documentId) {
      return;
    }
    void getDocument(documentId)
      .then((loaded) => {
        setDocument(loaded);
        setTags(loaded.tags.join(", "));
        setIssueCodes(loaded.issue_codes.join(", "));
        setNotes(loaded.notes ?? "");
        setPrivilegeFlag(loaded.privilege_flag);
        setReviewStatus(loaded.review_status);
      })
      .catch(() => setError("Unable to load document"));
  }, [documentId]);

  const selectedChunk = useMemo(
    () => document?.chunks.find((chunk) => chunk.id === selectedChunkId),
    [document, selectedChunkId],
  );
  const selectedChunkIndex = useMemo(
    () => document?.chunks.findIndex((chunk) => chunk.id === selectedChunkId) ?? -1,
    [document, selectedChunkId],
  );
  const highlightTerms = useMemo(() => {
    const terms = highlightQuery.match(/"([^"]+)"|[A-Za-z0-9][A-Za-z0-9_\-']*/g) ?? [];
    return terms.map((term) => term.replaceAll('"', "").trim()).filter(Boolean);
  }, [highlightQuery]);

  async function saveCoding() {
    if (!document) {
      return;
    }
    setStatus(null);
    try {
      const updated = await updateDocumentCoding(document.id, {
        tags: splitList(tags),
        issue_codes: splitList(issueCodes),
        notes,
        privilege_flag: privilegeFlag,
        review_status: reviewStatus,
      });
      setDocument(updated);
      setStatus("Review coding saved");
    } catch {
      setStatus("Unable to save review coding");
    }
  }

  async function runReprocess(stage = "all") {
    if (!document) {
      return;
    }
    setStatus(null);
    try {
      const updated = await reprocessDocument(document.id, stage);
      setDocument(updated);
      setStatus(stage === "all" ? "Document reprocessed" : `Retried ${stage}`);
    } catch {
      setStatus("Unable to reprocess document");
    }
  }

  if (error) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Link className="nav-button w-fit" href="/">
          <ArrowLeft size={17} />
          Workspace
        </Link>
        <p className="mt-6 rounded-md border border-line bg-white p-4 text-sm text-rose-700">{error}</p>
      </main>
    );
  }

  if (!document) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-8">
        <p className="rounded-md border border-line bg-white p-4 text-sm text-slate-600">Loading document...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-panel">
      <section className="border-b border-line bg-white">
        <div className="mx-auto max-w-5xl px-6 py-5">
          <Link className="nav-button w-fit" href="/">
            <ArrowLeft size={17} />
            Workspace
          </Link>
          <div className="mt-5 flex items-start gap-3">
            <span className="rounded-md bg-panel p-2 text-accent">
              <FileText size={20} />
            </span>
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Document Source</p>
              <h1 className="mt-1 text-2xl font-semibold text-ink">
                {document.subject || document.original_filename}
              </h1>
              <p className="mt-2 text-sm text-slate-600">
                {document.file_type} / {document.processing_status} / {document.document_type ?? "Unclassified"}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-5 px-6 py-6 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-md border border-line bg-white p-4">
          <h2 className="text-base font-semibold text-ink">Metadata</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <Meta label="Filename" value={document.original_filename} />
            <Meta label="Matter" value={document.matter_id ? String(document.matter_id) : "Unassigned"} />
            <Meta label="Custodian" value={document.custodian_id ? String(document.custodian_id) : "Unassigned"} />
            <Meta label="Sender" value={document.sender ?? "None"} />
            <Meta label="Recipients" value={document.recipients ?? "None"} />
            <Meta label="Date" value={document.document_date ?? document.created_at} />
            <Meta label="Chunks" value={String(document.chunks.length)} />
            <Meta label="OCR" value={document.ocr_status ?? "Not flagged"} />
            <Meta label="Review" value={document.review_status} />
            <Meta label="Privilege" value={document.privilege_flag ? "Flagged" : "Not flagged"} />
            <Meta label="Parent" value={document.parent_document_id ? String(document.parent_document_id) : "None"} />
            <Meta label="Attachment" value={document.attachment_filename ?? "None"} />
          </dl>
          <div className="mt-5 border-t border-line pt-4">
            <h3 className="text-sm font-semibold text-ink">Processing</h3>
            <div className="mt-2 space-y-1 text-sm text-slate-600">
              {Object.entries(document.processing_stages).length === 0 ? (
                <p>No processing stages recorded.</p>
              ) : (
                Object.entries(document.processing_stages).map(([stage, value]) => (
                  <p key={stage}>
                    <span className="font-semibold text-ink">{stage}:</span> {value}
                  </p>
                ))
              )}
              {document.processing_error && <p className="text-rose-700">{document.processing_error}</p>}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="nav-button" onClick={() => void runReprocess("all")} type="button">
                <RefreshCw size={16} />
                Reprocess
              </button>
              <button className="nav-button" onClick={() => void runReprocess("indexing")} type="button">
                Retry Index
              </button>
            </div>
          </div>
          <div className="mt-5 border-t border-line pt-4">
            <h3 className="text-sm font-semibold text-ink">Review Coding</h3>
            <div className="mt-3 space-y-3">
              <label className="block">
                <span className="form-label">Status</span>
                <select className="form-field" value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>
                  <option value="unreviewed">Unreviewed</option>
                  <option value="in_review">In review</option>
                  <option value="responsive">Responsive</option>
                  <option value="non_responsive">Non-responsive</option>
                  <option value="privileged">Privileged</option>
                  <option value="needs_follow_up">Needs follow-up</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input checked={privilegeFlag} onChange={(event) => setPrivilegeFlag(event.target.checked)} type="checkbox" />
                Privilege flag
              </label>
              <label className="block">
                <span className="form-label">Tags</span>
                <input className="form-field" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="hot, key doc" />
              </label>
              <label className="block">
                <span className="form-label">Issue codes</span>
                <input
                  className="form-field"
                  value={issueCodes}
                  onChange={(event) => setIssueCodes(event.target.value)}
                  placeholder="privilege, damages"
                />
              </label>
              <label className="block">
                <span className="form-label">Notes</span>
                <textarea className="form-field min-h-28" value={notes} onChange={(event) => setNotes(event.target.value)} />
              </label>
              <button className="primary-button" onClick={() => void saveCoding()} type="button">
                <Save size={17} />
                Save Coding
              </button>
              {status && <p className="text-sm text-slate-600">{status}</p>}
            </div>
          </div>
          {document.attachment_names.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-ink">Attachments</h3>
              <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
                {document.attachment_names.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            </div>
          )}
          {document.child_documents.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-ink">Document Family</h3>
              <div className="mt-2 space-y-2">
                {document.child_documents.map((child) => (
                  <Link className="block rounded-md border border-line bg-panel p-2 text-sm text-ink" href={`/documents/${child.id}`} key={child.id}>
                    {child.attachment_filename || child.original_filename}
                    <span className="mt-1 block text-xs text-slate-500">{child.processing_status}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
          {document.extraction_warnings.length > 0 && (
            <div className="mt-5 rounded-md border border-amber-200 bg-amber-50 p-3">
              <h3 className="text-sm font-semibold text-amber-900">Processing Notes</h3>
              <ul className="mt-2 list-disc pl-5 text-sm text-amber-800">
                {document.extraction_warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </aside>

        <div className="space-y-5">
          {selectedChunk && (
            <section className="rounded-md border border-accent bg-white p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="text-base font-semibold text-ink">Selected Citation Chunk</h2>
                <div className="flex gap-2">
                  {selectedChunkIndex > 0 && (
                    <Link className="nav-button" href={`/documents/${document.id}?chunk=${document.chunks[selectedChunkIndex - 1].id}&q=${encodeURIComponent(highlightQuery)}`}>
                      <ChevronUp size={16} />
                      Previous
                    </Link>
                  )}
                  {selectedChunkIndex >= 0 && selectedChunkIndex < document.chunks.length - 1 && (
                    <Link className="nav-button" href={`/documents/${document.id}?chunk=${document.chunks[selectedChunkIndex + 1].id}&q=${encodeURIComponent(highlightQuery)}`}>
                      <ChevronDown size={16} />
                      Next
                    </Link>
                  )}
                </div>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-700">{renderHighlightedText(selectedChunk.text, highlightTerms)}</p>
              <p className="mt-2 text-xs text-slate-500">
                chunk {selectedChunk.chunk_index + 1}: {selectedChunk.char_start}-{selectedChunk.char_end}
              </p>
            </section>
          )}

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Entities</h2>
            {document.entity_mentions.length === 0 ? (
              <p className="mt-3 text-sm text-slate-600">No entity mentions extracted.</p>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                {document.entity_mentions.slice(0, 40).map((mention) => (
                  <span
                    key={mention.id}
                    className="rounded-md border border-line bg-panel px-2 py-1 text-xs text-slate-700"
                    title={mention.citation}
                  >
                    {mention.entity_name} / {mention.entity_type}
                  </span>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Relationships</h2>
            {document.relationships.length === 0 ? (
              <p className="mt-3 text-sm text-slate-600">No document-scoped relationships extracted.</p>
            ) : (
              <div className="mt-3 space-y-2">
                {document.relationships.slice(0, 30).map((relationship) => (
                  <article key={relationship.id} className="rounded-md border border-line bg-panel p-3">
                    <p className="text-sm font-semibold text-ink">
                      {relationship.source_entity_name} {relationship.relationship_type.replaceAll("_", " ")}{" "}
                      {relationship.target_entity_name}
                    </p>
                    {relationship.evidence && (
                      <p className="mt-1 text-sm leading-6 text-slate-700">{relationship.evidence}</p>
                    )}
                    <p className="mt-1 text-xs text-slate-500">confidence {relationship.confidence}</p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Extracted Text</h2>
            <div className="mt-3 whitespace-pre-wrap rounded-md border border-line bg-panel p-3 text-sm leading-6 text-slate-700">
              {renderHighlightedText(document.extracted_text || "No extracted text available.", highlightTerms)}
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Chunks</h2>
            <div className="mt-3 space-y-3">
              {document.chunks.map((chunk) => (
                <article
                  key={chunk.id}
                  className={`rounded-md border p-3 ${
                    chunk.id === selectedChunkId ? "border-accent bg-blue-50" : "border-line bg-panel"
                  }`}
                >
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Chunk {chunk.chunk_index + 1} / {chunk.char_start}-{chunk.char_end}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{renderHighlightedText(chunk.text, highlightTerms)}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderHighlightedText(text: string, terms: string[]) {
  if (terms.length === 0) {
    return text;
  }
  const escaped = terms.map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  return text.split(pattern).map((part, index) =>
    terms.some((term) => part.toLowerCase() === term.toLowerCase()) ? (
      <mark className="rounded-sm bg-amber-200 px-0.5 text-ink" key={`${part}-${index}`}>
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-semibold text-ink">{label}</dt>
      <dd className="mt-1 break-words text-slate-600">{value}</dd>
    </div>
  );
}
