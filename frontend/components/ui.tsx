import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <section className="app-section-header">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">{eyebrow}</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">{title}</h1>
          {description && <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </section>
  );
}

export function Panel({ title, children, actions }: { title?: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="app-card">
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function MetricTile({ label, value, icon }: { label: string; value: number | string; icon?: ReactNode }) {
  return (
    <div className="app-card p-4">
      <div className="flex items-center justify-between text-slate-600">
        <span className="text-sm font-medium">{label}</span>
        {icon && <span className="text-accent">{icon}</span>}
      </div>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-line bg-panel p-6 text-center text-sm text-slate-600">
      {message}
    </div>
  );
}

export function Alert({ tone = "neutral", children }: { tone?: "neutral" | "danger"; children: ReactNode }) {
  const className =
    tone === "danger"
      ? "rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
      : "rounded-lg border border-line bg-white p-3 text-sm text-slate-700";
  return <div className={className}>{children}</div>;
}
