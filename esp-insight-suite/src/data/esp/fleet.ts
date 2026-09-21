// Deterministic sample fleet: 3 fictional fields, 25 fictional ESP wells.
// No real operator, field or OEM names are used.

import type { EspComponent, Field, OperatingState, Well } from "./types";

export const fields: Field[] = [
  { id: "NRD", name: "Nardah North", region: "Onshore Basin A", operator: "Fictional Upstream Co.", wellCount: 9 },
  { id: "KLS", name: "Kalisto West", region: "Onshore Basin B", operator: "Fictional Upstream Co.", wellCount: 9 },
  { id: "TMR", name: "Tamrin Deep", region: "Offshore Shelf C", operator: "Fictional Upstream Co.", wellCount: 7 },
];

export const fieldName = (id: string) => fields.find((f) => f.id === id)?.name ?? id;

/** Fictional, vendor-neutral pump families. */
const oems = [
  { oem: "Vertek Lift", family: "VX-Series", model: "VX-540" },
  { oem: "Corenta Systems", family: "CN-Flow", model: "CN-620" },
  { oem: "Halcyon Downhole", family: "HD-Prime", model: "HD-475" },
  { oem: "Meridian Artificial Lift", family: "MR-Stage", model: "MR-700" },
];

/** Deterministic pseudo-random in [0,1) from a string seed (no Math.random). */
export function hash01(seed: string) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 15;
  h = Math.imul(h, 2246822507);
  h ^= h >>> 13;
  return ((h >>> 0) % 100000) / 100000;
}

const jitter = (seed: string, spread: number) => (hash01(seed) - 0.5) * 2 * spread;

function components(w: {
  id: string;
  oem: string;
  pumpModel: string;
  stages: number;
  motorRatingHp: number;
  gasHandler: string;
  installDate: string;
  gaugeStatus: Well["gaugeStatus"];
}): EspComponent[] {
  const c = (
    group: EspComponent["group"],
    type: string,
    make: string,
    model: string,
    spec: string,
    tagCount: number,
    source: EspComponent["source"],
    status: EspComponent["status"] = "good",
  ): EspComponent => ({
    id: `${w.id}-${type.replace(/\s+/g, "-").toLowerCase()}`,
    group,
    type,
    make,
    model,
    spec,
    installed: w.installDate,
    tagCount,
    source,
    status,
  });
  return [
    c("Reservoir & Completion", "Reservoir unit", "—", "Zone B-2", "Sandstone, 7,400 ft TVD perfs", 4, "Asset ConneX"),
    c("Reservoir & Completion", "Casing", "—", "7 in 26 lb/ft", "Set at 7,650 ft", 1, "Asset ConneX"),
    c("Reservoir & Completion", "Tubing", "—", "2-7/8 in EUE", "2.441 in ID to 6,200 ft", 2, "Asset ConneX"),
    c("Downhole ESP String", "Multistage pump", w.oem, w.pumpModel, `${w.stages} stages, mixed flow`, 0, "Asset ConneX"),
    c("Downhole ESP String", "Pump intake", w.oem, "IN-38", "Bolt-on standard intake", 0, "Asset ConneX"),
    c(
      "Downhole ESP String",
      w.gasHandler === "None" ? "Gas handling (not installed)" : w.gasHandler,
      w.oem,
      w.gasHandler === "None" ? "—" : "GS-400",
      w.gasHandler === "None" ? "Standard intake only" : "Rotary, 42% GVF rating",
      0,
      "Asset ConneX",
    ),
    c("Downhole ESP String", "Protector / seal section", w.oem, "SL-31", "Labyrinth + bag, high-temp elastomer", 0, "Asset ConneX"),
    c("Downhole ESP String", "Submersible motor", w.oem, "MT-56", `${w.motorRatingHp} HP, 2-pole induction`, 3, "Asset ConneX"),
    c(
      "Downhole ESP String",
      "Downhole gauge (P/T/vibration)",
      "Sentiq Instruments",
      "DG-9",
      "PIP, PDP, motor temp, XY vibration",
      6,
      "OTConnex",
      w.gaugeStatus,
    ),
    c("Power & Control", "Power cable / MLE", "Arcline Cable", "AC-4", "#4 AWG flat, 6,240 ft + MLE", 0, "Asset ConneX"),
    c("Power & Control", "Variable speed drive", "Corenta Systems", "VSD-Q6", "480 V, 6-pulse, sine filter", 9, "OTConnex"),
    c("Power & Control", "Step-up transformer", "Arcline Power", "TX-750", "750 kVA, 480 V / 2,100 V", 2, "OTConnex"),
    c("Power & Control", "Surface controller / panel", "Corenta Systems", "SC-2", "Trip codes, restart logic", 5, "OTConnex"),
    c("Surface & Measurement", "Wellhead & choke", "—", "WH-5K", "5,000 psi, adjustable choke", 3, "OTConnex"),
    c("Surface & Measurement", "Flow measurement", "Sentiq Instruments", "MPFM-3", "Multiphase meter, group separator backup", 4, "OTConnex"),
  ];
}

