import { fields, hash01, wells } from "./fleet";
import type { FailureRecord, Intervention } from "./types";

export const runLifeFactors = [
  { factor: "Proper sizing / envelope compliance", weight: 0.22, note: "Time outside ROR drives downthrust and upthrust wear" },
  { factor: "Bottomhole / operating temperature", weight: 0.15, note: "Insulation and elastomer life fall with sustained high temperature" },
  { factor: "Free gas at intake", weight: 0.14, note: "Gas cycling causes thrust and seal damage" },
  { factor: "Fluid viscosity", weight: 0.07, note: "Head and efficiency correction; motor loading" },
  { factor: "Corrosion", weight: 0.09, note: "CO2 / H2S exposure and material selection" },
  { factor: "Sand / foreign material", weight: 0.13, note: "Abrasive wear of stages and bearings" },
  { factor: "Deposition / scale", weight: 0.08, note: "Head loss and mechanical drag" },
  { factor: "Electrical failures", weight: 0.07, note: "Cable, MLE, splice and motor winding integrity" },
  { factor: "Operational problems", weight: 0.03, note: "Repeat restarts, nuisance trips, unstable operation" },
  { factor: "Age / accumulated cycles", weight: 0.02, note: "Baseline wear-out" },
];

const failureModes = [
  { component: "Pump", mode: "Stage / bearing wear (abrasives)", factor: "Sand / foreign material" },
  { component: "Motor", mode: "Winding insulation failure", factor: "Electrical failures" },
  { component: "Cable / MLE", mode: "Insulation degradation at splice", factor: "Electrical failures" },
  { component: "Seal section", mode: "Bag / labyrinth failure", factor: "Bottomhole temperature" },
  { component: "Pump", mode: "Shaft break", factor: "Operational problems" },
  { component: "Pump", mode: "Scale-induced lock-up", factor: "Deposition / scale" },
  { component: "Gas separator", mode: "Rotor wear", factor: "Free gas at intake" },
  { component: "Motor", mode: "Thermal overload", factor: "Bottomhole temperature" },
  { component: "Downhole gauge", mode: "Comms / sensor failure", factor: "Electrical failures" },
];

export const failures: FailureRecord[] = Array.from({ length: 34 }, (_, i) => {
  const w = wells[i % wells.length]!;
  const fm = failureModes[Math.floor(hash01(`fm${i}`) * failureModes.length)]!;
  const runLife = 120 + Math.round(hash01(`rl${i}`) * 1150);
  const pulled = new Date(Date.UTC(2024, 0, 15) + i * 21 * 86400000).toISOString().slice(0, 10);
  return {
    id: `DIFA-${2100 + i}`,
    wellId: w.id,
    fieldId: w.fieldId,
    pulled,
    runLifeDays: runLife,
    failedComponent: fm.component,
    failureMode: fm.mode,
    rootCauseFactor: fm.factor,
    difaSummary:
      fm.mode === "Shaft break"
        ? "Teardown confirmed shaft failure at pump-protector coupling; heavy downthrust marking on lower stages."
        : fm.mode.includes("insulation")
          ? "Insulation resistance below limit at MLE splice; thermal ageing evident on winding sample."
          : fm.mode.includes("wear")
            ? "Abrasive wear on impeller skirts and diffuser hubs; radial bearings within 60% of wear limit."
            : "Deposition on stage internals with reduced flow passage; chemistry consistent with carbonate scale.",
    repeat: hash01(`rp${i}`) > 0.72,
    interventionCostKUsd: 240 + Math.round(hash01(`cost${i}`) * 420),
    deferredBbl: 4200 + Math.round(hash01(`def${i}`) * 26000),
  };
});

export const runLifeByField = fields.map((f) => {
  const recs = failures.filter((r) => r.fieldId === f.id);
  const mean = recs.reduce((a, r) => a + r.runLifeDays, 0) / Math.max(recs.length, 1);
  const sorted = [...recs].sort((a, b) => a.runLifeDays - b.runLifeDays);
  return {
    fieldId: f.id,
    field: f.name,
    pulls: recs.length,
    meanRunLife: Math.round(mean),
    medianRunLife: sorted.length ? sorted[Math.floor(sorted.length / 2)]!.runLifeDays : 0,
    shortestRunLife: sorted[0]?.runLifeDays ?? 0,
    repeatRate: +((recs.filter((r) => r.repeat).length / Math.max(recs.length, 1)) * 100).toFixed(0),
  };
});

export const runLifeBuckets = (() => {
  const edges = [0, 180, 360, 540, 720, 900, 1200];
  return edges.slice(0, -1).map((lo, i) => {
    const hi = edges[i + 1]!;
    const row: Record<string, number | string> = { bucket: `${lo}–${hi} d` };
    fields.forEach((f) => {
      row[f.name] = failures.filter((r) => r.fieldId === f.id && r.runLifeDays >= lo && r.runLifeDays < hi).length;
    });
    return row;
  });
})();

