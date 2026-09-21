import { wells } from "./fleet";
import type { EspException, ExceptionCategory, Severity, Well } from "./types";

const owners = ["A. Rahman (Prod Eng)", "M. Okafor (Ops)", "L. Vieira (Reliability)", "S. Devi (Artificial Lift)", "Unassigned"];

interface Recipe {
  category: ExceptionCategory;
  severity: Severity;
  rule: string;
  observation: (w: Well) => string;
  evidence: (w: Well) => string[];
  causes: { cause: string; weight: number }[];
  verify: string[];
  actions: string[];
  impactNote: (w: Well) => string;
  confidence: number;
  durationH: number;
}

const recipes: Partial<Record<Well["state"], Recipe>> = {
  "gas-interference": {
    category: "Suspected gas interference / unstable amps",
    severity: "critical",
    rule: "AmpInstability > 0.5 AND dPIP/dt < 0 AND rate variance > 6%",
    observation: (w) =>
      `Motor current oscillating ±6.2 A with PIP down ${Math.round(w.pipPsi * 0.18)} psi and liquid rate ${Math.round((1 - w.liquidRateBpd / w.designLiquidBpd) * 100)}% below expected at unchanged frequency.`,
    evidence: (w) => [
      `Amp instability index 0.62 (threshold 0.50)`,
      `PIP ${w.pipPsi} psi vs design ${w.designPipPsi} psi`,
      `Calculated intake GVF ${w.gvfPct.toFixed(1)}% vs separator rating 42%`,
      `Rate ${w.liquidRateBpd} bpd vs expected ${w.designLiquidBpd} bpd`,
      `Motor temperature ${w.motorTempF} degF, +9 degF in 12 h`,
    ],
    causes: [
      { cause: "Increased free gas at pump intake", weight: 0.62 },
      { cause: "Excessive drawdown below bubble point", weight: 0.21 },
      { cause: "Gas separator performance degradation", weight: 0.11 },
      { cause: "Gauge noise / instrumentation artefact", weight: 0.06 },
    ],
    verify: [
      "Compare casing pressure and annulus route with intake pressure trend",
      "Check latest well test GOR against design case GOR",
      "Confirm amp chart pattern on the VSD controller, not only historian",
      "Confirm gauge data quality over the same window",
    ],
    actions: [
      "Reduce frequency 1.5–2.0 Hz to raise intake pressure and stabilise loading",
      "Hold 2 h and re-evaluate amp band, PIP and rate",
      "If instability persists, evaluate deeper setting depth or higher-capacity gas handling in the next design case",
    ],
    impactNote: (w) => `${w.deferredBopd} BOPD currently deferred. Sustained gas cycling risks thrust and seal damage.`,
    confidence: 0.74,
    durationH: 12,
  },
  "high-motor-temp": {
    category: "High motor temperature",
    severity: "warning",
    rule: "MotorTemp > limit − 12 degF sustained 4 h",
    observation: (w) => `Motor temperature ${w.motorTempF} degF against ${w.motorTempLimitF} degF limit — margin ${w.motorTempLimitF - w.motorTempF} degF.`,
    evidence: (w) => [
      `Frequency raised 56.0 → ${w.hz} Hz nine days ago`,
      `Motor load ${w.motorLoadPct}% of ${w.motorRatingA} A rating`,
      `Motor temperature +14 degF since frequency change`,
      `Annular velocity below cooling guideline at current rate`,
    ],
    causes: [
      { cause: "Insufficient motor cooling flow at elevated speed", weight: 0.48 },
      { cause: "High motor loading / sustained overload", weight: 0.27 },
      { cause: "Elevated bottomhole temperature", weight: 0.15 },
      { cause: "Gauge temperature drift", weight: 0.1 },
    ],
    verify: ["Cross-check motor amps and kW for consistent loading", "Confirm gauge temperature against drive-estimated winding temp", "Review annular clearance and shroud configuration"],
    actions: ["Reduce frequency 1.0–1.5 Hz and monitor 4 h", "Set thermal watch notification at limit − 8 degF", "Evaluate motor shroud in redesign case"],
    impactNote: () => "No current deferment; sustained high temperature reduces insulation life and expected run life.",
    confidence: 0.81,
    durationH: 31,
  },
  "pump-wear": {
    category: "Suspected pump wear / declining head per stage",
    severity: "warning",
    rule: "Head-per-stage 60-day slope < −10% AND load rising",
    observation: (w) => `Head per stage down 17% over 60 days (${(w.headPerStage * 1.2).toFixed(1)} → ${w.headPerStage.toFixed(1)} ft) with vibration at ${w.vibrationG.toFixed(2)} g.`,
    evidence: (w) => [
      "Head-per-stage regression over 60 days, R² 0.86",
      `Rate ${w.liquidRateBpd} bpd vs expected ${w.designLiquidBpd} bpd`,
      `Pump ΔP ${w.pdpPsi - w.pipPsi} psi vs design ${w.designPdpPsi - w.designPipPsi} psi`,
      "Sand/solids reported by field on last visit",
    ],
    causes: [
      { cause: "Abrasive stage and bearing wear", weight: 0.55 },
      { cause: "Scale / deposition in stages", weight: 0.2 },
      { cause: "Downthrust operation history", weight: 0.15 },
      { cause: "Inflow decline misread as pump wear", weight: 0.1 },
    ],
    verify: ["Run well test to separate inflow decline from pump degradation", "Compare measured head against curve at the same flow and speed", "Review solids and scale sampling history"],
    actions: ["Add to intervention plan with production-impact ranking", "Avoid frequency increases that shift the point right of BEP", "Plan DIFA scope for stages, bearings and intake on pull"],
    impactNote: (w) => `${w.deferredBopd} BOPD below expected. Continued operation risks unplanned failure and rig-schedule exposure.`,
    confidence: 0.68,
    durationH: 1440,
  },
  "vsd-trip": {
    category: "VSD / power trip",
    severity: "critical",
    rule: "Drive fault event AND run status transition to 0",
    observation: (w) => (w.hz > 0
      ? "Drive tripped on F-021 undervoltage; auto-restart succeeded and the well is ramping to setpoint."
      : "Drive locked out after 3 trips in 24 h on F-014 overcurrent; well is down awaiting field check."),
    evidence: (w) => [
      w.hz > 0 ? "Trip code F-021 undervoltage at 15:44" : "Trip code F-014 overcurrent, lockout active",
      "Bus voltage dip to 1,742 V before trip",
      `Run status transition captured by OTConnex drive tags`,
      w.hz > 0 ? "Restart at 15:48, ramp 30 → 48 Hz" : "2 restart attempts blocked by lockout",
    ],
    causes: [
      { cause: "Supply / power quality disturbance", weight: 0.42 },
      { cause: "Drive or transformer fault", weight: 0.24 },
      { cause: "Downhole electrical degradation (cable/MLE/motor)", weight: 0.2 },
      { cause: "Drive protection setpoint too tight", weight: 0.14 },
    ],
    verify: ["Pull drive fault log and trend bus voltage around the event", "Megger cable and motor before repeat restart", "Check transformer taps and site power events"],
    actions: ["Restrict restart attempts until electrical check is complete", "Review restart logic and ramp profile", "If insulation is degraded, raise workover candidate"],
    impactNote: (w) => `${w.deferredBopd} BOPD deferred. Repeat trips are a leading avoidable-failure driver in this field.`,
    confidence: 0.86,
    durationH: 1.4,
  },
  "gauge-comms": {
    category: "Gauge communication / data quality",
    severity: "watch",
    rule: "Tag quality != GOOD for > 10% of window",
    observation: (w) => (w.gaugeStatus === "lost"
      ? "Downhole gauge signal lost for 19 h — surveillance is surface-signal only."
      : "Downhole gauge packet loss 34% over 6 h — analytics confidence reduced."),
    evidence: (w) => [
      `Gauge status ${w.gaugeStatus.toUpperCase()} in OTConnex tag quality log`,
      "PIP / PDP / motor temperature intermittently unavailable",
      "Downhole-derived exceptions downgraded to provisional",
      "Surface tags (Hz, A, V, WHP, rate) remain good",
    ],
    causes: [
      { cause: "Gauge / MLE communication hardware fault", weight: 0.46 },
      { cause: "Surface panel comms card or wiring", weight: 0.26 },
      { cause: "Signal attenuation on cable", weight: 0.18 },
      { cause: "Historian collector gap", weight: 0.1 },
    ],
    verify: ["Confirm at the panel whether the gauge card reads locally", "Check OTConnex collector health for the same window", "Review cable insulation readings"],
    actions: ["Raise gauge repair task for next field visit", "Switch this well to surface-signature diagnostics", "Mark dependent calculations with reduced confidence"],
    impactNote: () => "No direct deferment; reduced diagnostic sensitivity increases the chance of a missed early warning.",
    confidence: 0.9,
    durationH: 6,
  },
  "outside-ror-low": {
    category: "Outside ROR — low flow / downthrust",
    severity: "warning",
    rule: "Rate < ROR minimum (speed-corrected) sustained 2 h",
    observation: (w) => `Liquid rate ${w.liquidRateBpd} bpd against speed-corrected ROR minimum ${Math.round(w.rorMin * (w.hz / w.ratedHz))} bpd — operating left of range.`,
    evidence: (w) => [
      `Operating point ${(w.liquidRateBpd / w.bepRate).toFixed(2)} × BEP`,
      `Frequency ${w.hz} Hz reduced from 52.0 Hz two days ago`,
      `Motor load ${w.motorLoadPct}% — underloaded`,
      `PIP ${w.pipPsi} psi above design ${w.designPipPsi} psi (low drawdown)`,
    ],
    causes: [
      { cause: "Frequency set too low for pump size", weight: 0.44 },
      { cause: "Surface backpressure / choke restriction", weight: 0.24 },
      { cause: "Pump oversized for current inflow", weight: 0.22 },
      { cause: "Flow measurement error", weight: 0.1 },
    ],
    verify: ["Confirm choke position and flowline pressure", "Validate rate with well test / multiphase meter", "Recheck ROR limits against OEM curve for the installed stage count"],
    actions: ["Raise frequency ~1.5 Hz to re-enter ROR, or open choke", "If inflow cannot support ROR, raise a resize design case", "Record downthrust exposure hours for reliability"],
    impactNote: (w) => `${w.deferredBopd} BOPD below expected; downthrust accumulates stage and thrust-bearing wear.`,
    confidence: 0.79,
    durationH: 44,
  },
  "outside-ror-high": {
    category: "Outside ROR — high flow / upthrust",
    severity: "warning",
    rule: "Rate > ROR maximum (speed-corrected) sustained 2 h",
    observation: (w) => `Liquid rate ${w.liquidRateBpd} bpd against speed-corrected ROR maximum ${Math.round(w.rorMax * (w.hz / w.ratedHz))} bpd — operating right of range with motor load ${w.motorLoadPct}%.`,
    evidence: (w) => [
      `Operating point ${(w.liquidRateBpd / w.bepRate).toFixed(2)} × BEP`,
      `Frequency ${w.hz} Hz raised from 57.0 Hz three days ago`,
      `Motor temperature ${w.motorTempF} degF, margin ${w.motorTempLimitF - w.motorTempF} degF`,
      `Vibration ${w.vibrationG.toFixed(2)} g, trending up`,
    ],
    causes: [
      { cause: "Frequency above envelope for installed pump", weight: 0.5 },
      { cause: "Reduced surface backpressure", weight: 0.2 },
      { cause: "Pump undersized for current inflow", weight: 0.2 },
      { cause: "Rate allocation error", weight: 0.1 },
    ],
    verify: ["Confirm rate with multiphase meter", "Check motor nameplate loading and cable rating", "Recheck ROR maximum for installed stages"],
    actions: ["Reduce frequency ~1.0 Hz to re-enter ROR", "If rate is wanted, raise a resize design case for a larger pump", "Track upthrust exposure hours"],
    impactNote: () => "No deferment, but upthrust and thermal loading shorten expected run life.",
    confidence: 0.8,
    durationH: 55,
  },
  "motor-overload": {
    category: "Motor overload",
    severity: "critical",
    rule: "MotorLoad > 75% sustained 1 h with rising slope",
    observation: (w) => `Motor load ${w.motorLoadPct}% (${w.amps} A of ${w.motorRatingA} A) with a rising 7-day slope.`,
    evidence: (w) => [
      `Amps ${w.amps} A vs design ${w.designAmps} A`,
      `Motor temperature ${w.motorTempF} degF`,
      `Rate ${w.liquidRateBpd} bpd, right of BEP at ${(w.liquidRateBpd / w.bepRate).toFixed(2)} × BEP`,
      "Water cut increase raises produced fluid density and power demand",
    ],
    causes: [
      { cause: "Rising water cut / fluid density", weight: 0.4 },
      { cause: "Operation right of ROR", weight: 0.28 },
      { cause: "Mechanical drag / scale in stages", weight: 0.2 },
      { cause: "Voltage imbalance at the motor", weight: 0.12 },
    ],
    verify: ["Latest water cut and fluid SG from well test", "Drive kW vs amps consistency check", "Voltage balance across phases"],
    actions: ["Reduce frequency to bring load below 72%", "Recalculate TDH with current fluid SG", "Raise electrical check if imbalance is present"],
    impactNote: (w) => `${w.deferredBopd} BOPD at risk if the drive trips on overload.`,
    confidence: 0.77,
    durationH: 7,
  },
  "vibration-warning": {
    category: "Vibration warning",
    severity: "watch",
    rule: "XY vibration > 0.50 g sustained 30 min",
    observation: (w) => `XY vibration ${w.vibrationG.toFixed(2)} g above the 0.50 g alert threshold.`,
    evidence: (w) => [
      `Vibration ${w.vibrationG.toFixed(2)} g, 7-day rise from 0.31 g`,
      `Head per stage ${w.headPerStage.toFixed(1)} ft, mild decline`,
      `Run life ${w.runLifeDays} days`,
      "No trip or load excursion in the same window",
    ],
    causes: [
      { cause: "Bearing / shaft wear", weight: 0.4 },
      { cause: "Solids passing through stages", weight: 0.28 },
      { cause: "Gas slugging", weight: 0.2 },
      { cause: "Gauge accelerometer artefact", weight: 0.12 },
    ],
    verify: ["Check for correlated amp instability suggesting gas", "Review solids sampling", "Confirm sensor health in OTConnex"],
    actions: ["Keep operating point near BEP", "Increase surveillance frequency for this well", "Add to bad-actor watch list"],
    impactNote: () => "No deferment now; rising vibration is an early mechanical-degradation indicator.",
    confidence: 0.6,
    durationH: 9,
  },
  "stopped-unplanned": {
    category: "Unplanned stop",
    severity: "critical",
    rule: "Run status = 0 without planned-work flag",
    observation: () => "Well stopped without a planned-work flag; restart produced idle amps and no measurable flow.",
    evidence: (w) => [
      "Flow 0 bpd with drive reporting run",
      "Motor current at no-load value on restart attempt",
      `PIP building to ${w.pipPsi} psi (static)`,
      "PDP approximately equal to intake pressure",
    ],
    causes: [
      { cause: "Broken shaft / mechanical decoupling", weight: 0.58 },
      { cause: "Severe gas lock", weight: 0.18 },
      { cause: "Tubing leak or plugged discharge", weight: 0.14 },
      { cause: "Flow measurement failure", weight: 0.1 },
    ],
    verify: ["Confirm no-load amps against motor nameplate", "Compare PDP and PIP for pressure development", "Attempt controlled restart with engineering present"],
    actions: ["Stop repeat restart attempts", "Raise workover candidate with rig-schedule priority", "Plan DIFA on pull with shaft and coupling inspection"],
    impactNote: (w) => `${w.deferredBopd} BOPD fully deferred while down.`,
    confidence: 0.82,
    durationH: 20,
  },
  "stopped-planned": {
    category: "Unplanned stop",
    severity: "info",
    rule: "Run status = 0 with planned-work flag",
    observation: () => "Well stopped under planned flowline tie-in work; deferment is expected and tracked against the plan.",
    evidence: (w) => [`Permit W-4471 active`, `Down ${Math.round(34)} h against 48 h plan`, `Deferred ${w.deferredBopd} BOPD (planned)`],
    causes: [{ cause: "Planned surface work", weight: 1 }],
    verify: ["Confirm work completion window", "Confirm restart readiness checklist"],
    actions: ["Track against planned window", "Schedule post-restart stabilisation review"],
    impactNote: (w) => `${w.deferredBopd} BOPD planned deferment.`,
    confidence: 0.99,
    durationH: 34,
  },
};

