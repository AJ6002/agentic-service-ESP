/**
 * ESP-PMM — Engineering Asset Definition canonical domain contract.
 *
 * This file is the authoritative TypeScript expression of the governed input
 * model for ESP Performance Monitoring & Management. It is intentionally free
 * of UI concerns and free of persistence concerns so a backend implementation
 * (PostgreSQL/Timescale + Java/Python services) can be generated from it.
 *
 * Architecture boundaries (see docs/esp/BACKEND_HANDOFF.md):
 *  - ADVAIT Asset ConneX  = system of record for generic hierarchy / templates /
 *    master asset identity. ESP-PMM references those IDs, never re-masters them.
 *  - ADVAIT OTConnex      = system of record / interface for OT acquisition and
 *    live + historical time series. ESP-PMM stores only the canonical *mapping*.
 *  - ESP-PMM              = owner of ESP engineering definitions, OEM curve sets,
 *    design cases, operating envelopes, calculation configuration, reliability
 *    context and domain-derived results.
 *
 * Versioning rule: an APPROVED revision is immutable. Any change creates a new
 * revision (clone -> draft -> under-review -> approved, previous -> superseded).
 */

/* ------------------------------------------------------------------ */
/* Provenance primitives — apply to every engineering field           */
/* ------------------------------------------------------------------ */

export type SourceClass =
  | "Customer"
  | "OEM"
  | "Engineering"
  | "Field Test"
  | "OT"
  | "Calculated"
  | "Inferred"
  | "Default";

export type Confidence = "high" | "medium" | "low";

export type FieldValidationState = "valid" | "warning" | "error" | "unverified";

export type UnitSystem = "Field (US oilfield)" | "Metric (SI)";

export interface Provenance {
  sourceClass: SourceClass;
  /** Document, lab report, OEM catalogue sheet or canonical OT tag reference. */
  sourceRef?: string;
  /** Timestamp / test date the value is valid as of (ISO-8601). */
  sourceTimestamp?: string;
  effectiveFrom?: string;
  effectiveTo?: string;
  revision?: string;
  enteredBy?: string;
  approvedBy?: string;
  confidence: Confidence;
  required: boolean;
  validation: FieldValidationState;
  notes?: string;
}

/** A single engineering value with unit + provenance. `value === null` = missing. */
export interface EngField<T = number | string | boolean> {
  value: T | null;
  unit?: string;
  provenance: Provenance;
}

export type RevisionStatus = "draft" | "under-review" | "approved" | "superseded";

export type ReadinessCapability =
  | "Basic Surveillance"
  | "Pressure Analysis"
  | "Pump Performance"
  | "Gas Diagnostics"
  | "Reliability"
  | "AI Advisor Context"
  | "ML Training Eligibility";

export type ReadinessLevel = "READY" | "LIMITED" | "BLOCKED";

export interface ReadinessResult {
  capability: ReadinessCapability;
  level: ReadinessLevel;
  /** 0-100 completeness of the inputs backing this capability. */
  completenessPct: number;
  blockers: string[];
}

/* ------------------------------------------------------------------ */
/* 1) Customer / site / governance context                            */
/* ------------------------------------------------------------------ */

export interface GovernanceContext {
  customer: EngField<string>;
  businessUnit: EngField<string>;
  assetName: EngField<string>;
  fieldName: EngField<string>;
  blockOrConcession: EngField<string>;
  country: EngField<string>;
  region: EngField<string>;
  basin: EngField<string>;
  fieldId: EngField<string>;
  padId: EngField<string>;
  customerWellName: EngField<string>;
  advaitWellId: EngField<string>;
  aliases: EngField<string>;
  legacyIds: EngField<string>;
  environment: EngField<"Onshore" | "Offshore">;
  timezone: EngField<string>;
  unitSystem: EngField<UnitSystem>;
  currency: EngField<string>;
  assetCriticality: EngField<"1 - Critical" | "2 - High" | "3 - Medium" | "4 - Low">;
  productionPriority: EngField<string>;
  dataOwner: EngField<string>;
  engineeringOwner: EngField<string>;
  operationsOwner: EngField<string>;
  reliabilityOwner: EngField<string>;
  effectiveFrom: EngField<string>;
  effectiveTo: EngField<string>;
  sourceDocuments: EngField<string>;
  notes: EngField<string>;
}

