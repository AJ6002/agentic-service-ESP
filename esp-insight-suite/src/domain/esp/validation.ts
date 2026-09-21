/**
 * ESP-PMM — deterministic validation & readiness rules for the Engineering
 * Asset Definition. Pure functions, no UI, no side effects: the same rule set
 * can be re-implemented server-side (Java/Python) from these definitions.
 */

import type {
  AssetDefinitionRevision,
  AssetDefinitionSectionKey,
  EngField,
  ReadinessCapability,
  ReadinessResult,
  SectionMeta,
  SourceClass,
} from "./asset-definition";
import { REQUIRED_SIGNAL_IDS } from "./tag-dictionary";

export type FindingSeverity = "error" | "warning" | "info";

export interface ValidationRule {
  id: string;
  severity: FindingSeverity;
  section: AssetDefinitionSectionKey;
  title: string;
  rationale: string;
}

export interface ValidationFinding extends ValidationRule {
  detail: string;
  /** Field path used by the UI's navigate-to-field links. */
  fieldPath?: string | undefined;
}

export const VALIDATION_RULES: ValidationRule[] = [
  { id: "GEO-001", severity: "error", section: "geometry", title: "Pump setting depth missing", rationale: "Pump setting depth is required for pressure-gradient and TDH calculations." },
  { id: "GEO-002", severity: "error", section: "geometry", title: "Perforation depths missing", rationale: "Inflow datum and drawdown cannot be referenced without perforation depths." },
  { id: "GEO-003", severity: "warning", section: "geometry", title: "Tubing ID missing on a section", rationale: "Friction losses default to a generic model when tubing ID is absent." },
  { id: "RES-001", severity: "error", section: "reservoir", title: "Reservoir pressure ≤ flowing bottomhole pressure", rationale: "Inflow is physically invalid when Pr ≤ Pwf." },
  { id: "RES-002", severity: "warning", section: "reservoir", title: "Productivity index missing", rationale: "PI is needed for inflow prediction and drawdown limits." },
  { id: "RES-003", severity: "info", section: "reservoir", title: "Inflow test older than 180 days", rationale: "Stale inflow tests reduce confidence of expected-vs-actual analysis." },
  { id: "FLU-001", severity: "warning", section: "fluid", title: "Bubble point missing", rationale: "Free-gas estimation at intake relies on bubble-point pressure." },
  { id: "DSN-001", severity: "error", section: "designBasis", title: "ROR low ≥ ROR high", rationale: "Recommended operating range bounds are inverted or equal." },
  { id: "DSN-002", severity: "warning", section: "designBasis", title: "Design rate outside pump curve domain", rationale: "Target rate lies outside the catalogued curve flow domain." },
  { id: "DSN-003", severity: "error", section: "designBasis", title: "Stages missing while TDH and head/stage present", rationale: "Stage count is required to reconcile TDH with head per stage." },
  { id: "DSN-004", severity: "warning", section: "designBasis", title: "Motor rating below calculated demand", rationale: "Required BHP exceeds motor nameplate rating." },
  { id: "DSN-005", severity: "error", section: "designBasis", title: "Approved design case missing", rationale: "Actual-vs-design analysis requires an approved design case." },
  { id: "CRV-001", severity: "error", section: "curves", title: "Curve revision missing", rationale: "Curve provenance is required before pump performance analysis is trusted." },
  { id: "CRV-002", severity: "warning", section: "curves", title: "Curve set has fewer than 6 points", rationale: "Sparse curves degrade interpolation accuracy." },
  { id: "CMP-001", severity: "warning", section: "components", title: "Cable length missing", rationale: "Cable voltage drop cannot be estimated without length." },
  { id: "CMP-002", severity: "warning", section: "components", title: "Gas handling rating missing", rationale: "Gas diagnostics uses the rated GVF handling capability." },
  { id: "SIG-001", severity: "error", section: "signals", title: "Required canonical tags unmapped", rationale: "Surveillance and calculations depend on required canonical signals." },
  { id: "SIG-002", severity: "warning", section: "signals", title: "PIP / PDP mapping degraded", rationale: "Pressure analysis confidence drops when intake or discharge quality is not good." },
  { id: "SIG-003", severity: "warning", section: "signals", title: "Engineering units inconsistent with canonical definition", rationale: "Unit mismatch between source mapping and canonical dictionary." },
  { id: "ENV-001", severity: "error", section: "envelope", title: "Operating envelope not approved", rationale: "Exception generation requires an approved, versioned limit set." },
  { id: "ENV-002", severity: "warning", section: "envelope", title: "Motor temperature limits missing", rationale: "Thermal exceptions cannot be raised without warning/critical limits." },
  { id: "CAL-001", severity: "info", section: "calculation", title: "Generic demo correlations in use", rationale: "Results are indicative only; no OEM-certified method is selected." },
  { id: "LIV-001", severity: "warning", section: "signals", title: "Live surveillance prerequisites missing", rationale: "Data-quality heartbeat or run status is not available." },
  { id: "LIF-001", severity: "info", section: "lifecycle", title: "No DIFA record for last failure", rationale: "Root-cause learning is incomplete without teardown findings." },
];

