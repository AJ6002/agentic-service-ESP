import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, StatusPill } from "@/components/esp/ui";
import { CurveStatusBadge, FieldRow, ReliabilityBadge, isCalculationGrade, num } from "@/components/esp/engineering/governance";
import { byId, oemName, sectionsForSystem, sourceLabel } from "@/lib/esp-catalog/selectors";
import type { EngineeringCatalog } from "@/lib/esp-catalog/queries.functions";

/**
 * Governed engineering context for the Engineering Workbench: which CCED
 * installation is being reasoned about, which catalog model backs it, what the
 * evidence class is, and whether a deterministic calculation is permitted at all.
 * Read-only — no OT values, no setpoints, no writes.
 */
export function GovernedContextPanel({ catalog }: { catalog: EngineeringCatalog }) {
  const d = catalog;
  const [systemId, setSystemId] = useState<string>(d.installedSystems[0]?.id ?? "");
  const s = d.installedSystems.find((x) => x.id === systemId);

  if (!s) {
    return (
      <Panel title="Governed engineering context" subtitle="No governed installation records loaded">
        <p className="text-[11px] text-muted-foreground">
          The governed catalog is unavailable, so the scenarios above run on the demo design basis only.
        </p>
      </Panel>
    );
  }

  const well = byId(d.wells, s.well_id);
  const sections = sectionsForSystem(d, s.id);
  const pump = byId(d.pumpModels, s.normalized_pump_model_id ?? sections[0]?.pump_model_id ?? null);
  const points = pump ? d.curvePoints.filter((c) => c.pump_model_id === pump.id) : [];
  const composite = sections.length > 1 || /composite|tapered/i.test(s.assembly_type);
  const stagesUnknown = sections.some((x) => !x.stages_known);

  const blockers: string[] = [];
  if (!pump) blockers.push("Pump model unresolved against the governed catalog.");
  else if (!isCalculationGrade(pump.reliability_code)) blockers.push(`Pump evidence class ${pump.reliability_code} is discovery-only and must not drive calculations.`);
  if (composite) blockers.push("Composite / tapered assembly: a single-model curve cannot represent this string. Section-by-section curves are required before a combined operating point is computed.");
  if (stagesUnknown) blockers.push("Stage count is unknown on at least one section, so head per string cannot be built.");
  if (points.length === 0) blockers.push("No digitised curve points loaded — only BEP and floater/compression ROR bounds are defensible.");

  return (
    <Panel
      title="Governed engineering context"
      subtitle="Provenance behind any deterministic calculation for a real CCED installation"
      actions={
        <select
          value={systemId}
          onChange={(e) => setSystemId(e.target.value)}
          className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px] text-foreground"
        >
          {d.installedSystems.map((x) => (
            <option key={x.id} value={x.id}>
              {byId(d.wells, x.well_id)?.name ?? x.well_id} · {x.raw_designation ?? "blank designation"}
            </option>
          ))}
        </select>
      }
      bodyClassName="p-0"
    >
      <div className="flex flex-wrap items-center gap-1.5 border-b border-border px-2 py-1.5">
        <StatusPill tone={blockers.length ? "critical" : "normal"}>
          {blockers.length ? "Calculation blocked on governed inputs" : "Calculation-grade governed inputs"}
        </StatusPill>
        {pump && <ReliabilityBadge code={pump.reliability_code} />}
        {pump && <CurveStatusBadge status={pump.curve_completeness} digitisedPoints={points.length} />}
        <StatusPill tone={s.match_status === "resolved" ? "normal" : "watch"}>catalog match: {s.match_status}</StatusPill>
      </div>

      <FieldRow label="Well / installation" value={`${well?.name ?? s.well_id} · ${s.id}`} />
      <FieldRow label="Raw CCED designation" value={(s.raw_designation ?? "").trim() || "blank in source row"} />
      <FieldRow label="Normalized model" value={pump ? `${oemName(d, pump.oem_id)} ${pump.model}` : "unresolved"} />
      <FieldRow label="Assembly" value={`${s.assembly_type} · ${sections.length} pump section${sections.length === 1 ? "" : "s"}`} />
      <FieldRow label="Stage configuration" value={`${s.total_stages ?? "—"} stages${stagesUnknown ? " (partly unknown per section)" : ""}`} />
      <FieldRow
        label="Catalog CCED anchors"
        value={pump ? `${num(pump.cced_stage_min)}–${num(pump.cced_stage_max)} stages · ${num(pump.cced_motor_hp_min, 1)}–${num(pump.cced_motor_hp_max, 1)} hp · ${pump.cced_installed_count} installs` : "—"}
      />
      <FieldRow
        label="Floater ROR"
        value={pump?.floater_ror_min_bpd != null ? `${num(pump.floater_ror_min_bpd)} – ${num(pump.floater_ror_max_bpd)} bpd` : "not stated in source"}
      />
      <FieldRow
        label="Compression ROR"
        value={pump?.compression_ror_min_bpd != null ? `${num(pump.compression_ror_min_bpd)} – ${num(pump.compression_ror_max_bpd)} bpd` : "not stated in source"}
      />
      <FieldRow label="Evidence source" value={pump ? sourceLabel(d, pump.source_id) : "—"} />

      {blockers.length > 0 && (
        <div className="border-t border-critical/40 bg-critical/10 px-2 py-1.5 text-[10.5px] text-critical">
          <div className="font-medium">Governed calculation gate</div>
          <ul className="mt-0.5 list-disc space-y-0.5 pl-4 text-muted-foreground">
            {blockers.map((b) => <li key={b}>{b}</li>)}
          </ul>
        </div>
      )}

      <div className="border-t border-border px-2 py-1.5 text-[10.5px]">
        <Link to="/engineering/installations/$systemId" params={{ systemId: s.id }} className="text-info hover:underline">
          Open governed installation record →
        </Link>
      </div>
    </Panel>
  );
}
