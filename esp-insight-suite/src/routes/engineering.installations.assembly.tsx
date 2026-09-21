import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill } from "@/components/esp/ui";
import { CurveStatusBadge, ReliabilityBadge, num } from "@/components/esp/engineering/governance";
import { byId, oemName, sectionsForSystem } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/assembly")({
  head: () => ({
    meta: [
      { title: "ESP assembly / installed configuration — ADVAIT ESP-PMM" },
      { name: "description", content: "Installed ESP assemblies rendered top-down: pump sections (tapered capable), gas handling, protector, motor, sensor, cable and drive with catalog resolution status." },
      { property: "og:title", content: "ESP assembly / installed configuration" },
      { property: "og:description", content: "Top-down installed ESP string configuration for every governed well." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AssemblyView,
});

function AssemblyView() {
  const d = api.useLoaderData();
  const tapered = d.installedSystems.filter((s) => sectionsForSystem(d, s.id).length > 1).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="ESP Assembly / Installed Configuration"
        description="Physical string as configured downhole. Single, tapered and composite assemblies are all modelled as ordered pump sections against governed catalog models."
        meta={
          <>
            <StatusPill tone="info">{d.installedSystems.length} assemblies</StatusPill>
            <StatusPill tone="watch">{tapered} tapered / composite</StatusPill>
          </>
        }
      />

      <div className="grid gap-2.5 lg:grid-cols-2 2xl:grid-cols-3">
        {d.installedSystems.map((s) => {
          const well = byId(d.wells, s.well_id);
          const sections = sectionsForSystem(d, s.id);
          const stack = [
            { label: "VSD / transformer", value: byId(d.vsds, s.vsd_model_id)?.model },
            { label: "Cable / MLE", value: byId(d.cables, s.cable_model_id)?.model },
            ...sections.map((sec) => {
              const pm = byId(d.pumpModels, sec.pump_model_id);
              return {
                label: `Pump section #${sec.section_sequence}`,
                value: pm ? `${pm.model} · ${sec.stages_known ? `${sec.stages} stg` : "stages unknown"}` : `${sec.raw_designation ?? "unresolved"}`,
                pm,
              };
            }),
            { label: "Intake / gas handling", value: byId(d.gasHandling, s.gas_handling_model_id)?.model },
            { label: "Protector / seal", value: byId(d.protectors, s.protector_model_id)?.model },
            { label: "Motor", value: byId(d.motors, s.motor_model_id)?.model },
            { label: "Sensor / gauge", value: byId(d.sensors, s.sensor_model_id)?.model },
          ];

          return (
            <Panel
              key={s.id}
              title={well?.name ?? s.well_id}
              subtitle={`${s.assembly_type} · ${num(s.total_stages)} total stages · design ${num(s.design_hz, 1)} Hz`}
              bodyClassName="p-0"
              actions={<Link to="/engineering/installations/$systemId" params={{ systemId: s.id }} className="text-[10px] text-info hover:underline">Open</Link>}
            >
              <ul className="divide-y divide-border">
                {stack.map((row, i) => (
                  <li key={i} className="flex items-center gap-2 px-2 py-1">
                    <span className="w-[112px] shrink-0 text-[9.5px] tracking-wide text-muted-foreground uppercase">{row.label}</span>
                    <span className={`text-[10.5px] ${row.value ? "text-foreground" : "text-muted-foreground"}`}>{row.value ?? "not defined"}</span>
                    {"pm" in row && row.pm && (
                      <span className="ml-auto flex items-center gap-1">
                        <CurveStatusBadge status={row.pm.curve_completeness} digitisedPoints={d.curvePoints.filter((c) => c.pump_model_id === row.pm!.id).length} />
                        <ReliabilityBadge code={row.pm.reliability_code} />
                      </span>
                    )}
                  </li>
                ))}
              </ul>
              <div className="border-t border-border px-2 py-1 text-[10px] text-muted-foreground">
                Raw: <span className="num">{s.raw_designation ?? "—"}</span>
                {sections[0]?.pump_model_id && <> · OEM {oemName(d, byId(d.pumpModels, sections[0].pump_model_id)?.oem_id)}</>}
              </div>
            </Panel>
          );
        })}
      </div>
    </div>
  );
}
