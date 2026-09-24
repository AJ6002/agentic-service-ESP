import type { AdvisoryItem, Well } from "./types";

/** Advisor Preview content — decision support only, never control. */
export function advisoriesFor(well: Well): AdvisoryItem[] {
  const base: AdvisoryItem[] = [];
  const push = (a: Omit<AdvisoryItem, "id" | "wellId">) =>
    base.push({ ...a, id: `${well.id}-adv-${base.length + 1}`, wellId: well.id });

  switch (well.state) {
    case "gas-interference":
      push({
        kind: "Assessment",
        observation: `Motor current oscillation widened to ±6.2 A while PIP fell ${Math.round(well.pipPsi * 0.18)} psi over 12 h; liquid rate down ~9%.`,
        engineeringContext:
          "Falling intake pressure at constant frequency increases free gas at the intake. Gas fraction reduces the fluid density the stages act on, so developed pressure and rate drop while amps become erratic.",
        assessment: `Consistent with gas interference. Estimated intake GVF ${well.gvfPct.toFixed(1)}% against a 42% separator rating — degradation, not yet full gas lock.`,
        actions: [
          "Verify separator/annulus route and casing pressure trend",
          "Consider 1.5–2.0 Hz reduction to restore intake pressure and stabilise amps",
          "Recheck amp oscillation band and rate 2 h after the change",
        ],
        confidence: 0.74,
        evidence: ["Amp instability index 0.62", "PIP 12 h regression", "Rate vs expected variance", "GVF calculation at intake"],
      });
      break;
    case "high-motor-temp":
      push({
        kind: "Assessment",
        observation: `Motor temperature ${well.motorTempF} degF against ${well.motorTempLimitF} degF limit after 9 days at ${well.hz} Hz.`,
        engineeringContext:
          "Motor cooling depends on fluid velocity past the motor. Higher frequency raises both losses and heat generated per unit of cooling flow.",
        assessment: "Thermal margin is inside 10 degF. Sustained operation at this point shortens insulation life.",
        actions: [
          "Reduce frequency by 1.0–1.5 Hz and observe temperature for 4 h",
          "Confirm gauge temperature calibration against motor winding model",
          "Review annular velocity and shroud option in the next design case",
        ],
        confidence: 0.81,
        evidence: ["Motor temp 7-day trend", "Frequency change event", "Motor load 7-day trend"],
      });
      break;
    case "pump-wear":
      push({
        kind: "Predictive",
        observation: "Head per stage declined 17% over 60 days with rising vibration and elevated loading.",
        engineeringContext:
          "Progressive stage and thrust-bearing wear reduces head at a given flow and speed; abrasives accelerate the trend.",
        assessment:
          "Degradation pattern detected; elevated failure risk over the coming operating window. Illustrative model estimate only — not a guaranteed prediction.",
        actions: [
          "Add to intervention planning with production-impact ranking",
          "Sample for sand/solids and review inhibitor programme",
          "Avoid frequency increases that push the point further right of BEP",
        ],
        confidence: 0.63,
        evidence: ["Head-per-stage 60-day regression", "Vibration trend", "Sand report from field", "Run life 905 d vs field mean"],
      });
      break;
    case "gauge-comms":
      push({
        kind: "Assessment",
        observation: "Downhole gauge packet loss 34% over 6 h; PIP and motor temperature intermittently unavailable.",
        engineeringContext:
          "Diagnostics that depend on intake pressure lose sensitivity when gauge data quality degrades; surface signals alone cannot separate gas from inflow effects.",
        assessment: "Analytics confidence reduced. Treat downhole-derived exceptions on this well as provisional.",
        actions: [
          "Raise gauge repair task for the next field visit",
          "Fall back to surface-signature diagnostics until gauge recovers",
          "Flag affected calculations with data-quality badge",
        ],
        confidence: 0.9,
        evidence: ["OTConnex tag quality log", "Gauge comms event bands"],
      });
      break;
    case "normal":
      push({
        kind: "Optimization",
        observation: `Operating point sits at ${(well.liquidRateBpd / well.bepRate).toFixed(2)} of BEP with ${well.motorTempLimitF - well.motorTempF} degF thermal margin and ${100 - well.motorLoadPct}% load headroom.`,
        engineeringContext:
          "Affinity-law scenario indicates a modest frequency uplift keeps the point inside the recommended operating range while increasing rate.",
        assessment: `Illustrative uplift of ~${well.opportunityBopd || 45} BOPD available at +1.5 Hz, subject to inflow confirmation.`,
        actions: [
          "Run the frequency scenario in Engineering Workbench and record the case",
          "Confirm inflow with a recent well test before committing",
          "Step change and hold 24 h before further increase",
        ],
        confidence: 0.58,
        evidence: ["Frequency scenario (simplified affinity model)", "Envelope margins", "Latest well test"],
      });
      break;
    default:
      push({
        kind: "Assessment",
        observation: well.headline,
        engineeringContext:
          "Surveillance rules compare actual signals against the active design case and the recommended operating envelope.",
        assessment: "Evidence assembled from OTConnex tags and ESP-PMM calculations; engineer review required.",
        actions: ["Open the exception drawer for the full evidence chain", "Verify field conditions before any setpoint change"],
        confidence: 0.6,
        evidence: ["Operating point vs ROR", "Actual vs expected table", "Event history"],
      });
  }

  push({
    kind: "Predictive",
    observation: "Fleet pattern library matched 3 similar historical signatures in this field.",
    engineeringContext:
      "The future ESP Advisor concept combines deterministic calculation output, time-series features, operating state, maintenance history and anomaly detection.",
    assessment: "Similar signatures preceded intervention within 30–60 operating days. Illustrative model estimate.",
    actions: ["Review comparable wells in Reliability", "Confirm with a well test and DIFA history"],
    confidence: 0.52,
    evidence: ["Historical signature match (demo)", "DIFA records", "Run-life distribution"],
  });

  return base;
}
