import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { definitionByRevision, latestDefinition, revisionsFor, summaryFor } from "@/data/esp/asset-definitions";
import { fieldName, wellById, wells } from "@/data/esp/fleet";
import {
  ALL_SECTION_KEYS,
  collectFields,
  compareRevisions,
  completeness,
  otCoverage,
  readiness,
  sectionMeta,
  validateDefinition,
} from "@/domain/esp/validation";
import { SECTION_LABELS, type AssetDefinitionSectionKey } from "@/domain/esp/asset-definition";
import { PageHeader, Panel, StatusPill, Td, Th, type Tone } from "@/components/esp/ui";
import { EspWellVisual } from "@/components/esp/EspWellVisual";
import { PumpCurveChart } from "@/components/esp/charts";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/engineering/definition/$wellId")({
  head: ({ params }) => ({
    meta: [
      { title: `${params.wellId} asset definition — ADVAIT ESP-PMM` },
      {
        name: "description",
        content: `Versioned engineering asset definition for ${params.wellId}: hierarchy, geometry, inflow, PVT, design basis, OEM curves, OT tag dictionary, operating envelope and reliability context.`,
      },
      { property: "og:title", content: `${params.wellId} engineering asset definition` },
      { property: "og:description", content: "Governed ESP engineering inputs with provenance, validation and readiness." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WorkspacePage,
});

const provTone: Record<string, Tone> = {
  Customer: "info",
  OEM: "opportunity",
  Engineering: "normal",
  "Field Test": "watch",
  OT: "info",
  Calculated: "muted",
  Inferred: "watch",
  Default: "muted",
};

type Tab = "sections" | "validation" | "compare";

function FieldRows({ obj }: { obj: unknown }) {
  const rows = collectFields(obj);
  return (
    <table className="w-full border-collapse">
      <thead>
        <tr>
          <Th>Field</Th>
          <Th align="right">Value</Th>
          <Th>Unit</Th>
          <Th>Source</Th>
          <Th>Req</Th>
          <Th>Provenance</Th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ path, field }) => (
          <tr key={path} className="hover:bg-accent/40">
            <Td className="text-[11px] text-muted-foreground">{path}</Td>
            <Td align="right" mono className={field.value === null ? "text-critical" : ""}>
              {field.value === null || field.value === "" ? (field.provenance.required ? "missing ✱" : "—") : String(field.value)}
            </Td>
            <Td className="text-[10px] text-muted-foreground">{field.unit ?? ""}</Td>
            <Td>
              <StatusPill tone={provTone[field.provenance.sourceClass] ?? "muted"} dot={false}>
                {field.provenance.sourceClass}
              </StatusPill>
            </Td>
            <Td className="text-[10px] text-muted-foreground">{field.provenance.required ? "required" : "optional"}</Td>
            <Td className="max-w-[280px] text-[10px] whitespace-normal text-muted-foreground">
              {[field.provenance.sourceRef, field.provenance.sourceTimestamp, `confidence ${field.provenance.confidence}`, field.provenance.notes]
                .filter(Boolean)
                .join(" · ")}
            </Td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function WorkspacePage() {
  const { wellId } = Route.useParams();
  const well = wellById(wellId) ?? wells[0]!;
  const revisions = revisionsFor(well.id);
  const [revision, setRevision] = useState(latestDefinition(well.id)!.revision);
  const def = definitionByRevision(well.id, revision) ?? latestDefinition(well.id)!;
  const [tab, setTab] = useState<Tab>("sections");
  const [section, setSection] = useState<AssetDefinitionSectionKey>("governance");
  const [localStatus, setLocalStatus] = useState(def.status);
  const [toast, setToast] = useState<string | null>(null);
  const [leftRev, setLeftRev] = useState(revisions[0]!.revision);
  const [rightRev, setRightRev] = useState(revisions[revisions.length - 1]!.revision);
  const [diffFilter, setDiffFilter] = useState<"all" | "changed">("changed");

  const comp = useMemo(() => completeness(def), [def]);
  const findings = useMemo(() => validateDefinition(def), [def]);
  const ready = useMemo(() => readiness(def), [def]);
  const ot = useMemo(() => otCoverage(def), [def]);
  const summary = useMemo(() => summaryFor(well), [well]);
  const locked = localStatus === "approved";

  const act = (msg: string, next?: typeof localStatus) => {
    if (next) setLocalStatus(next);
    setToast(msg);
    window.setTimeout(() => setToast(null), 3200);
  };

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(def, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `asset-definition-${well.id}-${def.revision}.json`;
    a.click();
    URL.revokeObjectURL(url);
    act("Exported local JSON representation (mock — no backend call).");
  };

  const diffs = useMemo(() => {
    const l = definitionByRevision(well.id, leftRev)!;
    const r = definitionByRevision(well.id, rightRev)!;
    const all = compareRevisions(l, r);
    return diffFilter === "all" ? all : all.filter((d) => d.kind !== "unchanged");
  }, [well.id, leftRev, rightRev, diffFilter]);

  const btn = "rounded-sm border border-border bg-card px-2 py-0.5 text-[10.5px] hover:bg-accent disabled:opacity-40";

  return (
    <div className="space-y-2.5">
      <PageHeader
        title={`${well.id} — engineering asset definition`}
        description={`${fieldName(well.fieldId)} · ${well.padName} · definition ${def.definitionId} revision ${def.revision}. Approved revisions are immutable — clone to a new revision to edit engineering fields.`}
        meta={
          <>
            <StatusPill tone={localStatus === "approved" ? "normal" : localStatus === "draft" ? "watch" : "info"}>{localStatus}</StatusPill>
            <StatusPill tone={comp.pct >= 90 ? "normal" : comp.pct >= 75 ? "watch" : "critical"}>{comp.pct}% complete</StatusPill>
            <StatusPill tone={ot.requiredMissing.length ? "warning" : "normal"}>
              OT mapping {ot.pct}% · {ot.requiredMissing.length} required tags missing
            </StatusPill>
            <StatusPill tone={summary.readiness === "READY" ? "normal" : summary.readiness === "LIMITED" ? "watch" : "critical"}>
              Readiness {summary.readiness}
            </StatusPill>
            {locked && <StatusPill tone="muted">Engineering fields locked</StatusPill>}
          </>
        }
        actions={
          <div className="flex flex-wrap items-center gap-1.5">
            <select value={revision} onChange={(e) => setRevision(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px]">
              {revisions.map((r) => (
                <option key={r.revision} value={r.revision}>
                  {r.revision} — {r.status}
                </option>
              ))}
            </select>
            <button type="button" className={btn} disabled={locked} onClick={() => act("Draft saved locally (mock state only).")}>
              Save draft
            </button>
            <button type="button" className={btn} onClick={() => act(`Validation run: ${findings.filter((f) => f.severity === "error").length} errors, ${findings.filter((f) => f.severity === "warning").length} warnings.`)}>
              Validate
            </button>
            <button type="button" className={btn} disabled={locked} onClick={() => act("Submitted for approval (mock).", "under-review")}>
              Submit for approval
            </button>
            <button type="button" className={btn} disabled={locked} onClick={() => act("Revision approved and locked (mock).", "approved")}>
              Approve
            </button>
            <button type="button" className={btn} onClick={() => act("Cloned to new draft revision R3 (mock).", "draft")}>
              Clone revision
            </button>
            <button type="button" className={btn} onClick={exportJson}>
              Export JSON
            </button>
            <Link to="/engineering/definition" className={btn}>
              Registry
            </Link>
          </div>
        }
      />

      {toast && <div className="rounded border border-info/40 bg-info/15 px-2 py-1.5 text-[11px] text-info">{toast}</div>}

      <div className="flex gap-1.5">
        {(["sections", "validation", "compare"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              "rounded-sm border border-border px-2 py-1 text-[11px] capitalize",
              tab === t ? "bg-primary/20 font-semibold text-foreground" : "bg-card text-muted-foreground hover:bg-accent",
            )}
          >
            {t === "sections" ? "Definition sections" : t === "validation" ? "Validation & readiness" : "Revision compare"}
          </button>
        ))}
      </div>

      {tab === "sections" && (
        <div className="grid gap-2.5 xl:grid-cols-[240px_minmax(0,1fr)]">
          <Panel title="Sections" subtitle="Required / optional completion" bodyClassName="p-1.5">
            <ul className="space-y-0.5">
              {ALL_SECTION_KEYS.map((k) => {
                const m = sectionMeta(def, k);
                const done = m.requiredCount === 0 || m.requiredComplete === m.requiredCount;
                return (
                  <li key={k}>
                    <button
                      type="button"
                      onClick={() => setSection(k)}
                      className={cn(
                        "w-full rounded-sm border-l-2 px-2 py-1 text-left text-[11px]",
                        section === k ? "border-primary bg-primary/15 text-foreground" : "border-transparent text-muted-foreground hover:bg-accent",
                      )}
                    >
                      <span className="block truncate">{SECTION_LABELS[k]}</span>
                      <span className={cn("block text-[9.5px]", done ? "text-normal" : "text-watch")}>
                        req {m.requiredComplete}/{m.requiredCount} · opt {m.optionalComplete}/{m.optionalCount}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </Panel>

          <div className="min-w-0 space-y-2.5">
            <Panel title={SECTION_LABELS[section]} subtitle={locked ? "Approved revision — read-only" : "Draft revision — editable in a live build"} bodyClassName="overflow-x-auto p-0">
              {section === "hierarchy" ? (
                <div className="grid gap-2 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)] p-2">
                  <EspWellVisual well={well} variant="compact" />
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <Th>Asset ID</Th>
                        <Th>Class / level</Th>
                        <Th>Relationship</Th>
                        <Th>Make / model</Th>
                        <Th>Serial</Th>
                        <Th>Rating</Th>
                        <Th>Status</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {def.hierarchy.map((n) => (
                        <tr key={n.assetId} className="hover:bg-accent/40">
                          <Td className="text-[10.5px]">{n.assetId}</Td>
                          <Td className="text-[10.5px]">
                            {n.assetClass}
                            <span className="block text-[9.5px] text-muted-foreground">{n.level}</span>
                          </Td>
                          <Td className="text-[10.5px] text-muted-foreground">{n.relationshipType}</Td>
                          <Td className="text-[10.5px]">{[n.make, n.model].filter(Boolean).join(" ") || "—"}</Td>
                          <Td mono className="text-[10.5px]">{n.serialNumber ?? "—"}</Td>
                          <Td className="text-[10.5px] text-muted-foreground">{n.rating ?? "—"}</Td>
                          <Td className="text-[10.5px]">{n.status}</Td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : section === "curves" ? (
                <div className="space-y-2 p-2">
                  {def.curveSets.map((c) => (
                    <div key={c.curveSetId} className="space-y-2">
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
                        <StatusPill tone="opportunity" dot={false}>
                          {c.oem} {c.family} {c.model}
                        </StatusPill>
                        <StatusPill tone={c.curveRevision ? "normal" : "warning"}>{c.curveRevision ?? "curve revision missing"}</StatusPill>
                        <span>
                          base {c.baseFrequencyHz} Hz · BEP {c.bepBpd} bpd · ROR {c.rorLowBpd}–{c.rorHighBpd} bpd · SG {c.referenceFluidSg} · {c.testBasis}
                        </span>
                      </div>
                      <PumpCurveChart well={well} hz={c.baseFrequencyHz} actualFlow={well.liquidRateBpd} actualHead={well.designTdhFt} height={260} />
                      <table className="w-full border-collapse">
                        <thead>
                          <tr>
                            <Th align="right">Flow (bpd)</Th>
                            <Th align="right">Head/stage (ft)</Th>
                            <Th align="right">Efficiency (%)</Th>
                            <Th align="right">BHP/stage</Th>
                          </tr>
                        </thead>
                        <tbody>
                          {c.points.map((p) => (
                            <tr key={p.flowBpd}>
                              <Td align="right" mono>{p.flowBpd}</Td>
                              <Td align="right" mono>{p.headPerStageFt}</Td>
                              <Td align="right" mono>{p.efficiencyPct}</Td>
                              <Td align="right" mono>{p.bhpPerStage}</Td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              ) : section === "signals" ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Canonical ID / name</Th>
                      <Th>Category</Th>
                      <Th>Source system / tag</Th>
                      <Th>Unit</Th>
                      <Th align="right">Rate (s)</Th>
                      <Th>Range / limits</Th>
                      <Th>Quality</Th>
                      <Th>Req</Th>
                      <Th>Used by</Th>
                      <Th>Mapping</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {def.signalMappings.map((m) => (
                      <tr key={m.canonicalId} className="hover:bg-accent/40">
                        <Td className="text-[10.5px]">{m.canonicalId}</Td>
                        <Td className="text-[10.5px] text-muted-foreground">{m.engineeringUnit}</Td>
                        <Td className="max-w-[260px] text-[10px] whitespace-normal text-muted-foreground">
                          {m.sourceSystem ?? "—"}
                          <span className="block">{m.sourceTagPath ?? "no source tag"}</span>
                        </Td>
                        <Td className="text-[10.5px]">{m.engineeringUnit}</Td>
                        <Td align="right" mono>{m.sampleRateSec ?? "—"}</Td>
                        <Td className="text-[10px] text-muted-foreground">
                          {m.rangeMin ?? "—"}…{m.rangeMax ?? "—"}
                          {m.limitHigh !== null && <span className="block">hi {m.limitHigh}{m.limitHighHigh !== null ? ` / hihi ${m.limitHighHigh}` : ""}</span>}
                        </Td>
                        <Td>
                          <StatusPill tone={m.quality === "good" ? "normal" : m.quality === "unknown" ? "muted" : m.quality === "lost" ? "critical" : "watch"}>
                            {m.quality}
                          </StatusPill>
                        </Td>
                        <Td className="text-[10px] text-muted-foreground">{m.required ? "required" : "optional"}</Td>
                        <Td className="max-w-[200px] text-[10px] whitespace-normal text-muted-foreground">{m.usedBy.join(", ")}</Td>
                        <Td>
                          <StatusPill tone={m.mappingStatus === "mapped" ? "normal" : m.mappingStatus === "inferred" ? "watch" : "critical"}>
                            {m.mappingStatus}
                          </StatusPill>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : section === "wellTests" ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Test start</Th>
                      <Th>Source / method</Th>
                      <Th align="right">Liquid</Th>
                      <Th align="right">Oil</Th>
                      <Th align="right">WC %</Th>
                      <Th align="right">GOR</Th>
                      <Th align="right">WHP</Th>
                      <Th align="right">PIP</Th>
                      <Th align="right">PDP</Th>
                      <Th align="right">Hz</Th>
                      <Th align="right">Amps</Th>
                      <Th>Accepted</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {def.wellTests.map((t) => (
                      <tr key={t.id} className="hover:bg-accent/40">
                        <Td className="text-[10.5px]">{t.testStart}</Td>
                        <Td className="text-[10px] text-muted-foreground">
                          {t.source}
                          <span className="block">{t.method}</span>
                        </Td>
                        <Td align="right" mono>{t.liquidBpd ?? "—"}</Td>
                        <Td align="right" mono>{t.oilBopd ?? "—"}</Td>
                        <Td align="right" mono>{t.waterCutPct ?? "—"}</Td>
                        <Td align="right" mono>{t.gorScfStb ?? "—"}</Td>
                        <Td align="right" mono>{t.whpPsi ?? "—"}</Td>
                        <Td align="right" mono>{t.pipPsi ?? "—"}</Td>
                        <Td align="right" mono>{t.pdpPsi ?? "—"}</Td>
                        <Td align="right" mono>{t.frequencyHz ?? "—"}</Td>
                        <Td align="right" mono>{t.motorCurrentA ?? "—"}</Td>
                        <Td>
                          <StatusPill tone={t.accepted ? "normal" : "critical"}>{t.accepted ? `accepted · ${t.confidence}` : "rejected"}</StatusPill>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : section === "lifecycle" ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Date</Th>
                      <Th>Event</Th>
                      <Th align="right">Run life (d)</Th>
                      <Th>Failure mode / cause</Th>
                      <Th>Component</Th>
                      <Th>Action</Th>
                      <Th>DIFA</Th>
                      <Th>Repeat</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {def.lifecycle.map((e) => (
                      <tr key={e.id} className="hover:bg-accent/40">
                        <Td className="text-[10.5px]">{e.date}</Td>
                        <Td className="text-[10.5px]">{e.type}</Td>
                        <Td align="right" mono>{e.runLifeDays ?? "—"}</Td>
                        <Td className="max-w-[230px] text-[10px] whitespace-normal text-muted-foreground">
                          {e.failureMode ?? "—"}
                          {e.confirmedRootCause && <span className="block">root cause: {e.confirmedRootCause}</span>}
                          {!e.confirmedRootCause && e.suspectedCause && <span className="block">suspected: {e.suspectedCause}</span>}
                        </Td>
                        <Td className="text-[10.5px]">{e.componentFailed ?? "—"}</Td>
                        <Td className="max-w-[200px] text-[10px] whitespace-normal text-muted-foreground">{e.interventionAction ?? "—"}</Td>
                        <Td className="max-w-[200px] text-[10px] whitespace-normal text-muted-foreground">{e.difaFinding ?? "—"}</Td>
                        <Td>{e.repeatFailure ? <StatusPill tone="warning">repeat</StatusPill> : "—"}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : section === "provenance" ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Risk / context factor</Th>
                      <Th align="right">Score</Th>
                      <Th>Basis</Th>
                      <Th>Source class</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {def.riskFactors.map((r) => (
                      <tr key={r.key} className="hover:bg-accent/40">
                        <Td>{r.key}</Td>
                        <Td align="right" mono className={r.score > 70 ? "text-critical" : r.score > 45 ? "text-watch" : ""}>
                          {r.score}
                        </Td>
                        <Td className="text-[10.5px] text-muted-foreground">{r.basis}</Td>
                        <Td>
                          <StatusPill tone={provTone[r.sourceClass] ?? "muted"} dot={false}>
                            {r.sourceClass}
                          </StatusPill>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <FieldRows
                  obj={
                    section === "governance"
                      ? def.governance
                      : section === "geometry"
                        ? def.geometry
                        : section === "reservoir"
                          ? def.reservoir
                          : section === "fluid"
                            ? def.fluid
                            : section === "designBasis"
                              ? def.designBasis
                              : section === "components"
                                ? def.components
                                : section === "electrical"
                                  ? def.electrical
                                  : section === "envelope"
                                    ? def.envelope
                                    : section === "calculation"
                                      ? def.calculation
                                      : def.economics
                  }
                />
              )}
            </Panel>

            {section === "geometry" && (
              <Panel title="Repeatable casing / tubing sections" bodyClassName="overflow-x-auto p-0">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Section</Th>
                      <Th align="right">OD (in)</Th>
                      <Th align="right">ID (in)</Th>
                      <Th align="right">Weight / grade</Th>
                      <Th align="right">Top MD</Th>
                      <Th align="right">Bottom MD</Th>
                      <Th>Source</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...def.geometry.casingSections, ...def.geometry.tubingSections].map((s) => (
                      <tr key={s.id}>
                        <Td>{s.label}</Td>
                        <Td align="right" mono>{s.odIn}</Td>
                        <Td align="right" mono>{s.idIn}</Td>
                        <Td align="right" mono>
                          {"weightLbFt" in s ? `${s.weightLbFt ?? "—"} / ${s.grade ?? "—"}` : (s as { material: string | null }).material ?? "—"}
                        </Td>
                        <Td align="right" mono>{s.topMdFt}</Td>
                        <Td align="right" mono>{"shoeMdFt" in s ? s.shoeMdFt : (s as { bottomMdFt: number }).bottomMdFt}</Td>
                        <Td>
                          <StatusPill tone={provTone[s.sourceClass] ?? "muted"} dot={false}>
                            {s.sourceClass}
                          </StatusPill>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            )}
          </div>
        </div>
      )}

      {tab === "validation" && (
        <div className="grid gap-2.5 lg:grid-cols-2">
          <Panel title="Validation findings" subtitle={`${findings.filter((f) => f.severity === "error").length} errors · ${findings.filter((f) => f.severity === "warning").length} warnings · ${findings.filter((f) => f.severity === "info").length} info`} bodyClassName="p-0 overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Rule</Th>
                  <Th>Severity</Th>
                  <Th>Finding</Th>
                  <Th align="right">Go to</Th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f, i) => (
                  <tr key={`${f.id}-${i}`} className="hover:bg-accent/40">
                    <Td className="text-[10.5px]">{f.id}</Td>
                    <Td>
                      <StatusPill tone={f.severity === "error" ? "critical" : f.severity === "warning" ? "warning" : "info"}>{f.severity}</StatusPill>
                    </Td>
                    <Td className="max-w-[380px] text-[10.5px] whitespace-normal">
                      {f.title}
                      <span className="block text-[10px] text-muted-foreground">{f.detail}</span>
                      <span className="block text-[9.5px] text-muted-foreground">{f.rationale}</span>
                    </Td>
                    <Td align="right">
                      <button
                        type="button"
                        className={btn}
                        onClick={() => {
                          setTab("sections");
                          setSection(f.section);
                        }}
                      >
                        {f.fieldPath ?? f.section}
                      </button>
                    </Td>
                  </tr>
                ))}
                {!findings.length && (
                  <tr>
                    <Td className="text-[11px] text-muted-foreground">No findings — definition passes all deterministic checks.</Td>
                  </tr>
                )}
              </tbody>
            </table>
          </Panel>

          <Panel title="Readiness by capability" subtitle="Derived from mapped canonical signals and required engineering inputs" bodyClassName="p-0 overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Capability</Th>
                  <Th>Status</Th>
                  <Th align="right">Inputs</Th>
                  <Th>Blockers</Th>
                </tr>
              </thead>
              <tbody>
                {ready.map((r) => (
                  <tr key={r.capability} className="hover:bg-accent/40">
                    <Td>{r.capability}</Td>
                    <Td>
                      <StatusPill tone={r.level === "READY" ? "normal" : r.level === "LIMITED" ? "watch" : "critical"}>{r.level}</StatusPill>
                    </Td>
                    <Td align="right" mono>{r.completenessPct}%</Td>
                    <Td className="max-w-[260px] text-[10px] whitespace-normal text-muted-foreground">{r.blockers.join("; ") || "None"}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      )}

      {tab === "compare" && (
        <Panel
          title="Revision compare"
          subtitle="Added / removed / modified / unchanged engineering fields"
          actions={
            <div className="flex items-center gap-1.5 text-[10.5px]">
              <select value={leftRev} onChange={(e) => setLeftRev(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5">
                {revisions.map((r) => (
                  <option key={r.revision} value={r.revision}>
                    {r.revision}
                  </option>
                ))}
              </select>
              <span className="text-muted-foreground">vs</span>
              <select value={rightRev} onChange={(e) => setRightRev(e.target.value)} className="rounded-sm border border-border bg-card px-1.5 py-0.5">
                {revisions.map((r) => (
                  <option key={r.revision} value={r.revision}>
                    {r.revision}
                  </option>
                ))}
              </select>
              <button type="button" className={btn} onClick={() => setDiffFilter(diffFilter === "all" ? "changed" : "all")}>
                {diffFilter === "all" ? "Show changes only" : "Show all fields"}
              </button>
            </div>
          }
          bodyClassName="p-0 overflow-x-auto"
        >
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Field path</Th>
                <Th>Change</Th>
                <Th align="right">{leftRev}</Th>
                <Th align="right">{rightRev}</Th>
                <Th>Unit</Th>
                <Th>Source (left → right)</Th>
              </tr>
            </thead>
            <tbody>
              {diffs.map((d) => (
                <tr key={d.path} className="hover:bg-accent/40">
                  <Td className="text-[10.5px] text-muted-foreground">{d.path}</Td>
                  <Td>
                    <StatusPill tone={d.kind === "added" ? "normal" : d.kind === "removed" ? "critical" : d.kind === "modified" ? "watch" : "muted"}>{d.kind}</StatusPill>
                  </Td>
                  <Td align="right" mono>{d.left}</Td>
                  <Td align="right" mono>{d.right}</Td>
                  <Td className="text-[10px] text-muted-foreground">{d.unit ?? ""}</Td>
                  <Td className="text-[10px] text-muted-foreground">
                    {d.leftSource ?? "—"} → {d.rightSource ?? "—"}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}
