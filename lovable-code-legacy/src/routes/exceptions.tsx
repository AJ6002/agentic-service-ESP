import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { exceptions, severityRank } from "@/data/esp/exceptions";
import { fieldName } from "@/data/esp/fleet";
import { hoursToDuration, n0, usd } from "@/lib/esp/format";
import type { EspException, Severity } from "@/data/esp/types";
import { KpiStrip, Metric, Note, PageHeader, Panel, StatusPill, Td, Th, ToggleRow } from "@/components/esp/ui";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/exceptions")({
  head: () => ({
    meta: [
      { title: "Exception & Opportunity Queue — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Ranked ESP exception queue with evidence, likely causes, verification steps, recommended actions and acknowledge / assign / close workflow.",
      },
      { property: "og:title", content: "ESP Exception & Opportunity Queue" },
      { property: "og:description", content: "Evidence-backed ESP exceptions ranked by severity and production impact." },
    ],
  }),
  component: ExceptionQueue,
});

const severityTone: Record<Severity, "critical" | "warning" | "watch" | "info" | "opportunity"> = {
  critical: "critical",
  warning: "warning",
  watch: "watch",
  info: "info",
  opportunity: "opportunity",
};

const views = ["All", "Critical", "Warning", "Watch", "Opportunities", "Unassigned"] as const;