const rule = (id: string) => VALIDATION_RULES.find((r) => r.id === id)!;

const missing = (f: EngField<unknown> | undefined) => !f || f.value === null || f.value === "";
const num = (f: EngField<number> | undefined) => (f && typeof f.value === "number" ? f.value : null);

/* ------------------------------------------------------------------ */
/* Completeness                                                       */
/* ------------------------------------------------------------------ */

const isEngField = (v: unknown): v is EngField<unknown> =>
  !!v && typeof v === "object" && "provenance" in (v as Record<string, unknown>) && "value" in (v as Record<string, unknown>);

export function collectFields(obj: unknown, prefix = ""): { path: string; field: EngField<unknown> }[] {
  const out: { path: string; field: EngField<unknown> }[] = [];
  if (!obj || typeof obj !== "object") return out;
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (isEngField(v)) out.push({ path, field: v });
    else if (v && typeof v === "object" && !Array.isArray(v)) out.push(...collectFields(v, path));
  }
  return out;
}

const SECTION_FIELD_ROOTS: Partial<Record<AssetDefinitionSectionKey, keyof AssetDefinitionRevision>> = {
  governance: "governance",
  geometry: "geometry",
  reservoir: "reservoir",
  fluid: "fluid",
  designBasis: "designBasis",
  components: "components",
  electrical: "electrical",
  envelope: "envelope",
  calculation: "calculation",
  economics: "economics",
};

export function sectionMeta(def: AssetDefinitionRevision, key: AssetDefinitionSectionKey): SectionMeta {
  const root = SECTION_FIELD_ROOTS[key];
  if (root) {
    const fields = collectFields(def[root]);
    const req = fields.filter((f) => f.field.provenance.required);
    const opt = fields.filter((f) => !f.field.provenance.required);
    return {
      key,
      requiredCount: req.length,
      requiredComplete: req.filter((f) => !missing(f.field)).length,
      optionalCount: opt.length,
      optionalComplete: opt.filter((f) => !missing(f.field)).length,
    };
  }
  // Collection-based sections
  const counts: Record<string, [number, number, number, number]> = {
    hierarchy: [1, def.hierarchy.length ? 1 : 0, def.hierarchy.length, def.hierarchy.filter((n) => n.model || n.serialNumber).length],
    curves: [
      1,
      def.curveSets.length ? 1 : 0,
      def.curveSets.length * 2,
      def.curveSets.reduce((a, c) => a + (c.curveRevision ? 1 : 0) + (c.catalogDocumentRef ? 1 : 0), 0),
    ],
    signals: [
      REQUIRED_SIGNAL_IDS.length,
      def.signalMappings.filter((m) => m.required && m.mappingStatus === "mapped").length,
      def.signalMappings.length,
      def.signalMappings.filter((m) => m.mappingStatus === "mapped" || m.mappingStatus === "inferred").length,
    ],
    wellTests: [1, def.wellTests.filter((t) => t.accepted).length ? 1 : 0, def.wellTests.length, def.wellTests.length],
    lifecycle: [1, def.lifecycle.length ? 1 : 0, def.lifecycle.length, def.lifecycle.filter((e) => e.difaFinding).length],
    provenance: [1, 1, def.riskFactors.length, def.riskFactors.length],
  };
  const c = counts[key] ?? [0, 0, 0, 0];
  return { key, requiredCount: c[0]!, requiredComplete: c[1]!, optionalCount: c[2]!, optionalComplete: c[3]! };
}

export const ALL_SECTION_KEYS: AssetDefinitionSectionKey[] = [
  "governance",
  "hierarchy",
  "geometry",
  "reservoir",
  "fluid",
  "designBasis",
  "curves",
  "components",
  "electrical",
  "signals",
  "wellTests",
  "envelope",
  "calculation",
  "lifecycle",
  "economics",
  "provenance",
];

