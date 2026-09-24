// Deterministic time-series generation for trends. No Math.random, no I/O.
import { hash01 } from "./fleet";
import type { Well } from "./types";

export type Range = "24h" | "7d" | "30d" | "60d";

export const rangeConfig: Record<Range, { points: number; stepH: number; label: string }> = {
  "24h": { points: 96, stepH: 0.25, label: "Last 24 hours" },
  "7d": { points: 84, stepH: 2, label: "Last 7 days" },
  "30d": { points: 90, stepH: 8, label: "Last 30 days" },
  "60d": { points: 90, stepH: 16, label: "Last 60 days" },
};

export interface SeriesPoint {
  t: string;
  idx: number;
  hz: number;
  amps: number;
  pip: number;
  pdp: number;
  whp: number;
  rate: number;
  motorTemp: number;
  vib: number;
  headPerStage: number;
  expectedRate: number;
}

function wave(seed: string, i: number, freq: number) {
  const phase = hash01(seed) * Math.PI * 2;
  return Math.sin(i * freq + phase);
}

const NOW = Date.UTC(2026, 7, 13, 17, 0, 0);

function stamp(msAgo: number, stepH: number) {
  const d = new Date(NOW - msAgo);
  const iso = d.toISOString();
  return stepH < 1 ? iso.slice(11, 16) : stepH <= 8 ? `${iso.slice(5, 10)} ${iso.slice(11, 16)}` : iso.slice(5, 10);
}

export function buildSeries(well: Well, range: Range): SeriesPoint[] {
  const { points, stepH } = rangeConfig[range];
  const out: SeriesPoint[] = [];
  const stopped = well.hz === 0;
  const decay = well.state === "pump-wear" ? 1 : 0;

  for (let i = 0; i < points; i++) {
    const age = points - 1 - i; // steps ago
    const progress = i / (points - 1);
    const n = (k: string, amp: number) => wave(well.id + k, i, 0.42) * amp + wave(well.id + k + "2", i, 1.31) * amp * 0.45;

    // Trip / restart shaping for the last part of the window
    const tripped = stopped && age < points * 0.35;
    const gas = well.state === "gas-interference";
    const gasAmp = gas ? 1 + Math.abs(wave(well.id + "gas", i, 2.7)) * 3.4 : 1;

    const hz = tripped ? 0 : stopped ? 0 : well.hz + n("hz", 0.25);
    const amps = tripped
      ? 0
      : stopped
        ? 0
        : Math.max(well.amps + n("a", gas ? 2.6 : 0.7) * gasAmp, 0);
    const pip = well.gaugeStatus === "lost"
      ? 0
      : tripped
        ? well.pipPsi
        : Math.max(
            well.pipPsi * (gas ? 1.18 - 0.2 * progress : 1) + n("pip", gas ? 22 : 9),
            30,
          );
    const rateBase = stopped && tripped ? 0 : well.liquidRateBpd * (gas ? 0.94 + 0.1 * (1 - progress) : 1);
    const rate = Math.max(rateBase + n("q", gas ? 90 : 34), 0);
    const pdp = well.gaugeStatus === "lost" ? 0 : Math.max(well.pdpPsi + n("pdp", gas ? 55 : 18), 0);
    const motorTemp =
      well.gaugeStatus === "lost"
        ? 0
        : tripped
          ? well.motorTempF
          : well.motorTempF -
            (well.state === "high-motor-temp" || gas ? 9 * (1 - progress) : 0) +
            n("t", 2.2);

    out.push({
      t: stamp(age * stepH * 3600000, stepH),
      idx: i,
      hz: +hz.toFixed(1),
      amps: +amps.toFixed(1),
      pip: Math.round(pip),
      pdp: Math.round(pdp),
      whp: Math.round(well.whpPsi + n("whp", 6)),
      rate: Math.round(rate),
      motorTemp: Math.round(motorTemp),
      vib: +Math.max(well.vibrationG + n("v", 0.035), 0).toFixed(3),
      headPerStage: +(
        well.headPerStage * (1 - decay * 0.17 * (1 - progress)) +
        n("h", 0.35)
      ).toFixed(2),
      expectedRate: Math.round(well.designLiquidBpd),
    });
  }
  return out;
}

export interface EventBand {
  idxStart: number;
  idxEnd: number;
  label: string;
  tone: "critical" | "warning" | "watch" | "info" | "stopped";
}

