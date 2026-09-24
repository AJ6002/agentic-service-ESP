import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { ReliabilityBadge, num } from "@/components/esp/engineering/governance";
import { byId, sourceLabel, systemForWell } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/well")({
  head: () => ({
    meta: [
      { title: "Well & completion definitions — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed well and completion engineering: casing, tubing, perforations, pump setting depth, deviation, bottom-hole temperature, reservoir pressure and productivity index with provenance." },
      { property: "og:title", content: "Well & completion definitions" },
      { property: "og:description", content: "Completion geometry and reservoir inputs feeding ESP engineering calculations." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WellDefinition,
});

function WellDefinition() {
  const d = api.useLoaderData();
  const missing = d.wells.filter((w) => !d.wellEngineering.some((e) => e.well_id === w.id)).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Well & Completion Definition"
        description="Static well engineering that governs ESP calculations: completion geometry, setting depth, deviation and reservoir inputs. Sourced from completion records — not derived from OT trends."
        meta={
          <>
            <StatusPill tone="info">{d.wellEngineering.length} defined</StatusPill>
            <StatusPill tone={missing ? "warning" : "normal"}>{missing} wells without engineering record</StatusPill>
          </>
        }
      />

      <Panel title="Well engineering records" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Well</Th><Th>Field</Th><Th>Pad</Th><Th>Status</Th>
                <Th align="right">Csg OD in</Th><Th align="right">Csg lb/ft</Th><Th align="right">Tbg ID in</Th>
                <Th align="right">Pump depth ft</Th><Th align="right">Perfs ft</Th><Th align="right">Dev °</Th>
                <Th align="right">BHT °F</Th><Th align="right">Pres psi</Th><Th align="right">PI</Th>
                <Th>Evidence</Th><Th>Source</Th>
              </tr>
            </thead>
            <tbody>
              {d.wells.map((w) => {
                const e = d.wellEngineering.find((x) => x.well_id === w.id);
                const sys = systemForWell(d, w.id);
                return (
                  <tr key={w.id} className="hover:bg-accent/40">
                    <Td>
                      {sys ? <Link to="/engineering/installations/$systemId" params={{ systemId: sys.id }} className="text-info hover:underline">{w.name}</Link> : w.name}
                    </Td>
                    <Td className="text-[10.5px] text-muted-foreground">{byId(d.fields, w.field_id)?.name ?? "—"}</Td>
                    <Td className="text-[10.5px] text-muted-foreground">{w.pad_area ?? "—"}</Td>
                    <Td className="text-[10.5px] text-muted-foreground">{w.well_status}</Td>
                    <Td align="right" mono>{num(e?.casing_od_in, 3)}</Td>
                    <Td align="right" mono>{num(e?.casing_weight_lb_ft, 1)}</Td>
                    <Td align="right" mono>{num(e?.tubing_id_in, 3)}</Td>
                    <Td align="right" mono>{num(e?.pump_setting_depth_ft)}</Td>
                    <Td align="right" mono>{e?.perf_top_ft != null ? `${num(e.perf_top_ft)}–${num(e.perf_bottom_ft)}` : "—"}</Td>
                    <Td align="right" mono>{num(e?.deviation_at_pump_deg, 1)}</Td>
                    <Td align="right" mono>{num(e?.bht_f)}</Td>
                    <Td align="right" mono>{num(e?.reservoir_pressure_psi)}</Td>
                    <Td align="right" mono>{num(e?.productivity_index_bpd_psi, 2)}</Td>
                    <Td><ReliabilityBadge code={e?.reliability_code} /></Td>
                    <Td className="text-[10px] text-muted-foreground">{sourceLabel(d, e?.source_id)}</Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