type WellSeed = {
  id: string;
  fieldId: string;
  pad: string;
  state: OperatingState;
  health: number;
  runLife: number;
  oemIdx: number;
  stages: number;
  bep: number;
  hz: number;
  liquid: number;
  wc: number;
  pip: number;
  pdp: number;
  whp: number;
  amps: number;
  motorHp: number;
  motorTemp: number;
  vib: number;
  gvf: number;
  headline: string;
  lastEvent: string;
  lastEventAt: string;
  deferred?: number;
  opportunity?: number;
  gauge?: Well["gaugeStatus"];
  designLiquid?: number;
  expectedOil?: number;
  gasHandler?: Well["gasHandler"];
};

function build(s: WellSeed): Well {
  const oem = oems[s.oemIdx % oems.length]!;
  const designLiquid = s.designLiquid ?? Math.round(s.bep * 0.98);
  const wcFrac = 1 - s.wc / 100;
  const oil = Math.round(s.liquid * wcFrac);
  const expectedOil = s.expectedOil ?? Math.round(designLiquid * wcFrac);
  const motorRatingA = Math.round(s.motorHp * 0.62);
  const headPerStage = 26 + Math.round(jitter(s.id + "hps", 4));
  const designTdh = Math.round(headPerStage * s.stages * 0.92);
  const installDate = new Date(Date.now() - s.runLife * 86400000).toISOString().slice(0, 10);
  const gauge = s.gauge ?? "good";
  const pi = +(s.liquid / Math.max(2650 - (s.pip + 520), 60)).toFixed(2);
  return {
    id: s.id,
    name: `${s.pad} ${s.id.split("-")[1]}`,
    fieldId: s.fieldId,
    padName: s.pad,
    state: s.state,
    healthIndex: s.health,
    runLifeDays: s.runLife,
    priorRunLifeDays: 380 + Math.round(hash01(s.id + "prior") * 700),
    installDate,
    oem: oem.oem,
    pumpFamily: oem.family,
    pumpModel: oem.model,
    stages: s.stages,
    ratedHz: 60,
    motorRatingHp: s.motorHp,
    motorRatingA,
    motorRatingV: 2100,
    gasHandler: s.gasHandler ?? (s.gvf > 12 ? "Gas separator" : "Gas handler"),
    bepRate: s.bep,
    rorMin: Math.round(s.bep * 0.72),
    rorMax: Math.round(s.bep * 1.26),
    headPerStage,
    hz: s.hz,
    amps: s.amps,
    volts: 2050 + Math.round(jitter(s.id + "v", 45)),
    motorLoadPct: Math.round((s.amps / motorRatingA) * 100),
    motorTempF: s.motorTemp,
    motorTempLimitF: 285,
    vibrationG: s.vib,
    pipPsi: s.pip,
    pdpPsi: s.pdp,
    whpPsi: s.whp,
    reservoirPsi: 2650 + Math.round(jitter(s.id + "pr", 180)),
    pwfPsi: s.pip + 520 + Math.round(jitter(s.id + "pwf", 40)),
    liquidRateBpd: s.liquid,
    oilRateBopd: oil,
    waterCutPct: s.wc,
    gorScfStb: 240 + Math.round(hash01(s.id + "gor") * 520),
    fluidSg: +(1.02 + jitter(s.id + "sg", 0.05)).toFixed(3),
    piBpdPsi: pi,
    gvfPct: s.gvf,
    designHz: 55,
    designLiquidBpd: designLiquid,
    designOilBopd: Math.round(designLiquid * wcFrac),
    expectedOilBopd: expectedOil,
    designPipPsi: Math.round(s.pip * 1.12 + 40),
    designPdpPsi: Math.round(s.pdp * 1.03),
    designAmps: Math.round(motorRatingA * 0.72),
    designTdhFt: designTdh,
    deferredBopd: s.deferred ?? Math.max(expectedOil - oil, 0),
    opportunityBopd: s.opportunity ?? 0,
    dataQuality: gauge === "good" ? "good" : gauge,
    gaugeStatus: gauge,
    headline: s.headline,
    lastEvent: s.lastEvent,
    lastEventAt: s.lastEventAt,
    components: components({
      id: s.id,
      oem: oem.oem,
      pumpModel: oem.model,
      stages: s.stages,
      motorRatingHp: s.motorHp,
      gasHandler: s.gasHandler ?? (s.gvf > 12 ? "Gas separator" : "Gas handler"),
      installDate,
      gaugeStatus: gauge,
    }),
  };
}