/* ------------------------------------------------------------------ */
/* 2) Asset hierarchy & relationships — Asset ConneX contract         */
/* ------------------------------------------------------------------ */

export type AssetLevel =
  | "Field"
  | "Pad/Facility"
  | "Well"
  | "Completion"
  | "Artificial Lift System"
  | "ESP Assembly"
  | "ESP Component"
  | "Surface Asset";

export type AssetClass =
  | "Field"
  | "Pad"
  | "Well"
  | "Completion"
  | "Artificial Lift System"
  | "ESP Assembly"
  | "Pump Section"
  | "Intake"
  | "Gas Separator"
  | "Gas Handler"
  | "Protector"
  | "Motor"
  | "Downhole Gauge"
  | "MLE"
  | "Power Cable"
  | "Check Valve"
  | "Drain Valve"
  | "Shroud"
  | "Y-Tool"
  | "Accessory"
  | "VSD"
  | "Transformer"
  | "Switchboard"
  | "Junction Box"
  | "Wellhead"
  | "Choke"
  | "Flowmeter"
  | "MPFM"
  | "Test Separator Interface";

export type RelationshipType =
  | "contains"
  | "installed-in"
  | "connected-to"
  | "powers"
  | "measures"
  | "protects"
  | "bypasses";

export interface AssetNode {
  /** Canonical (Asset ConneX) asset ID. Stable across revisions. */
  assetId: string;
  parentAssetId: string | null;
  level: AssetLevel;
  assetClass: AssetClass;
  relationshipType: RelationshipType;
  name: string;
  make?: string;
  family?: string;
  model?: string;
  serialNumber?: string;
  partNumber?: string;
  seriesOrDiameterIn?: number;
  rating?: string;
  materialSpec?: string;
  installDate?: string;
  commissioningDate?: string;
  status: "installed" | "removed" | "spare" | "planned" | "not-installed";
  documentRef?: string;
  /** Sequence in the downhole string, shallow -> deep, where applicable. */
  stringOrder?: number;
}

/* ------------------------------------------------------------------ */
/* 3) Well / completion / geometry                                    */
/* ------------------------------------------------------------------ */

export interface CasingSection {
  id: string;
  label: string;
  odIn: number;
  idIn: number;
  weightLbFt: number | null;
  grade: string | null;
  topMdFt: number;
  shoeMdFt: number;
  shoeTvdFt: number | null;
  sourceClass: SourceClass;
}

export interface TubingSection {
  id: string;
  label: string;
  odIn: number;
  idIn: number;
  material: string | null;
  roughnessIn: number | null;
  topMdFt: number;
  bottomMdFt: number;
  sourceClass: SourceClass;
}

export interface WellGeometry {
  wellType: EngField<string>;
  trajectoryType: EngField<string>;
  surfaceLatitude: EngField<number>;
  surfaceLongitude: EngField<number>;
  datumReference: EngField<string>;
  referenceElevationFt: EngField<number>;
  totalMdFt: EngField<number>;
  totalTvdFt: EngField<number>;
  deviationSurveyRef: EngField<string>;
  packerDepthMdFt: EngField<number>;
  perfTopMdFt: EngField<number>;
  perfBottomMdFt: EngField<number>;
  perfTopTvdFt: EngField<number>;
  perfBottomTvdFt: EngField<number>;
  completionInterval: EngField<string>;
  pumpSettingMdFt: EngField<number>;
  pumpSettingTvdFt: EngField<number>;
  producingFluidLevelFt: EngField<number>;
  staticFluidLevelFt: EngField<number>;
  annulusPressureReference: EngField<string>;
  wellheadConfiguration: EngField<string>;
  chokeSizeIn64: EngField<number>;
  flowlineContext: EngField<string>;
  separatorPressurePsi: EngField<number>;
  knownRestrictions: EngField<string>;
  maxAllowableWorkingPressurePsi: EngField<number>;
  casingSections: CasingSection[];
  tubingSections: TubingSection[];
}

