/**
 * Deterministic demo Engineering Asset Definitions for the ESP-PMM mockup.
 *
 * Front-end mock only — no persistence, no integrations. Shapes intentionally
 * match src/domain/esp/asset-definition.ts so a backend can be generated later.
 * All customer, field, OEM and personnel names are fictional.
 */

import type {
  AssetDefinitionRevision,
  AssetDefinitionSummary,
  AssetNode,
  CalculationConfig,
  ComponentEngineering,
  Confidence,
  CurveSet,
  DesignBasis,
  EconomicContext,
  ElectricalSystem,
  EngField,
  FluidPvt,
  GovernanceContext,
  LifecycleEvent,
  OperatingEnvelope,
  Provenance,
  ReservoirInflow,
  RiskFactor,
  SourceClass,
  WellGeometry,
  WellTestRecord,
} from "@/domain/esp/asset-definition";
import { CANONICAL_SIGNALS, type SignalMapping, type SignalQualityState } from "@/domain/esp/tag-dictionary";
import { completeness, otCoverage, readiness, sourceMix, validateDefinition } from "@/domain/esp/validation";
import type { Well } from "./types";
import { fieldName, hash01, wells } from "./fleet";
import { pumpCurve } from "@/lib/esp/calc";

const NOW = "2026-08-13";

/* ------------------------------------------------------------------ */
/* EngField helpers                                                   */
/* ------------------------------------------------------------------ */

interface FieldOpts {
  unit?: string;
  required?: boolean;
  ref?: string;
  at?: string;
  by?: string;
  approvedBy?: string;
  confidence?: Confidence;
  notes?: string;
}

function ef<T>(value: T | null, source: SourceClass, opts: FieldOpts = {}): EngField<T> {
  const provenance: Provenance = {
    sourceClass: source,
    confidence: opts.confidence ?? (value === null ? "low" : source === "Default" || source === "Inferred" ? "low" : "high"),
    required: opts.required ?? false,
    validation: value === null ? (opts.required ? "error" : "unverified") : "valid",
  };
  if (opts.ref) provenance.sourceRef = opts.ref;
  if (opts.at) provenance.sourceTimestamp = opts.at;
  if (opts.by) provenance.enteredBy = opts.by;
  if (opts.approvedBy) provenance.approvedBy = opts.approvedBy;
  if (opts.notes) provenance.notes = opts.notes;
  const out: EngField<T> = { value, provenance };
  if (opts.unit) out.unit = opts.unit;
  return out;
}

const req = (v: unknown) => ({ required: true }) as FieldOpts & { required: true };
void req;

/* ------------------------------------------------------------------ */
/* Per-well deterministic characterisation                            */
/* ------------------------------------------------------------------ */

const REFERENCE_WELLS = ["ESP-104", "ESP-228", "ESP-097", "ESP-312", "ESP-076", "ESP-141", "ESP-205", "ESP-319"];

/** Which required signals a well fails to map (drives readiness differences). */
function unmappedFor(w: Well): string[] {
  switch (w.id) {
    case "ESP-104":
      return [];
    case "ESP-076":
      return ["ESP.PDP"];
    case "ESP-141":
      return ["ESP.CASING_PRESSURE"];
    case "ESP-205":
      return ["ESP.GAS_RATE" /* optional */, "ESP.CASING_PRESSURE"];
    case "ESP-319":
      return ["ESP.VIBRATION"];
    default:
      return hash01(w.id + "sig") > 0.72 ? ["ESP.GAS_RATE", "ESP.CHOKE_POSITION"] : hash01(w.id + "sig2") > 0.85 ? ["ESP.PDP"] : [];
  }
}

function qualityFor(w: Well, canonicalId: string): SignalQualityState {
  if (w.gaugeStatus !== "good" && ["ESP.PIP", "ESP.PDP", "ESP.MOTOR_TEMP", "ESP.VIBRATION", "ESP.DQ_HEARTBEAT"].includes(canonicalId))
    return w.gaugeStatus === "lost" ? "lost" : "degraded";
  if (w.state === "stopped-planned" || w.state === "stopped-unplanned") return "stale";
  return "good";
}

function signalMappings(w: Well): SignalMapping[] {
  const unmapped = unmappedFor(w);
  return CANONICAL_SIGNALS.map((s) => {
    const isUnmapped = unmapped.includes(s.canonicalId);
    const system =
      s.category === "Electrical" || s.category === "Drive" || s.category === "Run state"
        ? "VSD"
        : s.category === "Pressure" && s.canonicalId !== "ESP.WHP" && s.canonicalId !== "ESP.CASING_PRESSURE"
          ? "Downhole gauge"
          : s.category === "Temperature" || s.category === "Vibration" || s.category === "Data quality"
            ? "Downhole gauge"
            : s.category === "Production" || s.category === "Fluid properties"
              ? "Production system"
              : s.category === "Test data"
                ? "Manual test"
                : "SCADA";
    const tail = s.canonicalId.split(".")[1]!.toLowerCase();
    const mapping: SignalMapping = {
      canonicalId: s.canonicalId,
      wellId: w.id,
      sourceAssetId: isUnmapped ? null : `${w.id}-${system.toLowerCase().replace(/\s+/g, "-")}`,
      sourceSystem: isUnmapped ? null : (system as SignalMapping["sourceSystem"]),
      sourceTagPath: isUnmapped ? null : `OTX://${w.fieldId}/${w.id}/${system.replace(/\s+/g, "")}/${tail}`,
      connectionRef: isUnmapped ? null : `OTConnex-conn-${w.fieldId.toLowerCase()}-01`,
      protocol: isUnmapped ? null : system === "VSD" ? "Modbus TCP (via OTConnex)" : system === "SCADA" ? "OPC UA (via OTConnex)" : "Historian API",
      rawUnit: s.engineeringUnit === "bool" || s.engineeringUnit === "enum" || s.engineeringUnit === "code" ? null : s.engineeringUnit,
      engineeringUnit: s.engineeringUnit,
      scale: isUnmapped ? null : 1,
      offset: isUnmapped ? null : 0,
      dataType: s.dataType,
      sampleRateSec: isUnmapped ? null : s.category === "Production" ? 3600 : s.category === "Test data" ? 86400 : 2,
      historianEnabled: !isUnmapped,
      deadband: isUnmapped ? null : s.dataType === "float" ? 0.1 : 0,
      rangeMin: s.expectedMin,
      rangeMax: s.expectedMax,
      limitLowLow: null,
      limitLow: null,
      limitHigh: null,
      limitHighHigh: null,
      quality: isUnmapped ? "unknown" : qualityFor(w, s.canonicalId),
      lastGoodAt: isUnmapped ? null : `${NOW} 15:5${Math.floor(hash01(w.id + s.canonicalId) * 9)}`,
      required: s.required,
      usedBy: s.usedBy,
      fallbackSource: s.canonicalId === "ESP.PDP" && isUnmapped ? "Calculated from TDH model" : null,
      inferred: s.canonicalId === "ESP.PDP" && isUnmapped,
      timeSyncRule: "Source timestamp preferred; historian receipt time as fallback (UTC).",
      mappingStatus: isUnmapped ? (s.canonicalId === "ESP.PDP" ? "inferred" : "unmapped") : "mapped",
      sourceClass: "OT",
      confidence: isUnmapped ? "low" : qualityFor(w, s.canonicalId) === "good" ? "high" : "medium",
    };
    if (s.canonicalId === "ESP.MOTOR_TEMP") {
      mapping.limitHigh = w.motorTempLimitF - 20;
      mapping.limitHighHigh = w.motorTempLimitF;
    }
    if (s.canonicalId === "ESP.MOTOR_CURRENT") {
      mapping.limitLow = Math.round(w.motorRatingA * 0.35);
      mapping.limitHigh = Math.round(w.motorRatingA * 0.85);
      mapping.limitHighHigh = w.motorRatingA;
    }
    if (s.canonicalId === "ESP.PIP") mapping.limitLow = 250;
    return mapping;
  });
}

/* ------------------------------------------------------------------ */
/* Hierarchy                                                          */
/* ------------------------------------------------------------------ */

