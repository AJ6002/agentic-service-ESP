import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  badActors,
  componentDistribution,
  failureModePareto,
  failures,
  interventions,
  runLifeByFamily,
  runLifeByField,
  runLifeBuckets,
  runLifeFactors,
} from "@/data/esp/reliability";
import { fields, wellById } from "@/data/esp/fleet";
import { n0, usd } from "@/lib/esp/format";
import { ParetoChart, SimpleBar } from "@/components/esp/charts";
import { KpiStrip, Metric, Note, PageHeader, Panel, StatusPill, Td, Th, ToggleRow } from "@/components/esp/ui";
import { EspWellMini } from "@/components/esp/EspWellVisual";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reliability")({
  head: () => ({
    meta: [
      { title: "Reliability & Run Life — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "ESP run-life analytics, failure-mode Pareto, DIFA findings, bad-actor ranking and intervention planning across the ESP fleet.",
      },
      { property: "og:title", content: "ESP Reliability & Run Life" },
      { property: "og:description", content: "Run-life distributions, failure Pareto, DIFA records and intervention planning." },
    ],
  }),
  component: Reliability,
});

const tabs = ["Run life", "Failure analysis", "Bad actors", "Interventions", "DIFA records"] as const;

function Reliability() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("Run life");

  const meanRunLife = Math.round(failures.reduce((a, r) => a + r.runLifeDays, 0) / failures.length);
  const repeatRate = Math.round((failures.filter((r) => r.repeat).length / failures.length) * 100);
  const cost = failures.reduce((a, r) => a + r.interventionCostKUsd, 0);
  const deferred = failures.reduce((a, r) => a + r.deferredBbl, 0);

  return (
    <div className="space-y-3">
      <PageHeader
        title="Reliability & Run Life"
        description="Run life is the outcome of how wells were operated, not only of the equipment installed. This workspace links failure history and DIFA findings back to the operating factors ESP-PMM can influence — envelope compliance, temperature, free gas, abrasives and electrical integrity."
        meta={
          <>
            <StatusPill tone="info">34 pull records · 25 wells · 3 fields</StatusPill>
            <StatusPill tone="muted">Cost and deferment figures are illustrative</StatusPill>
          </>
        }
        actions={<ToggleRow options={tabs} value={tab} onChange={setTab} />}
      />

      <KpiStrip>
        <Metric label="Mean run life" value={n0(meanRunLife)} unit="days" sub="All recorded pulls" />
        <Metric label="Repeat failure rate" value={repeatRate} unit="%" tone={repeatRate > 25 ? "warning" : "normal"} sub="Same well within 2 runs" />
        <Metric label="Recorded pulls" value={failures.length} sub="With DIFA summary" />
        <Metric label="Intervention spend" value={usd(cost * 1000)} sub="Cumulative, illustrative" />
        <Metric label="Deferred volume" value={n0(deferred)} unit="bbl" tone="warning" sub="Associated with failures" />
        <Metric label="High-risk wells" value={badActors.filter((b) => b.riskScore > 60).length} tone="critical" sub="Risk score above 60" />
        <Metric label="Planned interventions" value={interventions.filter((i) => i.status !== "Executed").length} sub="Proposed or scheduled" />
      </KpiStrip>

      {tab === "Run life" && (
        <div className="grid gap-3 xl:grid-cols-2">
          <Panel title="Run-life distribution by field" subtitle="Pull counts per run-life bucket" bodyClassName="p-2">
            <SimpleBar
              data={runLifeBuckets}
              xKey="bucket"
              height={260}
              bars={fields.map((f, i) => ({ key: f.name, label: f.name, color: `var(--color-chart-${i + 1})` }))}
            />
          </Panel>
          <Panel title="Run life by field" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Field</Th>
                  <Th align="right">Pulls</Th>
                  <Th align="right">Mean d</Th>
                  <Th align="right">Median d</Th>
                  <Th align="right">Shortest d</Th>
                  <Th align="right">Repeat %</Th>
                </tr>
              </thead>
              <tbody>
                {runLifeByField.map((r) => (
                  <tr key={r.fieldId}>
                    <Td>{r.field}</Td>
                    <Td align="right" mono>{r.pulls}</Td>
                    <Td align="right" mono>{n0(r.meanRunLife)}</Td>
                    <Td align="right" mono>{n0(r.medianRunLife)}</Td>
                    <Td align="right" mono className="text-warning">{n0(r.shortestRunLife)}</Td>
                    <Td align="right" mono className={r.repeatRate > 25 ? "text-warning" : ""}>{r.repeatRate}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
          <Panel title="Mean run life by pump family" bodyClassName="p-2">
            <SimpleBar
              data={runLifeByFamily}
              xKey="family"
              layout="vertical"
              yWidth={170}
              height={280}
              bars={[{ key: "meanRunLife", label: "Mean run life (days)", color: "var(--color-chart-2)" }]}
            />
          </Panel>
          <Panel title="Run-life influencing factors" subtitle="Weighted model used for the ESP health index and risk score" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Factor</Th>
                  <Th align="right">Weight</Th>
                  <Th>Why it matters</Th>
                </tr>
              </thead>
              <tbody>
                {runLifeFactors.map((f) => (
                  <tr key={f.factor}>
                    <Td>{f.factor}</Td>
                    <Td align="right" mono>{(f.weight * 100).toFixed(0)}%</Td>
                    <Td className="text-muted-foreground">{f.note}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      )}

      {tab === "Failure analysis" && (
        <div className="grid gap-3 xl:grid-cols-2">
          <Panel title="Failure-mode Pareto" subtitle="Where reliability effort pays back first" bodyClassName="p-2">
            <ParetoChart data={failureModePareto} height={320} />
          </Panel>
          <Panel title="Failures by component" bodyClassName="p-2">
            <SimpleBar
              data={componentDistribution}
              xKey="component"
              layout="vertical"
              yWidth={130}
              height={320}
              bars={[{ key: "count", label: "Pulls", color: "var(--color-chart-4)" }]}
            />
          </Panel>
        </div>
      )}

      {tab === "Bad actors" && (
        <div className="space-y-3">
        <Panel title="Asset context" subtitle="Compact ESP string miniature per high-risk well — static reference view" bodyClassName="p-2">
          <div className="flex flex-wrap gap-3">
            {badActors.slice(0, 8).map((b) => {
              const w = wellById(b.wellId);
              if (!w) return null;
              return (
                <Link
                  key={b.wellId}
                  to="/wells/$wellId"
                  params={{ wellId: b.wellId }}
                  className="flex w-[86px] flex-col items-center rounded border border-border bg-card px-1 py-1.5 hover:bg-accent"
                >
                  <EspWellMini well={w} height={84} />
                  <span className="num mt-1 text-[10.5px] text-primary">{b.wellId}</span>
                  <span className="text-[9px] text-muted-foreground">risk {b.riskScore}</span>
                </Link>
              );
            })}
          </div>
        </Panel>
        <Panel title="Bad-actor ranking" subtitle="Composite of health index, failure history, repeat pulls and operating state" bodyClassName="p-0">
          <div className="overflow-auto panel-scroll" style={{ maxHeight: "calc(100vh - 300px)" }}>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Well</Th>
                  <Th>Field</Th>
                  <Th align="right">Risk score</Th>
                  <Th align="right">Health</Th>
                  <Th align="right">Run life d</Th>
                  <Th align="right">Prior run d</Th>
                  <Th align="right">Pulls</Th>
                  <Th>Repeat</Th>
                  <Th>Dominant factor</Th>
                  <Th align="right">Indicative RUL d</Th>
                  <Th align="right">Defer bopd</Th>
                </tr>
              </thead>
              <tbody>
                {badActors.map((b) => (
                  <tr key={b.wellId} className="hover:bg-accent/40">
                    <Td>
                      <Link to="/wells/$wellId" params={{ wellId: b.wellId }} className="num text-primary hover:underline">
                        {b.wellId}
                      </Link>
                    </Td>
                    <Td className="text-muted-foreground">{b.field}</Td>
                    <Td align="right" mono className={cn(b.riskScore > 70 ? "text-critical" : b.riskScore > 50 ? "text-warning" : "")}>
                      {b.riskScore}
                    </Td>
                    <Td align="right" mono>{b.healthIndex}</Td>
                    <Td align="right" mono>{n0(b.runLifeDays)}</Td>
                    <Td align="right" mono className="text-muted-foreground">{n0(b.priorRunLifeDays)}</Td>
                    <Td align="right" mono>{b.failures12m}</Td>
                    <Td>{b.repeat ? <StatusPill tone="warning">Repeat</StatusPill> : <span className="text-muted-foreground">—</span>}</Td>
                    <Td className="text-muted-foreground">{b.dominantFactor}</Td>
                    <Td align="right" mono>{b.rulEstimateDays}</Td>
                    <Td align="right" mono className={b.deferredBopd ? "text-warning" : ""}>{b.deferredBopd ? n0(b.deferredBopd) : "—"}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-border p-2">
            <Note>
              Remaining-useful-life values shown here are indicative placeholders produced by the demo risk model. Machine-learning RUL prediction is a
              later phase that requires accumulated fleet history and validated failure labels.
            </Note>
          </div>
        </Panel>
        </div>
      )}


      {tab === "Interventions" && (
        <Panel title="Intervention plan" subtitle="Recommended work ranked by impact and risk" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>ID</Th>
                <Th>Well</Th>
                <Th>Type</Th>
                <Th align="right">Priority</Th>
                <Th>Window</Th>
                <Th>Reason</Th>
                <Th align="right">Impact bopd</Th>
                <Th align="right">Risk</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody>
              {interventions.map((i) => (
                <tr key={i.id} className="hover:bg-accent/40">
                  <Td mono>{i.id}</Td>
                  <Td>
                    <Link to="/wells/$wellId" params={{ wellId: i.wellId }} className="num text-primary hover:underline">
                      {i.wellId}
                    </Link>
                  </Td>
                  <Td>{i.type}</Td>
                  <Td align="right" mono>P{i.priority}</Td>
                  <Td mono className="text-muted-foreground">{i.plannedWindow}</Td>
                  <Td className="max-w-[320px] truncate text-muted-foreground">{i.reason}</Td>
                  <Td align="right" mono>{i.impactBopd ? n0(i.impactBopd) : "—"}</Td>
                  <Td align="right" mono className={i.riskScore > 80 ? "text-critical" : ""}>{i.riskScore}</Td>
                  <Td>
                    <StatusPill tone={i.status === "Executed" ? "normal" : i.status === "Scheduled" ? "info" : "muted"}>{i.status}</StatusPill>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}

      {tab === "DIFA records" && (
        <Panel title="Pull and DIFA history" subtitle="Teardown findings linked to the operating factor that drove them" bodyClassName="p-0">
          <div className="overflow-auto panel-scroll" style={{ maxHeight: "calc(100vh - 300px)" }}>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Record</Th>
                  <Th>Well</Th>
                  <Th>Pulled</Th>
                  <Th align="right">Run life d</Th>
                  <Th>Component</Th>
                  <Th>Failure mode</Th>
                  <Th>Root-cause factor</Th>
                  <Th>DIFA summary</Th>
                  <Th align="right">Cost kUSD</Th>
                </tr>
              </thead>
              <tbody>
                {failures.map((r) => (
                  <tr key={r.id} className="hover:bg-accent/40">
                    <Td mono>{r.id}</Td>
                    <Td mono>{r.wellId}</Td>
                    <Td mono className="text-muted-foreground">{r.pulled}</Td>
                    <Td align="right" mono className={r.runLifeDays < 300 ? "text-warning" : ""}>{n0(r.runLifeDays)}</Td>
                    <Td>{r.failedComponent}</Td>
                    <Td>{r.failureMode}</Td>
                    <Td className="text-muted-foreground">{r.rootCauseFactor}</Td>
                    <Td className="max-w-[340px] truncate text-muted-foreground">{r.difaSummary}</Td>
                    <Td align="right" mono>{r.interventionCostKUsd}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