/* ------------------------------------------------------------------ */
/* 4) Reservoir / inflow model                                        */
/* ------------------------------------------------------------------ */

export type InflowModel = "Linear PI" | "Vogel" | "Composite" | "Other";

export interface ReservoirInflow {
  reservoirPressurePsi: EngField<number>;
  flowingBhpPsi: EngField<number>;
  reservoirTemperatureF: EngField<number>;
  bubblePointPsi: EngField<number>;
  productivityIndexBpdPsi: EngField<number>;
  aofBpd: EngField<number>;
  inflowModel: EngField<InflowModel>;
  skinOrModifier: EngField<number>;
  datumDepthTvdFt: EngField<number>;
  testDate: EngField<string>;
  testMethod: EngField<string>;
  quality: EngField<string>;
  notes: EngField<string>;
}

/* ------------------------------------------------------------------ */
/* 5) Fluid / PVT model                                               */
/* ------------------------------------------------------------------ */

export interface FluidPvt {
  oilApiGravity: EngField<number>;
  oilSg: EngField<number>;
  waterSg: EngField<number>;
  gasSg: EngField<number>;
  waterCutPct: EngField<number>;
  producedGorScfStb: EngField<number>;
  solutionGorScfStb: EngField<number>;
  boRbStb: EngField<number>;
  bgRcfScf: EngField<number>;
  oilViscosityCp: EngField<number>;
  waterViscosityCp: EngField<number>;
  gasZFactor: EngField<number>;
  salinityPpm: EngField<number>;
  h2sPpm: EngField<number>;
  co2MolPct: EngField<number>;
  solidsIndicator: EngField<string>;
  solidsConcentrationPptb: EngField<number>;
  depositionTendencies: EngField<string>;
  fluidTemperatureF: EngField<number>;
  pvtModel: EngField<string>;
  labReportRef: EngField<string>;
  testDate: EngField<string>;
}

/* ------------------------------------------------------------------ */
/* 6) ESP design basis / design case master                           */
/* ------------------------------------------------------------------ */

export interface DesignBasis {
  designCaseId: EngField<string>;
  designRevision: EngField<string>;
  approvalStatus: EngField<"Approved" | "Draft" | "Superseded">;
  approvedBy: EngField<string>;
  approvedDate: EngField<string>;
  targetLiquidBpd: EngField<number>;
  targetOilBopd: EngField<number>;
  minDesiredRateBpd: EngField<number>;
  nominalRateBpd: EngField<number>;
  maxDesiredRateBpd: EngField<number>;
  designWaterCutPct: EngField<number>;
  designGorScfStb: EngField<number>;
  designWhpPsi: EngField<number>;
  designCasingPressurePsi: EngField<number>;
  designReservoirPressurePsi: EngField<number>;
  designPwfPsi: EngField<number>;
  designPipPsi: EngField<number>;
  designPdpPsi: EngField<number>;
  designFrequencyHz: EngField<number>;
  designTdhFt: EngField<number>;
  pumpDifferentialPsi: EngField<number>;
  pumpFlowDownholeBpd: EngField<number>;
  pumpMake: EngField<string>;
  pumpFamily: EngField<string>;
  pumpModel: EngField<string>;
  pumpSeriesIn: EngField<number>;
  stages: EngField<number>;
  pumpSections: EngField<number>;
  designBepBpd: EngField<number>;
  rorLowBpd: EngField<number>;
  rorHighBpd: EngField<number>;
  headPerStageFt: EngField<number>;
  pumpEfficiencyPct: EngField<number>;
  requiredBhp: EngField<number>;
  gasAtIntakeGvfPct: EngField<number>;
  separatorEfficiencyPct: EngField<number>;
  motorHp: EngField<number>;
  motorKw: EngField<number>;
  motorVoltageV: EngField<number>;
  motorCurrentA: EngField<number>;
  motorFrequencyHz: EngField<number>;
  motorServiceFactor: EngField<number>;
  protectorSelection: EngField<string>;
  cableSelection: EngField<string>;
  transformerSizingKva: EngField<number>;
  vsdSizing: EngField<string>;
  assumptions: EngField<string>;
  exclusions: EngField<string>;
  engineeringDocumentRef: EngField<string>;
}