function hierarchy(w: Well): AssetNode[] {
  const base = `AC:${w.fieldId}`;
  const wellId = `${base}:${w.id}`;
  const asm = `${wellId}:ESP-ASSY`;
  const n = (
    assetId: string,
    parentAssetId: string | null,
    level: AssetNode["level"],
    assetClass: AssetNode["assetClass"],
    relationshipType: AssetNode["relationshipType"],
    name: string,
    extra: Partial<AssetNode> = {},
  ): AssetNode => ({
    assetId,
    parentAssetId,
    level,
    assetClass,
    relationshipType,
    name,
    status: "installed",
    installDate: w.installDate,
    commissioningDate: w.installDate,
    ...extra,
  });
  const serial = (suffix: string) => `${suffix}-${Math.round(hash01(w.id + suffix) * 90000 + 10000)}`;
  return [
    n(base, null, "Field", "Field", "contains", fieldName(w.fieldId)),
    n(`${base}:${w.padName}`, base, "Pad/Facility", "Pad", "contains", w.padName),
    n(wellId, `${base}:${w.padName}`, "Well", "Well", "contains", `${w.id} — ${w.name}`),
    n(`${wellId}:COMPL`, wellId, "Completion", "Completion", "contains", "Single-zone cased-hole completion", { documentRef: `COMPL-${w.id}-A` }),
    n(`${wellId}:ALS`, `${wellId}:COMPL`, "Artificial Lift System", "Artificial Lift System", "installed-in", "ESP artificial lift system"),
    n(asm, `${wellId}:ALS`, "ESP Assembly", "ESP Assembly", "contains", `${w.oem} ${w.pumpFamily} assembly`),
    n(`${asm}:PUMP-1`, asm, "ESP Component", "Pump Section", "contains", `${w.pumpModel} pump (upper)`, {
      make: w.oem,
      family: w.pumpFamily,
      model: w.pumpModel,
      serialNumber: serial("PMP"),
      partNumber: `${w.pumpModel}-STG`,
      seriesOrDiameterIn: 5.38,
      rating: `${w.stages} stages`,
      materialSpec: "Ni-resist / high-chrome stages",
      stringOrder: 1,
    }),
    n(`${asm}:INTAKE`, asm, "ESP Component", "Intake", "connected-to", "Bolt-on pump intake", { make: w.oem, model: "IN-38", serialNumber: serial("INT"), stringOrder: 2 }),
    ...(w.gasHandler === "None"
      ? []
      : [
          n(
            `${asm}:GAS`,
            asm,
            "ESP Component",
            w.gasHandler === "Gas separator" ? "Gas Separator" : "Gas Handler",
            "connected-to",
            w.gasHandler,
            { make: w.oem, model: "GS-400", serialNumber: serial("GAS"), rating: "42% GVF", stringOrder: 3 },
          ),
        ]),
    n(`${asm}:PROT`, asm, "ESP Component", "Protector", "protects", "Protector / seal section", {
      make: w.oem,
      model: "SL-31",
      serialNumber: serial("PRO"),
      rating: "Labyrinth + bag, tandem",
      stringOrder: 4,
    }),
    n(`${asm}:MOTOR`, asm, "ESP Component", "Motor", "powers", `Submersible motor ${w.motorRatingHp} hp`, {
      make: w.oem,
      model: "MT-56",
      serialNumber: serial("MTR"),
      rating: `${w.motorRatingHp} hp / ${w.motorRatingV} V / ${w.motorRatingA} A`,
      stringOrder: 5,
    }),
    n(`${asm}:GAUGE`, asm, "ESP Component", "Downhole Gauge", "measures", "Downhole gauge package", {
      make: "Sentiq Instruments",
      model: "DG-9",
      serialNumber: serial("GDG"),
      rating: "PIP/PDP/temp/vibration/leakage",
      status: w.gaugeStatus === "lost" ? "installed" : "installed",
      stringOrder: 6,
    }),
    n(`${asm}:MLE`, asm, "ESP Component", "MLE", "powers", "Motor lead extension", { make: "Arcline Cable", model: "MLE-4", rating: "5 kV, 400 degF" }),
    n(`${wellId}:CABLE`, wellId, "ESP Component", "Power Cable", "powers", "#4 AWG flat power cable", { make: "Arcline Cable", model: "AC-4", rating: `${Math.round(6200 * 1.02)} ft` }),
    n(`${asm}:CHECKV`, asm, "ESP Component", "Check Valve", "connected-to", "Tubing check valve", { rating: "Set 2 joints above discharge" }),
    n(`${asm}:DRAINV`, asm, "ESP Component", "Drain Valve", "connected-to", "Drain / bleeder valve"),
    ...(hash01(w.id + "shroud") > 0.72
      ? [n(`${asm}:SHROUD`, asm, "ESP Component", "Shroud", "bypasses", "Motor cooling shroud", { rating: "5-1/2 in shroud" })]
      : []),
    n(`${wellId}:VSD`, wellId, "Surface Asset", "VSD", "powers", "Variable speed drive", {
      make: "Corenta Systems",
      model: "VSD-Q6",
      serialNumber: serial("VSD"),
      rating: "480 V, 6-pulse, sine filter",
    }),
    n(`${wellId}:XFMR`, wellId, "Surface Asset", "Transformer", "powers", "Step-up transformer", { make: "Arcline Power", model: "TX-750", rating: "750 kVA, 480/2100 V" }),
    n(`${wellId}:SWBD`, wellId, "Surface Asset", "Switchboard", "powers", "Switchboard / junction box", { model: "JB-2", rating: "Vented junction box" }),
    n(`${wellId}:WH`, wellId, "Surface Asset", "Wellhead", "connected-to", "Wellhead & penetrator", { model: "WH-5K", rating: "5,000 psi" }),
    n(`${wellId}:CHOKE`, wellId, "Surface Asset", "Choke", "connected-to", "Adjustable production choke", { rating: "Positive/adjustable, 64ths" }),
    n(`${wellId}:MPFM`, wellId, "Surface Asset", "MPFM", "measures", "Multiphase flow meter", { make: "Sentiq Instruments", model: "MPFM-3" }),
    n(`${wellId}:TSEP`, wellId, "Surface Asset", "Test Separator Interface", "measures", "Pad test separator interface", { status: "installed" }),
  ];
}

/* ------------------------------------------------------------------ */
/* Sections                                                           */
/* ------------------------------------------------------------------ */

const OWNERS = [
  { data: "R. Anand", eng: "V. Kulkarni", ops: "S. Marek", rel: "T. Ibarra" },
  { data: "L. Fontaine", eng: "P. Osei", ops: "H. Nakamura", rel: "D. Whelan" },
  { data: "M. Ortiz", eng: "J. Bergman", ops: "A. Duarte", rel: "K. Sørensen" },
];

function governance(w: Well): GovernanceContext {
  const o = OWNERS[Math.floor(hash01(w.id + "own") * OWNERS.length) % OWNERS.length]!;
  const offshore = w.fieldId === "TMR";
  return {
    customer: ef("Fictional Upstream Co.", "Customer", { required: true, ref: "MSA-2024-017" }),
    businessUnit: ef(offshore ? "Offshore Production BU" : "Onshore Production BU", "Customer", { required: true }),
    assetName: ef(fieldName(w.fieldId), "Customer", { required: true }),
    fieldName: ef(fieldName(w.fieldId), "Customer", { required: true }),
    blockOrConcession: ef(`Block ${w.fieldId}-${offshore ? "12" : "4"}`, "Customer"),
    country: ef("Country X (demo)", "Customer", { required: true }),
    region: ef(offshore ? "Offshore Shelf C" : w.fieldId === "NRD" ? "Onshore Basin A" : "Onshore Basin B", "Customer"),
    basin: ef(offshore ? "Shelf C Basin" : "Basin A/B composite", "Customer"),
    fieldId: ef(w.fieldId, "Customer", { required: true }),
    padId: ef(w.padName, "Customer", { required: true }),
    customerWellName: ef(w.name, "Customer", { required: true }),
    advaitWellId: ef(w.id, "Engineering", { required: true, ref: "Asset ConneX canonical ID" }),
    aliases: ef(`${w.fieldId}-${w.id.split("-")[1]}`, "Customer"),
    legacyIds: ef<string>(hash01(w.id + "leg") > 0.5 ? `LEG-${w.id.split("-")[1]}A` : null, "Customer"),
    environment: ef(offshore ? "Offshore" : "Onshore", "Customer", { required: true }),
    timezone: ef("UTC+00:00 (demo)", "Customer", { required: true }),
    unitSystem: ef("Field (US oilfield)", "Engineering", { required: true }),
    currency: ef("USD", "Customer"),
    assetCriticality: ef(w.deferredBopd > 150 ? "1 - Critical" : w.deferredBopd > 50 ? "2 - High" : "3 - Medium", "Engineering", { required: true }),
    productionPriority: ef(`Rank ${Math.max(1, Math.round(hash01(w.id + "rank") * 25))} of 25`, "Engineering"),
    dataOwner: ef(o.data, "Customer", { required: true }),
    engineeringOwner: ef(o.eng, "Engineering", { required: true }),
    operationsOwner: ef(o.ops, "Customer", { required: true }),
    reliabilityOwner: ef(o.rel, "Customer" as SourceClass),
    effectiveFrom: ef(w.installDate, "Engineering", { required: true }),
    effectiveTo: ef<string>(null, "Engineering"),
    sourceDocuments: ef(`ESP-DESIGN-${w.id}.pdf; COMPL-${w.id}-A.pdf; PVT-${w.fieldId}-2025.pdf`, "Customer"),
    notes: ef("Demo definition — all names and values are fictional.", "Engineering"),
  };
}

