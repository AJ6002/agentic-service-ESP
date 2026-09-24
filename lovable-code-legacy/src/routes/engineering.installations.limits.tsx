import { createFileRoute, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { ReliabilityBadge, num } from "@/components/esp/engineering/governance";
import { byId, sourceLabel, systemForWell } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/limits")({
  head: () => ({
    meta: [
      { title: "Operating & design limits — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed ESP operating envelopes: recommended operating range, frequency band, minimum intake pressure, motor load, motor temperature and vibration limits with envelope basis." },
      { property: "og:title", content: "Operating & design limits" },
      { property: "og:description", content: "Envelope definitions consumed by surveillance and exception rules." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: LimitsView,
});

function LimitsView() {
  const d = api.useLoaderData();
  const derived = d.designLimits.filter((l) => (l.envelope_basis ?? "").toLowerCase().includes("catalog")).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Operating & Design Limits"
        description="Envelope definitions per installation. Limits are inherited from catalog ROR and motor/cable ratings, or overridden by an engineering-approved basis. Operations screens compare OT values against these limits — they are never edited from Operations."
        meta={
          <>
            <StatusPill tone="info">{d.designLimits.length} envelopes</StatusPill>
            <StatusPill tone="muted">{derived} catalog-derived</StatusPill>
          </>
        }
      />

      <Panel title="Envelope definitions" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Well</Th><Th>Pump (catalog ROR)</Th><Th align="right">ROR min</Th><Th align="right">ROR max</Th>
                <Th align="right">Min Hz</Th><Th align="right">Max Hz</Th><Th align="right">Min PIP psi</Th>
                <Th align="right">Max motor load %</Th><Th align="right">Max motor °F</Th><Th align="right">Max vib g</Th>
                <Th>Basis</Th><Th>Evidence</Th><Th>Source</Th>
              </tr>
            </thead>
            <tbody>
              {d.designLimits.map((l) => {
                const sys = systemForWell(d, l.well_id);
                const pump = sys ? byId(d.pumpModels, sys.normalized_pump_model_id) : undefined;
                return (
                  <tr key={l.well_id} className="hover:bg-accent/40">
                    <Td>{byId(d.wells, l.well_id)?.name ?? l.well_id}</Td>
                    <Td className="text-[10.5px] text-muted-foreground">
                      {pump ? `${pump.model} (${pump.ror_min_bpd != null ? `${num(pump.ror_min_bpd)}–${num(pump.ror_max_bpd)}` : "no ROR evidence"})` : "unresolved"}
                    </Td>
                    <Td align="right" mono>{num(l.ror_min_bpd)}</Td>
                    <Td align="right" mono>{num(l.ror_max_bpd)}</Td>
                    <Td align="right" mono>{num(l.min_hz, 1)}</Td>
                    <Td align="right" mono>{num(l.max_hz, 1)}</Td>
                    <Td align="right" mono>{num(l.min_pip_psi)}</Td>
                    <Td align="right" mono>{num(l.max_motor_load_pct)}</Td>
                    <Td align="right" mono>{num(l.max_motor_temp_f)}</Td>
                    <Td align="right" mono>{num(l.max_vibration_g, 2)}</Td>
                    <Td className="text-[10px] text-muted-foreground">{l.envelope_basis ?? "—"}</Td>
                    <Td><ReliabilityBadge code={l.reliability_code} /></Td>
                    <Td className="text-[10px] text-muted-foreground">{sourceLabel(d, l.source_id)}</Td>
                  </tr>
                );
              })}
              {d.designLimits.length === 0 && <tr><Td className="text-[11px] text-muted-foreground">No envelopes defined.</Td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