function ExceptionQueue() {
  const [view, setView] = useState<(typeof views)[number]>("All");
  const [selectedId, setSelectedId] = useState<string>(exceptions[0]?.id ?? "");
  const [statuses, setStatuses] = useState<Record<string, EspException["status"]>>({});

  const rows = useMemo(
    () =>
      exceptions
        .filter((e) => {
          switch (view) {
            case "All":
              return true;
            case "Critical":
              return e.severity === "critical";
            case "Warning":
              return e.severity === "warning";
            case "Watch":
              return e.severity === "watch";
            case "Opportunities":
              return e.severity === "opportunity";
            case "Unassigned":
              return (statuses[e.id] ?? e.status) === "Open";
          }
        })
        .sort((a, b) => severityRank[a.severity] - severityRank[b.severity] || b.impactBopd - a.impactBopd),
    [view, statuses],
  );

  const selected = exceptions.find((e) => e.id === selectedId) ?? rows[0];
  const status = selected ? (statuses[selected.id] ?? selected.status) : "Open";

  const setStatus = (id: string, s: EspException["status"]) => setStatuses((cur) => ({ ...cur, [id]: s }));

  const totals = {
    critical: exceptions.filter((e) => e.severity === "critical").length,
    warning: exceptions.filter((e) => e.severity === "warning").length,
    watch: exceptions.filter((e) => e.severity === "watch").length,
    opportunity: exceptions.filter((e) => e.severity === "opportunity").length,
    impact: exceptions.reduce((a, e) => a + e.impactBopd, 0),
    upside: exceptions.filter((e) => e.severity === "opportunity").reduce((a, e) => a + e.impactBopd, 0),
  };

  return (
    <div className="space-y-3">
      <PageHeader
        title="Exception & Opportunity Queue"
        description="One prioritised list for the whole ESP fleet. Every item states what was observed, what evidence supports it, how to verify it and what action is recommended — so surveillance turns into decisions instead of alarm noise."
        meta={
          <>
            <StatusPill tone="info">Rules evaluated on normalised OTConnex signals</StatusPill>
            <StatusPill tone="muted">Confidence values are demo heuristics</StatusPill>
          </>
        }
        actions={<ToggleRow options={views} value={view} onChange={setView} />}
      />

      <KpiStrip>
        <Metric label="Critical" value={totals.critical} tone="critical" sub="Immediate action" />
        <Metric label="Warning" value={totals.warning} tone="warning" sub="Same-shift review" />
        <Metric label="Watch" value={totals.watch} tone="watch" sub="Monitor trend" />
        <Metric label="Opportunities" value={totals.opportunity} tone="opportunity" sub="Upside candidates" />
        <Metric label="Impact at risk" value={n0(totals.impact)} unit="bopd" tone="warning" sub="Sum of active impacts" />
        <Metric label="Upside identified" value={n0(totals.upside)} unit="bopd" tone="opportunity" sub="Scenario estimates" />
        <Metric label="Value at stake" value={usd((totals.impact + totals.upside) * 68)} unit="/day" sub="Demo price deck" />
      </KpiStrip>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel title={`Queue — ${rows.length} items`} bodyClassName="p-0">
          <div className="overflow-auto panel-scroll" style={{ maxHeight: "calc(100vh - 330px)" }}>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Sev</Th>
                  <Th>Well</Th>
                  <Th>Category</Th>
                  <Th align="right">Impact</Th>
                  <Th align="right">Age</Th>
                  <Th>Status</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map((e) => (
                  <tr
                    key={e.id}
                    onClick={() => setSelectedId(e.id)}
                    className={cn("cursor-pointer hover:bg-accent/40", selected?.id === e.id && "bg-primary/10")}
                  >
                    <Td>
                      <StatusPill tone={severityTone[e.severity]}>{e.severity}</StatusPill>
                    </Td>
                    <Td mono>{e.wellId}</Td>
                    <Td className="max-w-[190px] truncate">{e.category}</Td>
                    <Td align="right" mono>{e.impactBopd ? n0(e.impactBopd) : "—"}</Td>
                    <Td align="right" mono className="text-muted-foreground">{hoursToDuration(e.durationH)}</Td>
                    <Td>
                      <StatusPill tone={(statuses[e.id] ?? e.status) === "Closed" ? "normal" : "muted"} dot={false}>
                        {statuses[e.id] ?? e.status}
                      </StatusPill>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        {selected && (
          <Panel
            title={`${selected.id} — ${selected.category}`}
            subtitle={`${selected.wellId} · ${fieldName(selected.fieldId)} · first seen ${selected.firstSeen}`}
            actions={
              <div className="flex items-center gap-1">
                {(["Acknowledged", "Assigned", "Closed"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStatus(selected.id, s)}
                    className={cn(
                      "rounded border px-2 py-1 text-[11px]",
                      status === s ? "border-primary/60 bg-primary/20 font-semibold text-foreground" : "border-border bg-card hover:bg-accent",
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
            }
          >
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <StatusPill tone={severityTone[selected.severity]}>{selected.severity}</StatusPill>
                <StatusPill tone="muted">Owner: {selected.owner}</StatusPill>
                <StatusPill tone="muted">Status: {status}</StatusPill>
                <StatusPill tone="info">Confidence {(selected.confidence * 100).toFixed(0)}%</StatusPill>
                <Link to="/wells/$wellId" params={{ wellId: selected.wellId }} className="text-[11px] text-primary hover:underline">
                  Open Well Monitor →
                </Link>
                <Link to="/engineering/workbench" search={{ well: selected.wellId }} className="text-[11px] text-primary hover:underline">
                  Analyse in Workbench →
                </Link>
              </div>

              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Rule</div>
                <p className="text-[12px]">{selected.rule}</p>
              </div>
              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Observation</div>
                <p className="text-[12px]">{selected.observation}</p>
              </div>

              <div className="grid gap-3 lg:grid-cols-2">
                <div>
                  <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Evidence</div>
                  <ul className="mt-1 space-y-1 text-[11px]">
                    {selected.evidence.map((x, i) => <li key={i}>· {x}</li>)}
                  </ul>
                </div>
                <div>
                  <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Likely causes (ranked)</div>
                  <div className="mt-1 space-y-1">
                    {selected.likelyCauses.map((c, i) => (
                      <div key={i}>
                        <div className="flex items-baseline justify-between text-[11px]">
                          <span>{c.cause}</span>
                          <span className="num text-muted-foreground">{(c.weight * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1 rounded bg-card">
                          <div className="h-1 rounded bg-chart-4" style={{ width: `${c.weight * 100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Verification steps</div>
                  <ul className="mt-1 space-y-1 text-[11px]">
                    {selected.verify.map((x, i) => <li key={i}>{i + 1}. {x}</li>)}
                  </ul>
                </div>
                <div>
                  <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Recommended action</div>
                  <ul className="mt-1 space-y-1 text-[11px]">
                    {selected.recommendedAction.map((x, i) => <li key={i}>{i + 1}. {x}</li>)}
                  </ul>
                </div>
              </div>

              <Note tone={selected.severity === "opportunity" ? "opportunity" : "warning"}>
                Production impact: {selected.impactNote} Estimated value {usd(selected.opportunityUsdDay)}/day.
              </Note>
              <Note>
                Workflow in this mockup is illustrative: acknowledge, assign and close update local state only. In the delivered module these transitions
                use the ADVAIT workflow and notification services with full audit history.
              </Note>
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}