function geometry(w: Well): WellGeometry {
  const h = hash01(w.id + "geo");
  const perfTop = 7300 + Math.round(h * 500);
  const pumpSet = 6100 + Math.round(hash01(w.id + "set") * 500);
  const missingSet = w.id === "ESP-141";
  return {
    wellType: ef("Oil producer", "Customer", { required: true }),
    trajectoryType: ef(h > 0.6 ? "Deviated (S-shape)" : "Vertical", "Customer", { required: true }),
    surfaceLatitude: ef(+(24.5 + h).toFixed(4), "Customer", { unit: "deg" }),
    surfaceLongitude: ef(+(52.1 + h * 0.8).toFixed(4), "Customer", { unit: "deg" }),
    datumReference: ef("KB (kelly bushing)", "Customer", { required: true }),
    referenceElevationFt: ef(42 + Math.round(h * 20), "Customer", { unit: "ft" }),
    totalMdFt: ef(perfTop + 420, "Customer", { unit: "ft", required: true }),
    totalTvdFt: ef(perfTop + 380, "Customer", { unit: "ft", required: true }),
    deviationSurveyRef: ef<string>(h > 0.6 ? `SURV-${w.id}-2023.las` : null, "Customer"),
    packerDepthMdFt: ef<number>(hash01(w.id + "pk") > 0.5 ? pumpSet - 260 : null, "Customer", { unit: "ft" }),
    perfTopMdFt: ef(perfTop, "Customer", { unit: "ft", required: true }),
    perfBottomMdFt: ef(perfTop + 180, "Customer", { unit: "ft", required: true }),
    perfTopTvdFt: ef(perfTop - 60, "Customer", { unit: "ft", required: true }),
    perfBottomTvdFt: ef(perfTop + 115, "Customer", { unit: "ft" }),
    completionInterval: ef("Zone B-2 sandstone", "Customer", { required: true }),
    pumpSettingMdFt: ef<number>(missingSet ? null : pumpSet, "Customer", { unit: "ft", required: true }),
    pumpSettingTvdFt: ef<number>(missingSet ? null : pumpSet - 90, "Calculated", { unit: "ft", required: true }),
    producingFluidLevelFt: ef<number>(w.hz > 0 ? pumpSet - 900 - Math.round(h * 400) : null, "Field Test", { unit: "ft" }),
    staticFluidLevelFt: ef(2100 + Math.round(h * 500), "Field Test", { unit: "ft" }),
    annulusPressureReference: ef("Casing head gauge, atmospheric reference", "Customer"),
    wellheadConfiguration: ef("5K conventional wellhead with ESP penetrator", "Customer", { required: true }),
    chokeSizeIn64: ef(28 + Math.round(h * 16), "Customer", { unit: "/64 in" }),
    flowlineContext: ef(`${w.padName} flowline to group separator`, "Customer"),
    separatorPressurePsi: ef(120 + Math.round(h * 40), "Customer", { unit: "psi" }),
    knownRestrictions: ef<string>(hash01(w.id + "shroud") > 0.72 ? "Motor shroud installed — reduced annular clearance" : null, "Engineering"),
    maxAllowableWorkingPressurePsi: ef(5000, "Customer", { unit: "psi" }),
    casingSections: [
      { id: `${w.id}-csg-1`, label: "Surface casing", odIn: 13.375, idIn: 12.415, weightLbFt: 68, grade: "K-55", topMdFt: 0, shoeMdFt: 1800, shoeTvdFt: 1800, sourceClass: "Customer" },
      { id: `${w.id}-csg-2`, label: "Intermediate casing", odIn: 9.625, idIn: 8.681, weightLbFt: 47, grade: "N-80", topMdFt: 0, shoeMdFt: 5200, shoeTvdFt: 5150, sourceClass: "Customer" },
      { id: `${w.id}-csg-3`, label: "Production casing", odIn: 7, idIn: 6.276, weightLbFt: 26, grade: "L-80", topMdFt: 0, shoeMdFt: perfTop + 320, shoeTvdFt: perfTop + 280, sourceClass: "Customer" },
    ],
    tubingSections: [
      { id: `${w.id}-tbg-1`, label: "Production tubing", odIn: 2.875, idIn: 2.441, material: "L-80 EUE", roughnessIn: 0.0006, topMdFt: 0, bottomMdFt: pumpSet, sourceClass: "Customer" },
      ...(hash01(w.id + "tbg") > 0.7
        ? [{ id: `${w.id}-tbg-2`, label: "Tail pipe", odIn: 2.375, idIn: 1.995, material: "L-80", roughnessIn: null, topMdFt: pumpSet, bottomMdFt: pumpSet + 120, sourceClass: "Customer" as SourceClass }]
        : []),
    ],
  };
}

function reservoir(w: Well): ReservoirInflow {
  const stale = w.id === "ESP-097" || w.id === "ESP-205";
  return {
    reservoirPressurePsi: ef(w.reservoirPsi, "Field Test", { unit: "psi", required: true, ref: `PBU-${w.id}-2025`, at: stale === true ? "2025-09-18" : "2026-05-04" }),
    flowingBhpPsi: ef(w.pwfPsi, "Calculated", { unit: "psi", required: true, notes: "Derived from PIP + fluid gradient to datum." }),
    reservoirTemperatureF: ef(196 + Math.round(hash01(w.id + "bht") * 30), "Field Test", { unit: "degF", required: true }),
    bubblePointPsi: ef<number>(w.id === "ESP-219" || w.id === "ESP-104" ? 1580 : hash01(w.id + "bp") > 0.25 ? 1180 + Math.round(hash01(w.id + "bp2") * 300) : null, "Field Test", {
      unit: "psi",
      required: true,
      ref: `PVT-${w.fieldId}-2025`,
    }),
    productivityIndexBpdPsi: ef(w.piBpdPsi, "Field Test", { unit: "bpd/psi", required: true, at: stale ? "2025-09-18" : "2026-05-04" }),
    aofBpd: ef(Math.round(w.piBpdPsi * w.reservoirPsi * 0.78), "Calculated", { unit: "bpd" }),
    inflowModel: ef(w.gvfPct > 12 ? "Composite" : "Linear PI", "Engineering", { required: true }),
    skinOrModifier: ef<number>(hash01(w.id + "skin") > 0.4 ? +(hash01(w.id + "sk2") * 4 - 1).toFixed(1) : null, "Engineering"),
    datumDepthTvdFt: ef(7340, "Engineering", { unit: "ft", required: true }),
    testDate: ef(stale ? "2025-09-18" : "2026-05-04", "Field Test", { required: true }),
    testMethod: ef(stale ? "Pressure build-up (legacy)" : "Multi-rate test with downhole gauge", "Field Test", { required: true }),
    quality: ef(stale ? "Medium — superseded by production drift" : "High", "Engineering"),
    notes: ef(stale ? "Inflow model due for re-test; expected-vs-actual gap partly attributable to stale PI." : "Consistent with recent well test.", "Engineering"),
  };
}

