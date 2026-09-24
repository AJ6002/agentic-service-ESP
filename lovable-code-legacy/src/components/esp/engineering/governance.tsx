import type { ReactNode } from "react";
import { StatusPill, type Tone } from "@/components/esp/ui";

/** Reliability classes used across the governed engineering catalog. */
export const RELIABILITY_CLASSES = [
  { code: "A1", label: "Current OEM model datasheet / direct model evidence", tone: "normal" as Tone, calcGrade: true },
  { code: "A2", label: "Current OEM catalog or official series/product evidence", tone: "normal" as Tone, calcGrade: true },
  { code: "B1", label: "Peer-reviewed literature or OEM training/reference", tone: "info" as Tone, calcGrade: true },
  { code: "B2", label: "Historical OEM-origin catalog / internal engineering reference", tone: "watch" as Tone, calcGrade: true },
  { code: "C1", label: "Curated secondary catalog (e.g. Pengtools) — discovery only", tone: "warning" as Tone, calcGrade: false },
  { code: "D", label: "Missing / unresolved / inferred — do not use for calculations", tone: "critical" as Tone, calcGrade: false },
];

const UNKNOWN_CLASS = { code: "D", label: "Missing / unresolved / inferred — do not use for calculations", tone: "critical" as Tone, calcGrade: false };

export function reliabilityInfo(code: string | null | undefined) {
  return RELIABILITY_CLASSES.find((r) => r.code === code) ?? UNKNOWN_CLASS;
}

export function isCalculationGrade(code: string | null | undefined) {
  return reliabilityInfo(code).calcGrade;
}

export function ReliabilityBadge({ code, title }: { code: string | null | undefined; title?: boolean }) {
  const info = reliabilityInfo(code);
  return (
    <StatusPill tone={info.tone} dot={false}>
      <span title={info.label}>{code ?? "D"}{title ? ` · ${info.label}` : ""}</span>
    </StatusPill>
  );
}

/**
 * Catalog curve availability (what the source document contains) is a DIFFERENT
 * fact from digitised curve points held in this build. A model is never shown as
 * a usable full curve unless actual source curve points are loaded — no synthetic
 * curve is ever generated or implied.
 */
export function curveAvailability(status: string | null | undefined): { label: string; tone: Tone } {
  const s = (status ?? "").toLowerCase();
  if (!s) return { label: "No curve evidence", tone: "critical" };
  if (s.includes("one-stage curve")) {
    return { label: s.includes("historical") ? "Historical catalog 1-stage curve" : "Catalog 1-stage curve", tone: "info" };
  }
  if (s.includes("composite") || s.includes("tapered")) return { label: "Composite — component curves", tone: "info" };
  if (s.includes("peer-reviewed") || s.includes("test/reference")) return { label: "Reference test point", tone: "watch" };
  if (s.includes("series envelope") || s.includes("envelope")) return { label: "BEP/Envelope only", tone: "watch" };
  if (s.includes("pending")) return { label: "Curve pending", tone: "warning" };
  if (s.includes("model index")) return { label: "Model index only", tone: "warning" };
  if (s.includes("unverified")) return { label: "Unverified model text", tone: "warning" };
  if (s.includes("blocked")) return { label: "Blocked — model unresolved", tone: "critical" };
  return { label: status ?? "No curve evidence", tone: "critical" };
}

/**
 * @param status catalog curve availability text from the governed source record
 * @param digitisedPoints number of digitised curve points actually loaded in this build
 */
export function CurveStatusBadge({
  status,
  digitisedPoints,
}: {
  status: string | null | undefined;
  digitisedPoints?: number;
}) {
  const c = curveAvailability(status);
  return (
    <span className="inline-flex items-center gap-1">
      <StatusPill tone={c.tone} dot={false}>{c.label}</StatusPill>
      {digitisedPoints === undefined ? null : digitisedPoints > 0 ? (
        <StatusPill tone="normal" dot={false}>{digitisedPoints} digitised pts</StatusPill>
      ) : (
        <StatusPill tone="watch" dot={false}>Not digitised</StatusPill>
      )}
    </span>
  );
}

export function VerificationBadge({ status }: { status: string | null | undefined }) {
  const tone: Tone = status === "verified" ? "normal" : status === "partially-verified" ? "watch" : "warning";
  return <StatusPill tone={tone} dot={false}>{status ?? "unverified"}</StatusPill>;
}

export function FieldRow({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border/60 px-2 py-1 last:border-b-0">
      <span className="text-[10px] tracking-wide text-muted-foreground uppercase">{label}</span>
      <span className="num text-right text-[11px] text-foreground" title={hint}>
        {value === null || value === undefined || value === "" ? <span className="text-muted-foreground">—</span> : value}
      </span>
    </div>
  );
}

export function num(v: number | null | undefined, digits = 0, suffix = "") {
  if (v === null || v === undefined) return "—";
  return `${Number(v).toLocaleString(undefined, { maximumFractionDigits: digits })}${suffix}`;
}
