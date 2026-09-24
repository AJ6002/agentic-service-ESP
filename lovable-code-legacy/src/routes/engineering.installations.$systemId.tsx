import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Metric } from "@/components/esp/ui";
import { CurveStatusBadge, FieldRow, ReliabilityBadge, num } from "@/components/esp/engineering/governance";
import { byId, oemName, sectionsForSystem, sourceLabel } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/$systemId")({
  head: ({ params }) => ({
    meta: [
      { title: `Installed ESP configuration ${params.systemId} — ADVAIT ESP-PMM` },
      { name: "description", content: `Governed installed ESP assembly ${params.systemId}: pump sections, motor, gas handling, protector, cable, VSD, sensor, well engineering, fluid PVT and design limits with provenance.` },
      { property: "og:title", content: `Installed ESP configuration ${params.systemId}` },
      { property: "og:description", content: "Installed configuration with catalog provenance and reliability classes." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SystemDetail,
});

function SystemDetail() {
  const d = api.useLoaderData();
  const { systemId } = Route.useParams();
  const s = d.installedSystems.find((x) => x.id === systemId);

  if (!s) {
    return <Panel title="Installation not found"><p className="text-[11px] text-muted-foreground">No installed system with id {systemId}.</p></Panel>;
  }

  const well = byId(d.wells, s.well_id);
  const field = well ? byId(d.fields, well.field_id) : undefined;
  const sections = sectionsForSystem(d, s.id);
  const motor = byId(d.motors, s.motor_model_id);
  const gas = byId(d.gasHandling, s.gas_handling_model_id);
  const protector = byId(d.protectors, s.protector_model_id);
  const cable = byId(d.cables, s.cable_model_id);
  const vsd = byId(d.vsds, s.vsd_model_id);
  const sensor = byId(d.sensors, s.sensor_model_id);
  const eng = d.wellEngineering.find((w) => w.well_id === s.well_id);
  const pvt = d.fluidPvt.find((w) => w.well_id === s.well_id);
  const limits = d.designLimits.find((w) => w.well_id === s.well_id);

  return (
    <div className="space-y-2.5">
      <PageHeader
        title={`${well?.name ?? s.well_id} — installed ESP configuration`}
        description={`${field?.enterprise ?? ""} · ${field?.name ?? ""} · ${well?.pad_area ?? "—"} · assembly type ${s.assembly_type}. Engineering definition only; live measurements are served by OTConnex on the Operations screens.`}
        meta={
          <>
            <StatusPill tone={s.match_status === "resolved" ? "normal" : s.match_status === "partial" ? "watch" : "critical"}>catalog match: {s.match_status}</StatusPill>
            <StatusPill tone="muted">match confidence {s.match_confidence != null ? `${Math.round(Number(s.match_confidence) * 100)}%` : "—"}</StatusPill>
            <Link to="/engineering/installations" className="text-[10.5px] text-info hover:underline">← Installed Fleet</Link>
          </>
        }
      />

      {s.unresolved_note && (
        <div className="rounded-md border border-warning/50 bg-warning/10 px-2.5 py-1.5 text-[11px] text-warning">
          Unresolved: {s.unresolved_note} — this installation is not calculation-grade until the construction is confirmed against OEM evidence.
        </div>
      )}

      <div className="grid grid-cols-2 gap-2 lg:grid-cols-6">
        <Metric label="Raw designation" value={<span className="text-[12px]">{s.raw_designation ?? "—"}</span>} />
        <Metric label="Pump sections" value={sections.length} sub="tapered-capable" />
        <Metric label="Total stages" value={s.total_stages ?? "—"} sub={sections.some((x) => !x.stages_known) ? "partly unknown" : "confirmed"} tone={sections.some((x) => !x.stages_known) ? "watch" : "normal"} />
        <Metric label="Design Hz" value={s.design_hz ?? "—"} unit="Hz" />
        <Metric label="Operating Hz (design basis)" value={s.operating_hz ?? "—"} unit="Hz" />
        <Metric label="Run life" value={s.run_life_days ?? "—"} unit="days" sub={s.install_date ?? ""} />
      </div>

      <Panel title="ESP assembly — pump sections" subtitle="Ordered top → bottom; each section resolves to a governed catalog pump model" bodyClassName="p-0">
        <ul className="divide-y divide-border">
          {sections.map((sec) => {
            const pm = byId(d.pumpModels, sec.pump_model_id);
            return (
              <li key={sec.id} className="flex flex-wrap items-center gap-2 px-2 py-1.5">
                <span className="num w-6 text-[11px] text-muted-foreground">#{sec.section_sequence}</span>
                <span className="text-[11px] text-foreground">
                  {pm ? (
                    <Link to="/engineering/catalog/pumps/$modelId" params={{ modelId: pm.id }} className="text-info hover:underline">{pm.model}</Link>
                  ) : (
                    <span className="text-warning">{sec.raw_designation ?? "unresolved"}</span>
                  )}
                </span>
                <span className="text-[10px] text-muted-foreground">{pm ? oemName(d, pm.oem_id) : "OEM unknown"}</span>
                <span className="num text-[10.5px]">{sec.stages_known ? `${sec.stages} stages` : "stages unknown"}</span>
                {pm && <CurveStatusBadge status={pm.curve_completeness} digitisedPoints={d.curvePoints.filter((c) => c.pump_model_id === pm.id).length} />}
                {pm && <ReliabilityBadge code={pm.reliability_code} />}
                {sec.note && <span className="text-[10px] text-muted-foreground">{sec.note}</span>}
              </li>
            );
          })}
          {sections.length === 0 && <li className="px-2 py-2 text-[11px] text-muted-foreground">No pump sections recorded.</li>}
        </ul>
      </Panel>

      <div className="grid gap-2.5 xl:grid-cols-3">
        <Panel title="Downhole string" subtitle="Governed component selections" bodyClassName="p-0">
          <FieldRow label="Gas handling" value={gas ? `${gas.model} · ${gas.device_type}` : "—"} />
          <FieldRow label="Max GVF" value={num(gas?.max_gvf_pct, 0, " %")} />
          <FieldRow label="Protector" value={protector ? `${protector.model}` : "—"} />
          <FieldRow label="Protector config" value={protector?.configuration ?? "—"} />
          <FieldRow label="Motor" value={motor ? motor.model : "—"} />
          <FieldRow label="Motor nameplate" value={motor ? `${num(motor.nameplate_hp)} hp · ${num(motor.nameplate_volts)} V · ${num(motor.nameplate_amps, 1)} A` : "—"} />
          <FieldRow label="Sensor" value={sensor ? sensor.model : "—"} />
          <FieldRow label="Sensor channels" value={sensor?.measured_channels ?? "—"} />
        </Panel>

        <Panel title="Power & control" subtitle="Cable / MLE, drive and transformer definition" bodyClassName="p-0">
          <FieldRow label="Cable / MLE" value={cable ? cable.model : "—"} />
          <FieldRow label="Conductor" value={cable ? `${cable.conductor_size_awg ?? "—"} · ${cable.cable_type ?? "—"}` : "—"} />
          <FieldRow label="Cable rating" value={cable ? `${num(cable.voltage_rating_v)} V · ${num(cable.max_temp_f)} °F` : "—"} />
          <FieldRow label="VSD" value={vsd ? `${vsd.model} (${vsd.drive_type ?? "—"})` : "—"} />
          <FieldRow label="VSD rating" value={vsd ? `${num(vsd.kva_rating)} kVA · ${num(vsd.output_volts)} V · ${num(vsd.output_amps)} A` : "—"} />
          <FieldRow label="Transformer note" value={vsd?.transformer_note ?? "—"} />
        </Panel>

        <Panel title="Well, fluid & limits" subtitle="Linked engineering definitions" bodyClassName="p-0">
          <FieldRow label="Pump setting depth" value={num(eng?.pump_setting_depth_ft, 0, " ft")} />
          <FieldRow label="Perforations" value={eng ? `${num(eng.perf_top_ft)} – ${num(eng.perf_bottom_ft)} ft` : "—"} />
          <FieldRow label="Casing / tubing" value={eng ? `${num(eng.casing_od_in, 3, '"')} csg · ${num(eng.tubing_id_in, 3, '"')} tbg ID` : "—"} />
          <FieldRow label="Reservoir pressure" value={num(eng?.reservoir_pressure_psi, 0, " psi")} />
          <FieldRow label="PI" value={num(eng?.productivity_index_bpd_psi, 2, " bpd/psi")} />
          <FieldRow label="Water cut / GOR" value={pvt ? `${num(pvt.water_cut_pct, 0, " %")} · ${num(pvt.gor_scf_stb, 0, " scf/stb")}` : "—"} />
          <FieldRow label="Oil API / bubble point" value={pvt ? `${num(pvt.oil_api, 1)} °API · ${num(pvt.bubble_point_psi, 0, " psi")}` : "—"} />
          <FieldRow label="ROR envelope" value={limits ? `${num(limits.ror_min_bpd)} – ${num(limits.ror_max_bpd)} bpd` : "—"} />
          <FieldRow label="Frequency envelope" value={limits ? `${num(limits.min_hz, 1)} – ${num(limits.max_hz, 1)} Hz` : "—"} />
          <FieldRow label="Envelope basis" value={limits?.envelope_basis ?? "—"} />
        </Panel>
      </div>

      <Panel title="Provenance for this installation" subtitle="Every governed value traces to a registered source and reliability class" bodyClassName="p-0">
        <ul className="divide-y divide-border text-[10.5px]">
          {[
            { what: "Well engineering", code: eng?.reliability_code, src: eng?.source_id },
            { what: "Fluid / PVT", code: pvt?.reliability_code, src: pvt?.source_id },
            { what: "Design limits", code: limits?.reliability_code, src: limits?.source_id },
            { what: "Motor model", code: motor?.reliability_code, src: motor?.source_id },
            { what: "Cable model", code: cable?.reliability_code, src: cable?.source_id },
            { what: "VSD model", code: vsd?.reliability_code, src: vsd?.source_id },
          ].map((r) => (
            <li key={r.what} className="flex items-center gap-2 px-2 py-1">
              <span className="w-36 text-muted-foreground">{r.what}</span>
              <ReliabilityBadge code={r.code} />
              <span className="text-muted-foreground">{sourceLabel(d, r.src)}</span>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