function fluid(w: Well): FluidPvt {
  const api = 28 + Math.round(hash01(w.id + "api") * 10);
  return {
    oilApiGravity: ef(api, "Field Test", { unit: "degAPI", required: true, ref: `PVT-${w.fieldId}-2025` }),
    oilSg: ef(+(141.5 / (131.5 + api)).toFixed(3), "Calculated", { required: true }),
    waterSg: ef(1.045, "Field Test", { required: true }),
    gasSg: ef(+(0.68 + hash01(w.id + "gsg") * 0.12).toFixed(3), "Field Test", { required: true }),
    waterCutPct: ef(w.waterCutPct, "Field Test", { unit: "%", required: true, at: "2026-08-05" }),
    producedGorScfStb: ef(w.gorScfStb, "Field Test", { unit: "scf/stb", required: true, at: "2026-08-05" }),
    solutionGorScfStb: ef(Math.round(w.gorScfStb * 0.72), "Calculated", { unit: "scf/stb" }),
    boRbStb: ef(+(1.15 + hash01(w.id + "bo") * 0.15).toFixed(3), "Calculated", { unit: "rb/stb", required: true }),
    bgRcfScf: ef(+(0.0052 + hash01(w.id + "bg") * 0.002).toFixed(5), "Calculated", { unit: "rcf/scf" }),
    oilViscosityCp: ef(+(1.4 + hash01(w.id + "mu") * 3.6).toFixed(2), "Field Test", { unit: "cP", required: true }),
    waterViscosityCp: ef(0.46, "Default", { unit: "cP" }),
    gasZFactor: ef<number>(hash01(w.id + "z") > 0.4 ? +(0.84 + hash01(w.id + "z2") * 0.1).toFixed(3) : null, "Calculated"),
    salinityPpm: ef(38000 + Math.round(hash01(w.id + "sal") * 24000), "Field Test", { unit: "ppm NaCl" }),
    h2sPpm: ef<number>(hash01(w.id + "h2s") > 0.6 ? Math.round(hash01(w.id + "h2s2") * 90) : null, "Field Test", { unit: "ppm" }),
    co2MolPct: ef(+(0.6 + hash01(w.id + "co2") * 2.4).toFixed(2), "Field Test", { unit: "mol%" }),
    solidsIndicator: ef(hash01(w.id + "sand") > 0.65 ? "Intermittent sand production reported" : "No solids reported", "Customer"),
    solidsConcentrationPptb: ef<number>(hash01(w.id + "sand") > 0.65 ? +(hash01(w.id + "sand2") * 8).toFixed(1) : null, "Field Test", { unit: "pptb" }),
    depositionTendencies: ef(
      hash01(w.id + "scale") > 0.55 ? "Calcite scaling tendency at intake; inhibitor programme active" : "Low deposition tendency",
      "Engineering",
    ),
    fluidTemperatureF: ef(190 + Math.round(hash01(w.id + "ft") * 28), "OT", { unit: "degF", required: true }),
    pvtModel: ef("Standing / Vazquez-Beggs (ADVAIT generic demo set)", "Default", { required: true }),
    labReportRef: ef(`PVT-${w.fieldId}-2025.pdf`, "Field Test"),
    testDate: ef("2025-11-22", "Field Test", { required: true }),
  };
}

function designBasis(w: Well): DesignBasis {
  const approved = w.id !== "ESP-141" && hash01(w.id + "appr") > 0.12;
  const bhp = Math.round(w.motorRatingHp * (w.id === "ESP-126" ? 1.06 : 0.74));
  const opt: FieldOpts = { approvedBy: "V. Kulkarni", at: w.installDate };
  return {
    designCaseId: ef(`DC-${w.id}-R2`, "Engineering", { required: true, ...opt }),
    designRevision: ef("R2", "Engineering", { required: true }),
    approvalStatus: ef(approved ? "Approved" : "Draft", "Engineering", { required: true }),
    approvedBy: ef<string>(approved ? "V. Kulkarni" : null, "Engineering", { required: true }),
    approvedDate: ef<string>(approved ? w.installDate : null, "Engineering"),
    targetLiquidBpd: ef(w.designLiquidBpd, "Engineering", { unit: "bpd", required: true }),
    targetOilBopd: ef(w.designOilBopd, "Engineering", { unit: "bopd", required: true }),
    minDesiredRateBpd: ef(w.rorMin, "Engineering", { unit: "bpd", required: true }),
    nominalRateBpd: ef(w.bepRate, "Engineering", { unit: "bpd", required: true }),
    maxDesiredRateBpd: ef(w.rorMax, "Engineering", { unit: "bpd", required: true }),
    designWaterCutPct: ef(Math.max(w.waterCutPct - 6, 5), "Engineering", { unit: "%", required: true }),
    designGorScfStb: ef(Math.round(w.gorScfStb * 0.85), "Engineering", { unit: "scf/stb", required: true }),
    designWhpPsi: ef(w.whpPsi, "Engineering", { unit: "psi", required: true }),
    designCasingPressurePsi: ef(140 + Math.round(hash01(w.id + "cp") * 90), "Engineering", { unit: "psi" }),
    designReservoirPressurePsi: ef(w.reservoirPsi, "Engineering", { unit: "psi", required: true }),
    designPwfPsi: ef(w.pwfPsi + 40, "Engineering", { unit: "psi", required: true }),
    designPipPsi: ef(w.designPipPsi, "Engineering", { unit: "psi", required: true }),
    designPdpPsi: ef(w.designPdpPsi, "Engineering", { unit: "psi", required: true }),
    designFrequencyHz: ef(w.designHz, "Engineering", { unit: "Hz", required: true }),
    designTdhFt: ef(w.designTdhFt, "Engineering", { unit: "ft", required: true }),
    pumpDifferentialPsi: ef(w.designPdpPsi - w.designPipPsi, "Calculated", { unit: "psi" }),
    pumpFlowDownholeBpd: ef(Math.round(w.designLiquidBpd * 1.06), "Calculated", { unit: "bpd" }),
    pumpMake: ef(w.oem, "OEM", { required: true }),
    pumpFamily: ef(w.pumpFamily, "OEM", { required: true }),
    pumpModel: ef(w.pumpModel, "OEM", { required: true }),
    pumpSeriesIn: ef(5.38, "OEM", { unit: "in", required: true }),
    stages: ef<number>(w.id === "ESP-076" ? null : w.stages, "OEM", { required: true }),
    pumpSections: ef(w.stages > 150 ? 2 : 1, "OEM", { required: true }),
    designBepBpd: ef(w.bepRate, "OEM", { unit: "bpd", required: true }),
    rorLowBpd: ef(w.id === "ESP-205" ? w.rorMax : w.rorMin, "OEM", { unit: "bpd", required: true }),
    rorHighBpd: ef(w.id === "ESP-205" ? w.rorMin : w.rorMax, "OEM", { unit: "bpd", required: true }),
    headPerStageFt: ef(w.headPerStage, "OEM", { unit: "ft/stage", required: true }),
    pumpEfficiencyPct: ef(62 + Math.round(hash01(w.id + "eff") * 8), "OEM", { unit: "%", required: true }),
    requiredBhp: ef(bhp, "Calculated", { unit: "hp", required: true }),
    gasAtIntakeGvfPct: ef(w.gvfPct, "Calculated", { unit: "%", required: true }),
    separatorEfficiencyPct: ef<number>(w.gasHandler === "Gas separator" ? 82 : w.gasHandler === "Gas handler" ? 55 : null, "OEM", { unit: "%" }),
    motorHp: ef(w.motorRatingHp, "OEM", { unit: "hp", required: true }),
    motorKw: ef(Math.round(w.motorRatingHp * 0.7457), "Calculated", { unit: "kW" }),
    motorVoltageV: ef(w.motorRatingV, "OEM", { unit: "V", required: true }),
    motorCurrentA: ef(w.motorRatingA, "OEM", { unit: "A", required: true }),
    motorFrequencyHz: ef(60, "OEM", { unit: "Hz", required: true }),
    motorServiceFactor: ef(1.15, "OEM"),
    protectorSelection: ef("SL-31 tandem, labyrinth + bag", "OEM", { required: true }),
    cableSelection: ef("#4 AWG flat, 5 kV, EPDM/lead", "OEM", { required: true }),
    transformerSizingKva: ef(750, "Engineering", { unit: "kVA" }),
    vsdSizing: ef("VSD-Q6 480 V, 6-pulse, sine-wave filter", "Engineering"),
    assumptions: ef("Steady-state single-zone inflow; no downhole choking; sand-free operation; design water cut per PVT report.", "Engineering"),
    exclusions: ef("Transient start-up loads, tubing scale build-up and reservoir depletion beyond 2 years excluded.", "Engineering"),
    engineeringDocumentRef: ef(`ESP-DESIGN-${w.id}.pdf`, "Engineering", { required: true }),
  };
}

