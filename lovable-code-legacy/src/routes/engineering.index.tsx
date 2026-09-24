import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, Metric, StatusPill } from "@/components/esp/ui";
import { isCalculationGrade, ReliabilityBadge } from "@/components/esp/engineering/governance";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/")({
  head: () => ({
    meta: [
      { title: "Asset Definitions overview — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed ESP engineering master data: OEM catalog, installed fleet, well and fluid definitions, design limits and provenance for every ESP installation." },
      { property: "og:title", content: "Asset Definitions overview — ADVAIT ESP-PMM" },
      { property: "og:description", content: "Asset ConneX governed engineering definitions behind the Engineering Workbench." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Overview,
});

function Overview() {
  const d = api.useLoaderData();
  const calcGradePumps = d.pumpModels.filter((p) => isCalculationGrade(p.reliability_code)).length;
  const withCurves = new Set(d.curvePoints.map((c) => c.pump_model_id)).size;
  const unresolved = d.installedSystems.filter((s) => s.match_status !== "resolved").length;
  const blocking = d.issues.filter((i) => i.status === "Blocking");
  const rawDesignations = d.installedSystems.filter((s) => (s.raw_designation ?? "").trim() !== "").length;
  const blankDesignations = d.installedSystems.length - rawDesignations;
  const ccedPriority = d.pumpModels.filter((p) => (p.cced_installed_count ?? 0) > 0).length;
  const discoveryReported = d.discovery[0]?.source_reported_total ?? null;

  const hierarchy: { level: string; entity: string; count: number; to?: string }[] = [
    { level: "Enterprise / Customer", entity: d.fields[0]?.enterprise ?? "—", count: 1 },
    { level: "Field", entity: "esp_fields", count: d.fields.length },
    { level: "Pad / Area", entity: "esp_wells.pad_area", count: new Set(d.wells.map((w) => w.pad_area ?? "—")).size },
    { level: "Well", entity: "esp_wells", count: d.wells.length, to: "/engineering/installations/well" },
    { level: "Artificial Lift System", entity: "lift_method = ESP", count: d.wells.filter((w) => w.lift_method === "ESP").length },
    { level: "ESP Assembly", entity: "esp_installed_systems", count: d.installedSystems.length, to: "/engineering/installations/assembly" },
    { level: "Pump Section(s)", entity: "esp_installed_pump_sections", count: d.pumpSections.length },
    { level: "Intake / Gas handler", entity: "esp_gas_handling_models", count: d.gasHandling.length },
    { level: "Protector", entity: "esp_protector_models", count: d.protectors.length },
    { level: "Motor", entity: "esp_motor_models", count: d.motors.length },
    { level: "Gauge / Sensor", entity: "esp_sensor_models", count: d.sensors.length },
    { level: "Cable / MLE", entity: "esp_cable_models", count: d.cables.length },
    { level: "VSD / Transformer / Panel", entity: "esp_vsd_models", count: d.vsds.length },
  ];

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Asset Definition Overview"
        description="Governed engineering master data (Asset ConneX concept). Every catalog value carries a source and reliability class; OT measurement remains in OTConnex and is never written here."
        meta={
          <>
            <StatusPill tone="info">Engineering configuration — read-only master data</StatusPill>
            <StatusPill tone={blocking.length ? "critical" : "normal"}>{blocking.length} blocking issues</StatusPill>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4 xl:grid-cols-7">
        <Metric label="CCED source rows" value={d.installedSystems.length} sub={`${rawDesignations} with raw designation · ${blankDesignations} blank`} tone={blankDesignations ? "watch" : "normal"} />
        <Metric label="Wells" value={d.wells.length} sub={`${d.fields.length} fields · ESP lift`} />
        <Metric label="Unresolved / partial match" value={unresolved} sub="excluded from calculations" tone={unresolved ? "watch" : "normal"} />
        <Metric label="Pump models" value={d.pumpModels.length} sub={`${ccedPriority} CCED-priority · ${calcGradePumps} calc-grade`} />
        <Metric label="Digitised curves" value={withCurves} sub={`${d.curvePoints.length} points loaded`} tone={withCurves ? "normal" : "warning"} />
        <Metric label="Secondary discovery" value={d.discovery.length} sub={discoveryReported ? `of ${discoveryReported} reported (C1)` : "C1 — discovery only"} tone="watch" />
        <Metric label="Evidence sources" value={d.sources.length} sub={`${d.aliases.length} raw → normalized aliases`} />
      </div>

      <div className="grid gap-2.5 xl:grid-cols-[1.1fr_1fr]">
        <Panel title="Engineering asset hierarchy" subtitle="Enterprise → Field → Pad → Well → Artificial Lift System → ESP Assembly → components" bodyClassName="p-0">
          <ul className="divide-y divide-border">
            {hierarchy.map((h, i) => (
              <li key={h.level} className="flex items-center gap-2 px-2 py-1">
                <span style={{ paddingLeft: `${Math.min(i, 6) * 8}px` }} className="text-[11px] text-foreground">
                  {i > 0 && <span className="mr-1 text-muted-foreground">└</span>}
                  {h.to ? <Link to={h.to} className="text-info hover:underline">{h.level}</Link> : h.level}
                </span>
                <span className="ml-auto text-[9.5px] text-muted-foreground">{h.entity}</span>
                <span className="num w-10 text-right text-[11px] text-foreground">{h.count}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <div className="space-y-2.5">
          <Panel title="Catalog reliability mix" subtitle="Pump models by evidence class — C1/D are discovery only, never calculation input" bodyClassName="p-0">
            <ul className="divide-y divide-border">
              {["A1", "A2", "B1", "B2", "C1", "D"].map((code) => {
                const n = d.pumpModels.filter((p) => p.reliability_code === code).length;
                return (
                  <li key={code} className="flex items-center gap-2 px-2 py-1">
                    <ReliabilityBadge code={code} />
                    <span className="text-[10.5px] text-muted-foreground">{isCalculationGrade(code) ? "calculation-grade" : "discovery / not usable"}</span>
                    <span className="num ml-auto text-[11px]">{n}</span>
                  </li>
                );
              })}
            </ul>
          </Panel>

          <Panel title="Blocking reconciliation items" subtitle="Must be resolved before the Engineering Workbench can compute against these installations" bodyClassName="p-0">
            <ul className="divide-y divide-border">
              {blocking.slice(0, 6).map((i) => (
                <li key={i.id} className="px-2 py-1.5">
                  <div className="flex items-center gap-2">
                    <StatusPill tone="critical">{i.category}</StatusPill>
                    <span className="text-[11px] text-foreground">{i.title}</span>
                    <span className="num ml-auto text-[10px] text-muted-foreground">{i.affected_installations} inst.</span>
                  </div>
                  <div className="mt-0.5 text-[10px] text-muted-foreground">{i.required_action}</div>
                </li>
              ))}
              {blocking.length === 0 && <li className="px-2 py-2 text-[11px] text-muted-foreground">No blocking items.</li>}
            </ul>
            <div className="border-t border-border px-2 py-1.5">
              <Link to="/engineering/governance/quality" className="text-[10.5px] text-info hover:underline">Open Data Quality &amp; Reconciliation →</Link>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
