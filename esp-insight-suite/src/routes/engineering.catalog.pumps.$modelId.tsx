import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { CurvePlot } from "@/components/esp/engineering/CurvePlot";
import { CurveStatusBadge, curveAvailability, FieldRow, ReliabilityBadge, VerificationBadge, isCalculationGrade, num } from "@/components/esp/engineering/governance";
import { byId, oemName, sourceLabel } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/catalog/pumps/$modelId")({
  head: ({ params }) => ({
    meta: [
      { title: `Pump model ${params.modelId} — ADVAIT ESP-PMM catalog` },
      { name: "description", content: `Governed OEM pump model record ${params.modelId}: geometry, materials, BEP, recommended operating range, digitised curve points, source evidence and installed usage.` },
      { property: "og:title", content: `Pump model ${params.modelId}` },
      { property: "og:description", content: "OEM pump model master data with provenance and curve availability." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: PumpModelDetail,
});

function PumpModelDetail() {
  const d = api.useLoaderData();
  const { modelId } = Route.useParams();
  const p = byId(d.pumpModels, modelId);

  if (!p) {
    return <Panel title="Pump model not found"><p className="text-[11px] text-muted-foreground">No catalog record for {modelId}.</p></Panel>;
  }

  const points = d.curvePoints.filter((c) => c.pump_model_id === p.id).sort((a, b) => a.point_sequence - b.point_sequence);
  const source = byId(d.sources, p.source_id);
  const usedBy = d.pumpSections.filter((s) => s.pump_model_id === p.id);
  const aliases = d.aliases.filter((a) => a.pump_model_id === p.id);
  const issues = d.issues.filter((i) => i.pump_model_id === p.id);

  return (
    <div className="space-y-2.5">
      <PageHeader
        title={`${p.model} — pump model definition`}
        description={`${oemName(d, p.oem_id)}${p.brand_line ? ` · ${p.brand_line}` : ""}${p.series ? ` · ${p.series} series` : ""}. ${p.application_note ?? ""}`}
        meta={
          <>
            <ReliabilityBadge code={p.reliability_code} title />
            <CurveStatusBadge status={p.curve_completeness} digitisedPoints={points.length} />
            <VerificationBadge status={p.verification_status} />
            <StatusPill tone={isCalculationGrade(p.reliability_code) ? "normal" : "critical"}>
              {isCalculationGrade(p.reliability_code) ? "Calculation-grade" : "Not for calculations"}
            </StatusPill>
            <Link to="/engineering/catalog" className="text-[10.5px] text-info hover:underline">← Equipment Catalog</Link>
          </>
        }
      />

      <div className="grid gap-2.5 xl:grid-cols-[1.15fr_1fr]">
        <Panel
          title="Performance curve"
          subtitle={points.length ? `${points.length} digitised points · ${points[0]?.stage_basis} · ${points[0]?.extraction_method}` : "No digitised curve available"}
        >
          {points.length ? (
            <>
              <CurvePlot model={p} points={points} />
              <p className="mt-1 text-[10px] text-muted-foreground">
                Solid = head per stage, dashed = power per stage, shaded band = recommended operating range. Points transcribed from {sourceLabel(d, points[0]?.source_id ?? p.source_id)}.
              </p>
            </>
          ) : (
            <div className="rounded border border-warning/50 bg-warning/10 p-3 text-[11px] text-warning">
              <div className="font-medium">No digitised curve points — {curveAvailability(p.curve_completeness).label}</div>
              <p className="mt-1 text-muted-foreground">
                Catalog curve availability is recorded as “{p.curve_completeness}”, but no source curve points are loaded in this build, so this model is NOT curve-complete. The Engineering Workbench must operate against BEP and floater/compression ROR bounds only — no synthetic curve is generated or shown as source truth.
              </p>
            </div>
          )}
        </Panel>

        <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-1">
          <Panel title="Design point & envelope" bodyClassName="p-0">
            <FieldRow label="Reference" value={`${num(p.reference_hz)} Hz · ${num(p.reference_rpm)} rpm`} />
            <FieldRow label="BEP flow" value={num(p.bep_flow_bpd, 0, " bpd")} />
            <FieldRow label="BEP head" value={num(p.bep_head_ft_per_stage, 2, " ft/stage")} />
            <FieldRow label="BEP power" value={num(p.bep_power_hp_per_stage, 3, " hp/stage")} />
            <FieldRow label="BEP efficiency" value={num(p.bep_efficiency_pct, 1, " %")} />
            <FieldRow label="Flow envelope" value={p.ror_min_bpd != null ? `${num(p.ror_min_bpd)} – ${num(p.ror_max_bpd)} bpd` : "—"} hint="Overall source-stated flow envelope for the model/series" />
            <FieldRow label="Floater ROR" value={p.floater_ror_min_bpd != null ? `${num(p.floater_ror_min_bpd)} – ${num(p.floater_ror_max_bpd)} bpd` : "not stated in source"} hint="Recommended operating range for floater construction (source-backed)" />
            <FieldRow label="Compression ROR" value={p.compression_ror_min_bpd != null ? `${num(p.compression_ror_min_bpd)} – ${num(p.compression_ror_max_bpd)} bpd` : "not stated in source"} hint="Recommended operating range for compression construction; left blank where the source does not state it" />
            <FieldRow label="WSW design capacity" value={p.wsw_design_min_bpd != null ? `${num(p.wsw_design_min_bpd)} – ${num(p.wsw_design_max_bpd)} bpd` : "—"} />
            <FieldRow label="WSW cross-check" value={p.wsw_crosscheck_result ?? "—"} />
          </Panel>

          <Panel title="Construction & limits" bodyClassName="p-0">
            <FieldRow label="Housing OD" value={num(p.od_in, 3, " in")} />
            <FieldRow label="Min casing" value={num(p.min_casing_in, 3, " in")} />
            <FieldRow label="Stage geometry" value={p.stage_geometry ?? "—"} />
            <FieldRow label="Stage material" value={p.stage_material ?? "—"} />
            <FieldRow label="Bearing material" value={p.bearing_material ?? "—"} />
            <FieldRow label="Shaft" value={p.shaft_material ? `${p.shaft_material} · ${num(p.shaft_diameter_in, 3, " in")}` : "—"} />
            <FieldRow label="Shaft hp limit" value={p.shaft_hp_limit != null ? `${num(p.shaft_hp_limit, 0)} hp standard${p.shaft_hp_high_strength != null ? ` / ${num(p.shaft_hp_high_strength, 0)} hp high strength` : ""}` : "—"} />
            <FieldRow label="Housing burst" value={num(p.housing_burst_psi, 0, " psi")} />
            <FieldRow label="Temperature" value={p.temperature_note ?? "—"} />
            <FieldRow label="Construction type" value={p.construction_type ?? "—"} />
          </Panel>
        </div>
      </div>

      <div className="grid gap-2.5 xl:grid-cols-3">
        <Panel title="Provenance" subtitle="Evidence backing every value on this record" bodyClassName="p-0">
          <FieldRow label="Source" value={source ? source.title : "No source recorded"} />
          <FieldRow label="Publisher" value={source?.publisher ?? "—"} />
          <FieldRow label="Type / revision" value={source ? `${source.source_type} · ${source.revision ?? "—"}` : "—"} />
          <FieldRow label="Document ref" value={source?.document_ref ?? "—"} />
          <FieldRow label="Document date" value={source?.document_date ?? "—"} />
          <FieldRow label="Usage rights" value={p.usage_rights_status} />
          <FieldRow label="Lifecycle" value={p.lifecycle_status} />
          <FieldRow label="Last review" value={p.last_review_date ?? "—"} />
        </Panel>

        <Panel title="Installed usage" subtitle="CCED installations referencing this model" bodyClassName="p-0">
          <FieldRow label="CCED installs" value={p.cced_installed_count} />
          <FieldRow label="Installed stage range" value={p.cced_stage_min != null ? `${num(p.cced_stage_min)} – ${num(p.cced_stage_max)} stages` : "—"} hint="Observed in CCED installation records, not an OEM limit" />
          <FieldRow label="Installed motor hp range" value={p.cced_motor_hp_min != null ? `${num(p.cced_motor_hp_min, 1)} – ${num(p.cced_motor_hp_max, 1)} hp` : "—"} />
          <FieldRow label="Raw aliases in CCED" value={p.cced_raw_aliases ?? "—"} />
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead><tr><Th>Well</Th><Th align="right">Section</Th><Th align="right">Stages</Th><Th>Note</Th></tr></thead>
              <tbody>
                {usedBy.map((sec) => {
                  const sys = byId(d.installedSystems, sec.installed_system_id);
                  const well = sys ? byId(d.wells, sys.well_id) : undefined;
                  return (
                    <tr key={sec.id} className="hover:bg-accent/40">
                      <Td>
                        {sys ? <Link to="/engineering/installations/$systemId" params={{ systemId: sys.id }} className="text-info hover:underline">{well?.name ?? sys.well_id}</Link> : "—"}
                      </Td>
                      <Td align="right" mono>#{sec.section_sequence}</Td>
                      <Td align="right" mono>{sec.stages_known ? sec.stages : "unknown"}</Td>
                      <Td className="text-[10px] text-muted-foreground">{sec.note ?? "—"}</Td>
                    </tr>
                  );
                })}
                {usedBy.length === 0 && <tr><Td className="text-[11px] text-muted-foreground">Catalog-only record — no current installations.</Td></tr>}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Aliases & open issues" subtitle="Raw CCED designations mapped to this model" bodyClassName="p-0">
          <ul className="divide-y divide-border text-[10.5px]">
            {aliases.map((a) => (
              <li key={a.id} className="flex items-center gap-2 px-2 py-1">
                <span className="num text-foreground">{a.raw_designation}</span>
                <StatusPill tone={a.mapping_status === "mapped" ? "normal" : a.mapping_status === "ambiguous" ? "watch" : "critical"}>{a.mapping_status}</StatusPill>
                <span className="num ml-auto text-muted-foreground">×{a.cced_occurrences}</span>
              </li>
            ))}
            {issues.map((i) => (
              <li key={i.id} className="px-2 py-1">
                <StatusPill tone={i.severity === "Blocking" ? "critical" : "watch"}>{i.severity}</StatusPill>{" "}
                <span className="text-foreground">{i.title}</span>
                <div className="text-[10px] text-muted-foreground">{i.required_action}</div>
              </li>
            ))}
            {aliases.length === 0 && issues.length === 0 && <li className="px-2 py-2 text-muted-foreground">No aliases or open issues.</li>}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