function curveSets(w: Well): CurveSet[] {
  const pts = pumpCurve(w, 60, 12).map((p) => ({
    flowBpd: p.flow,
    headPerStageFt: +(p.head / Math.max(w.stages, 1)).toFixed(2),
    efficiencyPct: p.efficiency,
    bhpPerStage: +(p.power / Math.max(w.stages, 1)).toFixed(4),
  }));
  const noRev = w.id === "ESP-097";
  return [
    {
      curveSetId: `CS-${w.oem.split(" ")[0]}-${w.pumpModel}-60`,
      oem: w.oem,
      family: w.pumpFamily,
      model: w.pumpModel,
      seriesOrDiameterIn: 5.38,
      curveRevision: noRev ? null : "Rev C (2025-03)",
      effectiveDate: noRev ? null : "2025-03-01",
      baseFrequencyHz: 60,
      referenceFluidSg: 1.0,
      referenceViscosityCp: 1.0,
      testBasis: "Water test, single-stage, ADVAIT original sample curve (not OEM artwork)",
      bepBpd: w.bepRate,
      rorLowBpd: w.rorMin,
      rorHighBpd: w.rorMax,
      toleranceMetadata: noRev ? null : "±5% head, ±8% power (catalogue tolerance)",
      points: pts,
      additionalFrequenciesHz: [50, 55],
      catalogDocumentRef: noRev ? null : `CATALOG-${w.pumpFamily}-2025.pdf`,
      provenance: {
        sourceClass: "OEM",
        ...(noRev ? {} : { sourceRef: `CATALOG-${w.pumpFamily}-2025.pdf` }),
        confidence: noRev ? "low" : "high",
        required: true,
        validation: noRev ? "warning" : "valid",
      },
    },
  ];
}

function components(w: Well): ComponentEngineering {
  const noCable = w.id === "ESP-319";
  return {
    pump: {
      model: ef(w.pumpModel, "OEM", { required: true }),
      seriesIn: ef(5.38, "OEM", { unit: "in", required: true }),
      stageType: ef("Mixed flow", "OEM", { required: true }),
      stages: ef(w.stages, "OEM", { required: true }),
      sections: ef(w.stages > 150 ? 2 : 1, "OEM", { required: true }),
      ratedRangeBpd: ef(`${w.rorMin}–${w.rorMax}`, "OEM", { unit: "bpd", required: true }),
      shaftMaterialNotes: ef("Monel shaft, high-chrome stages, abrasion-resistant bearings", "OEM"),
    },
    intake: {
      intakeType: ef(w.gasHandler === "None" ? "Standard bolt-on intake" : "Integrated intake with gas handling", "OEM", { required: true }),
      gasHandlingType: ef(w.gasHandler, "OEM", { required: true }),
      ratedGasHandlingGvfPct: ef<number>(w.gasHandler === "None" ? null : w.gasHandler === "Gas separator" ? 42 : 25, "OEM", { unit: "%", required: true }),
      separatorEfficiencyAssumptionPct: ef<number>(w.gasHandler === "Gas separator" ? 82 : w.gasHandler === "Gas handler" ? 55 : null, "Engineering", { unit: "%" }),
    },
    protector: {
      type: ef("Tandem protector", "OEM", { required: true }),
      configuration: ef("Labyrinth + positive seal bag", "OEM", { required: true }),
      chamberType: ef("Two-chamber", "OEM"),
      thrustRatingLb: ef(6800, "OEM", { unit: "lbf" }),
    },
    motor: {
      make: ef(w.oem, "OEM", { required: true }),
      model: ef("MT-56", "OEM", { required: true }),
      series: ef("562 series", "OEM"),
      hp: ef(w.motorRatingHp, "OEM", { unit: "hp", required: true }),
      kw: ef(Math.round(w.motorRatingHp * 0.7457), "Calculated", { unit: "kW" }),
      ratedVoltageV: ef(w.motorRatingV, "OEM", { unit: "V", required: true }),
      ratedCurrentA: ef(w.motorRatingA, "OEM", { unit: "A", required: true }),
      frequencyHz: ef(60, "OEM", { unit: "Hz", required: true }),
      speedRpm: ef(3500, "OEM", { unit: "rpm" }),
      temperatureClass: ef("Class H, 400 degF winding", "OEM", { required: true }),
      serviceFactor: ef(1.15, "OEM"),
    },
    gauge: {
      make: ef("Sentiq Instruments", "OEM", { required: true }),
      model: ef("DG-9", "OEM", { required: true }),
      channels: ef("PIP, PDP, intake temp, motor temp, XY vibration, leakage current", "OEM", { required: true }),
      pressureRangePsi: ef("0–5,000", "OEM", { unit: "psi", required: true }),
      temperatureRangeF: ef("32–400", "OEM", { unit: "degF" }),
      vibrationCapability: ef("0–5 g, XY axes", "OEM"),
      leakageCurrentCapability: ef("0–100 mA", "OEM"),
      accuracy: ef("±0.1% FS pressure, ±2 degF temperature", "OEM"),
    },
    cable: {
      type: ef("Flat power cable + MLE", "OEM", { required: true }),
      sizeAwg: ef("#4 AWG", "OEM", { required: true }),
      conductor: ef("Solid copper", "OEM"),
      insulation: ef("EPDM with lead barrier", "OEM", { required: true }),
      lengthFt: ef<number>(noCable ? null : 6200 + Math.round(hash01(w.id + "cbl") * 400), "OEM", { unit: "ft", required: true }),
      temperatureRatingF: ef(400, "OEM", { unit: "degF", required: true }),
      voltageRatingV: ef(5000, "OEM", { unit: "V", required: true }),
      estimatedVoltageDropV: ef<number>(noCable ? null : 95 + Math.round(hash01(w.id + "vd") * 45), "Calculated", { unit: "V" }),
      mleType: ef("Flat MLE, 400 degF", "OEM"),
    },
    surface: {
      transformerRating: ef("750 kVA, 480 V / 2,100 V", "OEM", { required: true }),
      vsdMake: ef("Corenta Systems", "OEM", { required: true }),
      vsdModel: ef("VSD-Q6", "OEM", { required: true }),
      vsdRating: ef("480 V, 250 kVA, 6-pulse", "OEM", { required: true }),
      vsdControlMode: ef("V/Hz open loop (monitoring reference only)", "Customer", { required: true }),
      junctionBoxId: ef(`JB-${w.id.split("-")[1]}`, "Customer"),
      switchboardId: ef(`SB-${w.padName}`, "Customer"),
    },
  };
}