/* ------------------------------------------------------------------ */
/* 7) OEM pump curves & performance catalog                           */
/* ------------------------------------------------------------------ */

export interface CurvePoint {
  flowBpd: number;
  headPerStageFt: number;
  efficiencyPct: number;
  bhpPerStage: number;
}

export interface CurveSet {
  curveSetId: string;
  oem: string;
  family: string;
  model: string;
  seriesOrDiameterIn: number;
  curveRevision: string | null;
  effectiveDate: string | null;
  baseFrequencyHz: number;
  referenceFluidSg: number;
  referenceViscosityCp: number;
  testBasis: string;
  bepBpd: number;
  rorLowBpd: number;
  rorHighBpd: number;
  toleranceMetadata: string | null;
  points: CurvePoint[];
  /** Optional additional frequency curve sets derived or catalogued. */
  additionalFrequenciesHz: number[];
  provenance: Provenance;
  catalogDocumentRef: string | null;
}

/* ------------------------------------------------------------------ */
/* 8) ESP component engineering details                               */
/* ------------------------------------------------------------------ */

export interface PumpEngineering {
  model: EngField<string>;
  seriesIn: EngField<number>;
  stageType: EngField<"Radial" | "Mixed flow" | "Axial" | "Unknown">;
  stages: EngField<number>;
  sections: EngField<number>;
  ratedRangeBpd: EngField<string>;
  shaftMaterialNotes: EngField<string>;
}

export interface IntakeEngineering {
  intakeType: EngField<string>;
  gasHandlingType: EngField<string>;
  ratedGasHandlingGvfPct: EngField<number>;
  separatorEfficiencyAssumptionPct: EngField<number>;
}

export interface ProtectorEngineering {
  type: EngField<string>;
  configuration: EngField<string>;
  chamberType: EngField<string>;
  thrustRatingLb: EngField<number>;
}

export interface MotorEngineering {
  make: EngField<string>;
  model: EngField<string>;
  series: EngField<string>;
  hp: EngField<number>;
  kw: EngField<number>;
  ratedVoltageV: EngField<number>;
  ratedCurrentA: EngField<number>;
  frequencyHz: EngField<number>;
  speedRpm: EngField<number>;
  temperatureClass: EngField<string>;
  serviceFactor: EngField<number>;
}

export interface GaugeEngineering {
  make: EngField<string>;
  model: EngField<string>;
  channels: EngField<string>;
  pressureRangePsi: EngField<string>;
  temperatureRangeF: EngField<string>;
  vibrationCapability: EngField<string>;
  leakageCurrentCapability: EngField<string>;
  accuracy: EngField<string>;
}

export interface CableEngineering {
  type: EngField<string>;
  sizeAwg: EngField<string>;
  conductor: EngField<string>;
  insulation: EngField<string>;
  lengthFt: EngField<number>;
  temperatureRatingF: EngField<number>;
  voltageRatingV: EngField<number>;
  estimatedVoltageDropV: EngField<number>;
  mleType: EngField<string>;
}

