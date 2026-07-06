"use client";

import { CheckCircle2, FlaskConical, RefreshCw, XCircle } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  getBenchmarks,
  getEvaluationMetrics,
  getEvaluationSummaries,
  getEvaluationTrends,
  getMatters,
  runEvaluation,
  type BenchmarkCase,
  type EvaluationMetric,
  type EvaluationSummary,
  type EvaluationTrendPoint,
  type Matter,
} from "../../lib/api";

type TaskType = "retrieval" | "answer" | "extraction" | "all";

export default function EvaluationPage() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkCase[]>([]);
  const [metrics, setMetrics] = useState<EvaluationMetric[]>([]);
  const [summaries, setSummaries] = useState<EvaluationSummary[]>([]);
  const [trends, setTrends] = useState<EvaluationTrendPoint[]>([]);
  const [latestRun, setLatestRun] = useState<EvaluationMetric[]>([]);
  const [matterId, setMatterId] = useState<number | undefined>();
  const [datasetName, setDatasetName] = useState("phase6_synthetic_retrieval");
  const [taskType, setTaskType] = useState<TaskType>("retrieval");
  const [limit, setLimit] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const datasets = useMemo(
    () => Array.from(new Set(benchmarks.map((benchmark) => benchmark.dataset_name))).sort(),
    [benchmarks],
  );
  const visibleBenchmarks = benchmarks.filter((benchmark) => benchmark.dataset_name === datasetName);
  const displayMetrics = latestRun.length > 0 ? latestRun : metrics;
  const passMetrics = displayMetrics.filter((metric) => metric.metric_name.includes("benchmark_pass"));
  const failedPassMetrics = passMetrics.filter((metric) => metric.metric_value < 1);
  const answerMetrics = latestByName(displayMetrics, [
    "answer_citation_validity",
    "answer_unsupported_term_rate",
    "answer_hallucination_risk",
  ]);
  const qdrantMetrics = latestByName(displayMetrics, [
    "qdrant_local_result_overlap",
    "qdrant_local_top_result_match",
    "qdrant_result_count_delta",
  ]);
  const extractionMetrics = latestByName(displayMetrics, [
    "classification_match",
    "document_date_match",
    "entity_coverage",
    "relationship_coverage",
    "ocr_term_coverage",
  ]);

  async function load(nextMatterId = matterId) {
    setIsLoading(true);
    setError(null);
    try {
      const [matterRows, benchmarkRows, metricRows, summaryRows, trendRows] = await Promise.all([
        getMatters(),
        getBenchmarks(),
        getEvaluationMetrics(nextMatterId),
        getEvaluationSummaries(nextMatterId),
        getEvaluationTrends("benchmark_pass", nextMatterId),
      ]);
      setMatters(matterRows);
      setBenchmarks(benchmarkRows);
      setMetrics(metricRows);
      setSummaries(summaryRows);
      setTrends(trendRows);
      if (!benchmarkRows.some((benchmark) => benchmark.dataset_name === datasetName) && benchmarkRows[0]) {
        setDatasetName(benchmarkRows[0].dataset_name);
      }
    } catch {
      setError("Unable to load evaluation data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function submitRun() {
    setIsRunning(true);
    setError(null);
    try {
      const response = await runEvaluation({
        matterId,
        datasetName,
        taskType,
        limit,
      });
      setLatestRun(response.metrics);
      const [metricRows, summaryRows, trendRows] = await Promise.all([
        getEvaluationMetrics(matterId),
        getEvaluationSummaries(matterId),
        getEvaluationTrends(taskType === "extraction" ? "extraction_benchmark_pass" : "benchmark_pass", matterId),
      ]);
      setMetrics(metricRows);
      setSummaries(summaryRows);
      setTrends(trendRows);
    } catch {
      setError("Unable to run evaluation");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Evaluation</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Benchmark quality review</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/" className="nav-button">
              Workspace
            </Link>
            <button className="nav-button" onClick={() => void load()} type="button">
              <RefreshCw size={18} />
              Refresh
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[340px_1fr]">
        <aside className="rounded-md border border-line bg-white p-4">
          <div className="flex items-center gap-2">
            <FlaskConical className="text-accent" size={18} />
            <h2 className="text-base font-semibold text-ink">Run Controls</h2>
          </div>
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="form-label">Matter</span>
              <select
                className="form-field"
                value={matterId ?? ""}
                onChange={(event) => {
                  const nextMatterId = event.target.value ? Number(event.target.value) : undefined;
                  setMatterId(nextMatterId);
                  setLatestRun([]);
                  void load(nextMatterId);
                }}
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
              <span className="form-label">Dataset</span>
              <select className="form-field" value={datasetName} onChange={(event) => setDatasetName(event.target.value)}>
                {datasets.map((dataset) => (
                  <option key={dataset} value={dataset}>
                    {dataset}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">Task</span>
              <select className="form-field" value={taskType} onChange={(event) => setTaskType(event.target.value as TaskType)}>
                <option value="retrieval">Retrieval</option>
                <option value="answer">Answer</option>
                <option value="extraction">Extraction</option>
                <option value="all">Combined</option>
              </select>
            </label>
            <label className="block">
              <span className="form-label">Result limit</span>
              <input
                className="form-field"
                min={1}
                max={50}
                type="number"
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
              />
            </label>
            <button className="primary-button" disabled={isRunning} onClick={() => void submitRun()} type="button">
              <FlaskConical size={17} />
              {isRunning ? "Running" : "Run Evaluation"}
            </button>
          </div>
        </aside>

        <div className="space-y-5">
          {error && <p className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

          <section className="grid gap-3 md:grid-cols-4">
            <Metric label="Benchmarks" value={visibleBenchmarks.length} />
            <Metric label="Metrics" value={displayMetrics.length} />
            <Metric label="Passes" value={passMetrics.filter((metric) => metric.metric_value >= 1).length} />
            <Metric label="Failures" value={failedPassMetrics.length} />
          </section>

          <section className="grid gap-3 md:grid-cols-3">
            {summaries.slice(0, 6).map((summary) => (
              <SummaryCard key={`${summary.dataset_name}-${summary.task_type}-${summary.metric_name}`} summary={summary} />
            ))}
          </section>

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Benchmark Results</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {passMetrics.length === 0 ? (
                <p className="text-sm text-slate-600">{isLoading ? "Loading evaluations" : "No benchmark pass metrics yet"}</p>
              ) : (
                passMetrics.map((metric) => <BenchmarkResult key={metric.id ?? `${metric.case_id}-${metric.metric_name}`} metric={metric} />)
              )}
            </div>
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <MetricPanel title="Answer Quality" metrics={answerMetrics} />
            <MetricPanel title="Qdrant Comparison" metrics={qdrantMetrics} />
            <MetricPanel title="Extraction Quality" metrics={extractionMetrics} />
            <TrendPanel trends={trends} />
          </section>

          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-base font-semibold text-ink">Metric History</h2>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[840px] border-collapse text-left text-sm">
                <thead className="border-b border-line text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="py-2 pr-3">Time</th>
                    <th className="py-2 pr-3">Dataset</th>
                    <th className="py-2 pr-3">Case</th>
                    <th className="py-2 pr-3">Task</th>
                    <th className="py-2 pr-3">Metric</th>
                    <th className="py-2 pr-3">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.slice(0, 80).map((metric) => (
                    <tr key={metric.id ?? `${metric.created_at}-${metric.metric_name}`} className="border-b border-line">
                      <td className="py-3 pr-3 text-slate-600">{new Date(metric.created_at).toLocaleString()}</td>
                      <td className="py-3 pr-3">{metric.dataset_name ?? "-"}</td>
                      <td className="py-3 pr-3">{metric.case_id ?? "-"}</td>
                      <td className="py-3 pr-3">{metric.task_type}</td>
                      <td className="py-3 pr-3 font-semibold text-ink">{metric.metric_name}</td>
                      <td className="py-3 pr-3">{formatMetric(metric.metric_value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function MetricPanel({ title, metrics }: { title: string; metrics: EvaluationMetric[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 space-y-3">
        {metrics.length === 0 ? (
          <p className="text-sm text-slate-600">No metrics yet</p>
        ) : (
          metrics.map((metric) => (
            <div key={metric.metric_name} className="flex items-center justify-between gap-3 rounded-md bg-panel p-3">
              <span className="text-sm font-semibold text-ink">{humanize(metric.metric_name)}</span>
              <span className="text-sm text-slate-700">{formatMetric(metric.metric_value)}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function SummaryCard({ summary }: { summary: EvaluationSummary }) {
  return (
    <article className="rounded-md border border-line bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{summary.task_type ?? "all"}</p>
      <h3 className="mt-1 text-sm font-semibold text-ink">{humanize(summary.metric_name)}</h3>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <span className="text-slate-600">Latest</span>
        <span className="text-right font-semibold text-ink">{formatMetric(summary.latest_value)}</span>
        <span className="text-slate-600">Average</span>
        <span className="text-right font-semibold text-ink">{formatMetric(summary.average_value)}</span>
        <span className="text-slate-600">Runs</span>
        <span className="text-right font-semibold text-ink">{summary.run_count}</span>
      </div>
    </article>
  );
}

function TrendPanel({ trends }: { trends: EvaluationTrendPoint[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-base font-semibold text-ink">Trend Points</h2>
      <div className="mt-4 space-y-2">
        {trends.length === 0 ? (
          <p className="text-sm text-slate-600">No trend data yet</p>
        ) : (
          trends.slice(-8).map((point, index) => (
            <div key={`${point.metric_name}-${point.created_at}-${index}`} className="grid grid-cols-[1fr_auto] gap-3 rounded-md bg-panel p-3 text-sm">
              <span className="text-slate-700">
                {point.case_id ?? point.dataset_name ?? point.metric_name}
                <span className="ml-2 text-xs text-slate-500">{new Date(point.created_at).toLocaleString()}</span>
              </span>
              <span className="font-semibold text-ink">{formatMetric(point.metric_value)}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function BenchmarkResult({ metric }: { metric: EvaluationMetric }) {
  const passed = metric.metric_value >= 1;
  const results = Array.isArray(metric.details?.results) ? metric.details.results : [];
  const owner = typeof metric.details?.owner === "string" ? metric.details.owner : null;
  const triage = typeof metric.details?.triage_notes === "string" ? metric.details.triage_notes : null;
  return (
    <article className="rounded-md border border-line bg-panel p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-ink">{metric.case_id ?? "benchmark"}</p>
          <p className="mt-1 text-xs text-slate-500">{new Date(metric.created_at).toLocaleString()}</p>
          {(owner || triage) && (
            <p className="mt-2 text-xs leading-5 text-slate-600">
              {owner ? `Owner: ${owner}. ` : ""}
              {triage ?? ""}
            </p>
          )}
        </div>
        <span className={`inline-flex items-center gap-1 text-sm font-semibold ${passed ? "text-emerald-700" : "text-rose-700"}`}>
          {passed ? <CheckCircle2 size={17} /> : <XCircle size={17} />}
          {passed ? "Pass" : "Fail"}
        </span>
      </div>
      {!passed && results.length > 0 && (
        <div className="mt-3 space-y-1 text-sm">
          {results.slice(0, 3).map((result, index) => {
            const row = result as { document_id?: number; chunk_id?: number; citation?: string; title?: string };
            return (
              <Link
                className="block text-accent hover:underline"
                href={`/documents/${row.document_id}${row.chunk_id ? `?chunk=${row.chunk_id}` : ""}`}
                key={`${row.document_id}-${row.chunk_id}-${index}`}
              >
                {row.title ?? row.citation ?? `Document ${row.document_id}`}
              </Link>
            );
          })}
        </div>
      )}
    </article>
  );
}

function latestByName(metrics: EvaluationMetric[], names: string[]) {
  return names
    .map((name) => metrics.find((metric) => metric.metric_name === name))
    .filter((metric): metric is EvaluationMetric => Boolean(metric));
}

function formatMetric(value: number) {
  if (Math.abs(value) > 1) {
    return value.toFixed(2);
  }
  return `${Math.round(value * 100)}%`;
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}
