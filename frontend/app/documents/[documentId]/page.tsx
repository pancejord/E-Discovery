"use client";

import { ArrowLeft, FileText } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { getDocument, type DocumentDetail } from "../../../lib/api";

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
  const documentId = Number(params.documentId);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) {
      return;
    }
    void getDocument(documentId)
      .then(setDocument)
      .catch(() => setError("Unable to load document"));
  }, [documentId]);

  const selectedChunk = useMemo(
    () => document?.chunks.find((chunk) => chunk.id === selectedChunkId),
    [document, selectedChunkId],
  );

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
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">Document Source</p>
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
          </dl>
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
              <h2 className="text-base font-semibold text-ink">Selected Citation Chunk</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">{selectedChunk.text}</p>
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
            <pre className="mt-3 whitespace-pre-wrap rounded-md border border-line bg-panel p-3 text-sm leading-6 text-slate-700">
              {document.extracted_text || "No extracted text available."}
            </pre>
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
                  <p className="mt-2 text-sm leading-6 text-slate-700">{chunk.text}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
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