/** Extra categories seeded to demonstrate the full exception taxonomy. */
const extras: EspException[] = [
  {
    id: "EX-9001",
    wellId: "ESP-263",
    fieldId: "KLS",
    category: "Tubing leak / recirculation suspicion",
    severity: "warning",
    firstSeen: "2026-08-12 04:10",
    durationH: 37,
    impactBopd: 85,
    opportunityUsdDay: 85 * 68,
    confidence: 0.57,
    owner: owners[3]!,
    status: "Acknowledged",
    rule: "Rate ↓ with PDP ↓ and current steady/rising at constant Hz",
    observation: "Surface rate fell 8% while discharge pressure fell and motor current held steady — flow may be recirculating downhole.",
    evidence: [
      "Rate 2,190 → 2,015 bpd at unchanged 54.5 Hz",
      "PDP down 90 psi, PIP roughly unchanged",
      "Motor current flat within ±0.6 A",
      "WHP unchanged — surface restriction not indicated",
    ],
    likelyCauses: [
      { cause: "Tubing leak / recirculation above pump", weight: 0.46 },
      { cause: "Worn stages passing fluid internally", weight: 0.3 },
      { cause: "Check-valve failure", weight: 0.14 },
      { cause: "Meter drift", weight: 0.1 },
    ],
    verify: ["Pressure-test tubing at next opportunity", "Compare separator allocation with multiphase meter", "Check fluid level shot if available"],
    recommendedAction: ["Schedule tubing integrity test", "Hold frequency stable pending test", "Prepare workover scope option"],
    impactNote: "85 BOPD below expected with rising uncertainty on allocated volumes.",
  },
  {
    id: "EX-9002",
    wellId: "ESP-118",
    fieldId: "NRD",
    category: "Intake / perforation restriction suspicion",
    severity: "warning",
    firstSeen: "2026-08-11 18:25",
    durationH: 71,
    impactBopd: 110,
    opportunityUsdDay: 110 * 68,
    confidence: 0.61,
    owner: owners[0]!,
    status: "Assigned",
    rule: "PIP ↓ with rate ↓ and drawdown above PI expectation",
    observation: "Intake pressure falling faster than the PI model predicts for the produced rate — restriction between reservoir and intake suspected.",
    evidence: [
      "Measured drawdown 42% above PI-model expectation",
      "Rate 2,050 bpd vs expected 2,156 bpd",
      "Vibration 0.58 g suggests solids movement",
      "Scale tendency flagged in water analysis",
    ],
    likelyCauses: [
      { cause: "Perforation / intake plugging (scale or solids)", weight: 0.48 },
      { cause: "Near-wellbore damage", weight: 0.24 },
      { cause: "Screen or intake debris", weight: 0.18 },
      { cause: "PI model out of date", weight: 0.1 },
    ],
    verify: ["Run pressure build-up or step-rate test", "Review last scale-inhibitor batch effectiveness", "Confirm PI from the most recent well test"],
    recommendedAction: ["Plan chemical / scale treatment", "Update PI in the active design case", "Monitor drawdown response after treatment"],
    impactNote: "110 BOPD deferred; unresolved restriction accelerates downthrust and wear.",
  },
  {
    id: "EX-9003",
    wellId: "ESP-312",
    fieldId: "TMR",
    category: "Optimization opportunity",
    severity: "opportunity",
    firstSeen: "2026-08-13 08:20",
    durationH: 9,
    impactBopd: 0,
    opportunityUsdDay: 95 * 68,
    confidence: 0.58,
    owner: owners[4]!,
    status: "Open",
    rule: "Inside ROR AND load < 70% AND thermal margin > 35 degF AND rate < 0.85 × BEP",
    observation: "Well is healthy with envelope, thermal and electrical headroom — a frequency uplift is available.",
    evidence: [
      "Operating point 0.80 × BEP",
      "Motor load 55% of rating",
      "Thermal margin 54 degF",
      "Simplified affinity scenario: +1.5 Hz → +95 BOPD",
    ],
    likelyCauses: [{ cause: "Conservative frequency setpoint", weight: 0.8 }, { cause: "Inflow better than design assumption", weight: 0.2 }],
    verify: ["Confirm inflow with recent well test", "Confirm separator and flowline capacity", "Check ROR maximum at target frequency"],
    recommendedAction: ["Record what-if case in Design Cases", "Step +1.5 Hz and hold 24 h", "Re-evaluate operating point and motor temperature"],
    impactNote: "Illustrative uplift 95 BOPD (~$6.5k/day at demo price deck).",
  },
  {
    id: "EX-9004",
    wellId: "ESP-307",
    fieldId: "TMR",
    category: "Optimization opportunity",
    severity: "opportunity",
    firstSeen: "2026-08-12 10:05",
    durationH: 31,
    impactBopd: 0,
    opportunityUsdDay: 55 * 68,
    confidence: 0.54,
    owner: owners[1]!,
    status: "Open",
    rule: "Inside ROR AND choke restriction detected",
    observation: "Wellhead pressure elevated versus field norm — choke or flowline restriction is costing available lift capacity.",
    evidence: ["WHP 335 psi vs field median 292 psi", "Operating point 0.91 × BEP", "TDH 6% above design at same rate"],
    likelyCauses: [{ cause: "Choke partially restricting", weight: 0.55 }, { cause: "Flowline deposition", weight: 0.3 }, { cause: "Separator backpressure", weight: 0.15 }],
    verify: ["Field check choke position", "Compare flowline pressure profile", "Review separator operating pressure"],
    recommendedAction: ["Open choke stepwise and observe rate", "Consider flowline cleanout", "Record resulting case for comparison"],
    impactNote: "Illustrative uplift 55 BOPD from reduced backpressure.",
  },
  {
    id: "EX-9005",
    wellId: "ESP-242",
    fieldId: "KLS",
    category: "Suspected pump wear / declining head per stage",
    severity: "warning",
    firstSeen: "2026-08-06 12:00",
    durationH: 176,
    impactBopd: 0,
    opportunityUsdDay: 0,
    confidence: 0.49,
    owner: owners[2]!,
    status: "Closed",
    rule: "Head-per-stage 30-day slope < −8%",
    observation: "Head decline flagged one week before the unplanned stop; superseded by the broken-shaft investigation.",
    evidence: ["Head per stage −9% over 30 days", "Vibration rising before stop", "Superseded by unplanned-stop exception"],
    likelyCauses: [{ cause: "Mechanical degradation preceding failure", weight: 0.7 }, { cause: "Solids damage", weight: 0.3 }],
    verify: ["Confirm on DIFA teardown"],
    recommendedAction: ["Closed — carried into workover scope"],
    impactNote: "Closed and rolled into the workover candidate for ESP-242.",
  },
];

