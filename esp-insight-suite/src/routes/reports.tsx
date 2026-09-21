import { createFileRoute } from "@tanstack/react-router";
import { fields, fleetSummary, wells } from "@/data/esp/fleet";
import { exceptions } from "@/data/esp/exceptions";
import { badActors, failureModePareto, failures, interventions, runLifeByField } from "@/data/esp/reliability";
import { n0, usd } from "@/lib/esp/format";
import { SimpleBar } from "@/components/esp/charts";
import { KpiStrip, Metric, Note, PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Management Scorecard & Reports — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "ESP fleet scorecard: availability, deferment, envelope compliance, run life, avoidable failures and where engineering effort should focus this week.",
      },
      { property: "og:title", content: "ESP Management Scorecard" },
      { property: "og:description", content: "Fleet availability, deferment, run life and avoidable-failure reporting for ESP operations." },
    ],
  }),
  component: Reports,
});

function Reports() {
  const s = fleetSummary();
  const insideRor = wells.filter((w) => w.hz > 0 && w.liquidRateBpd >= w.rorMin && w.liquidRateBpd <= w.rorMax).length;
  const running = wells.filter((w) => w.hz > 0).length;
  const compliance = Math.round((insideRor / running) * 100);
  const avoidable = failures.filter((r) => r.repeat).length;

  const fieldRows = fields.map((f) => {
    const fw = wells.filter((w) => w.fieldId === f.id);
    const run = fw.filter((w) => w.hz > 0);
    return {
      field: f.name,
      wells: fw.length,
      availability: Math.round((run.length / fw.length) * 100),
      health: Math.round(fw.reduce((a, w) => a + w.healthIndex, 0) / fw.length),
      oil: fw.reduce((a, w) => a + w.oilRateBopd, 0),
      deferred: fw.reduce((a, w) => a + w.deferredBopd, 0),
      upside: fw.reduce((a, w) => a + w.opportunityBopd, 0),
      compliance: Math.round((run.filter((w) => w.liquidRateBpd >= w.rorMin && w.liquidRateBpd <= w.rorMax).length / Math.max(run.length, 1)) * 100),
      openExceptions: exceptions.filter((e) => e.fieldId === f.id && e.status !== "Closed").length,
    };
  });

  return (
    <div className="space-y-3">
      <PageHeader
        title="Management Scorecard & Reports"
        description="One page for asset leadership: how much production the ESP fleet is losing, how much of it is avoidable, where run life is short and which wells deserve engineering and rig attention this week."
        meta={
          <>
            <StatusPill tone="info">Reporting period: last 24 hours and rolling 12 months</StatusPill>
            <StatusPill tone="muted">Demo price deck $68/bbl</StatusPill>
          </>
        }
      />

      <KpiStrip>
        <Metric label="Fleet availability" value={s.availability} unit="%" sub={`${running} of ${wells.length} running`} />
        <Metric label="Fleet health index" value={s.health} tone="watch" sub="Weighted composite" />
        <Metric label="Envelope compliance" value={compliance} unit="%" tone={compliance < 80 ? "warning" : "normal"} sub="Running wells inside ROR" />
        <Metric label="Deferment" value={n0(s.deferred)} unit="bopd" tone="warning" sub={usd(s.deferred * 68) + "/day"} />
        <Metric label="Identified upside" value={n0(s.opportunity)} unit="bopd" tone="opportunity" sub={usd(s.opportunity * 68) + "/day"} />
        <Metric label="Repeat / avoidable pulls" value={avoidable} tone="critical" sub={`of ${failures.length} recorded pulls`} />
        <Metric label="Rig work queued" value={interventions.filter((i) => i.type.includes("Workover")).length} sub="Workover candidates" />
      </KpiStrip>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <Panel title="Field scorecard" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Field</Th>
                <Th align="right">Wells</Th>
                <Th align="right">Avail %</Th>
                <Th align="right">Health</Th>
                <Th align="right">Oil bopd</Th>
                <Th align="right">Defer bopd</Th>
                <Th align="right">Upside bopd</Th>
                <Th align="right">Envelope %</Th>
                <Th align="right">Open exc.</Th>
              </tr>
            </thead>
            <tbody>
              {fieldRows.map((r) => (
                <tr key={r.field}>
                  <Td>{r.field}</Td>
                  <Td align="right" mono>{r.wells}</Td>
                  <Td align="right" mono>{r.availability}</Td>
                  <Td align="right" mono>{r.health}</Td>
                  <Td align="right" mono>{n0(r.oil)}</Td>
                  <Td align="right" mono className="text-warning">{n0(r.deferred)}</Td>
                  <Td align="right" mono className="text-opportunity">{n0(r.upside)}</Td>
                  <Td align="right" mono className={r.compliance < 80 ? "text-warning" : ""}>{r.compliance}</Td>
                  <Td align="right" mono>{r.openExceptions}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Deferment and upside by field" bodyClassName="p-2">
          <SimpleBar
            data={fieldRows.map((r) => ({ field: r.field, deferred: r.deferred, upside: r.upside }))}
            xKey="field"
            height={230}
            bars={[
              { key: "deferred", label: "Deferred bopd", color: "var(--color-warning)" },
              { key: "upside", label: "Upside bopd", color: "var(--color-opportunity)" },
            ]}
          />
        </Panel>
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="Where to focus this week" subtitle="Highest combined production and reliability exposure" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Well</Th>
                <Th align="right">Risk</Th>
                <Th align="right">Defer bopd</Th>
                <Th>Dominant factor</Th>
              </tr>
            </thead>
            <tbody>
              {badActors.slice(0, 8).map((b) => (
                <tr key={b.wellId}>
                  <Td mono>{b.wellId}</Td>
                  <Td align="right" mono>{b.riskScore}</Td>
                  <Td align="right" mono>{b.deferredBopd ? n0(b.deferredBopd) : "—"}</Td>
                  <Td className="text-muted-foreground">{b.dominantFactor}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Run life by field" bodyClassName="p-2">
          <SimpleBar
            data={runLifeByField.map((r) => ({ field: r.field, mean: r.meanRunLife, median: r.medianRunLife }))}
            xKey="field"
            height={230}
            bars={[
              { key: "mean", label: "Mean run life (d)", color: "var(--color-chart-2)" },
              { key: "median", label: "Median run life (d)", color: "var(--color-chart-1)" },
            ]}
          />
        </Panel>

        <Panel title="Top failure modes" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Failure mode</Th>
                <Th align="right">Pulls</Th>
                <Th align="right">Cum %</Th>
              </tr>
            </thead>
            <tbody>
              {failureModePareto.slice(0, 7).map((r) => (
                <tr key={r.mode}>
                  <Td>{r.mode}</Td>
                  <Td align="right" mono>{r.count}</Td>
                  <Td align="right" mono className="text-muted-foreground">{r.cumulativePct}</Td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-2">
            <Note>
              Reports in the delivered module are scheduled and distributed through the ADVAIT notification service, with export to PDF and Excel and a
              stored snapshot for each reporting period.
            </Note>
          </div>
        </Panel>
      </div>
    </div>
  );
}
