import { createFileRoute, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { ReliabilityBadge, num } from "@/components/esp/engineering/governance";
import { byId, sourceLabel } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/fluid")({
  head: () => ({
    meta: [
      { title: "Fluid / PVT definitions — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed fluid and PVT definitions per well: oil API, gas SG, water SG, GOR, bubble point, water cut, viscosity, CO2 and H2S with sample date and evidence class." },
      { property: "og:title", content: "Fluid / PVT definitions" },
      { property: "og:description", content: "PVT inputs governing ESP gas handling and TDH calculations." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: FluidDefinition,
});

function FluidDefinition() {
  const d = api.useLoaderData();
  const stale = d.fluidPvt.filter((p) => !p.sample_date).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Fluid / PVT Definition"
        description="Fluid properties governing gas handling assessment, TDH and pump degradation analysis. Where a PVT sample date is missing the record is treated as provisional."
        meta={
          <>
            <StatusPill tone="info">{d.fluidPvt.length} PVT records</StatusPill>
            <StatusPill tone={stale ? "watch" : "normal"}>{stale} without sample date</StatusPill>
          </>
        }
      />
      <Panel title="Fluid / PVT records" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Well</Th><Th align="right">Oil °API</Th><Th align="right">Gas SG</Th><Th align="right">Water SG</Th>
                <Th align="right">GOR scf/stb</Th><Th align="right">Pb psi</Th><Th align="right">Water cut %</Th>
                <Th align="right">Visc cP</Th><Th align="right">CO₂ %</Th><Th align="right">H₂S ppm</Th>
                <Th>Sample date</Th><Th>Evidence</Th><Th>Source</Th>
              </tr>
            </thead>
            <tbody>
              {d.fluidPvt.map((p) => (
                <tr key={p.well_id} className="hover:bg-accent/40">
                  <Td>{byId(d.wells, p.well_id)?.name ?? p.well_id}</Td>
                  <Td align="right" mono>{num(p.oil_api, 1)}</Td>
                  <Td align="right" mono>{num(p.gas_sg, 3)}</Td>
                  <Td align="right" mono>{num(p.water_sg, 3)}</Td>
                  <Td align="right" mono>{num(p.gor_scf_stb)}</Td>
                  <Td align="right" mono>{num(p.bubble_point_psi)}</Td>
                  <Td align="right" mono>{num(p.water_cut_pct, 1)}</Td>
                  <Td align="right" mono>{num(p.viscosity_cp, 2)}</Td>
                  <Td align="right" mono>{num(p.co2_pct, 2)}</Td>
                  <Td align="right" mono>{num(p.h2s_ppm)}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{p.sample_date ?? "—"}</Td>
                  <Td><ReliabilityBadge code={p.reliability_code} /></Td>
                  <Td className="text-[10px] text-muted-foreground">{sourceLabel(d, p.source_id)}</Td>
                </tr>
              ))}
              {d.fluidPvt.length === 0 && <tr><Td className="text-[11px] text-muted-foreground">No PVT records defined.</Td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
