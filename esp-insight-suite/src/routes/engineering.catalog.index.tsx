import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { CurveStatusBadge, ReliabilityBadge, VerificationBadge, num } from "@/components/esp/engineering/governance";
import { oemName, sourceLabel } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

const TABS = [
  "Pump Models",
  "Pump Curves",
  "Motors",
  "Intake / Gas handling",
  "Protectors / Seals",
  "Cables / MLE",
  "VSD / Transformers",
  "Downhole Sensors",
  "Discovery (secondary)",
] as const;
type Tab = (typeof TABS)[number];

export const Route = createFileRoute("/engineering/catalog/")({
  head: () => ({
    meta: [
      { title: "ESP equipment catalog — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed OEM equipment catalog: pump models and curves, motors, gas handling, protectors, cables, VSDs and downhole sensors, each with source provenance and reliability class." },
      { property: "og:title", content: "ESP equipment catalog" },
      { property: "og:description", content: "OEM catalog master data with provenance, reliability grading and curve availability." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Catalog,
});

function Catalog() {
  const d = api.useLoaderData();
  const [tab, setTab] = useState<Tab>("Pump Models");
  const [oem, setOem] = useState("all");
  const curveModelIds = new Set(d.curvePoints.map((p) => p.pump_model_id));

  const f = <T extends { oem_id: string }>(rows: T[]) => rows.filter((r) => oem === "all" || r.oem_id === oem);

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Equipment Catalog"
        description="OEM reference master data. Values are transcribed from registered evidence only — where no curve evidence exists the record is marked BEP/Envelope only or Curve pending, never back-filled with synthetic performance."
        meta={
          <>
            <StatusPill tone="info">{d.pumpModels.length} pump models</StatusPill>
            <StatusPill tone="watch">{d.pumpModels.filter((p) => !curveModelIds.has(p.id)).length} without digitised curve</StatusPill>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-sm border px-2 py-0.5 text-[10.5px] ${tab === t ? "border-primary bg-primary/15 text-foreground" : "border-border text-muted-foreground hover:text-foreground"}`}
          >
            {t}
          </button>
        ))}
        <select className="ml-auto rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px] text-foreground" value={oem} onChange={(e) => setOem(e.target.value)}>
          <option value="all">All OEMs</option>
          {d.oems.map((o) => (
            <option key={o.id} value={o.id}>{o.name}</option>
          ))}
        </select>
      </div>

      {tab === "Pump Models" && (
        <Panel title="Pump models" subtitle="Series, geometry, BEP and recommended operating range with evidence class" bodyClassName="p-0">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Model</Th><Th>OEM</Th><Th>Series</Th><Th align="right">OD in</Th>
                  <Th align="right">BEP bpd</Th><Th align="right">ft/stage</Th><Th align="right">hp/stage</Th>
                  <Th align="right">Floater ROR bpd</Th><Th align="right">Compression ROR bpd</Th><Th>Curve evidence</Th><Th>WSW check</Th><Th>Evidence</Th><Th align="right">Installed</Th>
                </tr>
              </thead>
              <tbody>
                {f(d.pumpModels).map((p) => (
                  <tr key={p.id} className="hover:bg-accent/40">
                    <Td><Link to="/engineering/catalog/pumps/$modelId" params={{ modelId: p.id }} className="text-info hover:underline">{p.model}</Link></Td>
                    <Td className="text-[10.5px] text-muted-foreground">{oemName(d, p.oem_id)}</Td>
                    <Td className="text-[10.5px] text-muted-foreground">{p.series ?? "—"}</Td>
                    <Td align="right" mono>{num(p.od_in, 2)}</Td>
                    <Td align="right" mono>{num(p.bep_flow_bpd)}</Td>
                    <Td align="right" mono>{num(p.bep_head_ft_per_stage, 1)}</Td>
                    <Td align="right" mono>{num(p.bep_power_hp_per_stage, 2)}</Td>
                    <Td align="right" mono>
                      {p.floater_ror_min_bpd != null
                        ? `${num(p.floater_ror_min_bpd)}–${num(p.floater_ror_max_bpd)}`
                        : p.ror_min_bpd != null
                          ? <span className="text-muted-foreground" title="Series/overall flow envelope — source does not state a floater-specific range">{num(p.ror_min_bpd)}–{num(p.ror_max_bpd)} env</span>
                          : "—"}
                    </Td>
                    <Td align="right" mono>{p.compression_ror_min_bpd != null ? `${num(p.compression_ror_min_bpd)}–${num(p.compression_ror_max_bpd)}` : "—"}</Td>
                    <Td><CurveStatusBadge status={p.curve_completeness} digitisedPoints={d.curvePoints.filter((c) => c.pump_model_id === p.id).length} /></Td>
                    <Td className="text-[10px] text-muted-foreground">{p.wsw_crosscheck_result ?? "—"}</Td>
                    <Td><ReliabilityBadge code={p.reliability_code} /></Td>
                    <Td align="right" mono>{p.cced_installed_count}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === "Pump Curves" && (
        <Panel title="Pump curve evidence" subtitle="Catalog curve availability (what the source document holds) is tracked separately from digitised points loaded in this build. Zero points = no usable curve; no synthetic curve is ever generated." bodyClassName="p-0">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr><Th>Model</Th><Th>OEM</Th><Th align="right">Points</Th><Th align="right">Ref Hz</Th><Th align="right">Ref rpm</Th><Th>Basis</Th><Th>Extraction</Th><Th>Revision</Th><Th>Status</Th></tr>
              </thead>
              <tbody>
                {f(d.pumpModels).map((p) => {
                  const pts = d.curvePoints.filter((c) => c.pump_model_id === p.id);
                  return (
                    <tr key={p.id} className="hover:bg-accent/40">
                      <Td><Link to="/engineering/catalog/pumps/$modelId" params={{ modelId: p.id }} className="text-info hover:underline">{p.model}</Link></Td>
                      <Td className="text-[10.5px] text-muted-foreground">{oemName(d, p.oem_id)}</Td>
                      <Td align="right" mono>{pts.length}</Td>
                      <Td align="right" mono>{num(p.reference_hz)}</Td>
                      <Td align="right" mono>{num(p.reference_rpm)}</Td>
                      <Td className="text-[10px] text-muted-foreground">{pts[0]?.stage_basis ?? "—"}</Td>
                      <Td className="text-[10px] text-muted-foreground">{pts[0]?.extraction_method ?? "—"}</Td>
                      <Td mono className="text-[10px]">{pts[0]?.curve_revision ?? "—"}</Td>
                      <Td><CurveStatusBadge status={p.curve_completeness} digitisedPoints={pts.length} /></Td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === "Motors" && (
        <Panel title="Motor models" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Series", "OD in", "hp", "V", "A", "Winding", "Max °F", "Evidence", "Verification", "Installed"]}
            rows={f(d.motors).map((m) => [m.model, oemName(d, m.oem_id), m.series ?? "—", num(m.od_in, 2), num(m.nameplate_hp), num(m.nameplate_volts), num(m.nameplate_amps, 1), m.winding_type ?? "—", num(m.max_temp_f), <ReliabilityBadge key="r" code={m.reliability_code} />, <VerificationBadge key="v" status={m.verification_status} />, m.cced_installed_count])}
          />
        </Panel>
      )}

      {tab === "Intake / Gas handling" && (
        <Panel title="Intake / gas separators / gas handlers" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Device type", "OD in", "Max GVF %", "Max bpd", "Evidence", "Verification", "Installed"]}
            rows={f(d.gasHandling).map((g) => [g.model, oemName(d, g.oem_id), g.device_type, num(g.od_in, 2), num(g.max_gvf_pct), num(g.max_flow_bpd), <ReliabilityBadge key="r" code={g.reliability_code} />, <VerificationBadge key="v" status={g.verification_status} />, g.cced_installed_count])}
          />
        </Panel>
      )}

      {tab === "Protectors / Seals" && (
        <Panel title="Protectors / seal sections" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Configuration", "Chambers", "Elastomer", "OD in", "Thrust lbf", "Evidence", "Installed"]}
            rows={f(d.protectors).map((p) => [p.model, oemName(d, p.oem_id), p.configuration ?? "—", p.chamber_count ?? "—", p.elastomer ?? "—", num(p.od_in, 2), num(p.thrust_bearing_rating_lbf), <ReliabilityBadge key="r" code={p.reliability_code} />, p.cced_installed_count])}
          />
        </Panel>
      )}

      {tab === "Cables / MLE" && (
        <Panel title="Cables / motor lead extensions" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Type", "AWG", "V rating", "Max °F", "Ω/kft", "Armor", "Evidence", "Installed"]}
            rows={f(d.cables).map((c) => [c.model, oemName(d, c.oem_id), c.cable_type ?? "—", c.conductor_size_awg ?? "—", num(c.voltage_rating_v), num(c.max_temp_f), num(c.resistance_ohm_per_kft, 3), c.armor ?? "—", <ReliabilityBadge key="r" code={c.reliability_code} />, c.cced_installed_count])}
          />
        </Panel>
      )}

      {tab === "VSD / Transformers" && (
        <Panel title="VSD / drives / transformers" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Drive type", "kVA", "Output V", "Output A", "Transformer note", "Evidence", "Installed"]}
            rows={f(d.vsds).map((v) => [v.model, oemName(d, v.oem_id), v.drive_type ?? "—", num(v.kva_rating), num(v.output_volts), num(v.output_amps), v.transformer_note ?? "—", <ReliabilityBadge key="r" code={v.reliability_code} />, v.cced_installed_count])}
          />
        </Panel>
      )}

      {tab === "Downhole Sensors" && (
        <Panel title="Downhole sensors / gauges" bodyClassName="p-0">
          <SimpleTable
            head={["Model", "OEM", "Channels", "Pressure psi", "Max °F", "Evidence", "Source", "Installed"]}
            rows={d.sensors.filter((s) => oem === "all" || s.oem_id === oem).map((s) => [s.model, oemName(d, s.oem_id), s.measured_channels ?? "—", num(s.pressure_rating_psi), num(s.max_temp_f), <ReliabilityBadge key="r" code={s.reliability_code} />, sourceLabel(d, s.source_id), s.cced_installed_count])}
          />
        </Panel>
      )}
      {tab === "Discovery (secondary)" && (
        <Panel
          title="Secondary catalog discovery — not engineering evidence"
          subtitle={`${d.discovery.length} loaded${d.discovery[0]?.source_reported_total ? ` of ${d.discovery[0].source_reported_total} reported by the source` : ""}. Reliability C1: model existence only — no OEM verification, no captured performance curve. Never used as calculation input.`}
          bodyClassName="p-0"
        >
          <div className="border-b border-warning/40 bg-warning/10 px-2.5 py-1.5 text-[10.5px] text-warning">
            Discovery rows are retained to widen model coverage and support future OEM verification. Promotion to the governed catalog requires OEM datasheet or catalog evidence (A1/A2) before any engineering use.
          </div>
          <SimpleTable
            head={["Manufacturer", "Brand", "Series", "Raw model", "Normalized", "Evidence", "OEM verification", "Curve status", "Engineering use"]}
            rows={d.discovery.slice(0, 400).map((r) => [
              r.manufacturer_raw ?? "—",
              r.brand_raw ?? "—",
              r.series_raw ?? "—",
              r.model_raw ?? "—",
              r.normalized_model ?? "—",
              <ReliabilityBadge key="r" code={r.reliability_code} />,
              r.oem_verification ?? "—",
              r.performance_curve_status ?? "—",
              r.engineering_use ?? "Discovery only",
            ])}
          />
          {d.discovery.length > 400 && (
            <div className="border-t border-border px-2.5 py-1.5 text-[10px] text-muted-foreground">
              Showing the first 400 of {d.discovery.length} discovery rows.
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}

function SimpleTable({ head, rows }: { head: string[]; rows: (React.ReactNode)[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>{head.map((h) => <Th key={h}>{h}</Th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="hover:bg-accent/40">
              {r.map((cell, j) => (
                <Td key={j} className="text-[10.5px]">{cell}</Td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><Td className="text-[11px] text-muted-foreground">No records.</Td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
