import { createFileRoute, getRouteApi } from "@tanstack/react-router";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { RELIABILITY_CLASSES, ReliabilityBadge, VerificationBadge } from "@/components/esp/engineering/governance";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/governance/sources")({
  head: () => ({
    meta: [
      { title: "Source & provenance registry — ADVAIT ESP-PMM" },
      { name: "description", content: "Registry of every evidence document behind the ESP engineering catalog, with publisher, document reference, revision, usage rights, verification status and reliability class." },
      { property: "og:title", content: "Source & provenance registry" },
      { property: "og:description", content: "Evidence documents and reliability grading rules for governed ESP master data." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Sources,
});

function Sources() {
  const d = api.useLoaderData();

  const usage = (id: string) =>
    d.pumpModels.filter((p) => p.source_id === id).length +
    d.motors.filter((m) => m.source_id === id).length +
    d.cables.filter((c) => c.source_id === id).length +
    d.vsds.filter((v) => v.source_id === id).length +
    d.protectors.filter((p) => p.source_id === id).length +
    d.gasHandling.filter((g) => g.source_id === id).length +
    d.sensors.filter((s) => s.source_id === id).length;

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Source / Provenance Registry"
        description="Nothing enters the catalog without a registered source. Reliability class controls whether a value may be used for engineering calculations or only for discovery and cross-reference."
        meta={<StatusPill tone="info">{d.sources.length} registered sources</StatusPill>}
      />

      <Panel title="Reliability classification" subtitle="Governance rule applied to every governed value" bodyClassName="p-0">
        <ul className="divide-y divide-border">
          {RELIABILITY_CLASSES.map((r) => (
            <li key={r.code} className="flex items-center gap-2 px-2 py-1">
              <ReliabilityBadge code={r.code} />
              <span className="text-[10.5px] text-foreground">{r.label}</span>
              <span className="ml-auto text-[10px] text-muted-foreground">{r.calcGrade ? "usable for calculations" : "discovery / cross-reference only"}</span>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Evidence documents" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr><Th>Title</Th><Th>Publisher</Th><Th>Type</Th><Th>Reference</Th><Th>Revision</Th><Th>Date</Th><Th>Usage rights</Th><Th>Verification</Th><Th>Class</Th><Th align="right">Records</Th></tr>
            </thead>
            <tbody>
              {d.sources.map((s) => (
                <tr key={s.id} className="hover:bg-accent/40">
                  <Td className="text-[10.5px]">{s.title}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{s.publisher}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{s.source_type}</Td>
                  <Td mono className="text-[10px] text-muted-foreground">{s.document_ref ?? "—"}</Td>
                  <Td mono className="text-[10px]">{s.revision ?? "—"}</Td>
                  <Td className="text-[10px] text-muted-foreground">{s.document_date ?? "—"}</Td>
                  <Td className="text-[10px] text-muted-foreground">{s.usage_rights_status}</Td>
                  <Td><VerificationBadge status={s.verification_status} /></Td>
                  <Td><ReliabilityBadge code={s.reliability_code} /></Td>
                  <Td align="right" mono>{usage(s.id)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
