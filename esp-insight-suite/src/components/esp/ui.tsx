import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export type Tone = "normal" | "watch" | "warning" | "critical" | "stopped" | "info" | "opportunity" | "muted";

const toneClasses: Record<Tone, string> = {
  normal: "bg-normal/15 text-normal border-normal/40",
  watch: "bg-watch/15 text-watch border-watch/40",
  warning: "bg-warning/15 text-warning border-warning/40",
  critical: "bg-critical/20 text-critical border-critical/50",
  stopped: "bg-stopped/20 text-stopped-foreground border-stopped/50",
  info: "bg-info/15 text-info border-info/40",
  opportunity: "bg-opportunity/15 text-opportunity border-opportunity/40",
  muted: "bg-muted text-muted-foreground border-border",
};

export const textTone: Record<Tone, string> = {
  normal: "text-normal",
  watch: "text-watch",
  warning: "text-warning",
  critical: "text-critical",
  stopped: "text-stopped-foreground",
  info: "text-info",
  opportunity: "text-opportunity",
  muted: "text-muted-foreground",
};

const dotClasses: Record<Tone, string> = {
  normal: "bg-normal",
  watch: "bg-watch",
  warning: "bg-warning",
  critical: "bg-critical",
  stopped: "bg-stopped",
  info: "bg-info",
  opportunity: "bg-opportunity",
  muted: "bg-muted-foreground",
};

export function StatusPill({
  tone = "muted",
  children,
  dot = true,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-[11px] font-medium whitespace-nowrap",
        toneClasses[tone],
        className,
      )}
    >
      {dot && <span className={cn("size-1.5 shrink-0 rounded-full", dotClasses[tone])} />}
      {children}
    </span>
  );
}

export function Panel({
  title,
  subtitle,
  actions,
  children,
  className,
  bodyClassName,
  footer,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  footer?: ReactNode;
}) {
  return (
    <section className={cn("flex min-w-0 flex-col overflow-hidden rounded-md border border-border bg-panel", className)}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-border bg-panel-header px-3 py-2">
          <div className="min-w-0">
            <h2 className="truncate text-[12px] font-semibold tracking-wide text-foreground uppercase">{title}</h2>
            {subtitle && <p className="mt-0.5 truncate text-[11px] text-muted-foreground">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
        </header>
      )}
      <div className={cn("min-w-0 flex-1", bodyClassName ?? "p-3")}>{children}</div>
      {footer && <footer className="border-t border-border px-3 py-1.5 text-[11px] text-muted-foreground">{footer}</footer>}
    </section>
  );
}

export function Metric({
  label,
  value,
  unit,
  sub,
  tone,
  className,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0 rounded border border-border bg-card px-2.5 py-2", className)}>
      <div className="truncate text-[10px] font-medium tracking-wider text-muted-foreground uppercase">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className={cn("num text-[17px] leading-none font-semibold", tone && textTone[tone])}>{value}</span>
        {unit && <span className="text-[10px] text-muted-foreground">{unit}</span>}
      </div>
      {sub && <div className="mt-1 truncate text-[10px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

export function KpiStrip({ children }: { children: ReactNode }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">{children}</div>
  );
}

export function DataQualityBadge({ quality }: { quality: "good" | "degraded" | "stale" | "lost" }) {
  const map = {
    good: { tone: "normal" as Tone, label: "Data good" },
    degraded: { tone: "watch" as Tone, label: "Data degraded" },
    stale: { tone: "watch" as Tone, label: "Data stale" },
    lost: { tone: "critical" as Tone, label: "Gauge signal lost" },
  };
  const m = map[quality];
  return <StatusPill tone={m.tone}>{m.label}</StatusPill>;
}

export function ToggleRow<T extends string>({
  options,
  value,
  onChange,
  size = "sm",
}: {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  size?: "sm" | "xs";
}) {
  return (
    <div className="inline-flex overflow-hidden rounded border border-border">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          onClick={() => onChange(o)}
          className={cn(
            "border-r border-border px-2 py-1 text-[11px] transition-colors last:border-r-0",
            size === "xs" && "px-1.5 py-0.5 text-[10px]",
            value === o
              ? "bg-primary/20 font-semibold text-foreground"
              : "bg-card text-muted-foreground hover:bg-accent hover:text-foreground",
          )}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

export function Note({ children, tone = "muted" }: { children: ReactNode; tone?: Tone }) {
  return (
    <p
      className={cn(
        "rounded border px-2 py-1.5 text-[11px] leading-relaxed",
        tone === "muted" ? "border-border bg-card text-muted-foreground" : toneClasses[tone],
      )}
    >
      {children}
    </p>
  );
}

export function PageHeader({
  title,
  description,
  meta,
  actions,
}: {
  title: string;
  description: string;
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-3">
      <div className="min-w-0">
        <h1 className="text-[15px] font-semibold text-foreground">{title}</h1>
        <p className="mt-0.5 max-w-4xl text-[12px] text-muted-foreground">{description}</p>
        {meta && <div className="mt-2 flex flex-wrap items-center gap-1.5">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Th({ children, className, align = "left" }: { children?: ReactNode; className?: string; align?: "left" | "right" }) {
  return (
    <th
      className={cn(
        "sticky top-0 z-10 border-b border-border bg-panel-header px-2 py-1.5 text-[10px] font-semibold tracking-wider text-muted-foreground uppercase",
        align === "right" ? "text-right" : "text-left",
        className,
      )}
    >
      {children}
    </th>
  );
}

export function Td({
  children,
  className,
  align = "left",
  mono,
}: {
  children?: ReactNode;
  className?: string;
  align?: "left" | "right";
  mono?: boolean;
}) {
  return (
    <td
      className={cn(
        "border-b border-border/60 px-2 py-1.5 text-[12px] whitespace-nowrap",
        align === "right" && "text-right",
        mono && "num",
        className,
      )}
    >
      {children}
    </td>
  );
}

export function SortHeader<T extends string>({
  label,
  field,
  sort,
  onSort,
  align = "left",
}: {
  label: string;
  field: T;
  sort: { field: T; dir: "asc" | "desc" };
  onSort: (f: T) => void;
  align?: "left" | "right";
}) {
  const active = sort.field === field;
  return (
    <Th align={align}>
      <button
        type="button"
        onClick={() => onSort(field)}
        className={cn("inline-flex items-center gap-1 uppercase hover:text-foreground", active && "text-foreground")}
      >
        {label}
        <span className="text-[9px] opacity-70">{active ? (sort.dir === "asc" ? "▲" : "▼") : "↕"}</span>
      </button>
    </Th>
  );
}
