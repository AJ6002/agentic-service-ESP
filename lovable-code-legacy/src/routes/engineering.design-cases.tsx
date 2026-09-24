import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { casesForWell, designCases } from "@/data/esp/design-cases";
import { wellById, wells } from "@/data/esp/fleet";
import { n0, n1, signed } from "@/lib/esp/format";
import { Note, PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/engineering/design-cases")({
  head: () => ({
    meta: [
      { title: "Design Case Manager — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Manage ESP design, current and what-if cases: inputs, calculated outputs, model-versus-actual comparison and case status governance.",
      },
      { property: "og:title", content: "ESP Design Case Manager" },
      { property: "og:description", content: "Design, current and what-if ESP cases with model-versus-actual comparison." },
    ],
  }),
  component: DesignCaseManager,
});

function DesignCaseManager() {
  const [wellId, setWellId] = useState(wells[0]!.id);
  const well = wellById(wellId)!;
  const cases = casesForWell(wellId);
  const [aId, setAId] = useState(cases[0]?.id ?? "");
  const [bId, setBId] = useState(cases[1]?.id ?? cases[0]?.id ?? "");
  const list = casesForWell(wellId);
  const a = list.find((c) => c.id === aId) ?? list[0]!;
  const b = list.find((c) => c.id === bId) ?? list[1] ?? list[0]!;

  const inputRows: [string, number, number, string][] = [
    ["Reservoir pressure", a.inputs.reservoirPsi, b.inputs.reservoirPsi, "psi"],
    ["Productivity index", a.inputs.piBpdPsi, b.inputs.piBpdPsi, "bpd/psi"],
    ["Water cut", a.inputs.waterCutPct, b.inputs.waterCutPct, "%"],
    ["GOR", a.inputs.gorScfStb, b.inputs.gorScfStb, "scf/stb"],
    ["Fluid SG", a.inputs.fluidSg, b.inputs.fluidSg, "-"],
    ["Wellhead pressure", a.inputs.whpPsi, b.inputs.whpPsi, "psi"],
    ["Tubing ID", a.inputs.tubingId, b.inputs.tubingId, "in"],
    ["Pump setting depth", a.inputs.pumpSettingFt, b.inputs.pumpSettingFt, "ft"],
    ["Perforation depth", a.inputs.perfDepthFt, b.inputs.perfDepthFt, "ft"],
    ["Frequency", a.inputs.hz, b.inputs.hz, "Hz"],
    ["Stages", a.inputs.stages, b.inputs.stages, "-"],
  ];

  const outputRows: [string, number, number, string][] = [
    ["Liquid rate", a.outputs.liquidBpd, b.outputs.liquidBpd, "bpd"],
    ["Oil rate", a.outputs.oilBopd, b.outputs.oilBopd, "bopd"],
    ["Total dynamic head", a.outputs.tdhFt, b.outputs.tdhFt, "ft"],
    ["Pump intake pressure", a.outputs.pipPsi, b.outputs.pipPsi, "psi"],
    ["Pump discharge pressure", a.outputs.pdpPsi, b.outputs.pdpPsi, "psi"],
    ["Brake horsepower", a.outputs.bhp, b.outputs.bhp, "hp"],
    ["Pump efficiency", a.outputs.efficiencyPct, b.outputs.efficiencyPct, "%"],
    ["Motor loading", a.outputs.motorLoadPct, b.outputs.motorLoadPct, "%"],
    ["Free gas at intake", a.outputs.gvfPct, b.outputs.gvfPct, "%"],
  ];

  return (
    <div className="space-y-3">
      <PageHeader
        title="Design Case Manager"
        description="Design intent, current conditions and what-if cases live side by side with the inputs that produced them. Comparing a case against measured behaviour is how design validation and pump resizing decisions are justified."
        meta={
          <>
            <StatusPill tone="info">{designCases.length} cases across {wells.length} wells</StatusPill>
            <StatusPill tone="muted">Every output is recalculated from its stored inputs</StatusPill>
          </>
        }
        actions={
          <div className="flex items-center gap-2">
            <select
              value={wellId}
              onChange={(e) => {
                const next = casesForWell(e.target.value);
                setWellId(e.target.value);
                setAId(next[0]?.id ?? "");
                setBId(next[1]?.id ?? next[0]?.id ?? "");
              }}
              className="rounded border border-border bg-card px-2 py-1 text-[12px]"
            >
              {wells.map((w) => (
                <option key={w.id} value={w.id}>{w.id}</option>
              ))}
            </select>
            <Link to="/engineering/workbench" search={{ well: wellId }} className="rounded border border-primary/50 bg-primary/15 px-2 py-1 text-[11px] font-semibold text-primary hover:bg-primary/25">
              Open in Workbench
            </Link>
          </div>
        }
      />

      <div className="grid gap-3 xl:grid-cols-[300px_minmax(0,1fr)]">
        <Panel title={`Cases — ${well.id}`} bodyClassName="p-0">
          <div className="divide-y divide-border">
            {cases.map((c) => (
              <div key={c.id} className={cn("px-2.5 py-2", (c.id === a.id || c.id === b.id) && "bg-primary/10")}>
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-medium">{c.name}</span>
                  <StatusPill tone={c.kind === "Design" ? "info" : c.kind === "Current" ? "normal" : "opportunity"} dot={false}>
                    {c.kind}
                  </StatusPill>
                </div>
                <div className="num mt-0.5 text-[10px] text-muted-foreground">
                  {c.id} · {c.author} · updated {c.updated} · {c.status}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">{c.note}</p>
                <div className="mt-1.5 flex gap-1">
                  <button type="button" onClick={() => setAId(c.id)} className="rounded border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent">
                    Set as A
                  </button>
                  <button type="button" onClick={() => setBId(c.id)} className="rounded border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent">
                    Set as B
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <div className="grid gap-3 lg:grid-cols-2">
          <Panel title="Case inputs" subtitle={`A: ${a.name}   vs   B: ${b.name}`} bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Input</Th>
                  <Th align="right">A</Th>
                  <Th align="right">B</Th>
                  <Th align="right">Delta</Th>
                </tr>
              </thead>
              <tbody>
                {inputRows.map(([label, x, y, unit]) => (
                  <tr key={label}>
                    <Td>{label} <span className="text-muted-foreground">({unit})</span></Td>
                    <Td align="right" mono>{n1(x)}</Td>
                    <Td align="right" mono>{n1(y)}</Td>
                    <Td align="right" mono className={x === y ? "text-muted-foreground" : "text-watch"}>{signed(y - x, 1)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Calculated outputs" subtitle="Deterministic engine output for each stored case" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Output</Th>
                  <Th align="right">A</Th>
                  <Th align="right">B</Th>
                  <Th align="right">Delta</Th>
                </tr>
              </thead>
              <tbody>
                {outputRows.map(([label, x, y, unit]) => (
                  <tr key={label}>
                    <Td>{label} <span className="text-muted-foreground">({unit})</span></Td>
                    <Td align="right" mono>{n1(x)}</Td>
                    <Td align="right" mono>{n1(y)}</Td>
                    <Td align="right" mono className={cn(y === x ? "text-muted-foreground" : y > x ? "text-opportunity" : "text-warning")}>
                      {signed(y - x, 1)}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Model versus actual" subtitle="Case A against the latest measured snapshot" bodyClassName="p-0" className="lg:col-span-2">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Parameter</Th>
                  <Th align="right">Case A</Th>
                  <Th align="right">Measured</Th>
                  <Th align="right">Variance</Th>
                  <Th>Interpretation</Th>
                </tr>
              </thead>
              <tbody>
                {([
                  ["Liquid rate (bpd)", a.outputs.liquidBpd, well.liquidRateBpd, "Rate shortfall points to inflow, wear, gas or backpressure"],
                  ["Oil rate (bopd)", a.outputs.oilBopd, well.oilRateBopd, "Check water cut against the case assumption"],
                  ["PIP (psi)", a.outputs.pipPsi, well.pipPsi, "Lower than modelled intake pressure means deeper drawdown"],
                  ["PDP (psi)", a.outputs.pdpPsi, well.pdpPsi, "Pump ΔP shortfall indicates degraded head per stage"],
                  ["Motor loading (%)", a.outputs.motorLoadPct, well.motorLoadPct, "Electrical margin against nameplate"],
                  ["Free gas at intake (%)", a.outputs.gvfPct, well.gvfPct, "Gas handling adequacy at current intake pressure"],
                ] as [string, number, number, string][]).map(([label, model, actual, note]) => {
                  const varPct = ((actual - model) / (model || 1)) * 100;
                  return (
                    <tr key={label}>
                      <Td>{label}</Td>
                      <Td align="right" mono className="text-muted-foreground">{n0(model)}</Td>
                      <Td align="right" mono>{n0(actual)}</Td>
                      <Td align="right" mono className={Math.abs(varPct) > 10 ? "text-warning" : "text-normal"}>{signed(varPct, 1)}%</Td>
                      <Td className="text-muted-foreground">{note}</Td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="p-2">
              <Note>
                Case governance in the delivered module keeps one active design case per well, retains superseded cases for audit and records who approved
                each change. This mockup keeps case selection in local state only.
              </Note>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
