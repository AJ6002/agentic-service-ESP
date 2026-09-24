import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { fields, fieldName, fleetSummary, stateLabels, stateTone, wells } from "@/data/esp/fleet";
import { exceptions, needsAttention, optimizationQueue } from "@/data/esp/exceptions";
import { FleetTable } from "@/components/esp/FleetTable";
import { KpiStrip, Metric, Panel, PageHeader, StatusPill, Td, Th } from "@/components/esp/ui";
import { SimpleBar } from "@/components/esp/charts";
import { EspWellVisual } from "@/components/esp/EspWellVisual";
import { hoursToDuration, n0, usd } from "@/lib/esp/format";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ESP Fleet Cockpit — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Centralised ESP fleet surveillance: health index, availability, production deferment, ranked attention queue and optimization opportunities across 25 wells.",
      },
      { property: "og:title", content: "ESP Fleet Cockpit — ADVAIT ESP-PMM" },
      {
        property: "og:description",
        content: "Fleet-wide ESP surveillance with exception ranking, deferment tracking and optimization opportunities.",
      },
    ],
  }),
  component: FleetCockpit,
});

function FleetCockpit() {
  const s = fleetSummary();
  const attention = needsAttention().slice(0, 9);
  const ranked = [...wells].sort((a, b) => a.healthIndex - b.healthIndex);
  const [selectedId, setSelectedId] = useState(ranked[0]!.id);
  const selected = wells.find((w) => w.id === selectedId) ?? ranked[0]!;
  const opportunities = optimizationQueue();

  const byCategory = Object.entries(
    exceptions
      .filter((e) => e.status !== "Closed")
      .reduce<Record<string, number>>((acc, e) => {
        acc[e.category] = (acc[e.category] ?? 0) + 1;
        return acc;
      }, {}),
  )
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count);

  const deferByField = fields.map((f) => ({
    field: f.name,
    deferred: wells.filter((w) => w.fieldId === f.id).reduce((a, w) => a + w.deferredBopd, 0),
    opportunity: wells.filter((w) => w.fieldId === f.id).reduce((a, w) => a + w.opportunityBopd, 0),
  }));

  return (
    <div className="space-y-3">
      <PageHeader
        title="ESP Fleet Cockpit"
        description="Centralised surveillance across 3 fields and 25 ESP wells. Ranked by production impact and reliability risk so intervention effort goes where it pays — fewer preventable trips, fewer repeat field visits, faster reaction."
        meta={
          <>
            <StatusPill tone="info">Signals: OTConnex (SCADA · historian · VSD · downhole gauges)</StatusPill>
            <StatusPill tone="info">Asset model: Asset ConneX ESP templates</StatusPill>
            <StatusPill tone="info">Scope: ESP artificial lift · 25 wells · 3 fields</StatusPill>
            <StatusPill tone="muted">Demo price deck $68/bbl</StatusPill>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 rounded-sm border border-border bg-panel px-2 py-1.5">
        <span className="pr-1 text-[9px] font-semibold tracking-widest text-muted-foreground uppercase">ESP fleet</span>
        {fields.map((f) => {
          const fw = wells.filter((w) => w.fieldId === f.id);
          const alarmed = fw.filter((w) => w.state !== "normal").length;
          return (
            <StatusPill key={f.id} tone={alarmed > fw.length / 2 ? "watch" : "normal"}>
              {f.name} · {fw.length} wells · {alarmed} off-normal
            </StatusPill>
          );
        })}
        <StatusPill tone="info">
          Inside recommended range{" "}
          {Math.round((wells.filter((w) => w.state !== "outside-ror-low" && w.state !== "outside-ror-high").length / wells.length) * 100)}%
        </StatusPill>
        <Link
          to="/engineering"
          className="ml-auto rounded-sm border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          Engineering Configuration →
        </Link>
      </div>

      <KpiStrip>
        <Metric label="Wells running" value={`${s.running}/${s.total}`} sub={`${s.down} down`} tone="normal" />
        <Metric label="Availability" value={s.availability} unit="%" sub="Run status weighted, 24 h" />
        <Metric label="Fleet ESP health index" value={s.health} sub="Weighted envelope + thermal + degradation" tone="watch" />
        <Metric label="Oil rate" value={n0(s.oil)} unit="bopd" sub="Allocated, latest scan" />
        <Metric label="Production deferment" value={n0(s.deferred)} unit="bopd" sub="Vs expected from active cases" tone="warning" />
        <Metric label="Optimization upside" value={n0(s.opportunity)} unit="bopd" sub="Illustrative scenario estimates" tone="opportunity" />
        <Metric label="Value at stake" value={usd(s.valueUsdDay)} unit="/day" sub="Deferment + upside" />
      </KpiStrip>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        <Panel
          title="Needs attention now"
          subtitle="Ranked by severity then production impact — the operational queue for this shift"
          bodyClassName="p-0"
          actions={
            <Link to="/exceptions" className="text-[11px] text-primary hover:underline">
              Open full queue →
            </Link>
          }
        >
          <div className="overflow-auto panel-scroll" style={{ maxHeight: 340 }}>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Sev</Th>
                  <Th>Well</Th>
                  <Th>Category</Th>
                  <Th align="right">Impact bopd</Th>
                  <Th align="right">Age</Th>
                  <Th align="right">Conf.</Th>
                  <Th>Owner</Th>
                </tr>
              </thead>
              <tbody>
                {attention.map((e) => (
                  <tr key={e.id} className="hover:bg-accent/40">
                    <Td>
                      <StatusPill tone={e.severity === "critical" ? "critical" : e.severity === "warning" ? "warning" : "watch"}>
                        {e.severity}
                      </StatusPill>
                    </Td>
                    <Td>
                      <Link to="/wells/$wellId" params={{ wellId: e.wellId }} className="num text-primary hover:underline">
                        {e.wellId}
                      </Link>
                    </Td>
                    <Td className="max-w-[300px] truncate">{e.category}</Td>
                    <Td align="right" mono>{e.impactBopd ? n0(e.impactBopd) : "—"}</Td>
                    <Td align="right" mono>{hoursToDuration(e.durationH)}</Td>
                    <Td align="right" mono>{(e.confidence * 100).toFixed(0)}%</Td>
                    <Td className="text-muted-foreground">{e.owner}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="space-y-3">
          <Panel title="Optimization opportunities" subtitle="Healthy wells with envelope, thermal and electrical headroom" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Well</Th>
                  <Th>Basis</Th>
                  <Th align="right">Upside</Th>
                  <Th align="right">Conf.</Th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((e) => (
                  <tr key={e.id} className="hover:bg-accent/40">
                    <Td>
                      <Link to="/engineering/workbench" search={{ well: e.wellId }} className="num text-primary hover:underline">
                        {e.wellId}
                      </Link>
                    </Td>
                    <Td className="max-w-[220px] truncate text-muted-foreground">{e.rule}</Td>
                    <Td align="right" mono className="text-opportunity">{usd(e.opportunityUsdDay)}/d</Td>
                    <Td align="right" mono>{(e.confidence * 100).toFixed(0)}%</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Open exceptions by category" subtitle="Where surveillance effort is concentrated right now" bodyClassName="p-2">
            <div className="space-y-1.5">
              {byCategory.map((c) => (
                <div key={c.category}>
                  <div className="flex items-baseline justify-between gap-2 text-[11px]">
                    <span className="truncate">{c.category}</span>
                    <span className="num shrink-0 text-muted-foreground">{c.count}</span>
                  </div>
                  <div className="mt-0.5 h-1.5 rounded bg-card">
                    <div
                      className="h-1.5 rounded bg-chart-4"
                      style={{ width: `${(c.count / Math.max(...byCategory.map((x) => x.count))) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

        </div>
      </div>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Panel title="Fleet register" subtitle="Actual vs envelope for every ESP well — click a well to open Well Monitor" bodyClassName="p-0">
          <FleetTable maxHeight="480px" />
        </Panel>

        <div className="space-y-3">
          <Panel
            title="Selected well visual"
            subtitle="Data-linked ESP status callouts for the well in focus"
            bodyClassName="p-2"
            actions={
              <select
                value={selected.id}
                onChange={(e) => setSelectedId(e.target.value)}
                className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px]"
                aria-label="Select well for visualization"
              >
                {ranked.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.id} — {stateLabels[w.state]}
                  </option>
                ))}
              </select>
            }
          >
            <EspWellVisual well={selected} variant="compact" />
            <div className="mt-1 flex items-center justify-between text-[10px]">
              <StatusPill tone={stateTone[selected.state]}>{stateLabels[selected.state]}</StatusPill>
              <Link to="/wells/$wellId" params={{ wellId: selected.id }} className="text-primary hover:underline">
                Open Well Monitor →
              </Link>
            </div>
          </Panel>
          <Panel title="Deferment & upside by field" bodyClassName="p-2">
            <SimpleBar
              data={deferByField}
              xKey="field"
              height={210}
              bars={[
                { key: "deferred", label: "Deferred bopd", color: "var(--color-warning)" },
                { key: "opportunity", label: "Upside bopd", color: "var(--color-opportunity)" },
              ]}
            />
          </Panel>
          <Panel title="Worst actors — health index" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Well</Th>
                  <Th>State</Th>
                  <Th align="right">Health</Th>
                  <Th align="right">Defer</Th>
                </tr>
              </thead>
              <tbody>
                {[...wells]
                  .sort((a, b) => a.healthIndex - b.healthIndex)
                  .slice(0, 8)
                  .map((w) => (
                    <tr key={w.id} className="hover:bg-accent/40">
                      <Td>
                        <Link to="/wells/$wellId" params={{ wellId: w.id }} className="num text-primary hover:underline">
                          {w.id}
                        </Link>
                        <span className="ml-1 text-[10px] text-muted-foreground">{fieldName(w.fieldId)}</span>
                      </Td>
                      <Td>
                        <StatusPill tone={stateTone[w.state]}>{stateLabels[w.state]}</StatusPill>
                      </Td>
                      <Td align="right" mono>{w.healthIndex}</Td>
                      <Td align="right" mono>{w.deferredBopd ? n0(w.deferredBopd) : "—"}</Td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </Panel>
        </div>
      </div>
    </div>
  );
}