function electrical(w: Well): ElectricalSystem {
  return {
    powerSource: ef("Field grid via pad substation", "Customer", { required: true }),
    nominalSupplyVoltageV: ef(480, "Customer", { unit: "V", required: true }),
    transformerPrimaryV: ef(480, "OEM", { unit: "V", required: true }),
    transformerSecondaryV: ef(2100, "OEM", { unit: "V", required: true }),
    transformerKva: ef(750, "OEM", { unit: "kVA", required: true }),
    vsdMake: ef("Corenta Systems", "OEM", { required: true }),
    vsdModel: ef("VSD-Q6", "OEM", { required: true }),
    vsdFirmwareRef: ef("FW 4.2.1 (demo)", "Customer"),
    vsdRatedKva: ef(250, "OEM", { unit: "kVA", required: true }),
    vsdRatedCurrentA: ef(Math.round(w.motorRatingA * 1.35), "OEM", { unit: "A", required: true }),
    vsdRatedVoltageV: ef(480, "OEM", { unit: "V", required: true }),
    minFrequencyHz: ef(35, "Engineering", { unit: "Hz", required: true }),
    maxFrequencyHz: ef(62, "Engineering", { unit: "Hz", required: true }),
    nominalFrequencyHz: ef(w.designHz, "Engineering", { unit: "Hz", required: true }),
    outputVoltageRangeV: ef("0–480 (drive) / 0–2,300 (secondary)", "OEM"),
    outputCurrentRangeA: ef(`0–${Math.round(w.motorRatingA * 1.35)}`, "OEM"),
    motorRatedVoltageV: ef(w.motorRatingV, "OEM", { unit: "V", required: true }),
    motorRatedCurrentA: ef(w.motorRatingA, "OEM", { unit: "A", required: true }),
    motorRatedHp: ef(w.motorRatingHp, "OEM", { unit: "hp", required: true }),
    motorRatedKw: ef(Math.round(w.motorRatingHp * 0.7457), "Calculated", { unit: "kW" }),
    currentImbalanceLimitPct: ef(5, "Engineering", { unit: "%", required: true }),
    voltageImbalanceLimitPct: ef(3, "Engineering", { unit: "%" }),
    overloadLimitPct: ef(115, "Engineering", { unit: "%", required: true }),
    underloadLimitPct: ef(45, "Engineering", { unit: "%", required: true }),
    powerFactor: ef<number>(hash01(w.id + "pf") > 0.3 ? +(0.84 + hash01(w.id + "pf2") * 0.1).toFixed(2) : null, "OT"),
    cableVoltageDropAssumption: ef("IEEE-style resistive drop at 60 degC conductor temperature", "Engineering"),
    groundingConfigurationRef: ef(`GND-${w.padName}-STD`, "Customer"),
    restartDelayStrategy: ef("30 min backspin dwell then 3 restart attempts (configuration reference only)", "Customer", { required: true }),
    backspinWaitMin: ef(30, "Customer", { unit: "min", required: true }),
    tripCodeDictionaryRef: ef("VSD-Q6 trip code dictionary v4 (F-0xx series)", "OEM", { required: true }),
  };
}

function envelope(w: Well): OperatingEnvelope {
  const approved = w.id !== "ESP-076";
  return {
    envelopeRevision: ef("E3", "Engineering", { required: true }),
    approvalStatus: ef(approved ? "Approved" : "Under review", "Engineering", { required: true }),
    approvedBy: ef<string>(approved ? "V. Kulkarni" : null, "Engineering", { required: true }),
    limitSource: ef("Engineering", "Engineering", { required: true }),
    minFrequencyHz: ef(42, "Engineering", { unit: "Hz", required: true }),
    maxFrequencyHz: ef(60, "Engineering", { unit: "Hz", required: true }),
    rorLowBpd: ef(w.rorMin, "OEM", { unit: "bpd", required: true }),
    rorHighBpd: ef(w.rorMax, "OEM", { unit: "bpd", required: true }),
    bepReferenceBpd: ef(w.bepRate, "OEM", { unit: "bpd", required: true }),
    lowFlowCautionBpd: ef(Math.round(w.rorMin * 1.05), "Engineering", { unit: "bpd", required: true }),
    lowFlowTripPreventionBpd: ef(Math.round(w.rorMin * 0.85), "Engineering", { unit: "bpd", required: true }),
    highFlowCautionBpd: ef(Math.round(w.rorMax * 0.95), "Engineering", { unit: "bpd", required: true }),
    minPipPsi: ef(250, "Engineering", { unit: "psi", required: true }),
    drawdownMarginPsi: ef(120, "Engineering", { unit: "psi" }),
    gvfCautionPct: ef(w.gasHandler === "Gas separator" ? 30 : 18, "Engineering", { unit: "%", required: true }),
    motorLoadMinPct: ef(45, "Engineering", { unit: "%", required: true }),
    motorLoadMaxPct: ef(85, "Engineering", { unit: "%", required: true }),
    motorTempWarningF: ef<number>(w.id === "ESP-133" ? null : w.motorTempLimitF - 20, "Engineering", { unit: "degF", required: true }),
    motorTempCriticalF: ef<number>(w.id === "ESP-133" ? null : w.motorTempLimitF, "OEM", { unit: "degF", required: true }),
    vibrationWarningG: ef(0.5, "Engineering", { unit: "g", required: true }),
    vibrationCriticalG: ef(0.85, "Engineering", { unit: "g", required: true }),
    maxWhpPsi: ef(1200, "Customer", { unit: "psi" }),
    maxPdpPsi: ef(4200, "OEM", { unit: "psi" }),
    startsPerHourGuidance: ef(1, "OEM", { required: true }),
    startsPerDayGuidance: ef(3, "OEM" ),
    restartDwellMin: ef(30, "OEM", { unit: "min", required: true }),
    dataQualityPrerequisite: ef("PIP, motor current and frequency quality = good within 15 min", "Engineering", { required: true }),
    hysteresisPct: ef(3, "Engineering", { unit: "%", required: true }),
    persistenceMin: ef(20, "Engineering", { unit: "min", required: true }),
  };
}

function calculation(w: Well): CalculationConfig {
  return {
    unitSystem: ef("Field (US oilfield)", "Engineering", { required: true }),
    iprMethod: ef(w.gvfPct > 12 ? "Composite (Vogel below Pb)" : "Linear PI", "Engineering", { required: true }),
    pvtCorrelation: ef("Standing / Vazquez-Beggs (generic demo)", "Default", { required: true }),
    multiphaseCorrelation: ef("Placeholder — Hagedorn & Brown style gradient (demo)", "Default", { required: true }),
    frictionModel: ef("Darcy-Weisbach with Colebrook friction factor", "Engineering", { required: true }),
    fluidDensityMethod: ef("Water-cut weighted mixture density", "Engineering", { required: true }),
    separatorEfficiencyMethod: ef("Fixed efficiency assumption from design basis", "Engineering", { required: true }),
    curveInterpolationMethod: ef("Monotone cubic on catalogued curve points", "Engineering", { required: true }),
    frequencyCorrectionMethod: ef("Affinity laws (Q∝N, H∝N², P∝N³)", "Engineering", { required: true }),
    viscosityCorrectionMethod: ef("Placeholder — no viscosity correction applied in demo", "Default"),
    gasCorrectionMethod: ef("Placeholder — simple GVF derate at intake", "Default"),
    tdhMethod: ef("Net lift + friction + surface backpressure head", "Engineering", { required: true }),
    piCalculationMethod: ef("Rate / (Pr − Pwf) at test conditions", "Engineering", { required: true }),
    headToPressureBasis: ef("Mixture SG at intake conditions", "Engineering", { required: true }),
    calculationWindow: ef("15-minute rolling window", "Engineering", { required: true }),
    smoothing: ef("Median-of-5 on noisy electrical channels", "Engineering"),
    minDataQuality: ef("Quality = good on required signals; heartbeat < 300 s", "Engineering", { required: true }),
    calculationVersionId: ef("ESP-CALC-2026.08.1", "Engineering", { required: true }),
    engineeringOwner: ef("V. Kulkarni", "Engineering", { required: true }),
    approvalStatus: ef("Approved for demo use", "Engineering", { required: true }),
    genericCorrelations: true,
  };
}

