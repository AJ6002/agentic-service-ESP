// ESP-PMM domain types. Pure data contracts — no UI, no side effects.
// These shapes are intentionally close to what a real ADVAIT ESP-PMM API
// would return so the mock data layer can later be swapped for services.

export type OperatingState =
  | "normal"
  | "outside-ror-low"
  | "outside-ror-high"
  | "gas-interference"
  | "pump-wear"
  | "motor-overload"
  | "high-motor-temp"
  | "vsd-trip"
  | "gauge-comms"
  | "vibration-warning"
  | "stopped-planned"
  | "stopped-unplanned"
  | "starting"
  | "ramping";

export type Severity = "critical" | "warning" | "watch" | "info" | "opportunity";

export type DataQuality = "good" | "degraded" | "stale" | "lost";

export interface Field {
  id: string;
  name: string;
  region: string;
  operator: string;
  wellCount: number;
}

/** ESP is a system, not just a pump — component registry per well. */
export interface EspComponent {
  id: string;
  group:
    | "Reservoir & Completion"
    | "Downhole ESP String"
    | "Power & Control"
    | "Surface & Measurement";
  type: string;
  make: string;
  model: string;
  spec: string;
  installed: string;
  tagCount: number;
  source: "OTConnex" | "Asset ConneX";
  status: DataQuality;
}

export interface Well {
  id: string;
  name: string;
  fieldId: string;
  padName: string;
  state: OperatingState;
  healthIndex: number; // 0-100 ESP health index
  runLifeDays: number;
  priorRunLifeDays: number;
  installDate: string;

  // Equipment
  oem: string;
  pumpFamily: string;
  pumpModel: string;
  stages: number;
  ratedHz: number;
  motorRatingHp: number;
  motorRatingA: number;
  motorRatingV: number;
  gasHandler: "Gas separator" | "Gas handler" | "None";

  // Envelope
  bepRate: number; // bpd at BEP
  rorMin: number; // bpd
  rorMax: number; // bpd
  headPerStage: number; // ft/stage at operating point (design)

  // Actual operating snapshot
  hz: number;
  amps: number;
  volts: number;
  motorLoadPct: number;
  motorTempF: number;
  motorTempLimitF: number;
  vibrationG: number;
  pipPsi: number;
  pdpPsi: number;
  whpPsi: number;
  reservoirPsi: number;
  pwfPsi: number;
  liquidRateBpd: number;
  oilRateBopd: number;
  waterCutPct: number;
  gorScfStb: number;
  fluidSg: number;
  piBpdPsi: number;
  gvfPct: number;

  // Expected / design case
  designHz: number;
  designLiquidBpd: number;
  designOilBopd: number;
  expectedOilBopd: number;
  designPipPsi: number;
  designPdpPsi: number;
  designAmps: number;
  designTdhFt: number;

  // Performance / economics
  deferredBopd: number;
  opportunityBopd: number;
  dataQuality: DataQuality;
  gaugeStatus: DataQuality;
  headline: string;
  lastEvent: string;
  lastEventAt: string;
  components: EspComponent[];
}

export type ExceptionCategory =
  | "Outside ROR — low flow / downthrust"
  | "Outside ROR — high flow / upthrust"
  | "Suspected gas interference / unstable amps"
  | "Suspected pump wear / declining head per stage"
  | "Motor overload"
  | "High motor temperature"
  | "VSD / power trip"
  | "Gauge communication / data quality"
  | "Vibration warning"
  | "Tubing leak / recirculation suspicion"
  | "Intake / perforation restriction suspicion"
  | "Unplanned stop"
  | "Optimization opportunity";

export interface EspException {
  id: string;
  wellId: string;
  fieldId: string;
  category: ExceptionCategory;
  severity: Severity;
  firstSeen: string;
  durationH: number;
  impactBopd: number;
  opportunityUsdDay: number;
  confidence: number; // 0-1, demo heuristic
  owner: string;
  status: "Open" | "Acknowledged" | "Assigned" | "Closed";
  rule: string;
  observation: string;
  evidence: string[];
  likelyCauses: { cause: string; weight: number }[];
  verify: string[];
  recommendedAction: string[];
  impactNote: string;
}

export interface DesignCase {
  id: string;
  wellId: string;
  name: string;
  kind: "Design" | "Current" | "What-if";
  author: string;
  updated: string;
  status: "Active" | "Draft" | "Superseded";
  inputs: {
    reservoirPsi: number;
    piBpdPsi: number;
    waterCutPct: number;
    gorScfStb: number;
    fluidSg: number;
    whpPsi: number;
    tubingId: number;
    pumpSettingFt: number;
    perfDepthFt: number;
    hz: number;
    stages: number;
  };
  outputs: {
    liquidBpd: number;
    oilBopd: number;
    tdhFt: number;
    pipPsi: number;
    pdpPsi: number;
    bhp: number;
    efficiencyPct: number;
    motorLoadPct: number;
    gvfPct: number;
  };
  note: string;
}

export interface TroubleshootingCase {
  id: string;
  wellId: string;
  title: string;
  symptom: string;
  signature: {
    tag: "Flow" | "WHP" | "Motor current" | "PDP" | "PIP" | "Motor temp";
    direction: "up" | "down" | "flat" | "erratic";
    note: string;
  }[];
  causes: { cause: string; confidence: number; rationale: string }[];
  verify: string[];
  actions: string[];
  tripCode?: string;
}

export interface FailureRecord {
  id: string;
  wellId: string;
  fieldId: string;
  pulled: string;
  runLifeDays: number;
  failedComponent: string;
  failureMode: string;
  rootCauseFactor: string;
  difaSummary: string;
  repeat: boolean;
  interventionCostKUsd: number;
  deferredBbl: number;
}

export interface Intervention {
  id: string;
  wellId: string;
  type: "Workover / ESP replacement" | "VSD service" | "Gauge repair" | "Chemical / scale treatment" | "Redesign & resize";
  priority: 1 | 2 | 3;
  plannedWindow: string;
  reason: string;
  impactBopd: number;
  riskScore: number;
  status: "Proposed" | "Scheduled" | "Executed";
}

export interface AdvisoryItem {
  id: string;
  wellId: string;
  kind: "Assessment" | "Predictive" | "Optimization";
  observation: string;
  engineeringContext: string;
  assessment: string;
  actions: string[];
  confidence: number;
  evidence: string[];
}