export function buildEvents(well: Well, range: Range): EventBand[] {
  const { points } = rangeConfig[range];
  const at = (f: number) => Math.round(points * f);
  const events: EventBand[] = [];
  switch (well.state) {
    case "vsd-trip":
      events.push({ idxStart: at(0.58), idxEnd: at(0.63), label: "VSD trip", tone: "critical" });
      events.push({ idxStart: at(0.63), idxEnd: at(0.78), label: "Shut-in", tone: "stopped" });
      events.push({ idxStart: at(0.78), idxEnd: at(0.88), label: "Restart / ramp", tone: "info" });
      break;
    case "gas-interference":
      events.push({ idxStart: at(0.42), idxEnd: at(0.66), label: "Amp instability onset", tone: "warning" });
      events.push({ idxStart: at(0.8), idxEnd: at(1), label: "PIP decline", tone: "warning" });
      break;
    case "high-motor-temp":
      events.push({ idxStart: at(0.35), idxEnd: at(0.48), label: "Frequency increase 56 → 58.5 Hz", tone: "info" });
      events.push({ idxStart: at(0.72), idxEnd: at(1), label: "Motor temp watch", tone: "warning" });
      break;
    case "pump-wear":
      events.push({ idxStart: at(0.1), idxEnd: at(1), label: "Head-per-stage decline", tone: "warning" });
      break;
    case "gauge-comms":
      events.push({ idxStart: at(0.55), idxEnd: at(0.72), label: "Gauge data loss", tone: "watch" });
      events.push({ idxStart: at(0.85), idxEnd: at(0.95), label: "Gauge data loss", tone: "watch" });
      break;
    case "stopped-planned":
      events.push({ idxStart: at(0.3), idxEnd: at(1), label: "Planned shutdown", tone: "stopped" });
      break;
    case "stopped-unplanned":
      events.push({ idxStart: at(0.4), idxEnd: at(0.46), label: "Unplanned stop", tone: "critical" });
      events.push({ idxStart: at(0.46), idxEnd: at(1), label: "Down — awaiting diagnosis", tone: "stopped" });
      break;
    case "outside-ror-high":
      events.push({ idxStart: at(0.5), idxEnd: at(1), label: "Right of ROR", tone: "warning" });
      break;
    case "outside-ror-low":
      events.push({ idxStart: at(0.45), idxEnd: at(1), label: "Left of ROR", tone: "warning" });
      break;
    case "motor-overload":
      events.push({ idxStart: at(0.6), idxEnd: at(1), label: "Load > 75%", tone: "critical" });
      break;
    case "vibration-warning":
      events.push({ idxStart: at(0.66), idxEnd: at(1), label: "Vibration alert", tone: "watch" });
      break;
    default:
      events.push({ idxStart: at(0.2), idxEnd: at(0.24), label: "Setpoint change", tone: "info" });
  }
  return events;
}

export interface StateSegment {
  state: string;
  tone: "normal" | "watch" | "warning" | "critical" | "stopped" | "info";
  fromH: number;
  toH: number;
}

export function stateTimeline(well: Well): StateSegment[] {
  const base: StateSegment[] = [{ state: "Normal", tone: "normal", fromH: -24, toH: -14 }];
  switch (well.state) {
    case "vsd-trip":
      return [
        ...base,
        { state: "Normal", tone: "normal", fromH: -14, toH: -1.4 },
        { state: "Trip (F-021)", tone: "critical", fromH: -1.4, toH: -1.2 },
        { state: "Stopped", tone: "stopped", fromH: -1.2, toH: -0.6 },
        { state: "Starting", tone: "info", fromH: -0.6, toH: -0.4 },
        { state: "Ramping / stabilizing", tone: "info", fromH: -0.4, toH: 0 },
      ];
    case "gas-interference":
      return [
        ...base,
        { state: "Normal", tone: "normal", fromH: -14, toH: -9 },
        { state: "Unstable amps", tone: "watch", fromH: -9, toH: -4 },
        { state: "Suspected gas interference", tone: "warning", fromH: -4, toH: 0 },
      ];
    case "stopped-unplanned":
      return [
        ...base,
        { state: "Normal", tone: "normal", fromH: -14, toH: -8 },
        { state: "Unplanned stop", tone: "critical", fromH: -8, toH: -7.6 },
        { state: "Restart attempt", tone: "info", fromH: -7.6, toH: -7.2 },
        { state: "Stopped — no flow", tone: "stopped", fromH: -7.2, toH: 0 },
      ];
    case "stopped-planned":
      return [
        ...base,
        { state: "Planned shutdown", tone: "stopped", fromH: -14, toH: 0 },
      ];
    case "gauge-comms":
      return [
        ...base,
        { state: "Normal", tone: "normal", fromH: -14, toH: -10 },
        { state: "Gauge degraded", tone: "watch", fromH: -10, toH: -6 },
        { state: "Normal (surface only)", tone: "info", fromH: -6, toH: -3 },
        { state: "Gauge degraded", tone: "watch", fromH: -3, toH: 0 },
      ];
    case "high-motor-temp":
      return [
        ...base,
        { state: "Ramping / stabilizing", tone: "info", fromH: -14, toH: -12 },
        { state: "Normal", tone: "normal", fromH: -12, toH: -5 },
        { state: "High motor temperature", tone: "warning", fromH: -5, toH: 0 },
      ];
    case "outside-ror-low":
      return [...base, { state: "Normal", tone: "normal", fromH: -14, toH: -11 }, { state: "Low flow / underloaded", tone: "warning", fromH: -11, toH: 0 }];
    case "outside-ror-high":
      return [...base, { state: "Normal", tone: "normal", fromH: -14, toH: -9 }, { state: "High flow / overloaded", tone: "warning", fromH: -9, toH: 0 }];
    case "motor-overload":
      return [...base, { state: "Normal", tone: "normal", fromH: -14, toH: -7 }, { state: "Overloaded", tone: "critical", fromH: -7, toH: 0 }];
    case "pump-wear":
      return [...base, { state: "Normal (degrading)", tone: "watch", fromH: -14, toH: 0 }];
    case "vibration-warning":
      return [...base, { state: "Normal", tone: "normal", fromH: -14, toH: -6 }, { state: "Vibration warning", tone: "watch", fromH: -6, toH: 0 }];
    default:
      return [...base, { state: "Normal", tone: "normal", fromH: -14, toH: 0 }];
  }
}