export function completeness(def: AssetDefinitionRevision) {
  const metas = ALL_SECTION_KEYS.map((k) => sectionMeta(def, k));
  const req = metas.reduce((a, m) => a + m.requiredCount, 0);
  const reqDone = metas.reduce((a, m) => a + m.requiredComplete, 0);
  const opt = metas.reduce((a, m) => a + m.optionalCount, 0);
  const optDone = metas.reduce((a, m) => a + m.optionalComplete, 0);
  // Required inputs weighted 3x optional inputs.
  const pct = Math.round(((reqDone * 3 + optDone) / Math.max(req * 3 + opt, 1)) * 100);
  return { metas, pct, requiredMissing: req - reqDone, optionalMissing: opt - optDone };
}

export function sourceMix(def: AssetDefinitionRevision): Record<SourceClass, number> {
  const mix: Record<SourceClass, number> = {
    Customer: 0,
    OEM: 0,
    Engineering: 0,
    "Field Test": 0,
    OT: 0,
    Calculated: 0,
    Inferred: 0,
    Default: 0,
  };
  for (const root of Object.values(SECTION_FIELD_ROOTS)) {
    for (const { field } of collectFields(def[root!])) {
      if (field.value === null || field.value === "") continue;
      mix[field.provenance.sourceClass] += 1;
    }
  }
  return mix;
}

export function otCoverage(def: AssetDefinitionRevision) {
  const total = def.signalMappings.length || 1;
  const mapped = def.signalMappings.filter((m) => m.mappingStatus === "mapped").length;
  const requiredMissing = REQUIRED_SIGNAL_IDS.filter(
    (id) => !def.signalMappings.some((m) => m.canonicalId === id && m.mappingStatus === "mapped"),
  );
  return { pct: Math.round((mapped / total) * 100), requiredMissing };
}

/* ------------------------------------------------------------------ */
/* Validation                                                         */
/* ------------------------------------------------------------------ */