function buildFromWells(): EspException[] {
  const list: EspException[] = [];
  wells.forEach((w, i) => {
    const r = recipes[w.state];
    if (!r) return;
    list.push({
      id: `EX-${1000 + i}`,
      wellId: w.id,
      fieldId: w.fieldId,
      category: r.category,
      severity: r.severity,
      firstSeen: w.lastEventAt,
      durationH: r.durationH,
      impactBopd: w.deferredBopd,
      opportunityUsdDay: w.deferredBopd * 68,
      confidence: r.confidence,
      owner: owners[i % owners.length]!,
      status: i % 5 === 0 ? "Acknowledged" : i % 7 === 0 ? "Assigned" : "Open",
      rule: r.rule,
      observation: r.observation(w),
      evidence: r.evidence(w),
      likelyCauses: r.causes,
      verify: r.verify,
      recommendedAction: r.actions,
      impactNote: r.impactNote(w),
    });
  });
  return list;
}

export const exceptions: EspException[] = [...buildFromWells(), ...extras];

export const exceptionsForWell = (wellId: string) => exceptions.filter((e) => e.wellId === wellId);

export const severityRank: Record<Severity, number> = {
  critical: 0,
  warning: 1,
  watch: 2,
  info: 3,
  opportunity: 4,
};

export const needsAttention = () =>
  exceptions
    .filter((e) => e.status !== "Closed" && e.severity !== "opportunity")
    .sort((a, b) => severityRank[a.severity] - severityRank[b.severity] || b.impactBopd - a.impactBopd);

export const optimizationQueue = () =>
  exceptions.filter((e) => e.severity === "opportunity" && e.status !== "Closed").sort((a, b) => b.opportunityUsdDay - a.opportunityUsdDay);