export interface SurfaceEngineering {
  transformerRating: EngField<string>;
  vsdMake: EngField<string>;
  vsdModel: EngField<string>;
  vsdRating: EngField<string>;
  vsdControlMode: EngField<string>;
  junctionBoxId: EngField<string>;
  switchboardId: EngField<string>;
}

export interface ComponentEngineering {
  pump: PumpEngineering;
  intake: IntakeEngineering;
  protector: ProtectorEngineering;
  motor: MotorEngineering;
  gauge: GaugeEngineering;
  cable: CableEngineering;
  surface: SurfaceEngineering;
}

/* ------------------------------------------------------------------ */
/* 9) Electrical / VSD / power system definition                      */
/* ------------------------------------------------------------------ */

export interface ElectricalSystem {
  powerSource: EngField<string>;
  nominalSupplyVoltageV: EngField<number>;
  transformerPrimaryV: EngField<number>;
  transformerSecondaryV: EngField<number>;
  transformerKva: EngField<number>;
  vsdMake: EngField<string>;
  vsdModel: EngField<string>;
  vsdFirmwareRef: EngField<string>;
  vsdRatedKva: EngField<number>;
  vsdRatedCurrentA: EngField<number>;
  vsdRatedVoltageV: EngField<number>;
  minFrequencyHz: EngField<number>;
  maxFrequencyHz: EngField<number>;
  nominalFrequencyHz: EngField<number>;
  outputVoltageRangeV: EngField<string>;
  outputCurrentRangeA: EngField<string>;
  motorRatedVoltageV: EngField<number>;
  motorRatedCurrentA: EngField<number>;
  motorRatedHp: EngField<number>;
  motorRatedKw: EngField<number>;
  currentImbalanceLimitPct: EngField<number>;
  voltageImbalanceLimitPct: EngField<number>;
  overloadLimitPct: EngField<number>;
  underloadLimitPct: EngField<number>;
  powerFactor: EngField<number>;
  cableVoltageDropAssumption: EngField<string>;
  groundingConfigurationRef: EngField<string>;
  /** Configuration reference only — ESP-PMM never issues control commands. */
  restartDelayStrategy: EngField<string>;
  backspinWaitMin: EngField<number>;
  tripCodeDictionaryRef: EngField<string>;
}

/* ------------------------------------------------------------------ */
/* 11) Well test / field measurement records                          */
/* ------------------------------------------------------------------ */

export interface WellTestRecord {
  id: string;
  testStart: string;
  durationH: number;
  source: "Test separator" | "MPFM" | "Manual" | "Group separator" | "Allocated";
  method: string;
  liquidBpd: number | null;
  oilBopd: number | null;
  waterBwpd: number | null;
  gasMscfd: number | null;
  waterCutPct: number | null;
  gorScfStb: number | null;
  whpPsi: number | null;
  casingPressurePsi: number | null;
  pipPsi: number | null;
  pdpPsi: number | null;
  frequencyHz: number | null;
  motorCurrentA: number | null;
  flowingBhpPsi: number | null;
  fluidLevelFt: number | null;
  accepted: boolean;
  confidence: Confidence;
  comments: string;
}

/* ------------------------------------------------------------------ */
/* 12) Operating envelope & surveillance limits                       */
/* ------------------------------------------------------------------ */