export interface WhatChangedItem {
  label: string;
  from: string;
  to: string;
  window: string;
  tone: "normal" | "watch" | "warning" | "critical" | "info";
}

export function whatChanged(well: Well): WhatChangedItem[] {
  const items: WhatChangedItem[] = [];
  const t = (
    label: string,
    from: string,
    to: string,
    window: string,
    tone: WhatChangedItem["tone"] = "info",
  ) => items.push({ label, from, to, window, tone });

  switch (well.state) {
    case "gas-interference":
      t("Motor current band", "±1.4 A", "±6.2 A", "last 9 h", "warning");
      t("Pump intake pressure", `${Math.round(well.pipPsi * 1.18)} psi`, `${well.pipPsi} psi`, "last 12 h", "warning");
      t("Motor temperature", `${well.motorTempF - 9} degF`, `${well.motorTempF} degF`, "last 12 h", "watch");
      t("Liquid rate", `${Math.round(well.liquidRateBpd * 1.09)} bpd`, `${well.liquidRateBpd} bpd`, "last 12 h", "warning");
      break;
    case "high-motor-temp":
      t("Frequency setpoint", "56.0 Hz", `${well.hz} Hz`, "9 days ago", "info");
      t("Motor temperature", `${well.motorTempF - 14} degF`, `${well.motorTempF} degF`, "since change", "warning");
      t("Motor load", `${well.motorLoadPct - 8}%`, `${well.motorLoadPct}%`, "since change", "watch");
      break;
    case "pump-wear":
      t("Head per stage", `${(well.headPerStage * 1.2).toFixed(1)} ft`, `${well.headPerStage.toFixed(1)} ft`, "60 days", "warning");
      t("Liquid rate", `${Math.round(well.liquidRateBpd * 1.15)} bpd`, `${well.liquidRateBpd} bpd`, "60 days", "warning");
      t("Vibration", "0.28 g", `${well.vibrationG.toFixed(2)} g`, "60 days", "watch");
      break;
    case "vsd-trip":
      t("Drive state", "Run", "Trip F-021 → restart", "1.4 h", "critical");
      t("Bus voltage (pre-trip)", "2,050 V", "1,742 V", "trip instant", "critical");
      t("Frequency", "54.0 Hz", `${well.hz} Hz (ramping)`, "last 25 min", "info");
      break;
    case "gauge-comms":
      t("Gauge packet loss", "0%", "34%", "last 6 h", "watch");
      t("Analytics confidence", "High", "Reduced", "last 6 h", "watch");
      break;
    case "outside-ror-low":
      t("Frequency setpoint", "52.0 Hz", `${well.hz} Hz`, "2 days ago", "info");
      t("Liquid rate", `${Math.round(well.rorMin * 1.05)} bpd`, `${well.liquidRateBpd} bpd`, "2 days", "warning");
      break;
    case "outside-ror-high":
      t("Frequency setpoint", "57.0 Hz", `${well.hz} Hz`, "3 days ago", "info");
      t("Motor load", `${well.motorLoadPct - 6}%`, `${well.motorLoadPct}%`, "3 days", "warning");
      break;
    case "stopped-unplanned":
      t("Flow", `${Math.round(well.bepRate * 0.9)} bpd`, "0 bpd", "at stop", "critical");
      t("Motor current", "44.0 A", "idle on restart", "restart attempt", "critical");
      t("PIP", "690 psi", `${well.pipPsi} psi (building)`, "since stop", "warning");
      break;
    default:
      t("Operating point", "inside ROR", "inside ROR", "24 h", "normal");
      t("Motor load", `${well.motorLoadPct - 1}%`, `${well.motorLoadPct}%`, "24 h", "normal");
  }
  return items;
}
