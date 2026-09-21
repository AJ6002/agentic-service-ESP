import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader, Panel, Metric, StatusPill, Td, Th } from "@/components/esp/ui";
import { byId } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/governance/quality")({
  head: () => ({
    meta: [
      { title: "Data quality & reconciliation — ADVAIT ESP-PMM" },
      { name: "description", content: "Reconciliation queue for unresolved ESP catalog constructions, ambiguous designations, missing curve evidence and incomplete installation records, with owner and required action." },
      { property: "og:title", content: "Data quality & reconciliation" },
      { property: "og:description", content: "Open engineering data issues blocking calculation readiness." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Quality,
});

function Quality() {
  const d = api.useLoaderData();
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");

  const rows = d.issues.filter(
    (i) => (severity === "all" || i.severity === severity) && (status === "all" || i.status === status),
  );

  const byStatus = (s: string) => d.issues.filter((i) => i.status === s).length;
  const counts = {
    blocking: byStatus("Blocking"),
    open: byStatus("Open"),
    governance: byStatus("Governance"),
    resolved: byStatus("Resolved"),
  };

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Data Quality & Reconciliation"
        description="Every unresolved designation, ambiguous construction and missing evidence item is tracked here rather than being silently defaulted. Items stay open until OEM evidence or a customer record resolves them."
        meta={<StatusPill tone={counts.blocking ? "critical" : "normal"}>{counts.blocking} blocking open</StatusPill>}
      />

      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Metric label="Blocking" value={counts.blocking} tone="critical" sub="excluded from calculations" />
        <Metric label="Open" value={counts.open} tone="warning" sub="reconciliation in progress" />
        <Metric label="Governance" value={counts.governance} tone="watch" sub="usage-rights / evidence policy" />
        <Metric label="Resolved" value={counts.resolved} tone="normal" sub="closed with evidence" />
      </div>

      <Panel
        title="Reconciliation queue"
        bodyClassName="p-0"
        actions={
          <div className="flex gap-1.5 text-[10.5px]">
            <select className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground" value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="all">All severities</option><option value="Blocking">Blocking</option><option value="Major">Major</option><option value="Minor">Minor</option>
            </select>
            <select className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All statuses</option><option value="Blocking">Blocking</option><option value="Open">Open</option><option value="Governance">Governance</option><option value="Resolved">Resolved</option>
            </select>
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr><Th>Severity</Th><Th>Category</Th><Th>Issue</Th><Th>Scope</Th><Th>Raw designation</Th><Th align="right">Affected</Th><Th>Required action</Th><Th>Owner</Th><Th>Status</Th></tr>
            </thead>
            <tbody>
              {rows.map((i) => {
                const pm = byId(d.pumpModels, i.pump_model_id);
                return (
                  <tr key={i.id} className="align-top hover:bg-accent/40">
                    <Td><StatusPill tone={i.severity === "Blocking" ? "critical" : i.severity === "Major" ? "warning" : "watch"}>{i.severity}</StatusPill></Td>
                    <Td className="text-[10.5px] text-muted-foreground">{i.category}</Td>
                    <Td className="text-[10.5px]">
                      <div className="text-foreground">{i.title}</div>
                      {i.detail && <div className="text-[10px] text-muted-foreground">{i.detail}</div>}
                      {pm && (
                        <Link to="/engineering/catalog/pumps/$modelId" params={{ modelId: pm.id }} className="text-[10px] text-info hover:underline">{pm.model} →</Link>
                      )}
                    </Td>
                    <Td className="text-[10px] text-muted-foreground">{i.scope ?? "—"}</Td>
                    <Td mono className="text-[10px]">{i.raw_designation ?? "—"}</Td>
                    <Td align="right" mono>{i.affected_installations}</Td>
                    <Td className="text-[10px] text-muted-foreground">{i.required_action ?? "—"}</Td>
                    <Td className="text-[10px] text-muted-foreground">{i.owner ?? "unassigned"}</Td>
                    <Td className="text-[10.5px] text-muted-foreground">{i.status}</Td>
                  </tr>
                );
              })}
              {rows.length === 0 && <tr><Td className="text-[11px] text-muted-foreground">No issues in this filter.</Td></tr>}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Catalog alias mapping" subtitle="Raw CCED designations normalized against catalog models" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead><tr><Th>Raw designation</Th><Th>Entity</Th><Th>Normalized OEM</Th><Th>Normalized series</Th><Th>Normalized model</Th><Th>Construction variant</Th><Th>Status</Th><Th align="right">Occurrences</Th><Th>Note</Th></tr></thead>
            <tbody>
              {d.aliases.map((a) => (
                <tr key={a.id} className="hover:bg-accent/40">
                  <Td mono className="text-[10.5px]">{a.raw_designation}</Td>
                  <Td className="text-[10px] text-muted-foreground">{a.entity_kind}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{byId(d.oems, a.normalized_oem_id)?.name ?? "—"}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{a.normalized_series ?? "—"}</Td>
                  <Td className="text-[10.5px]">{a.normalized_model ?? "—"}</Td>
                  <Td className="text-[10px] text-muted-foreground">{a.construction_variant ?? "—"}</Td>
                  <Td><StatusPill tone={a.mapping_status === "mapped" ? "normal" : a.mapping_status === "ambiguous" ? "watch" : "critical"}>{a.mapping_status}</StatusPill></Td>
                  <Td align="right" mono>{a.cced_occurrences}</Td>
                  <Td className="text-[10px] text-muted-foreground">{a.note ?? "—"}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
