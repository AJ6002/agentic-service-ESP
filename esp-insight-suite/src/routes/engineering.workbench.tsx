import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";
import { wellById, wells } from "@/data/esp/fleet";
import { frequencyScenario, envelopePosition, curveHeadAt, pressureProfile } from "@/lib/esp/calc";
import { n0, n1, n2, signed, usd } from "@/lib/esp/format";
import { PumpCurveChart, TdhWaterfall } from "@/components/esp/charts";
import { PressureProfile } from "@/components/esp/PressureProfile";
import { EspWellVisual } from "@/components/esp/EspWellVisual";
import { KpiStrip, Metric, Note, PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { GovernedContextPanel } from "@/components/esp/engineering/GovernedContextPanel";
import { cn } from "@/lib/utils";

const engineeringApi = getRouteApi("/engineering");

const searchSchema = z.object({ well: z.string().optional() });

export const Route = createFileRoute("/engineering/workbench")({
  validateSearch: searchSchema,
  head: () => ({
    meta: [
      { title: "Engineering Workbench — ESP design & what-if | ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Pump curves with BEP and recommended operating range, TDH breakdown, pressure profile and deterministic frequency what-if scenarios for ESP wells.",
      },
      { property: "og:title", content: "ESP Engineering Workbench — ADVAIT ESP-PMM" },
      { property: "og:description", content: "Deterministic ESP engineering: pump curves, TDH, pressure profile and frequency scenarios." },
    ],
  }),
  component: Workbench,
});

function Workbench() {
  const { well: wellParam } = Route.useSearch();
  const catalog = engineeringApi.useLoaderData();
  const navigate = Route.useNavigate();
  const well = wellById(wellParam ?? "") ?? wells[0]!;
  const [hz, setHz] = useState<number>(well.hz || well.designHz);
  const [compare, setCompare] = useState(true);

  const scenario = frequencyScenario(well, hz);
  const current = frequencyScenario(well, well.hz || well.designHz);
  const env = envelopePosition(well);
  const head = curveHeadAt(well, hz, scenario.liquidBpd);
  const nodes = pressureProfile(well);

  const sweep = [-4, -2, 0, 2, 4].map((d) => frequencyScenario(well, Math.max(35, Math.min(65, (well.hz || well.designHz) + d))));

  const rows: [string, number, number, string][] = [
    ["Liquid rate", current.liquidBpd, scenario.liquidBpd, "bpd"],
    ["Oil rate", current.oilBopd, scenario.oilBopd, "bopd"],
    ["Total dynamic head", current.tdhFt, scenario.tdhFt, "ft"],
    ["Pump intake pressure", current.pipPsi, scenario.pipPsi, "psi"],
    ["Pump discharge pressure", current.pdpPsi, scenario.pdpPsi, "psi"],
    ["Motor current", current.amps, scenario.amps, "A"],
    ["Motor loading", current.motorLoadPct, scenario.motorLoadPct, "%"],
    ["Motor temperature (est.)", current.motorTempF, scenario.motorTempF, "degF"],
    ["Pump efficiency", current.efficiencyPct, scenario.efficiencyPct, "%"],
    ["Free gas at intake", current.gvfPct, scenario.gvfPct, "%"],
  ];

  return (
    <div className="space-y-3">
      <PageHeader
        title="Engineering Workbench"
        description="Deterministic ESP engineering on the same governed data the control room sees. Curves, TDH, pressure profile and frequency scenarios are calculated from design and measured inputs — no black-box output, every number is traceable to its inputs."
        meta={
          <>
            <StatusPill tone="info">Affinity-law scaling · demo correlation set</StatusPill>
            <StatusPill tone="muted">Inputs: Asset ConneX design case + OTConnex measurements</StatusPill>
          </>
        }
        actions={
          <div className="flex items-center gap-2">
          <Link to="/engineering/catalog" className="rounded border border-border bg-card px-2 py-1 text-[11px] hover:bg-accent">
            Governed catalog & provenance
          </Link>
          <select
            value={well.id}
            onChange={(e) => {
              const w = wellById(e.target.value)!;
              setHz(w.hz || w.designHz);
              navigate({ search: { well: e.target.value } });
            }}
            className="rounded border border-border bg-card px-2 py-1 text-[12px]"
          >
            {wells.map((w) => (
              <option key={w.id} value={w.id}>
                {w.id} — {w.pumpModel}
              </option>
            ))}
          </select>
          </div>
        }
      />

      <GovernedContextPanel catalog={catalog} />

      <KpiStrip>
        <Metric label="Well" value={well.id} sub={`${well.oem} ${well.pumpModel}`} />
        <Metric label="Stages" value={n0(well.stages)} sub={`Head/stage design ${n1(well.headPerStage)} ft`} />
        <Metric label="Rated motor" value={`${well.motorRatingHp}`} unit="hp" sub={`${well.motorRatingA} A · ${well.motorRatingV} V`} />
        <Metric label="BEP rate" value={n0(well.bepRate)} unit="bpd" sub={`ROR ${n0(well.rorMin)}–${n0(well.rorMax)} bpd`} />
        <Metric label="Q / Q BEP" value={n2(env.bepRatio)} sub={env.inside ? "Inside ROR" : "Outside ROR"} tone={env.inside ? "normal" : "warning"} />
        <Metric label="Scenario frequency" value={n1(hz)} unit="Hz" sub={`Current ${n1(well.hz || 0)} Hz`} tone="info" />
        <Metric
          label="Scenario oil delta"
          value={signed(scenario.oilBopd - current.oilBopd)}
          unit="bopd"
          sub={usd(Math.abs(scenario.oilBopd - current.oilBopd) * 68) + "/day"}
          tone={scenario.oilBopd >= current.oilBopd ? "opportunity" : "warning"}
        />
      </KpiStrip>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel
          title="Pump performance curve"
          subtitle="Head, efficiency and power with BEP marker and recommended operating range shading"
          actions={
            <label className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} />
              Show 50 / 55 / 60 Hz family
            </label>
          }
          bodyClassName="p-2"
        >
          <PumpCurveChart
            well={well}
            hz={hz}
            actualFlow={scenario.liquidBpd}
            actualHead={Math.round(head)}
            {...(compare ? { compareHz: [50, 55, 60] } : {})}
            height={340}
          />
          <Note tone={scenario.envelope === "Inside ROR" ? "normal" : "warning"}>{scenario.note}</Note>
        </Panel>

        <Panel title="Frequency what-if" subtitle="Move the drive setpoint and read the engineering consequence">
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>35 Hz</span>
                <span className="num text-[13px] font-semibold text-foreground">{n1(hz)} Hz</span>
                <span>65 Hz</span>
              </div>
              <input
                type="range"
                min={35}
                max={65}
                step={0.5}
                value={hz}
                onChange={(e) => setHz(Number(e.target.value))}
                className="mt-1 w-full accent-primary"
              />
              <div className="mt-1 flex gap-1">
                {[well.designHz, 50, 55, 58, 60].map((v, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setHz(v)}
                    className="rounded border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent"
                  >
                    {n1(v)} Hz
                  </button>
                ))}
              </div>
            </div>

            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Parameter</Th>
                  <Th align="right">Current</Th>
                  <Th align="right">Scenario</Th>
                  <Th align="right">Delta</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map(([label, a, b, unit]) => (
                  <tr key={label}>
                    <Td>
                      {label} <span className="text-muted-foreground">({unit})</span>
                    </Td>
                    <Td align="right" mono className="text-muted-foreground">{n1(a)}</Td>
                    <Td align="right" mono>{n1(b)}</Td>
                    <Td align="right" mono className={cn(b === a ? "text-muted-foreground" : b > a ? "text-opportunity" : "text-warning")}>
                      {signed(b - a, 1)}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>

            <Note tone={scenario.motorLoadPct > 78 || scenario.motorTempF > well.motorTempLimitF ? "critical" : "muted"}>
              Constraint check: motor loading {scenario.motorLoadPct}% of nameplate (limit 80%), motor temperature {scenario.motorTempF} degF against {well.motorTempLimitF} degF limit,
              envelope status {scenario.envelope.toLowerCase()}. Setpoint changes remain a human decision — ESP-PMM proposes, the operator approves.
            </Note>
          </div>
        </Panel>
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="TDH breakdown" subtitle={`At ${n1(hz)} Hz — lift, friction and backpressure components`} bodyClassName="p-2">
          <TdhWaterfall well={well} hz={hz} height={220} />
        </Panel>
        <Panel title="Pressure profile & well context" subtitle="Reservoir to wellhead with pump ΔP — PIP / PDP / WHP marked on the string" bodyClassName="p-2">
          <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_170px]">
            <PressureProfile well={well} />
            <EspWellVisual well={well} variant="compact" />
          </div>
        </Panel>
        <Panel title="Frequency sweep" subtitle="Envelope and loading across ±4 Hz" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th align="right">Hz</Th>
                <Th align="right">Liquid</Th>
                <Th align="right">Oil</Th>
                <Th align="right">Load %</Th>
                <Th align="right">PIP</Th>
                <Th>Envelope</Th>
              </tr>
            </thead>
            <tbody>
              {sweep.map((s) => (
                <tr key={s.hz} className={s.hz === Math.round(hz) ? "bg-primary/10" : ""}>
                  <Td align="right" mono>{n1(s.hz)}</Td>
                  <Td align="right" mono>{n0(s.liquidBpd)}</Td>
                  <Td align="right" mono>{n0(s.oilBopd)}</Td>
                  <Td align="right" mono className={s.motorLoadPct > 78 ? "text-critical" : ""}>{s.motorLoadPct}</Td>
                  <Td align="right" mono>{n0(s.pipPsi)}</Td>
                  <Td>
                    <StatusPill tone={s.envelope === "Inside ROR" ? "normal" : "warning"} dot={false}>{s.envelope}</StatusPill>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border p-2">
            <table className="w-full border-collapse">
              <tbody>
                {nodes.map((n) => (
                  <tr key={n.label}>
                    <Td className="text-muted-foreground">{n.label}</Td>
                    <Td align="right" mono>{n0(n.psi)} psi</Td>
                    <Td align="right" mono className="text-muted-foreground">{n0(n.depthFt)} ft</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
