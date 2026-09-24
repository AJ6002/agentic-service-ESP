/**
 * ESP-PMM — canonical OT signal / tag dictionary contract (OTConnex boundary).
 *
 * ESP-PMM stores the canonical signal definition and the per-well mapping to a
 * source tag. Raw and historical time series remain in OTConnex / the historian
 * and are NEVER duplicated into asset-definition tables.
 */

import type { Confidence, SourceClass } from "./asset-definition";

export type SignalCategory =
  | "Run state"
  | "Electrical"
  | "Drive"
  | "Pressure"
  | "Temperature"
  | "Vibration"
  | "Production"
  | "Fluid properties"
  | "Surface / choke"
  | "Test data"
  | "Data quality";

export type SignalSourceSystem =
  | "SCADA"
  | "Historian"
  | "VSD"
  | "Downhole gauge"
  | "Production system"
  | "Manual test"
  | "Calculated";

export type SignalDataType = "float" | "int" | "bool" | "string" | "enum";

export type MappingStatus = "mapped" | "unmapped" | "partial" | "deprecated" | "inferred";

export type SignalQualityState = "good" | "degraded" | "stale" | "lost" | "unknown";

/** Canonical (fleet-wide) signal definition — the ESP-PMM standard vocabulary. */
export interface CanonicalSignal {
  canonicalId: string;
  canonicalName: string;
  category: SignalCategory;
  /** Asset class that normally produces the signal. */
  sourceAssetClass: string;
  engineeringUnit: string;
  dataType: SignalDataType;
  required: boolean;
  /** Expected engineering range, used for validation and range checks. */
  expectedMin: number | null;
  expectedMax: number | null;
  /** Downstream calculations / capabilities that consume this signal. */
  usedBy: string[];
  description: string;
}

/** Per-well mapping of a canonical signal to a concrete OT source. */
export interface SignalMapping {
  canonicalId: string;
  wellId: string;
  sourceAssetId: string | null;
  sourceSystem: SignalSourceSystem | null;
  sourceTagPath: string | null;
  /** Connection metadata only — no protocol drivers live in ESP-PMM. */
  connectionRef: string | null;
  protocol: string | null;
  rawUnit: string | null;
  engineeringUnit: string;
  scale: number | null;
  offset: number | null;
  dataType: SignalDataType;
  sampleRateSec: number | null;
  historianEnabled: boolean;
  deadband: number | null;
  rangeMin: number | null;
  rangeMax: number | null;
  limitLowLow: number | null;
  limitLow: number | null;
  limitHigh: number | null;
  limitHighHigh: number | null;
  quality: SignalQualityState;
  lastGoodAt: string | null;
  required: boolean;
  usedBy: string[];
  fallbackSource: string | null;
  inferred: boolean;
  timeSyncRule: string;
  mappingStatus: MappingStatus;
  sourceClass: SourceClass;
  confidence: Confidence;
  notes?: string;
}

const sig = (
  canonicalId: string,
  canonicalName: string,
  category: SignalCategory,
  sourceAssetClass: string,
  engineeringUnit: string,
  dataType: SignalDataType,
  required: boolean,
  expectedMin: number | null,
  expectedMax: number | null,
  usedBy: string[],
  description: string,
): CanonicalSignal => ({
  canonicalId,
  canonicalName,
  category,
  sourceAssetClass,
  engineeringUnit,
  dataType,
  required,
  expectedMin,
  expectedMax,
  usedBy,
  description,
});