export function validateDefinition(def: AssetDefinitionRevision): ValidationFinding[] {
  const out: ValidationFinding[] = [];
  const add = (id: string, detail: string, fieldPath?: string) => out.push({ ...rule(id), detail, fieldPath });

  // Geometry
  if (missing(def.geometry.pumpSettingMdFt)) add("GEO-001", "geometry.pumpSettingMdFt is empty.", "geometry.pumpSettingMdFt");
  if (missing(def.geometry.perfTopMdFt) || missing(def.geometry.perfBottomMdFt))
    add("GEO-002", "Perforation top and/or bottom MD is empty.", "geometry.perfTopMdFt");
  if (def.geometry.tubingSections.some((t) => !t.idIn))
    add("GEO-003", "One or more tubing sections have no internal diameter.", "geometry.tubingSections");

  // Reservoir
  const pr = num(def.reservoir.reservoirPressurePsi);
  const pwf = num(def.reservoir.flowingBhpPsi);
  if (pr !== null && pwf !== null && pr <= pwf) add("RES-001", `Pr ${pr} psi ≤ Pwf ${pwf} psi.`, "reservoir.reservoirPressurePsi");
  if (missing(def.reservoir.productivityIndexBpdPsi)) add("RES-002", "PI not supplied.", "reservoir.productivityIndexBpdPsi");
  const testDate = def.reservoir.testDate.value;
  if (typeof testDate === "string" && testDate) {
    const days = Math.round((Date.parse("2026-08-13") - Date.parse(testDate)) / 86400000);
    if (days > 180) add("RES-003", `Last inflow test is ${days} days old.`, "reservoir.testDate");
  }

  // Fluid
  if (missing(def.reservoir.bubblePointPsi)) add("FLU-001", "Bubble-point pressure not supplied.", "fluid.bubblePointPsi");

  // Design basis
  const rorLow = num(def.designBasis.rorLowBpd);
  const rorHigh = num(def.designBasis.rorHighBpd);
  if (rorLow !== null && rorHigh !== null && rorLow >= rorHigh) add("DSN-001", `ROR low ${rorLow} ≥ ROR high ${rorHigh}.`, "designBasis.rorLowBpd");
  const target = num(def.designBasis.targetLiquidBpd);
  const curve = def.curveSets[0];
  if (target !== null && curve && curve.points.length) {
    const lo = curve.points[0]!.flowBpd;
    const hi = curve.points[curve.points.length - 1]!.flowBpd;
    if (target < lo || target > hi) add("DSN-002", `Target ${target} bpd outside curve domain ${lo}-${hi} bpd.`, "designBasis.targetLiquidBpd");
  }
  if (missing(def.designBasis.stages) && !missing(def.designBasis.designTdhFt) && !missing(def.designBasis.headPerStageFt))
    add("DSN-003", "Stage count missing while TDH and head/stage are populated.", "designBasis.stages");
  const bhp = num(def.designBasis.requiredBhp);
  const hp = num(def.designBasis.motorHp);
  if (bhp !== null && hp !== null && bhp > hp) add("DSN-004", `Required ${bhp} bhp vs motor ${hp} hp.`, "designBasis.motorHp");
  if (def.designBasis.approvalStatus.value !== "Approved") add("DSN-005", "No approved design case linked to this revision.", "designBasis.approvalStatus");

  // Curves
  for (const c of def.curveSets) {
    if (!c.curveRevision) add("CRV-001", `${c.oem} ${c.model}: curve revision not recorded.`, "curves");
    if (c.points.length < 6) add("CRV-002", `${c.oem} ${c.model}: only ${c.points.length} curve points.`, "curves");
  }
  if (!def.curveSets.length) add("CRV-001", "No OEM curve set attached.", "curves");

  // Components
  if (missing(def.components.cable.lengthFt)) add("CMP-001", "Cable length not supplied.", "components.cable.lengthFt");
  if (missing(def.components.intake.ratedGasHandlingGvfPct)) add("CMP-002", "Rated gas handling not supplied.", "components.intake.ratedGasHandlingGvfPct");

  // Signals
  const ot = otCoverage(def);
  if (ot.requiredMissing.length) add("SIG-001", `${ot.requiredMissing.length} required tags unmapped: ${ot.requiredMissing.slice(0, 4).join(", ")}${ot.requiredMissing.length > 4 ? " …" : ""}`, "signals");
  const pressure = def.signalMappings.filter((m) => m.canonicalId === "ESP.PIP" || m.canonicalId === "ESP.PDP");
  if (pressure.some((m) => m.quality !== "good")) add("SIG-002", "PIP and/or PDP signal quality is not good.", "signals");
  const unitMismatch = def.signalMappings.filter((m) => m.rawUnit && m.engineeringUnit && m.scale === null);
  if (unitMismatch.length) add("SIG-003", `${unitMismatch.length} mapping(s) have a raw unit but no scaling factor.`, "signals");
  const heartbeat = def.signalMappings.find((m) => m.canonicalId === "ESP.DQ_HEARTBEAT");
  if (!heartbeat || heartbeat.mappingStatus !== "mapped") add("LIV-001", "Data-quality heartbeat is not mapped.", "signals");

  // Envelope
  if (def.envelope.approvalStatus.value !== "Approved") add("ENV-001", "Operating envelope revision is not approved.", "envelope.approvalStatus");
  if (missing(def.envelope.motorTempWarningF) || missing(def.envelope.motorTempCriticalF))
    add("ENV-002", "Motor temperature warning/critical limits incomplete.", "envelope.motorTempWarningF");

  // Calculation
  if (def.calculation.genericCorrelations) add("CAL-001", "Generic ADVAIT demo correlations selected — not OEM-certified.", "calculation.pvtCorrelation");

  // Lifecycle
  const lastFailure = def.lifecycle.filter((e) => e.type === "Failure").at(-1);
  if (lastFailure && !lastFailure.difaFinding) add("LIF-001", `No DIFA finding recorded for failure on ${lastFailure.date}.`, "lifecycle");

  return out;
}

/* ------------------------------------------------------------------ */
/* Readiness by capability                                            */
/* ------------------------------------------------------------------ */