function wellTests(w: Well): WellTestRecord[] {
  const dates = ["2026-08-05", "2026-07-08", "2026-06-11", "2026-05-04"];
  return dates.map((d, i) => {
    const drift = 1 - i * 0.015;
    const liquid = Math.round((w.liquidRateBpd || w.designLiquidBpd) * drift);
    const oil = Math.round(liquid * (1 - w.waterCutPct / 100));
    return {
      id: `WT-${w.id}-${d}`,
      testStart: `${d} 06:00`,
      durationH: 12,
      source: i % 3 === 0 ? "Test separator" : i % 3 === 1 ? "MPFM" : "Group separator",
      method: i % 3 === 0 ? "Two-phase separator test" : "Inline multiphase measurement",
      liquidBpd: liquid,
      oilBopd: oil,
      waterBwpd: liquid - oil,
      gasMscfd: Math.round((oil * w.gorScfStb) / 1000),
      waterCutPct: w.waterCutPct,
      gorScfStb: w.gorScfStb,
      whpPsi: w.whpPsi,
      casingPressurePsi: 150 + Math.round(hash01(w.id + d) * 80),
      pipPsi: w.gaugeStatus === "lost" ? null : Math.round(w.pipPsi * (1 + i * 0.02)),
      pdpPsi: w.gaugeStatus === "lost" ? null : Math.round(w.pdpPsi * (1 + i * 0.01)),
      frequencyHz: w.hz || w.designHz,
      motorCurrentA: +(w.amps || w.designAmps).toFixed(1),
      flowingBhpPsi: i === 0 ? w.pwfPsi : null,
      fluidLevelFt: i === 0 ? 5200 + Math.round(hash01(w.id + "fl") * 400) : null,
      accepted: !(i === 2 && hash01(w.id + "rej") > 0.6),
      confidence: i % 3 === 1 ? "medium" : "high",
      comments: i === 0 ? "Latest accepted test used for model calibration." : "Routine monthly test.",
    };
  });
}

function lifecycle(w: Well): LifecycleEvent[] {
  const install = w.installDate;
  const events: LifecycleEvent[] = [
    {
      id: `LC-${w.id}-1`,
      type: "Installation",
      date: install,
      runHours: null,
      runLifeDays: null,
      startsCount: null,
      stopsCount: null,
      tripsCount: null,
      failureMode: null,
      suspectedCause: null,
      confirmedRootCause: null,
      componentFailed: null,
      interventionAction: `ESP ${w.pumpModel} / ${w.motorRatingHp} hp installed on ${w.padName}`,
      difaFinding: null,
      evidenceRef: `WO-${w.id}-INSTALL`,
      repeatFailure: false,
      conditionsBeforeFailure: null,
    },
    {
      id: `LC-${w.id}-2`,
      type: "Commissioning",
      date: install,
      runHours: 0,
      runLifeDays: 0,
      startsCount: 1,
      stopsCount: 0,
      tripsCount: 0,
      failureMode: null,
      suspectedCause: null,
      confirmedRootCause: null,
      componentFailed: null,
      interventionAction: "Start-up, ramp to design frequency, baseline test recorded",
      difaFinding: null,
      evidenceRef: `COMM-${w.id}`,
      repeatFailure: false,
      conditionsBeforeFailure: null,
    },
  ];
  const priorFailure = {
    id: `LC-${w.id}-3`,
    type: "Failure" as const,
    date: new Date(Date.parse(install) - 86400000 * 30).toISOString().slice(0, 10),
    runHours: w.priorRunLifeDays * 22,
    runLifeDays: w.priorRunLifeDays,
    startsCount: 18 + Math.round(hash01(w.id + "st") * 30),
    stopsCount: 17 + Math.round(hash01(w.id + "sp") * 30),
    tripsCount: 4 + Math.round(hash01(w.id + "tr") * 12),
    failureMode: hash01(w.id + "fm") > 0.5 ? "Motor winding short" : "Pump stage wear / loss of head",
    suspectedCause: hash01(w.id + "fm") > 0.5 ? "Thermal overload with restricted cooling" : "Abrasive wear from produced solids",
    confirmedRootCause: hash01(w.id + "rc") > 0.35 ? (hash01(w.id + "fm") > 0.5 ? "Insufficient fluid velocity past motor" : "Sand ingress through intake") : null,
    componentFailed: hash01(w.id + "fm") > 0.5 ? "Motor" : "Pump section",
    interventionAction: "Workover — full ESP string replacement",
    difaFinding: hash01(w.id + "difa") > 0.3 ? "Teardown confirmed downthrust wear on lower stages; motor windings discoloured." : null,
    evidenceRef: `DIFA-${w.id}-${w.priorRunLifeDays}`,
    repeatFailure: hash01(w.id + "rep") > 0.65,
    conditionsBeforeFailure: "Rising motor temperature with declining rate over the final 21 days.",
  };
  events.push(priorFailure);
  if (w.state === "vsd-trip")
    events.push({
      id: `LC-${w.id}-4`,
      type: "Trip",
      date: NOW,
      runHours: w.runLifeDays * 23,
      runLifeDays: w.runLifeDays,
      startsCount: 3,
      stopsCount: 3,
      tripsCount: 3,
      failureMode: "Drive trip F-021 undervoltage",
      suspectedCause: "Grid dip on pad feeder",
      confirmedRootCause: null,
      componentFailed: null,
      interventionAction: "Auto-restart after backspin dwell; ramp to setpoint",
      difaFinding: null,
      evidenceRef: `TRIP-${w.id}-F021`,
      repeatFailure: true,
      conditionsBeforeFailure: "Stable operation, no thermal excursion.",
    });
  if (w.gaugeStatus !== "good")
    events.push({
      id: `LC-${w.id}-5`,
      type: "Gauge repair",
      date: NOW,
      runHours: null,
      runLifeDays: w.runLifeDays,
      startsCount: null,
      stopsCount: null,
      tripsCount: null,
      failureMode: "Gauge telemetry packet loss",
      suspectedCause: "Surface card / cable termination",
      confirmedRootCause: null,
      componentFailed: "Downhole gauge interface",
      interventionAction: "Surface card inspection scheduled",
      difaFinding: null,
      evidenceRef: `WO-${w.id}-GAUGE`,
      repeatFailure: false,
      conditionsBeforeFailure: null,
    });
  return events;
}

function riskFactors(w: Well): RiskFactor[] {
  const s = (k: string, base: number) => Math.min(95, Math.max(5, Math.round(base + hash01(w.id + k) * 25)));
  return [
    { key: "Sizing quality", score: w.state === "outside-ror-low" || w.state === "outside-ror-high" ? 78 : s("sz", 25), basis: "Operating point vs ROR and BEP", sourceClass: "Calculated" },
    { key: "Bottomhole temperature", score: w.motorTempF > 265 ? 82 : s("bht", 30), basis: "Motor temperature vs class rating", sourceClass: "OT" },
    { key: "Free gas", score: w.gvfPct > 15 ? 85 : s("fg", 20), basis: "GVF at intake vs handling rating", sourceClass: "Calculated" },
    { key: "Viscosity", score: s("vis", 18), basis: "Oil viscosity from PVT report", sourceClass: "Field Test" },
    { key: "Corrosion", score: s("cor", 24), basis: "CO2 / H2S content and water chemistry", sourceClass: "Field Test" },
    { key: "Sand / foreign material", score: hash01(w.id + "sand") > 0.65 ? 74 : s("sand3", 18), basis: "Solids reports and vibration signature", sourceClass: "Customer" },
    { key: "Scale / deposition", score: hash01(w.id + "scale") > 0.55 ? 66 : s("sc", 16), basis: "Scaling tendency and inhibitor coverage", sourceClass: "Engineering" },
    { key: "Electrical", score: w.state === "vsd-trip" ? 80 : s("el", 22), basis: "Trip history, imbalance and leakage current", sourceClass: "OT" },
    { key: "Operational", score: s("op", 28), basis: "Starts per day, envelope excursions", sourceClass: "OT" },
    { key: "Equipment age", score: Math.min(95, Math.round((w.runLifeDays / 1200) * 100)), basis: "Run days vs fleet mean run life", sourceClass: "Calculated" },
  ];
}

function economics(w: Well): EconomicContext {
  return {
    baselineOilBopd: ef(w.expectedOilBopd, "Engineering", { unit: "bopd", required: true }),
    allocatedOilSource: ef("Pad allocation from group separator, back-allocated by MPFM", "Customer", { required: true }),
    defermentBasis: ef("Expected oil (design/curve based) minus allocated oil, floored at zero", "Engineering", { required: true }),
    targetOilBopd: ef(Math.round(w.expectedOilBopd * 1.05), "Customer", { unit: "bopd" }),
    uptimeTargetPct: ef(96, "Customer", { unit: "%", required: true }),
    oilPriceUsdBbl: ef(72, "Customer", { unit: "USD/bbl", required: true, at: "2026-07-01", notes: "Assumption — planning price, effective 2026-07-01." }),
    valueBasis: ef("Net realised price less variable lifting cost (assumption)", "Customer", { required: true }),
    interventionCostKUsd: ef(w.fieldId === "TMR" ? 780 : 420, "Customer", { unit: "kUSD", required: true }),
    opportunityValuationBasis: ef("Incremental oil × price × expected persistence (30 d)", "Engineering", { required: true }),
    productionCriticality: ef(w.deferredBopd > 150 ? "High" : "Medium", "Engineering"),
    rankingWeight: ef(+(0.4 + hash01(w.id + "rw") * 0.6).toFixed(2), "Engineering"),
  };
}