/** Canonical ESP signal catalogue (fleet-wide standard vocabulary). */
export const CANONICAL_SIGNALS: CanonicalSignal[] = [
  sig("ESP.RUN_STATUS", "Run status", "Run state", "VSD", "bool", "bool", true, 0, 1, ["Availability", "Uptime", "All surveillance"], "Motor energised indication."),
  sig("ESP.OPERATING_STATE", "Operating state", "Run state", "VSD", "enum", "enum", true, null, null, ["State machine", "Exception engine"], "Derived/reported operating state of the ESP system."),
  sig("ESP.START_STOP_EVENT", "Start / stop event", "Run state", "VSD", "event", "bool", true, 0, 1, ["Starts per day", "Reliability"], "Start and stop transitions with timestamps."),
  sig("ESP.FREQUENCY", "Drive output frequency", "Drive", "VSD", "Hz", "float", true, 20, 70, ["Affinity scaling", "Pump curve", "TDH"], "VSD output frequency at the motor."),
  sig("ESP.MOTOR_SPEED", "Motor speed", "Drive", "Motor", "rpm", "float", false, 0, 4200, ["Affinity scaling"], "Measured or computed shaft speed where available."),
  sig("ESP.MOTOR_CURRENT", "Motor current (average)", "Electrical", "VSD", "A", "float", true, 0, 200, ["Motor loading", "Gas diagnostics", "Wear diagnostics"], "Average of the three phase currents."),
  sig("ESP.PHASE_CURRENT_A", "Phase A current", "Electrical", "VSD", "A", "float", false, 0, 200, ["Imbalance check"], "Per-phase current for imbalance analysis."),
  sig("ESP.PHASE_CURRENT_B", "Phase B current", "Electrical", "VSD", "A", "float", false, 0, 200, ["Imbalance check"], "Per-phase current for imbalance analysis."),
  sig("ESP.PHASE_CURRENT_C", "Phase C current", "Electrical", "VSD", "A", "float", false, 0, 200, ["Imbalance check"], "Per-phase current for imbalance analysis."),
  sig("ESP.MOTOR_VOLTAGE", "Motor voltage", "Electrical", "VSD", "V", "float", true, 0, 4160, ["Motor loading", "Cable drop"], "Drive output voltage to the motor."),
  sig("ESP.PHASE_VOLTAGE_AB", "Phase voltage A-B", "Electrical", "VSD", "V", "float", false, 0, 4160, ["Imbalance check"], "Line-to-line voltage."),
  sig("ESP.ACTIVE_POWER", "Active power", "Electrical", "VSD", "kW", "float", false, 0, 500, ["Energy intensity", "Motor loading"], "Real electrical power drawn."),
  sig("ESP.POWER_FACTOR", "Power factor", "Electrical", "VSD", "-", "float", false, 0, 1, ["Electrical health"], "Displacement power factor."),
  sig("ESP.CURRENT_LEAKAGE", "Current leakage", "Electrical", "Downhole Gauge", "mA", "float", false, 0, 100, ["Insulation degradation"], "Leakage current / insulation indicator."),
  sig("ESP.VSD_TRIP_CODE", "VSD trip code", "Drive", "VSD", "code", "string", true, null, null, ["Trip diagnostics", "Reliability"], "Latest drive fault / trip code."),
  sig("ESP.WHP", "Wellhead / tubing pressure", "Pressure", "Wellhead", "psi", "float", true, 0, 5000, ["Pressure analysis", "TDH"], "Flowing tubing pressure at wellhead."),
  sig("ESP.CASING_PRESSURE", "Casing / annulus pressure", "Pressure", "Wellhead", "psi", "float", true, 0, 5000, ["Gas diagnostics", "Fluid level"], "Annulus pressure reference."),
  sig("ESP.PIP", "Pump intake pressure", "Pressure", "Downhole Gauge", "psi", "float", true, 0, 5000, ["Pressure analysis", "Gas diagnostics", "Drawdown"], "Pressure at the pump intake."),
  sig("ESP.PDP", "Pump discharge pressure", "Pressure", "Downhole Gauge", "psi", "float", true, 0, 6000, ["Pump performance", "Head per stage"], "Pressure at the pump discharge."),
  sig("ESP.DOWNHOLE_TEMP", "Downhole (intake) temperature", "Temperature", "Downhole Gauge", "degF", "float", true, 0, 400, ["PVT", "Reliability"], "Fluid temperature at intake."),
  sig("ESP.MOTOR_TEMP", "Motor winding / oil temperature", "Temperature", "Downhole Gauge", "degF", "float", true, 0, 450, ["Thermal margin", "Reliability"], "Motor temperature measurement."),
  sig("ESP.VIBRATION", "Vibration (XY)", "Vibration", "Downhole Gauge", "g", "float", false, 0, 5, ["Mechanical diagnostics"], "Downhole vibration amplitude."),
  sig("ESP.LIQUID_RATE", "Liquid rate", "Production", "MPFM", "bpd", "float", true, 0, 12000, ["Operating point", "ROR compliance"], "Total liquid production rate."),
  sig("ESP.OIL_RATE", "Oil rate", "Production", "Production system", "bopd", "float", true, 0, 10000, ["Deferment", "Economics"], "Allocated or measured oil rate."),
  sig("ESP.WATER_RATE", "Water rate", "Production", "Production system", "bwpd", "float", false, 0, 12000, ["Water cut"], "Water production rate."),
  sig("ESP.GAS_RATE", "Gas rate", "Production", "MPFM", "Mscf/d", "float", false, 0, 20000, ["GVF", "Gas diagnostics"], "Gas production rate."),
  sig("ESP.WATER_CUT", "Water cut", "Fluid properties", "Production system", "%", "float", true, 0, 100, ["Fluid density", "TDH"], "Produced water fraction."),
  sig("ESP.GOR", "Producing GOR", "Fluid properties", "Production system", "scf/stb", "float", false, 0, 5000, ["GVF", "Gas diagnostics"], "Gas-oil ratio."),
  sig("ESP.CHOKE_POSITION", "Choke position / size", "Surface / choke", "Choke", "/64 in", "float", false, 0, 128, ["Backpressure analysis"], "Surface choke setting."),
  sig("ESP.FLUID_LEVEL", "Fluid level", "Pressure", "Well", "ft", "float", false, 0, 15000, ["Inflow calibration"], "Producing / static fluid level where measured."),
  sig("ESP.TEST_SEPARATOR_DATA", "Separator / well test data", "Test data", "Test Separator Interface", "mixed", "float", false, null, null, ["Model calibration"], "Dated well-test measurement set."),
  sig("ESP.DQ_HEARTBEAT", "Data-quality heartbeat", "Data quality", "Downhole Gauge", "sec", "float", true, 0, 3600, ["Confidence gating", "All analytics"], "Age of last good acquisition packet."),
];

export const canonicalSignalById = (id: string) => CANONICAL_SIGNALS.find((s) => s.canonicalId === id);

export const REQUIRED_SIGNAL_IDS = CANONICAL_SIGNALS.filter((s) => s.required).map((s) => s.canonicalId);