export const runLifeByFamily = (() => {
  const map = new Map<string, { total: number; count: number }>();
  wells.forEach((w) => {
    const key = `${w.oem} ${w.pumpFamily}`;
    const cur = map.get(key) ?? { total: 0, count: 0 };
    cur.total += w.runLifeDays;
    cur.count += 1;
    map.set(key, cur);
  });
  return [...map.entries()].map(([family, v]) => ({
    family,
    meanRunLife: Math.round(v.total / v.count),
    population: v.count,
  }));
})();

export const failureModePareto = (() => {
  const map = new Map<string, number>();
  failures.forEach((r) => map.set(r.failureMode, (map.get(r.failureMode) ?? 0) + 1));
  const rows = [...map.entries()].map(([mode, count]) => ({ mode, count })).sort((a, b) => b.count - a.count);
  const total = rows.reduce((a, r) => a + r.count, 0);
  let cum = 0;
  return rows.map((r) => {
    cum += r.count;
    return { ...r, cumulativePct: +((cum / total) * 100).toFixed(0) };
  });
})();

export const componentDistribution = (() => {
  const map = new Map<string, number>();
  failures.forEach((r) => map.set(r.failedComponent, (map.get(r.failedComponent) ?? 0) + 1));
  return [...map.entries()].map(([component, count]) => ({ component, count })).sort((a, b) => b.count - a.count);
})();

export const badActors = wells
  .map((w) => {
    const recs = failures.filter((r) => r.wellId === w.id);
    const risk =
      (100 - w.healthIndex) * 0.5 +
      recs.length * 6 +
      (recs.filter((r) => r.repeat).length ? 12 : 0) +
      (w.state === "pump-wear" || w.state === "gas-interference" ? 10 : 0);
    return {
      wellId: w.id,
      field: w.fieldId,
      failures12m: recs.length,
      repeat: recs.some((r) => r.repeat),
      runLifeDays: w.runLifeDays,
      priorRunLifeDays: w.priorRunLifeDays,
      healthIndex: w.healthIndex,
      deferredBopd: w.deferredBopd,
      riskScore: +risk.toFixed(0),
      dominantFactor: recs[0]?.rootCauseFactor ?? "Envelope compliance",
      rulEstimateDays: Math.max(30, Math.round(360 - risk * 3)),
    };
  })
  .sort((a, b) => b.riskScore - a.riskScore);

export const interventions: Intervention[] = [
  { id: "INT-401", wellId: "ESP-242", type: "Workover / ESP replacement", priority: 1, plannedWindow: "2026-08-22 → 08-27", reason: "Suspected broken shaft, well down, full deferment", impactBopd: 1050, riskScore: 96, status: "Scheduled" },
  { id: "INT-402", wellId: "ESP-338", type: "VSD service", priority: 1, plannedWindow: "2026-08-15", reason: "Repeat F-014 trips with lockout; electrical verification required", impactBopd: 1180, riskScore: 91, status: "Scheduled" },
  { id: "INT-403", wellId: "ESP-097", type: "Workover / ESP replacement", priority: 2, plannedWindow: "2026-09-08 → 09-13", reason: "Head-per-stage decline 17% over 60 days", impactBopd: 210, riskScore: 78, status: "Proposed" },
  { id: "INT-404", wellId: "ESP-271", type: "Redesign & resize", priority: 2, plannedWindow: "2026-09-19", reason: "Abrasive wear with chronic downthrust exposure; resize with abrasion-resistant stages", impactBopd: 130, riskScore: 72, status: "Proposed" },
  { id: "INT-405", wellId: "ESP-118", type: "Chemical / scale treatment", priority: 2, plannedWindow: "2026-08-19", reason: "Intake / perforation restriction suspicion with scale tendency", impactBopd: 110, riskScore: 64, status: "Proposed" },
  { id: "INT-406", wellId: "ESP-076", type: "Gauge repair", priority: 3, plannedWindow: "2026-08-26", reason: "Intermittent gauge comms reducing analytics confidence", impactBopd: 0, riskScore: 41, status: "Proposed" },
  { id: "INT-407", wellId: "ESP-331", type: "Gauge repair", priority: 3, plannedWindow: "2026-08-27", reason: "Gauge signal lost; surface-only surveillance", impactBopd: 0, riskScore: 44, status: "Proposed" },
  { id: "INT-408", wellId: "ESP-205", type: "Redesign & resize", priority: 3, plannedWindow: "2026-10-02", reason: "Pump oversized for current inflow; chronic left-of-ROR operation", impactBopd: 120, riskScore: 58, status: "Proposed" },
  { id: "INT-409", wellId: "ESP-126", type: "Redesign & resize", priority: 2, plannedWindow: "2026-09-25", reason: "Motor loading at 79% with rising water cut", impactBopd: 60, riskScore: 69, status: "Proposed" },
  { id: "INT-410", wellId: "ESP-133", type: "Workover / ESP replacement", priority: 3, plannedWindow: "Executed 2026-08-12", reason: "Planned flowline tie-in with ESP inspection", impactBopd: 0, riskScore: 22, status: "Executed" },
];

export const interventionTimeline = interventions
  .filter((i) => i.status !== "Executed")
  .map((i) => ({ ...i, week: i.plannedWindow.slice(0, 7) }));