const seeds: WellSeed[] = [
  // ---- Reference wells (detailed narratives) ----
  {
    id: "ESP-104", fieldId: "NRD", pad: "NRD-Pad-2", state: "gas-interference", health: 52, runLife: 412, oemIdx: 0,
    stages: 148, bep: 2400, hz: 54.5, liquid: 1810, wc: 38, pip: 385, pdp: 2360, whp: 260, amps: 46.5,
    motorHp: 120, motorTemp: 249, vib: 0.34, gvf: 21.5,
    headline: "Gas interference developing — oscillatory current, falling PIP, rising motor temp",
    lastEvent: "Current oscillation band widened to ±6.2 A", lastEventAt: "2026-08-13 14:05",
    deferred: 168, expectedOil: 1290, gasHandler: "Gas separator",
  },
  {
    id: "ESP-228", fieldId: "KLS", pad: "KLS-Pad-1", state: "high-motor-temp", health: 61, runLife: 268, oemIdx: 1,
    stages: 132, bep: 2650, hz: 58.5, liquid: 2720, wc: 52, pip: 640, pdp: 2510, whp: 305, amps: 58.2,
    motorHp: 130, motorTemp: 276, vib: 0.21, gvf: 6.2,
    headline: "Motor thermal margin < 10 degF after 9 days at elevated frequency",
    lastEvent: "Motor temperature 276 degF vs 285 degF limit", lastEventAt: "2026-08-13 12:40",
    deferred: 0,
  },
  {
    id: "ESP-097", fieldId: "NRD", pad: "NRD-Pad-1", state: "pump-wear", health: 44, runLife: 905, oemIdx: 2,
    stages: 164, bep: 2100, hz: 56, liquid: 1420, wc: 61, pip: 720, pdp: 1985, whp: 245, amps: 39.4,
    motorHp: 110, motorTemp: 238, vib: 0.42, gvf: 4.4,
    headline: "Head per stage down 17% over 60 days — progressive stage wear",
    lastEvent: "Head-per-stage 60-day regression flagged", lastEventAt: "2026-08-12 22:15",
    deferred: 210,
  },
  {
    id: "ESP-312", fieldId: "TMR", pad: "TMR-Pad-A", state: "normal", health: 88, runLife: 331, oemIdx: 3,
    stages: 124, bep: 3100, hz: 52, liquid: 2480, wc: 34, pip: 910, pdp: 2740, whp: 340, amps: 51.0,
    motorHp: 150, motorTemp: 231, vib: 0.16, gvf: 3.1,
    headline: "Healthy — spare envelope and motor margin support a frequency uplift",
    lastEvent: "Optimization candidate created by surveillance rule", lastEventAt: "2026-08-13 08:20",
    deferred: 0, opportunity: 95,
  },
  {
    id: "ESP-076", fieldId: "KLS", pad: "KLS-Pad-3", state: "gauge-comms", health: 66, runLife: 190, oemIdx: 0,
    stages: 140, bep: 2200, hz: 55, liquid: 1960, wc: 45, pip: 505, pdp: 2280, whp: 275, amps: 43.1,
    motorHp: 120, motorTemp: 244, vib: 0.19, gvf: 7.8,
    headline: "Intermittent downhole gauge comms — analytics confidence reduced",
    lastEvent: "Gauge packet loss 34% over last 6 h", lastEventAt: "2026-08-13 11:02",
    gauge: "degraded",
  },
  {
    id: "ESP-141", fieldId: "NRD", pad: "NRD-Pad-4", state: "vsd-trip", health: 57, runLife: 121, oemIdx: 1,
    stages: 136, bep: 2500, hz: 48, liquid: 1740, wc: 49, pip: 690, pdp: 2190, whp: 250, amps: 40.2,
    motorHp: 130, motorTemp: 252, vib: 0.24, gvf: 5.6,
    headline: "Unplanned VSD trip (F-021 undervoltage) — restarted, ramping to setpoint",
    lastEvent: "Auto-restart succeeded, ramp in progress", lastEventAt: "2026-08-13 15:48",
    deferred: 140,
  },
  {
    id: "ESP-205", fieldId: "KLS", pad: "KLS-Pad-2", state: "outside-ror-low", health: 58, runLife: 512, oemIdx: 2,
    stages: 152, bep: 2600, hz: 47.5, liquid: 1560, wc: 40, pip: 830, pdp: 2405, whp: 290, amps: 33.8,
    motorHp: 130, motorTemp: 236, vib: 0.29, gvf: 4.9,
    headline: "Operating left of ROR — downthrust risk on stages and thrust bearing",
    lastEvent: "Rate 1,560 bpd vs ROR minimum 1,872 bpd", lastEventAt: "2026-08-12 19:30",
    deferred: 120,
  },
  {
    id: "ESP-319", fieldId: "TMR", pad: "TMR-Pad-B", state: "outside-ror-high", health: 55, runLife: 208, oemIdx: 3,
    stages: 118, bep: 2400, hz: 59.5, liquid: 3180, wc: 55, pip: 470, pdp: 2295, whp: 315, amps: 61.4,
    motorHp: 140, motorTemp: 262, vib: 0.37, gvf: 8.9,
    headline: "Operating right of ROR — upthrust risk with motor load at 71%",
    lastEvent: "Rate 3,180 bpd vs ROR maximum 3,024 bpd", lastEventAt: "2026-08-13 09:55",
  },
  // ---- Remaining fleet ----
  { id: "ESP-101", fieldId: "NRD", pad: "NRD-Pad-1", state: "normal", health: 91, runLife: 288, oemIdx: 0, stages: 130, bep: 2300, hz: 53, liquid: 2210, wc: 36, pip: 720, pdp: 2400, whp: 265, amps: 44.0, motorHp: 120, motorTemp: 229, vib: 0.14, gvf: 3.4, headline: "Normal running inside ROR", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00" },
  { id: "ESP-112", fieldId: "NRD", pad: "NRD-Pad-2", state: "normal", health: 85, runLife: 640, oemIdx: 1, stages: 142, bep: 2500, hz: 55, liquid: 2380, wc: 44, pip: 660, pdp: 2455, whp: 270, amps: 47.8, motorHp: 130, motorTemp: 240, vib: 0.18, gvf: 5.1, headline: "Normal running, mild efficiency drift", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00" },
  { id: "ESP-118", fieldId: "NRD", pad: "NRD-Pad-3", state: "vibration-warning", health: 63, runLife: 455, oemIdx: 2, stages: 156, bep: 2200, hz: 56.5, liquid: 2050, wc: 58, pip: 590, pdp: 2310, whp: 255, amps: 45.2, motorHp: 120, motorTemp: 251, vib: 0.58, gvf: 6.0, headline: "XY vibration above 0.5 g alert threshold", lastEvent: "Vibration alert latched", lastEventAt: "2026-08-13 03:12" },
  { id: "ESP-126", fieldId: "NRD", pad: "NRD-Pad-3", state: "motor-overload", health: 47, runLife: 96, oemIdx: 3, stages: 128, bep: 2400, hz: 58, liquid: 2540, wc: 63, pip: 520, pdp: 2380, whp: 300, amps: 63.5, motorHp: 130, motorTemp: 268, vib: 0.31, gvf: 9.7, headline: "Motor load 79% with rising trend — overload risk", lastEvent: "Overload pre-alarm", lastEventAt: "2026-08-13 10:15", deferred: 60 },
  { id: "ESP-133", fieldId: "NRD", pad: "NRD-Pad-4", state: "stopped-planned", health: 74, runLife: 372, oemIdx: 0, stages: 138, bep: 2300, hz: 0, liquid: 0, wc: 47, pip: 1180, pdp: 1180, whp: 90, amps: 0, motorHp: 120, motorTemp: 196, vib: 0, gvf: 2.2, headline: "Stopped for planned flowline tie-in work", lastEvent: "Planned shutdown, permit W-4471", lastEventAt: "2026-08-12 07:00", deferred: 640 },
  { id: "ESP-149", fieldId: "NRD", pad: "NRD-Pad-4", state: "normal", health: 82, runLife: 233, oemIdx: 1, stages: 134, bep: 2600, hz: 54, liquid: 2420, wc: 41, pip: 700, pdp: 2470, whp: 280, amps: 48.9, motorHp: 130, motorTemp: 243, vib: 0.2, gvf: 4.2, headline: "Normal running inside ROR", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00" },
  { id: "ESP-219", fieldId: "KLS", pad: "KLS-Pad-2", state: "gas-interference", health: 54, runLife: 145, oemIdx: 3, stages: 126, bep: 2250, hz: 57, liquid: 1680, wc: 33, pip: 340, pdp: 2150, whp: 245, amps: 42.1, motorHp: 120, motorTemp: 256, vib: 0.33, gvf: 24.8, headline: "Erratic amps and pressures — free gas at intake", lastEvent: "Amp instability index 0.62", lastEventAt: "2026-08-13 13:20", deferred: 140, gasHandler: "Gas separator" },
  { id: "ESP-234", fieldId: "KLS", pad: "KLS-Pad-2", state: "normal", health: 90, runLife: 301, oemIdx: 0, stages: 132, bep: 2700, hz: 53.5, liquid: 2560, wc: 39, pip: 780, pdp: 2540, whp: 285, amps: 50.4, motorHp: 140, motorTemp: 234, vib: 0.15, gvf: 3.6, headline: "Normal running, best-in-field efficiency", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00", opportunity: 40 },
  { id: "ESP-242", fieldId: "KLS", pad: "KLS-Pad-3", state: "stopped-unplanned", health: 31, runLife: 74, oemIdx: 1, stages: 140, bep: 2400, hz: 0, liquid: 0, wc: 56, pip: 1240, pdp: 1240, whp: 85, amps: 0, motorHp: 130, motorTemp: 188, vib: 0, gvf: 3.0, headline: "Unplanned stop — suspected broken shaft, no flow on restart", lastEvent: "Restart attempt failed, idle amps", lastEventAt: "2026-08-12 21:44", deferred: 1050 },
  { id: "ESP-256", fieldId: "KLS", pad: "KLS-Pad-4", state: "outside-ror-low", health: 60, runLife: 623, oemIdx: 2, stages: 150, bep: 2500, hz: 48.5, liquid: 1610, wc: 52, pip: 860, pdp: 2380, whp: 265, amps: 34.9, motorHp: 130, motorTemp: 233, vib: 0.26, gvf: 4.1, headline: "Left of ROR after choke change — downthrust exposure", lastEvent: "Envelope exception raised", lastEventAt: "2026-08-12 16:05", deferred: 95 },
  { id: "ESP-263", fieldId: "KLS", pad: "KLS-Pad-4", state: "normal", health: 79, runLife: 412, oemIdx: 3, stages: 136, bep: 2350, hz: 54.5, liquid: 2190, wc: 48, pip: 690, pdp: 2360, whp: 262, amps: 45.1, motorHp: 120, motorTemp: 246, vib: 0.22, gvf: 5.4, headline: "Normal running, watch scale trend", lastEvent: "Scale inhibitor batch completed", lastEventAt: "2026-08-11 09:30" },
  { id: "ESP-271", fieldId: "KLS", pad: "KLS-Pad-1", state: "pump-wear", health: 49, runLife: 787, oemIdx: 0, stages: 158, bep: 2150, hz: 57.5, liquid: 1490, wc: 66, pip: 700, pdp: 1930, whp: 240, amps: 40.8, motorHp: 110, motorTemp: 247, vib: 0.44, gvf: 4.6, headline: "Declining head with elevated loading — abrasive wear suspected", lastEvent: "Sand production reported by field", lastEventAt: "2026-08-10 14:10", deferred: 130 },
  { id: "ESP-301", fieldId: "TMR", pad: "TMR-Pad-A", state: "normal", health: 92, runLife: 176, oemIdx: 1, stages: 120, bep: 3000, hz: 51.5, liquid: 2760, wc: 30, pip: 980, pdp: 2760, whp: 350, amps: 52.6, motorHp: 150, motorTemp: 226, vib: 0.13, gvf: 2.8, headline: "Normal running, new install performing to design", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00" },
  { id: "ESP-307", fieldId: "TMR", pad: "TMR-Pad-A", state: "normal", health: 84, runLife: 549, oemIdx: 2, stages: 128, bep: 2900, hz: 53, liquid: 2640, wc: 43, pip: 880, pdp: 2690, whp: 335, amps: 53.9, motorHp: 150, motorTemp: 241, vib: 0.19, gvf: 3.9, headline: "Normal running inside ROR", lastEvent: "Routine surveillance pass", lastEventAt: "2026-08-13 06:00", opportunity: 55 },
  { id: "ESP-324", fieldId: "TMR", pad: "TMR-Pad-B", state: "high-motor-temp", health: 59, runLife: 244, oemIdx: 3, stages: 122, bep: 2800, hz: 58, liquid: 2900, wc: 57, pip: 610, pdp: 2610, whp: 330, amps: 60.1, motorHp: 150, motorTemp: 272, vib: 0.28, gvf: 7.1, headline: "Motor temperature trending to limit at current frequency", lastEvent: "High-temp watch raised", lastEventAt: "2026-08-13 07:35" },
  { id: "ESP-331", fieldId: "TMR", pad: "TMR-Pad-C", state: "gauge-comms", health: 68, runLife: 133, oemIdx: 0, stages: 126, bep: 2700, hz: 54, liquid: 2470, wc: 46, pip: 0, pdp: 0, whp: 320, amps: 49.2, motorHp: 140, motorTemp: 0, vib: 0, gvf: 4.0, headline: "Downhole gauge signal lost — surface-only surveillance", lastEvent: "Gauge comms lost 19 h ago", lastEventAt: "2026-08-12 20:50", gauge: "lost" },
  { id: "ESP-338", fieldId: "TMR", pad: "TMR-Pad-C", state: "vsd-trip", health: 53, runLife: 87, oemIdx: 1, stages: 130, bep: 2600, hz: 0, liquid: 0, wc: 51, pip: 1090, pdp: 1090, whp: 95, amps: 0, motorHp: 140, motorTemp: 205, vib: 0, gvf: 3.3, headline: "VSD locked out on F-014 overcurrent — awaiting field check", lastEvent: "3rd trip in 24 h, lockout active", lastEventAt: "2026-08-13 05:22", deferred: 1180 },
];

export const wells: Well[] = seeds.map(build);

export const wellById = (id: string) => wells.find((w) => w.id === id);

export const stateLabels: Record<OperatingState, string> = {
  normal: "Normal",
  "outside-ror-low": "Outside ROR — low flow",
  "outside-ror-high": "Outside ROR — high flow",
  "gas-interference": "Gas interference",
  "pump-wear": "Pump wear",
  "motor-overload": "Motor overload",
  "high-motor-temp": "High motor temp",
  "vsd-trip": "VSD trip",
  "gauge-comms": "Gauge comms",
  "vibration-warning": "Vibration warning",
  "stopped-planned": "Stopped — planned",
  "stopped-unplanned": "Stopped — unplanned",
  starting: "Starting",
  ramping: "Ramping / stabilizing",
};

export const stateTone: Record<OperatingState, "normal" | "watch" | "warning" | "critical" | "stopped" | "info"> = {
  normal: "normal",
  "outside-ror-low": "warning",
  "outside-ror-high": "warning",
  "gas-interference": "warning",
  "pump-wear": "warning",
  "motor-overload": "critical",
  "high-motor-temp": "warning",
  "vsd-trip": "critical",
  "gauge-comms": "watch",
  "vibration-warning": "watch",
  "stopped-planned": "stopped",
  "stopped-unplanned": "critical",
  starting: "info",
  ramping: "info",
};

export const fleetSummary = () => {
  const running = wells.filter((w) => w.hz > 0).length;
  const down = wells.length - running;
  const deferred = wells.reduce((a, w) => a + w.deferredBopd, 0);
  const opportunity = wells.reduce((a, w) => a + w.opportunityBopd, 0);
  const oil = wells.reduce((a, w) => a + w.oilRateBopd, 0);
  const health = wells.reduce((a, w) => a + w.healthIndex, 0) / wells.length;
  const availability = (running / wells.length) * 100;
  return {
    total: wells.length,
    running,
    down,
    oil,
    deferred,
    opportunity,
    health: +health.toFixed(1),
    availability: +availability.toFixed(1),
    valueUsdDay: (deferred + opportunity) * 68,
  };
};
