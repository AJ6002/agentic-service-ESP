import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { assetDefinitionRegistry } from "@/data/esp/asset-definitions";
import { fields } from "@/data/esp/fleet";
import { PageHeader, Panel, StatusPill, Td, Th, type Tone } from "@/components/esp/ui";
import { n0 } from "@/lib/esp/format";

export const Route = createFileRoute("/engineering/definition/")({
  head: () => ({
    meta: [
      { title: "Engineering Asset Definition — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Governed ESP engineering asset definition registry: revision status, completeness, OT tag coverage, curve availability and engineering readiness across the ESP fleet.",
      },
      { property: "og:title", content: "ESP Engineering Asset Definition registry" },
      { property: "og:description", content: "Versioned ESP engineering inputs with provenance, validation and readiness by capability." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RegistryPage,
});

const readinessTone: Record<string, Tone> = { READY: "normal", LIMITED: "watch", BLOCKED: "critical" };
const statusTone: Record<string, Tone> = { approved: "normal", draft: "watch", "under-review": "info", superseded: "muted" };

const MISSING_CATEGORIES = ["Geometry", "Inflow", "PVT", "Curves", "OT mapping", "Design case", "Envelope", "Components"];

function bar(pct: number, tone: string) {
  return (
    <span className="inline-flex w-24 items-center gap-1.5">
      <span className="h-1.5 flex-1 rounded-sm bg-muted">
        <span className={`block h-full rounded-sm ${tone}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </span>
      <span className="num w-8 text-right text-[11px]">{pct}%</span>
    </span>
  );
}

function RegistryPage() {
  const [field, setField] = useState("all");
  const [readinessFilter, setReadinessFilter] = useState("all");
  const [minCompleteness, setMinCompleteness] = useState(0);
  const [missing, setMissing] = useState("all");

  const rows = useMemo(
    () =>
      assetDefinitionRegistry.filter(
        (r) =>
          (field === "all" || r.fieldId === field) &&
          (readinessFilter === "all" || r.readiness === readinessFilter) &&
          r.completenessPct >= minCompleteness &&
          (missing === "all" || r.missingCategories.includes(missing)),
      ),
    [field, readinessFilter, minCompleteness, missing],
  );

  const exportJson = (wellId: string) => {
    const payload = JSON.stringify(assetDefinitionRegistry.find((r) => r.wellId === wellId), null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `asset-definition-summary-${wellId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Engineering Asset Definition"
        description="Governed input foundation for ESP surveillance, engineering calculations, reliability analytics and future AI/ML. Versioned, source-aware and provenance-tracked — front-end demo data only."
        meta={
          <>
            <StatusPill tone="info">{assetDefinitionRegistry.length} wells governed</StatusPill>
            <StatusPill tone="normal">{assetDefinitionRegistry.filter((r) => r.status === "approved").length} approved revisions</StatusPill>
            <StatusPill tone="watch">{assetDefinitionRegistry.filter((r) => r.readiness !== "READY").length} with readiness gaps</StatusPill>
            <StatusPill tone="muted">Asset ConneX identity · OTConnex acquisition</StatusPill>
          </>
        }
      />

      <Panel
        title="Definition registry"
        subtitle="Completeness, OT mapping coverage, curve availability and engineering readiness per well"
        actions={
          <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] text-muted-foreground">
            <select value={field} onChange={(e) => setField(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground">
              <option value="all">All fields</option>
              {fields.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
            <select value={readinessFilter} onChange={(e) => setReadinessFilter(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground">
              <option value="all">Any readiness</option>
              <option value="READY">READY</option>
              <option value="LIMITED">LIMITED</option>
              <option value="BLOCKED">BLOCKED</option>
            </select>
            <select value={minCompleteness} onChange={(e) => setMinCompleteness(Number(e.target.value))} className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground">
              <option value={0}>Any completeness</option>
              <option value={70}>≥ 70%</option>
              <option value={85}>≥ 85%</option>
              <option value={95}>≥ 95%</option>
            </select>
            <select value={missing} onChange={(e) => setMissing(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground">
              <option value="all">Any missing data</option>
              {MISSING_CATEGORIES.map((m) => (
                <option key={m} value={m}>
                  Missing: {m}
                </option>
              ))}
            </select>
          </div>
        }
        bodyClassName="overflow-x-auto"
      >
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <Th>Well / field / pad</Th>
              <Th>Rev</Th>
              <Th>Status</Th>
              <Th>Completeness</Th>
              <Th>OT coverage</Th>
              <Th>Curves</Th>
              <Th>Design case</Th>
              <Th>Readiness</Th>
              <Th>Missing inputs</Th>
              <Th>Source mix</Th>
              <Th>Updated / owner</Th>
              <Th align="right">Actions</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.wellId} className="hover:bg-accent/40">
                <Td>
                  <Link to="/engineering/definition/$wellId" params={{ wellId: r.wellId }} className="font-medium text-foreground hover:text-primary">
                    {r.wellId}
                  </Link>
                  <span className="block text-[10px] text-muted-foreground">
                    {r.fieldId} · {r.padName}
                  </span>
                </Td>
                <Td mono>{r.revision}</Td>
                <Td>
                  <StatusPill tone={statusTone[r.status] ?? "muted"}>{r.status}</StatusPill>
                </Td>
                <Td>{bar(r.completenessPct, r.completenessPct >= 90 ? "bg-normal" : r.completenessPct >= 75 ? "bg-watch" : "bg-critical")}</Td>
                <Td>{bar(r.otCoveragePct, r.otCoveragePct >= 90 ? "bg-normal" : r.otCoveragePct >= 75 ? "bg-watch" : "bg-critical")}</Td>
                <Td>
                  <StatusPill tone={r.curveAvailability === "Full" ? "normal" : r.curveAvailability === "Partial" ? "watch" : "critical"}>
                    {r.curveAvailability}
                  </StatusPill>
                </Td>
                <Td mono>{r.lastApprovedDesignCase ?? "—"}</Td>
                <Td>
                  <StatusPill tone={readinessTone[r.readiness] ?? "muted"}>{r.readiness}</StatusPill>
                </Td>
                <Td className="max-w-[220px] text-[11px] whitespace-normal text-muted-foreground">
                  {r.requiredMissing ? `${r.requiredMissing} required fields · ` : ""}
                  {r.requiredTagsMissing ? `${r.requiredTagsMissing} required tags · ` : ""}
                  {r.missingCategories.join(", ") || "None"}
                </Td>
                <Td className="text-[10px] text-muted-foreground">
                  {Object.entries(r.sourceMix)
                    .filter(([, v]) => v > 0)
                    .map(([k, v]) => `${k.slice(0, 4)} ${n0(v)}`)
                    .join(" · ")}
                </Td>
                <Td className="text-[10px] text-muted-foreground">
                  {r.updatedAt}
                  <span className="block">{r.owner}</span>
                </Td>
                <Td align="right">
                  <div className="flex justify-end gap-1">
                    <Link
                      to="/engineering/definition/$wellId"
                      params={{ wellId: r.wellId }}
                      className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent"
                    >
                      Open
                    </Link>
                    <Link
                      to="/engineering/definition/$wellId"
                      params={{ wellId: r.wellId }}
                      search={{ tab: "compare" }}
                      className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent"
                    >
                      Compare
                    </Link>
                    <Link
                      to="/engineering/definition/$wellId"
                      params={{ wellId: r.wellId }}
                      search={{ tab: "validation" }}
                      className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent"
                    >
                      Validate
                    </Link>
                    <button
                      type="button"
                      onClick={() => exportJson(r.wellId)}
                      className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10px] hover:bg-accent"
                    >
                      Export JSON
                    </button>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