const CAPABILITY_INPUTS: Record<ReadinessCapability, { signals: string[]; check: (d: AssetDefinitionRevision) => string[] }> = {
  "Basic Surveillance": {
    signals: ["ESP.RUN_STATUS", "ESP.FREQUENCY", "ESP.MOTOR_CURRENT", "ESP.DQ_HEARTBEAT"],
    check: () => [],
  },
  "Pressure Analysis": {
    signals: ["ESP.PIP", "ESP.PDP", "ESP.WHP"],
    check: (d) => [
      ...(missing(d.geometry.pumpSettingMdFt) ? ["Pump setting depth missing"] : []),
      ...(missing(d.fluid.waterCutPct) ? ["Water cut missing"] : []),
    ],
  },
  "Pump Performance": {
    signals: ["ESP.FREQUENCY", "ESP.LIQUID_RATE", "ESP.PIP", "ESP.PDP"],
    check: (d) => [
      ...(d.curveSets.length ? [] : ["No OEM curve set"]),
      ...(d.curveSets[0] && !d.curveSets[0].curveRevision ? ["Curve revision missing"] : []),
      ...(missing(d.designBasis.stages) ? ["Stage count missing"] : []),
      ...(d.designBasis.approvalStatus.value !== "Approved" ? ["Design case not approved"] : []),
    ],
  },
  "Gas Diagnostics": {
    signals: ["ESP.PIP", "ESP.CASING_PRESSURE", "ESP.MOTOR_CURRENT", "ESP.GAS_RATE"],
    check: (d) => [
      ...(missing(d.reservoir.bubblePointPsi) ? ["Bubble point missing"] : []),
      ...(missing(d.components.intake.ratedGasHandlingGvfPct) ? ["Gas handling rating missing"] : []),
    ],
  },
  Reliability: {
    signals: ["ESP.RUN_STATUS", "ESP.MOTOR_TEMP"],
    check: (d) => (d.lifecycle.length ? [] : ["No lifecycle history"]),
  },
  "AI Advisor Context": {
    signals: ["ESP.PIP", "ESP.PDP", "ESP.MOTOR_CURRENT", "ESP.MOTOR_TEMP", "ESP.LIQUID_RATE"],
    check: (d) => (d.wellTests.some((t) => t.accepted) ? [] : ["No accepted well test for calibration"]),
  },
  "ML Training Eligibility": {
    signals: ["ESP.PIP", "ESP.PDP", "ESP.MOTOR_CURRENT", "ESP.VIBRATION", "ESP.LIQUID_RATE", "ESP.MOTOR_TEMP"],
    check: (d) => [
      ...(d.lifecycle.filter((e) => e.type === "Failure").length ? [] : ["No labelled failure events"]),
      ...(d.signalMappings.some((m) => m.quality !== "good") ? ["Signal quality gaps in training window"] : []),
    ],
  },
};

export function readiness(def: AssetDefinitionRevision): ReadinessResult[] {
  return (Object.keys(CAPABILITY_INPUTS) as ReadinessCapability[]).map((capability) => {
    const spec = CAPABILITY_INPUTS[capability];
    const unmapped = spec.signals.filter(
      (id) => !def.signalMappings.some((m) => m.canonicalId === id && (m.mappingStatus === "mapped" || m.mappingStatus === "inferred")),
    );
    const degraded = spec.signals.filter((id) => def.signalMappings.some((m) => m.canonicalId === id && m.quality !== "good" && m.mappingStatus === "mapped"));
    const blockers = [...unmapped.map((s) => `${s} unmapped`), ...spec.check(def)];
    const soft = degraded.map((s) => `${s} quality degraded`);
    const satisfied = spec.signals.length - unmapped.length;
    const completenessPct = Math.round(((satisfied / spec.signals.length) * 0.7 + (blockers.length ? 0 : 0.3)) * 100);
    const level: ReadinessResult["level"] = blockers.length >= 2 ? "BLOCKED" : blockers.length === 1 || soft.length ? "LIMITED" : "READY";
    return { capability, level, completenessPct, blockers: [...blockers, ...soft] };
  });
}

/* ------------------------------------------------------------------ */
/* Revision compare                                                   */
/* ------------------------------------------------------------------ */

export type DiffKind = "added" | "removed" | "modified" | "unchanged";

export interface DiffRow {
  path: string;
  kind: DiffKind;
  left: string;
  right: string;
  unit?: string | undefined;
  leftSource?: SourceClass | undefined;
  rightSource?: SourceClass | undefined;
}

const show = (v: unknown) => (v === null || v === "" || v === undefined ? "—" : String(v));

export function compareRevisions(a: AssetDefinitionRevision, b: AssetDefinitionRevision): DiffRow[] {
  const left = new Map(collectFields(a).map((f) => [f.path, f.field]));
  const right = new Map(collectFields(b).map((f) => [f.path, f.field]));
  const paths = [...new Set([...left.keys(), ...right.keys()])].sort();
  return paths.map((path) => {
    const l = left.get(path);
    const r = right.get(path);
    const lv = l ? l.value : undefined;
    const rv = r ? r.value : undefined;
    let kind: DiffKind = "unchanged";
    if ((lv === null || lv === undefined || lv === "") && rv !== null && rv !== undefined && rv !== "") kind = "added";
    else if ((rv === null || rv === undefined || rv === "") && lv !== null && lv !== undefined && lv !== "") kind = "removed";
    else if (String(lv) !== String(rv)) kind = "modified";
    return {
      path,
      kind,
      left: show(lv),
      right: show(rv),
      unit: r?.unit ?? l?.unit,
      leftSource: l?.provenance.sourceClass,
      rightSource: r?.provenance.sourceClass,
    };
  });
}
