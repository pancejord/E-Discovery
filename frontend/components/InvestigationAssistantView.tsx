"use client";

import { Bot, FileText, RefreshCw, Send, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { askAssistant, getMatters, type AIAnswer, type Matter } from "../lib/api";

export function InvestigationAssistantView() {
  const [question, setQuestion] = useState("What do the documents say about the contract and Rule 26?");
  const [answer, setAnswer] = useState<AIAnswer | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [answerMode, setAnswerMode] = useState("summary");
  const [applyRedactions, setApplyRedactions] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matterError, setMatterError] = useState<string | null>(null);

  useEffect(() => {
    void getMatters()
      .then((rows) => {
        setMatters(rows);
        if (rows.length > 0) {
          setMatterId(rows[0].id);
        }
      })
      .catch(() => setMatterError("Unable to load matters"));
  }, []);

  async function submitQuestion() {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setAnswer(
        await askAssistant({
          question: trimmed,
          limit: 5,
          matterId,
          answerMode,
          applyRedactions,
        }),
      );
    } catch {
      setError("Unable to generate an answer");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Assistant</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Cited answers from discovery evidence</h1>
          </div>
            {answer && (
            <div className="rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">
              {answer.provider} / {answer.model ?? "no model"} / {answer.answer_mode}
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-5 lg:grid-cols-[1fr_340px]">
        <div className="rounded-md border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <div className="flex items-center gap-2 text-base font-semibold text-ink">
              <Bot size={18} />
              Ask Documents
            </div>
          </div>
          <div className="space-y-3 p-4">
            <label className="block">
              <span className="form-label">Matter</span>
              <select
                className="form-field"
                value={matterId ?? ""}
                onChange={(event) => setMatterId(event.target.value ? Number(event.target.value) : undefined)}
              >
                <option value="">All matters</option>
                {matters.map((matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.name}
                  </option>
                ))}
              </select>
            </label>
            {matterError && <p className="text-sm text-rose-700">{matterError}</p>}
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <label className="block">
                <span className="form-label">Answer mode</span>
                <select className="form-field" value={answerMode} onChange={(event) => setAnswerMode(event.target.value)}>
                  <option value="summary">Summary</option>
                  <option value="chronology">Chronology</option>
                  <option value="issues">Issues list</option>
                  <option value="contradiction">Contradiction check</option>
                  <option value="privilege">Privilege risk</option>
                  <option value="deposition">Deposition prep</option>
                </select>
              </label>
              <label className="flex items-end gap-2 pb-2 text-sm text-slate-700">
                <input
                  checked={applyRedactions}
                  className="h-4 w-4"
                  onChange={(event) => setApplyRedactions(event.target.checked)}
                  type="checkbox"
                />
                Redact external prompts
              </label>
            </div>
            <textarea
              className="min-h-[120px] w-full resize-y rounded-md border border-line px-3 py-2 text-sm text-ink"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about the uploaded documents"
            />
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-semibold text-white disabled:opacity-60"
                onClick={() => void submitQuestion()}
                type="button"
                disabled={isLoading}
              >
                {isLoading ? <RefreshCw size={17} /> : <Send size={17} />}
                {isLoading ? "Asking" : "Ask"}
              </button>
              {error && <span className="text-sm text-rose-700">{error}</span>}
            </div>
          </div>

          <div className="border-t border-line p-4">
            {isLoading ? (
              <p className="text-sm text-slate-600">Generating a cited answer...</p>
            ) : answer ? (
              <div className="space-y-4">
                <section>
                  <h2 className="text-base font-semibold text-ink">Answer</h2>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{answer.answer}</p>
                </section>

                <section>
                  <h2 className="text-base font-semibold text-ink">Sources</h2>
                  <div className="mt-2 space-y-2">
                    {answer.sources.length === 0 ? (
                      <p className="text-sm text-slate-600">No cited sources were retrieved.</p>
                    ) : (
                      answer.sources.map((source) => (
                        <article key={source.citation} className="rounded-md border border-line bg-panel p-3">
                          <Link
                            className="flex items-center gap-2 text-sm font-semibold text-ink"
                            href={`/documents/${source.document_id}?chunk=${source.chunk_id}`}
                          >
                            <FileText size={16} />
                            {source.title}
                          </Link>
                          <p className="mt-2 text-sm leading-6 text-slate-700">{source.snippet}</p>
                          <p className="mt-2 text-xs text-slate-500">{source.citation}</p>
                        </article>
                      ))
                    )}
                  </div>
                </section>
              </div>
            ) : (
              <p className="text-sm text-slate-600">Ask a question to generate a cited answer.</p>
            )}
          </div>
        </div>

        <aside className="rounded-md border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <div className="flex items-center gap-2 text-base font-semibold text-ink">
              <ShieldCheck size={18} />
              Grounding
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 p-4">
            <Signal label="Citations" value={answer?.grounding.citation_count ?? 0} />
            <Signal label="Valid" value={answer?.grounding.valid_citation_count ?? 0} />
            <Signal label="Unsupported" value={answer?.grounding.unsupported_terms.length ?? 0} />
            <Signal label="Risk" value={answer?.grounding.hallucination_risk_score ?? 0} />
          </div>
          <div className="border-t border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Policy</h2>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <p>External allowed: {String(Boolean(answer?.policy.external_allowed))}</p>
              <p>Redactions applied: {answer?.redactions_applied ? `${answer.redaction_count}` : "0"}</p>
              <p>Mode: {answer?.answer_mode ?? answerMode}</p>
            </div>
          </div>
          <div className="border-t border-line px-4 py-3">
            <h2 className="text-base font-semibold text-ink">Unsupported Terms</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {(answer?.grounding.unsupported_terms ?? []).length === 0 ? (
                <span className="text-sm text-slate-600">None detected</span>
              ) : (
                answer?.grounding.unsupported_terms.map((term) => (
                  <span key={term} className="rounded-md border border-line bg-panel px-2 py-1 text-xs text-slate-700">
                    {term}
                  </span>
                ))
              )}
            </div>
          </div>
          <div className="border-t border-line px-4 py-3 text-sm leading-6 text-slate-600">
            External AI calls are disabled unless configured on the backend. The local mode returns extractive cited
            answers from retrieved source chunks.
          </div>
        </aside>
      </section>
    </main>
  );
}

function Signal({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-panel p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}
