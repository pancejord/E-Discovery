import {
  BarChart3,
  Bot,
  FileSearch,
  GitBranch,
  Search,
  ShieldCheck,
  Upload,
} from "lucide-react";
import Link from "next/link";

const metrics = [
  { label: "Documents", value: "0", hint: "Awaiting ingestion" },
  { label: "Entities", value: "0", hint: "NER pending" },
  { label: "Relationships", value: "0", hint: "Graph pending" },
  { label: "Evaluation Runs", value: "0", hint: "No benchmarks yet" },
];

const workstreams = [
  {
    title: "Document Intake",
    detail: "Upload, parse, and normalize matter documents.",
    icon: Upload,
  },
  {
    title: "AI Search",
    detail: "Blend keyword, metadata, vector retrieval, and citations.",
    icon: Search,
  },
  {
    title: "Entity Review",
    detail: "Track people, organizations, dates, and legal references.",
    icon: FileSearch,
  },
  {
    title: "Knowledge Graph",
    detail: "Map communications and document relationships.",
    icon: GitBranch,
  },
  {
    title: "Analytics",
    detail: "Review counts, timelines, custodians, and file types.",
    icon: BarChart3,
  },
  {
    title: "Evaluation",
    detail: "Measure retrieval relevance and citation quality.",
    icon: ShieldCheck,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">
                Litigation Analytics Workspace
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-ink">
                eDiscovery investigation dashboard
              </h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">
                <Upload size={18} />
                Upload
              </button>
              <Link
                href="/assistant"
                className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink"
              >
                <Bot size={18} />
                Assistant
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink"
              >
                <BarChart3 size={18} />
                Dashboard
              </Link>
              <Link
                href="/graph"
                className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink"
              >
                <GitBranch size={18} />
                Graph
              </Link>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="rounded-md border border-line bg-panel p-4">
                <p className="text-sm text-slate-600">{metric.label}</p>
                <p className="mt-1 text-2xl font-semibold text-ink">{metric.value}</p>
                <p className="mt-1 text-xs text-slate-500">{metric.hint}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-md border border-line bg-white p-4">
          <h2 className="text-base font-semibold text-ink">Matter Setup</h2>
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="text-sm text-slate-600">Matter name</span>
              <input
                className="mt-1 w-full rounded-md border border-line px-3 py-2"
                placeholder="New investigation"
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600">Custodian</span>
              <input
                className="mt-1 w-full rounded-md border border-line px-3 py-2"
                placeholder="Optional"
              />
            </label>
            <button className="w-full rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
              Create Matter
            </button>
          </div>
        </aside>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {workstreams.map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.title} className="rounded-md border border-line bg-white p-4">
                <div className="flex items-start gap-3">
                  <span className="rounded-md bg-panel p-2 text-accent">
                    <Icon size={20} />
                  </span>
                  <div>
                    <h2 className="text-base font-semibold text-ink">{item.title}</h2>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{item.detail}</p>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
