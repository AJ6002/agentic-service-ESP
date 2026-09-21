import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { ReliabilityBadge } from "@/components/esp/engineering/governance";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/governance/import")({
  head: () => ({
    meta: [
      { title: "Import & catalog administration — ADVAIT ESP-PMM" },
      { name: "description", content: "Catalog administration: OEM registry, ingestion pipeline from customer records and OEM documents, governance rules and the Asset ConneX / OTConnex integration boundary." },
      { property: "og:title", content: "Import & catalog administration" },
      { property: "og:description", content: "How governed ESP master data enters the platform and what governance rules apply." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ImportAdmin,
});

function ImportAdmin() {
  const d = api.useLoaderData();

  const stages = [
    { step: "1 · Capture", detail: "Customer installation register and OEM documents are loaded as raw designations with the exact text preserved." },
    { step: "2 · Normalize", detail: "Raw designations are mapped to catalog OEM / series / model via the alias table; ambiguous text stays flagged, never auto-assigned." },
    { step: "3 · Evidence", detail: "Each catalog value is attached to a registered source and reliability class before it can be published." },
    { step: "4 · Digitise", detail: "Curves are digitised only from A1/A2 evidence; otherwise the record stays BEP/Envelope only or Curve pending." },
    { step: "5 · Validate", detail: "Engineering validation gates each installation as READY / LIMITED / BLOCKED for Workbench calculations." },
    { step: "6 · Publish", detail: "Approved definitions become the input contract for surveillance envelopes, exceptions and reliability analytics." },
  ];

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Import / Catalog Administration"
        description="Administrative boundary of the governed catalog. Asset ConneX governs engineering identity and master data; OTConnex supplies live and historical measurement. Definitions are never inferred from OT trends."
        meta={
          <>
            <StatusPill tone="info">{d.oems.length} OEMs</StatusPill>
            <StatusPill tone="muted">{d.aliases.length} alias mappings</StatusPill>
          </>
        }
      />

      <div className="grid gap-2.5 xl:grid-cols-[1fr_1fr]">
        <Panel title="Ingestion pipeline" subtitle="Deterministic, evidence-first path from raw record to governed definition" bodyClassName="p-0">
          <ul className="divide-y divide-border">
            {stages.map((s) => (
              <li key={s.step} className="px-2 py-1.5">
                <div className="text-[11px] font-medium text-foreground">{s.step}</div>
                <div className="text-[10px] text-muted-foreground">{s.detail}</div>
              </li>
            ))}
          </ul>
        </Panel>

        <div className="space-y-2.5">
          <Panel title="OEM registry" bodyClassName="p-0">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead><tr><Th>OEM</Th><Th>Lifecycle</Th><Th align="right">Pump models</Th><Th align="right">Motors</Th><Th>Legal note</Th></tr></thead>
                <tbody>
                  {d.oems.map((o) => (
                    <tr key={o.id} className="hover:bg-accent/40">
                      <Td className="text-[10.5px]">{o.name}</Td>
                      <Td className="text-[10px] text-muted-foreground">{o.lifecycle_status}</Td>
                      <Td align="right" mono>{d.pumpModels.filter((p) => p.oem_id === o.id).length}</Td>
                      <Td align="right" mono>{d.motors.filter((m) => m.oem_id === o.id).length}</Td>
                      <Td className="text-[10px] text-muted-foreground">{o.legal_note ?? "—"}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="Governance rules in force" bodyClassName="p-0">
            <ul className="divide-y divide-border text-[10.5px]">
              <li className="flex items-center gap-2 px-2 py-1"><ReliabilityBadge code="A1" /><span className="text-muted-foreground">OEM datasheet values may be published as calculation inputs.</span></li>
              <li className="flex items-center gap-2 px-2 py-1"><ReliabilityBadge code="C1" /><span className="text-muted-foreground">Secondary catalogs are discovery aids; they never populate published values.</span></li>
              <li className="flex items-center gap-2 px-2 py-1"><ReliabilityBadge code="D" /><span className="text-muted-foreground">Unresolved constructions remain unresolved — no synthetic curve or assumed stage count.</span></li>
              <li className="px-2 py-1 text-muted-foreground">Usage rights are recorded per source; restricted documents are referenced, not reproduced.</li>
              <li className="px-2 py-1 text-muted-foreground">
                Open items are worked in the <Link to="/engineering/governance/quality" className="text-info hover:underline">reconciliation queue</Link> and gated by{" "}
                <Link to="/engineering/governance/validation" className="text-info hover:underline">engineering validation</Link>.
              </li>
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}