export interface OperatingEnvelope {
  envelopeRevision: EngField<string>;
  approvalStatus: EngField<string>;
  approvedBy: EngField<string>;
  limitSource: EngField<"OEM" | "Customer" | "Engineering" | "Site standard">;
  minFrequencyHz: EngField<number>;
  maxFrequencyHz: EngField<number>;
  rorLowBpd: EngField<number>;
  rorHighBpd: EngField<number>;
  bepReferenceBpd: EngField<number>;
  lowFlowCautionBpd: EngField<number>;
  lowFlowTripPreventionBpd: EngField<number>;
  highFlowCautionBpd: EngField<number>;
  minPipPsi: EngField<number>;
  drawdownMarginPsi: EngField<number>;
  gvfCautionPct: EngField<number>;
  motorLoadMinPct: EngField<number>;
  motorLoadMaxPct: EngField<number>;
  motorTempWarningF: EngField<number>;
  motorTempCriticalF: EngField<number>;
  vibrationWarningG: EngField<number>;
  vibrationCriticalG: EngField<number>;
  maxWhpPsi: EngField<number>;
  maxPdpPsi: EngField<number>;
  startsPerHourGuidance: EngField<number>;
  startsPerDayGuidance: EngField<number>;
  restartDwellMin: EngField<number>;
  dataQualityPrerequisite: EngField<string>;
  hysteresisPct: EngField<number>;
  persistenceMin: EngField<number>;
}

/* ------------------------------------------------------------------ */
/* 13) Calculation / engineering model configuration                  */
/* ------------------------------------------------------------------ */

export interface CalculationConfig {
  unitSystem: EngField<UnitSystem>;
  iprMethod: EngField<string>;
  pvtCorrelation: EngField<string>;
  multiphaseCorrelation: EngField<string>;
  frictionModel: EngField<string>;
  fluidDensityMethod: EngField<string>;
  separatorEfficiencyMethod: EngField<string>;
  curveInterpolationMethod: EngField<string>;
  frequencyCorrectionMethod: EngField<string>;
  viscosityCorrectionMethod: EngField<string>;
  gasCorrectionMethod: EngField<string>;
  tdhMethod: EngField<string>;
  piCalculationMethod: EngField<string>;
  headToPressureBasis: EngField<string>;
  calculationWindow: EngField<string>;
  smoothing: EngField<string>;
  minDataQuality: EngField<string>;
  calculationVersionId: EngField<string>;
  engineeringOwner: EngField<string>;
  approvalStatus: EngField<string>;
  /** True when generic/demo correlations are in use (never OEM-certified). */
  genericCorrelations: boolean;
}

/* ------------------------------------------------------------------ */
/* 14) Maintenance / reliability / lifecycle                          */
/* ------------------------------------------------------------------ */

export type LifecycleEventType =
  | "Installation"
  | "Commissioning"
  | "Pull / workover"
  | "Component replacement"
  | "Failure"
  | "Trip"
  | "Chemical treatment"
  | "Gauge repair"
  | "Redesign";

export interface LifecycleEvent {
  id: string;
  type: LifecycleEventType;
  date: string;
  runHours: number | null;
  runLifeDays: number | null;
  startsCount: number | null;
  stopsCount: number | null;
  tripsCount: number | null;
  failureMode: string | null;
  suspectedCause: string | null;
  confirmedRootCause: string | null;
  componentFailed: string | null;
  interventionAction: string | null;
  difaFinding: string | null;
  evidenceRef: string | null;
  repeatFailure: boolean;
  conditionsBeforeFailure: string | null;
}

export type RiskFactorKey =
  | "Sizing quality"
  | "Bottomhole temperature"
  | "Free gas"
  | "Viscosity"
  | "Corrosion"
  | "Sand / foreign material"
  | "Scale / deposition"
  | "Electrical"
  | "Operational"
  | "Equipment age";

export interface RiskFactor {
  key: RiskFactorKey;
  /** 0-100, higher = higher risk contribution. */
  score: number;
  basis: string;
  sourceClass: SourceClass;
}

/* ------------------------------------------------------------------ */
/* 15) Production / economic context (assumptions)                    */
/* ------------------------------------------------------------------ */

export interface EconomicContext {
  baselineOilBopd: EngField<number>;
  allocatedOilSource: EngField<string>;
  defermentBasis: EngField<string>;
  targetOilBopd: EngField<number>;
  uptimeTargetPct: EngField<number>;
  oilPriceUsdBbl: EngField<number>;
  valueBasis: EngField<string>;
  interventionCostKUsd: EngField<number>;
  opportunityValuationBasis: EngField<string>;
  productionCriticality: EngField<string>;
  rankingWeight: EngField<number>;
}

