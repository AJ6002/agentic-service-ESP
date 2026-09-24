import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, Metric, StatusPill, Td, Th } from "@/components/esp/ui";
import { isCalculationGrade } from "@/components/esp/engineering/governance";
import { byId, sectionsForSystem } from "@/lib/esp-catalog/selectors";
import type { EngineeringCatalog } from "@/lib/esp-catalog/queries.functions";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/governance/validation")({
  head: () => ({
    meta: [
      { title: "Engineering validation — ADVAIT ESP-PMM" },
      { name: "description", content: "Deterministic readiness checks that decide whether each installed ESP definition can drive Engineering Workbench calculations, surveillance envelopes and reliability analytics." },
      { property: "og:title", content: "Engineering validation" },
      { property: "og:description", content: "Per-installation gating of calculation, envelope and analytics readiness." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Validation,
});

interface Check {
  systemId: string;
  well: string;
  blockers: string[];
  warnings: string[];
}

function evaluate(d: EngineeringCatalog): Check[] {
  return d.installedSystems.map((s) => {
    const blockers: string[] = [];
    const warnings: string[] = [];
    const sections = sectionsForSystem(d, s.id);
    const pump = byId(d.pumpModels, s.normalized_pump_model_id ?? sections[0]?.pump_model_id ?? null);
    const motor = byId(d.motors, s.motor_model_id);
    const eng = d.wellEngineering.find((w) => w.well_id === s.well_id);
    const pvt = d.fluidPvt.find((w) => w.well_id === s.well_id);
    const limits = d.designLimits.find((w) => w.well_id === s.well_id);
    const curvePts = pump ? d.curvePoints.filter((c) => c.pump_model_id === pump.id).length : 0;

    if (!pump) blockers.push("Pump model unresolved against catalog");
    else if (!isCalculationGrade(pump.reliability_code)) blockers.push(`Pump evidence class ${pump.reliability_code} is not calculation-grade`);
    if (sections.length === 0) blockers.push("No pump sections recorded");
    if (sections.some((x) => !x.stages_known)) blockers.push("Stage count unknown on at least one section");
    if (!eng) blockers.push("No well engineering record (depth/completion)");
    if (!pvt) blockers.push("No fluid / PVT definition");
    if (!limits) warnings.push("No operating envelope defined — surveillance falls back to catalog ROR");
    if (!motor) warnings.push("Motor model not selected — motor loading cannot be evaluated");
    if (pump && curvePts === 0) warnings.push("No digitised curve — operating point limited to BEP/ROR bounds");
    if (pump?.wsw_crosscheck_result && /mismatch|conflict/i.test(pump.wsw_crosscheck_result)) warnings.push(`WSW cross-check: ${pump.wsw_crosscheck_result}`);
    if (s.match_status !== "resolved") warnings.push(`Catalog match status is ${s.match_status}`);

    return { systemId: s.id, well: byId(d.wells, s.well_id)?.name ?? s.well_id, blockers, warnings };
  });
}

export function Validation() {
  const d = api.useLoaderData();
  const checks = evaluate(d);
  const ready = checks.filter((c) => c.blockers.length === 0 && c.warnings.length === 0).length;
  const limited = checks.filter((c) => c.blockers.length === 0 && c.warnings.length > 0).length;
  const blocked = checks.filter((c) => c.blockers.length > 0).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Engineering Validation"
        description="Deterministic gates between governed definitions and downstream analytics. A blocked installation is excluded from Engineering Workbench calculations rather than computed on assumed inputs."
        meta={<StatusPill tone={blocked ? "critical" : "normal"}>{blocked} blocked · {limited} limited · {ready} ready</StatusPill>}
      />

      <div className="grid grid-cols-3 gap-2">
        <Metric label="Calculation ready" value={ready} tone="normal" sub="all inputs calculation-grade" />
        <Metric label="Limited" value={limited} tone="watch" sub="computes with stated caveats" />
        <Metric label="Blocked" value={blocked} tone="critical" sub="missing or non-grade inputs" />
      </div>

      <Panel
        title="WSW customer-capacity vs catalog ROR cross-check"
        subtitle="Customer-declared design capacity reconciled against the source-backed compression ROR of the normalized model. Nothing is inferred where the source row is silent."
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead><tr><Th>Well</Th><Th>Raw pump type</Th><Th>Normalized</Th><Th>Customer capacity</Th><Th>Catalog compression ROR</Th><Th>Result</Th><Th>Note</Th></tr></thead>
            <tbody>
              {d.validations.map((v) => (
                <tr key={v.id} className="align-top hover:bg-accent/40">
                  <Td mono className="text-[10.5px]">{v.well_id ?? "—"}</Td>
                  <Td mono className="text-[10.5px]">{v.pump_type_raw ?? "not stated in source"}</Td>
                  <Td className="text-[10.5px]">{v.normalized_oem ? `${v.normalized_oem} ${v.normalized_model ?? ""}` : "unresolved"}</Td>
                  <Td mono className="text-[10.5px]">{v.customer_capacity_range ?? "—"}</Td>
                  <Td mono className="text-[10.5px]">
                    {v.catalog_ror_min_bpd != null ? `${Number(v.catalog_ror_min_bpd).toLocaleString()} – ${Number(v.catalog_ror_max_bpd).toLocaleString()} bpd` : "not loaded"}
                  </Td>
                  <Td>
                    <StatusPill tone={v.range_verification === "MATCH" ? "normal" : v.range_verification === "N/A" ? "watch" : "critical"}>
                      {v.range_verification ?? "—"}
                    </StatusPill>
                  </Td>
                  <Td className="text-[10px] text-muted-foreground">{v.notes ?? "—"}</Td>
                </tr>
              ))}
              {d.validations.length === 0 && <tr><Td className="text-[11px] text-muted-foreground">No WSW cross-check rows loaded.</Td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Per-installation readiness" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead><tr><Th>Well</Th><Th>Readiness</Th><Th>Blockers</Th><Th>Warnings</Th></tr></thead>
            <tbody>
              {checks.map((c) => (
                <tr key={c.systemId} className="align-top hover:bg-accent/40">
                  <Td>
                    <Link to="/engineering/installations/$systemId" params={{ systemId: c.systemId }} className="text-info hover:underline">{c.well}</Link>
                  </Td>
                  <Td>
                    <StatusPill tone={c.blockers.length ? "critical" : c.warnings.length ? "watch" : "normal"}>
                      {c.blockers.length ? "BLOCKED" : c.warnings.length ? "LIMITED" : "READY"}
                    </StatusPill>
                  </Td>
                  <Td className="text-[10px] text-critical">{c.blockers.join(" · ") || "—"}</Td>
                  <Td className="text-[10px] text-muted-foreground">{c.warnings.join(" · ") || "—"}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