/* ------------------------------------------------------------------ */
/* Revision assembly                                                  */
/* ------------------------------------------------------------------ */

function baseRevision(w: Well, revision: string, status: AssetDefinitionRevision["status"]): AssetDefinitionRevision {
  const o = OWNERS[Math.floor(hash01(w.id + "own") * OWNERS.length) % OWNERS.length]!;
  return {
    definitionId: `EAD-${w.id}`,
    wellId: w.id,
    fieldId: w.fieldId,
    revision,
    status,
    createdBy: o.eng,
    createdAt: w.installDate,
    updatedBy: o.eng,
    updatedAt: status === "approved" ? "2026-06-28" : "2026-08-12",
    approvedBy: status === "approved" ? "V. Kulkarni" : null,
    approvedAt: status === "approved" ? "2026-06-28" : null,
    supersededBy: null,
    changeSummary:
      status === "superseded"
        ? "Initial commissioning definition."
        : status === "approved"
          ? "Approved engineering baseline: curve set attached, envelope E3, OT mapping completed."
          : "Draft: updated inflow test, revised envelope thresholds and OT mapping gaps.",
    governance: governance(w),
    hierarchy: hierarchy(w),
    geometry: geometry(w),
    reservoir: reservoir(w),
    fluid: fluid(w),
    designBasis: designBasis(w),
    curveSets: curveSets(w),
    components: components(w),
    electrical: electrical(w),
    signalMappings: signalMappings(w),
    wellTests: wellTests(w),
    envelope: envelope(w),
    calculation: calculation(w),
    lifecycle: lifecycle(w),
    riskFactors: riskFactors(w),
    economics: economics(w),
  };
}

/** Older revision: a few deliberately different / missing values so compare is meaningful. */
function priorRevision(w: Well): AssetDefinitionRevision {
  const r = baseRevision(w, "R1", "superseded");
  r.supersededBy = "R2";
  r.updatedAt = "2025-12-04";
  r.approvedBy = "P. Osei";
  r.approvedAt = "2025-12-04";
  r.reservoir.reservoirPressurePsi = ef(w.reservoirPsi + 140, "Field Test", { unit: "psi", required: true, at: "2025-06-02" });
  r.reservoir.productivityIndexBpdPsi = ef(+(w.piBpdPsi * 1.18).toFixed(2), "Field Test", { unit: "bpd/psi", required: true, at: "2025-06-02" });
  r.reservoir.testDate = ef("2025-06-02", "Field Test", { required: true });
  r.fluid.waterCutPct = ef(Math.max(w.waterCutPct - 7, 3), "Field Test", { unit: "%", required: true, at: "2025-06-02" });
  r.envelope.envelopeRevision = ef("E2", "Engineering", { required: true });
  r.envelope.persistenceMin = ef(10, "Engineering", { unit: "min", required: true });
  r.envelope.gvfCautionPct = ef(15, "Engineering", { unit: "%", required: true });
  r.components.cable.estimatedVoltageDropV = ef<number>(null, "Calculated", { unit: "V" });
  r.geometry.producingFluidLevelFt = ef<number>(null, "Field Test", { unit: "ft" });
  r.designBasis.designRevision = ef("R1", "Engineering", { required: true });
  r.economics.oilPriceUsdBbl = ef(65, "Customer", { unit: "USD/bbl", required: true, at: "2025-07-01" });
  return r;
}

const approvedFor = (w: Well) => !["ESP-076", "ESP-141", "ESP-097"].includes(w.id);

function buildRevisions(w: Well): AssetDefinitionRevision[] {
  const prior = priorRevision(w);
  const current = baseRevision(w, "R2", approvedFor(w) ? "approved" : "draft");
  return [prior, current];
}

export const assetDefinitionsByWell: Record<string, AssetDefinitionRevision[]> = Object.fromEntries(
  wells.map((w) => [w.id, buildRevisions(w)]),
);

export const revisionsFor = (wellId: string) => assetDefinitionsByWell[wellId] ?? [];

export const latestDefinition = (wellId: string) => {
  const revs = revisionsFor(wellId);
  return revs[revs.length - 1];
};

export const definitionByRevision = (wellId: string, revision: string) => revisionsFor(wellId).find((r) => r.revision === revision);

/* ------------------------------------------------------------------ */
/* Registry rollup                                                    */
/* ------------------------------------------------------------------ */

function missingCategories(def: AssetDefinitionRevision): string[] {
  const out: string[] = [];
  const errs = validateDefinition(def);
  if (errs.some((e) => e.section === "geometry")) out.push("Geometry");
  if (errs.some((e) => e.section === "reservoir")) out.push("Inflow");
  if (errs.some((e) => e.section === "fluid")) out.push("PVT");
  if (errs.some((e) => e.section === "curves")) out.push("Curves");
  if (errs.some((e) => e.section === "signals")) out.push("OT mapping");
  if (errs.some((e) => e.section === "designBasis")) out.push("Design case");
  if (errs.some((e) => e.section === "envelope")) out.push("Envelope");
  if (errs.some((e) => e.section === "components")) out.push("Components");
  return out;
}

export function summaryFor(w: Well): AssetDefinitionSummary {
  const def = latestDefinition(w.id)!;
  const comp = completeness(def);
  const ot = otCoverage(def);
  const rd = readiness(def);
  const blocked = rd.filter((r) => r.level === "BLOCKED").length;
  const limited = rd.filter((r) => r.level === "LIMITED").length;
  const curve = def.curveSets[0];
  return {
    definitionId: def.definitionId,
    wellId: w.id,
    wellName: w.name,
    fieldId: w.fieldId,
    padName: w.padName,
    revision: def.revision,
    status: def.status,
    completenessPct: comp.pct,
    requiredMissing: comp.requiredMissing,
    otCoveragePct: ot.pct,
    requiredTagsMissing: ot.requiredMissing.length,
    curveAvailability: !curve ? "Missing" : curve.curveRevision ? "Full" : "Partial",
    lastApprovedDesignCase: def.designBasis.approvalStatus.value === "Approved" ? (def.designBasis.designCaseId.value as string) : null,
    readiness: blocked ? "BLOCKED" : limited ? "LIMITED" : "READY",
    missingCategories: missingCategories(def),
    sourceMix: sourceMix(def),
    updatedAt: def.updatedAt,
    owner: (def.governance.engineeringOwner.value as string) ?? "—",
  };
}

export const assetDefinitionRegistry: AssetDefinitionSummary[] = wells.map(summaryFor);

export const referenceWells = REFERENCE_WELLS;

/* ------------------------------------------------------------------ */
/* Canonical read helpers (stable names for backend parity)            */
/* ------------------------------------------------------------------ */

/** Latest revision for a well, or undefined when the well is unknown. */
export const getAssetDefinition = (wellId: string): AssetDefinitionRevision | undefined => latestDefinition(wellId);

/** Registry rollups for all demo wells. */
export const assetDefinitionSummaries = (): AssetDefinitionSummary[] => assetDefinitionRegistry;

/**
 * Pure clone of an approved/superseded revision into a new draft revision.
 * Does not mutate the source; approved revisions stay immutable.
 */
export function cloneRevision(
  def: AssetDefinitionRevision,
  opts: { by: string; at?: string; changeSummary?: string } = { by: "engineer" },
): AssetDefinitionRevision {
  const at = opts.at ?? def.updatedAt;
  const n = Number((def.revision.match(/\d+/) ?? ["0"])[0]) + 1;
  return {
    ...structuredClone(def),
    revision: `R${n}`,
    status: "draft",
    createdBy: opts.by,
    createdAt: at,
    updatedBy: opts.by,
    updatedAt: at,
    approvedBy: null,
    approvedAt: null,
    supersededBy: null,
    changeSummary: opts.changeSummary ?? `Cloned from ${def.revision} for revision`,
  };
}