/* ------------------------------------------------------------------ */
/* Revision aggregate                                                 */
/* ------------------------------------------------------------------ */

export interface SectionMeta {
  key: AssetDefinitionSectionKey;
  requiredCount: number;
  requiredComplete: number;
  optionalCount: number;
  optionalComplete: number;
}

export type AssetDefinitionSectionKey =
  | "governance"
  | "hierarchy"
  | "geometry"
  | "reservoir"
  | "fluid"
  | "designBasis"
  | "curves"
  | "components"
  | "electrical"
  | "signals"
  | "wellTests"
  | "envelope"
  | "calculation"
  | "lifecycle"
  | "economics"
  | "provenance";

export interface AssetDefinitionRevision {
  /** Stable canonical definition id, shared by all revisions of a well. */
  definitionId: string;
  wellId: string;
  fieldId: string;
  revision: string;
  status: RevisionStatus;
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
  approvedBy: string | null;
  approvedAt: string | null;
  supersededBy: string | null;
  changeSummary: string;

  governance: GovernanceContext;
  hierarchy: AssetNode[];
  geometry: WellGeometry;
  reservoir: ReservoirInflow;
  fluid: FluidPvt;
  designBasis: DesignBasis;
  curveSets: CurveSet[];
  components: ComponentEngineering;
  electrical: ElectricalSystem;
  /** Canonical OT signal mappings — see domain/esp/tag-dictionary.ts */
  signalMappings: import("./tag-dictionary").SignalMapping[];
  wellTests: WellTestRecord[];
  envelope: OperatingEnvelope;
  calculation: CalculationConfig;
  lifecycle: LifecycleEvent[];
  riskFactors: RiskFactor[];
  economics: EconomicContext;
}

/** Registry row = derived rollup used by the Asset Definition registry screen. */
export interface AssetDefinitionSummary {
  definitionId: string;
  wellId: string;
  wellName: string;
  fieldId: string;
  padName: string;
  revision: string;
  status: RevisionStatus;
  completenessPct: number;
  requiredMissing: number;
  otCoveragePct: number;
  requiredTagsMissing: number;
  curveAvailability: "Full" | "Partial" | "Missing";
  lastApprovedDesignCase: string | null;
  readiness: ReadinessLevel;
  missingCategories: string[];
  sourceMix: Record<SourceClass, number>;
  updatedAt: string;
  owner: string;
}

export const SECTION_LABELS: Record<AssetDefinitionSectionKey, string> = {
  governance: "1 · Customer / site / governance",
  hierarchy: "2 · Asset hierarchy & relationships",
  geometry: "3 · Well / completion / geometry",
  reservoir: "4 · Reservoir / inflow model",
  fluid: "5 · Fluid / PVT model",
  designBasis: "6 · ESP design basis",
  curves: "7 · OEM curves & catalog",
  components: "8 · Component engineering",
  electrical: "9 · Electrical / VSD / power",
  signals: "10 · Canonical OT tag dictionary",
  wellTests: "11 · Well test / field data",
  envelope: "12 · Operating envelope & limits",
  calculation: "13 · Calculation configuration",
  lifecycle: "14 · Maintenance / reliability",
  economics: "15 · Production / economic context",
  provenance: "16 · Provenance & governance audit",
};

/**
 * Top-level canonical engineering asset definition for an ESP installation.
 *
 * This is the read-only contract returned by the asset-definition registry and
 * consumed by surveillance, engineering calculations, reliability analytics, AI
 * advisor context, and ML training pipelines. It is intentionally versioned and
 * immutable once approved: every material change produces a new revision rather
 * than mutating an existing one.
 */
export interface EspEngineeringAssetDefinition extends AssetDefinitionRevision {
  /** Discriminator for multi-asset APM registries. */
  assetCategory: "ESP";
}

