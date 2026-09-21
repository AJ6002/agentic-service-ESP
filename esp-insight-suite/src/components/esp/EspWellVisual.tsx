import { useState } from "react";
import type { Well } from "@/data/esp/types";
import { stateLabels, stateTone } from "@/data/esp/fleet";
import { n0, n1 } from "@/lib/esp/format";
import { textTone, type Tone } from "./ui";
import { cn } from "@/lib/utils";

/**
 * Original ESP well system visualization.
 * Drawn entirely from SVG primitives — no vendor artwork, no logos.
 * Animation is demo-only and driven by the existing simulated well values.
 * Visualization only: nothing here writes, commands or controls equipment.
 */

export type EspSubsystem =
  | "vsd"
  | "wellhead"
  | "tubing"
  | "pump"
  | "intake"
  | "protector"
  | "motor"
  | "cable"
  | "gauge"
  | "perfs";

type Hotspot = {
  key: EspSubsystem | string;
  subsystem: EspSubsystem;
  label: string;
  x: number;
  y: number;
  value: string;
  unit: string;
  design: string;
  tone: Tone;
  status: string;
};

const VB_W = 380;
const VB_H = 470;

function tempTone(w: Well): Tone {
  if (!w.motorTempF) return "muted";
  if (w.motorTempF > w.motorTempLimitF) return "critical";
  if (w.motorTempF > w.motorTempLimitF - 12) return "warning";
  return "normal";
}

function loadTone(w: Well): Tone {
  if (!w.hz) return "stopped";
  if (w.motorLoadPct > 78) return "critical";
  if (w.motorLoadPct > 70) return "watch";
  return "normal";
}

function deltaTone(actual: number, design: number, tol = 8): Tone {
  if (!design) return "muted";
  const d = Math.abs((actual - design) / design) * 100;
  if (d <= tol) return "normal";
  if (d <= tol * 2.2) return "watch";
  return "warning";
}

function buildHotspots(w: Well): Hotspot[] {
  const state = stateLabels[w.state];
  const running = w.hz > 0;
  const gaugeOk = w.gaugeStatus === "good";
  return [
    {
      key: "hz",
      subsystem: "vsd",
      label: "Drive frequency",
      x: 40,
      y: 44,
      value: running ? n1(w.hz) : "0.0",
      unit: "Hz",
      design: `${n1(w.designHz)} Hz design`,
      tone: running ? deltaTone(w.hz, w.designHz, 6) : "stopped",
      status: running ? state : stateLabels[w.state],
    },
    {
      key: "whp",
      subsystem: "wellhead",
      label: "Wellhead pressure",
      x: 246,
      y: 44,
      value: n0(w.whpPsi),
      unit: "psi",
      design: "flowline / choke context",
      tone: "info",
      status: state,
    },
    {
      key: "rate",
      subsystem: "tubing",
      label: "Liquid production rate",
      x: 160,
      y: 168,
      value: n0(w.liquidRateBpd),
      unit: "bpd",
      design: `${n0(w.designLiquidBpd)} bpd design · ROR ${n0(w.rorMin)}–${n0(w.rorMax)}`,
      tone: !running
        ? "stopped"
        : w.liquidRateBpd < w.rorMin
          ? "warning"
          : w.liquidRateBpd > w.rorMax
            ? "warning"
            : "normal",
      status: !running
        ? state
        : w.liquidRateBpd < w.rorMin
          ? "Low-flow / downthrust risk"
          : w.liquidRateBpd > w.rorMax
            ? "High-flow / upthrust risk"
            : state,
    },
    {
      key: "pdp",
      subsystem: "pump",
      label: "Pump discharge pressure",
      x: 160,
      y: 296,
      value: w.pdpPsi ? n0(w.pdpPsi) : "no data",
      unit: w.pdpPsi ? "psi" : "",
      design: `${n0(w.designPdpPsi)} psi design`,
      tone: w.pdpPsi ? deltaTone(w.pdpPsi, w.designPdpPsi, 8) : "muted",
      status: w.pdpPsi ? state : "Gauge communication issue",
    },
    {
      key: "vib",
      subsystem: "pump",
      label: "Pump vibration",
      x: 160,
      y: 330,
      value: n2v(w.vibrationG),
      unit: "g",
      design: "0.35 g typical alarm",
      tone: !running ? "stopped" : w.vibrationG > 0.35 ? "critical" : w.vibrationG > 0.25 ? "watch" : "normal",
      status: w.vibrationG > 0.25 ? "Vibration / pump wear watch" : state,
    },
    {
      key: "pip",
      subsystem: "intake",
      label: "Pump intake pressure",
      x: 160,
      y: 366,
      value: w.pipPsi ? n0(w.pipPsi) : "no data",
      unit: w.pipPsi ? "psi" : "",
      design: `${n0(w.designPipPsi)} psi design · GVF ${n1(w.gvfPct)}%`,
      tone: w.pipPsi ? deltaTone(w.pipPsi, w.designPipPsi, 10) : "muted",
      status: w.gvfPct > 18 ? "Gas interference risk" : w.pipPsi ? state : "Gauge communication issue",
    },
    {
      key: "amps",
      subsystem: "motor",
      label: "Motor current / load",
      x: 160,
      y: 410,
      value: running ? n1(w.amps) : "0.0",
      unit: "A",
      design: `${w.motorRatingA} A rated · ${running ? w.motorLoadPct : 0}% load`,
      tone: loadTone(w),
      status: w.motorLoadPct > 78 ? "Motor overload" : state,
    },
    {
      key: "temp",
      subsystem: "motor",
      label: "Motor temperature",
      x: 160,
      y: 430,
      value: w.motorTempF ? n0(w.motorTempF) : "no data",
      unit: w.motorTempF ? "degF" : "",
      design: `${w.motorTempLimitF} degF limit`,
      tone: tempTone(w),
      status: tempTone(w) === "normal" ? state : "High motor temperature",
    },
    {
      key: "gauge",
      subsystem: "gauge",
      label: "Downhole gauge",
      x: 200,
      y: 448,
      value: w.gaugeStatus,
      unit: "",
      design: "continuous PIP / PDP / temp telemetry",
      tone: gaugeOk ? "normal" : w.gaugeStatus === "lost" ? "critical" : "watch",
      status: gaugeOk ? "Normal" : "Gauge communication issue",
    },
    {
      key: "perfs",
      subsystem: "perfs",
      label: "Inflow / perforations",
      x: 210,
      y: 380,
      value: n0(w.pwfPsi),
      unit: "psi Pwf",
      design: `Pr ${n0(w.reservoirPsi)} psi · PI ${w.piBpdPsi.toFixed(2)} bpd/psi`,
      tone: "info",
      status: state,
    },
  ];
}

const n2v = (v: number) => v.toFixed(2);

const toneStroke: Record<Tone, string> = {
  normal: "var(--color-normal)",
  watch: "var(--color-watch)",
  warning: "var(--color-warning)",
  critical: "var(--color-critical)",
  stopped: "var(--color-stopped)",
  info: "var(--color-info)",
  opportunity: "var(--color-opportunity)",
  muted: "var(--color-muted-foreground)",
};

export function EspWellVisual({
  well,
  variant = "full",
  highlight,
  className,
}: {
  well: Well;
  variant?: "full" | "compact";
  highlight?: EspSubsystem | undefined;
  className?: string;
}) {
  const [active, setActive] = useState<string | null>(null);
  const hotspots = buildHotspots(well);
  const hot = hotspots.find((h) => h.key === active) ?? null;

  const running = well.hz > 0;
  const tripped = well.state === "vsd-trip" || well.state === "stopped-unplanned";
  const unstable = well.state === "gas-interference" || well.state === "vibration-warning";
  // Animation speed scales with the simulated drive frequency (demo only).
  const flowDur = running ? Math.max(1.1, 4.2 - (well.hz - 35) * 0.075) : 0;
  const labels = variant === "full";

  const dim = (s: EspSubsystem) => (highlight && highlight !== s ? 0.35 : 1);
  const ring = (s: EspSubsystem) => highlight === s;

  const label = (x: number, y: number, text: string, anchor: "start" | "end" = "start") =>
    labels ? (
      <text x={x} y={y} textAnchor={anchor} fill="var(--color-muted-foreground)" fontSize="8.5">
        {text}
      </text>
    ) : null;

  const flowDots = (count: number, x: number, fromY: number, toY: number, delayStep: number) =>
    running
      ? Array.from({ length: count }).map((_, i) => (
          <circle
            key={i}
            className="esp-anim esp-flow-up"
            cx={x}
            cy={fromY}
            r={unstable && i % 2 === 0 ? 2.6 : 1.8}
            fill={unstable && i % 2 === 0 ? "var(--color-watch)" : "var(--color-chart-1)"}
            style={
              {
                "--esp-from": "0px",
                "--esp-to": `${toY - fromY}px`,
                animationDuration: `${flowDur}s`,
                animationDelay: `${i * delayStep}s`,
              } as React.CSSProperties
            }
          />
        ))
      : null;

  return (
    <div className={cn("relative w-full", className)}>
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        className="w-full"
        style={{ maxHeight: variant === "full" ? 560 : 380 }}
        role="img"
        aria-label={`ESP well system visualization for ${well.id} — ${stateLabels[well.state]}`}
      >
        {/* ground / surface */}
        <line x1="0" y1="70" x2={VB_W} y2="70" stroke="var(--color-border)" />
        <rect x="0" y="70" width={VB_W} height={VB_H - 70} fill="var(--color-panel)" opacity="0.35" />
        {label(4, 84, "Surface")}

        {/* VSD + transformer + surface panel */}
        <g opacity={dim("vsd")}>
          <rect
            x="14"
            y="26"
            width="50"
            height="36"
            rx="2"
            fill="var(--color-card)"
            stroke={ring("vsd") ? "var(--color-primary)" : "var(--color-border)"}
            strokeWidth={ring("vsd") ? 1.8 : 1}
          />
          <text x="39" y="40" textAnchor="middle" fontSize="8.5" fill="var(--color-foreground)">
            VSD
          </text>
          <text x="39" y="52" textAnchor="middle" fontSize="8" fill="var(--color-muted-foreground)">
            {running ? `${n1(well.hz)} Hz` : tripped ? "trip" : "off"}
          </text>
          <rect x="74" y="32" width="32" height="30" rx="2" fill="var(--color-card)" stroke="var(--color-border)" />
          <text x="90" y="51" textAnchor="middle" fontSize="8" fill="var(--color-muted-foreground)">
            TX
          </text>
          <line x1="106" y1="47" x2="136" y2="47" stroke="var(--color-border)" />
        </g>

        {/* wellhead + choke + flowline (with surface flow animation) */}
        <g opacity={dim("wellhead")}>
          <rect
            x="136"
            y="52"
            width="40"
            height="18"
            fill="var(--color-panel-header)"
            stroke={ring("wellhead") ? "var(--color-primary)" : "var(--color-border)"}
            strokeWidth={ring("wellhead") ? 1.8 : 1}
          />
          <line x1="176" y1="44" x2="330" y2="44" stroke="var(--color-chart-1)" strokeWidth="1.6" />
          <line x1="156" y1="52" x2="156" y2="44" stroke="var(--color-chart-1)" strokeWidth="1.6" />
          <line x1="156" y1="44" x2="176" y2="44" stroke="var(--color-chart-1)" strokeWidth="1.6" />
          <circle cx="236" cy="44" r="5.5" fill="var(--color-background)" stroke="var(--color-chart-1)" strokeWidth="1.3" />
          {running &&
            Array.from({ length: 4 }).map((_, i) => (
              <circle
                key={i}
                className="esp-anim esp-flow-right"
                cx="176"
                cy="44"
                r="1.8"
                fill="var(--color-chart-1)"
                style={
                  {
                    "--esp-from": "0px",
                    "--esp-to": "154px",
                    animationDuration: `${flowDur * 1.2}s`,
                    animationDelay: `${i * (flowDur * 0.3)}s`,
                  } as React.CSSProperties
                }
              />
            ))}
          {label(258, 34, "Choke + flow meter")}
          {label(258, 58, "To production flowline")}
        </g>

        {/* casing + annulus */}
        <rect x="120" y="70" width="80" height={VB_H - 100} fill="none" stroke="var(--color-border)" />
        <rect
          x="142"
          y="70"
          width="36"
          height="230"
          fill="var(--color-background)"
          stroke={ring("tubing") ? "var(--color-primary)" : "var(--color-border)"}
          strokeWidth={ring("tubing") ? 1.8 : 1}
          opacity={dim("tubing")}
        />
        {label(206, 110, "Casing")}
        {label(206, 122, "Production tubing")}

        {/* production flow up the tubing */}
        <g opacity={dim("tubing")}>{flowDots(7, 160, 296, 74, flowDur / 7)}</g>

        {/* power cable / MLE with pulse */}
        <g opacity={dim("cable")}>
          <path
            d="M39 62 L39 66 L130 66 L130 404 L136 404"
            fill="none"
            stroke={ring("cable") ? "var(--color-primary)" : "var(--color-chart-5)"}
            strokeWidth="1.5"
          />
          {running && (
            <path
              d="M39 62 L39 66 L130 66 L130 404 L136 404"
              className="esp-anim esp-power-pulse"
              fill="none"
              stroke="var(--color-chart-5)"
              strokeWidth="2.4"
              strokeDasharray="26 460"
            />
          )}
          {label(4, 150, "Power cable / MLE")}
        </g>

        {/* pump discharge + multistage pump */}
        <g opacity={dim("pump")}>
          <rect x="140" y="288" width="40" height="12" fill="var(--color-chart-1)" opacity="0.35" stroke="var(--color-chart-1)" />
          <g className={running ? "esp-anim esp-pump-activity" : undefined} style={{ animationDuration: `${flowDur}s` }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <rect
                key={i}
                x="140"
                y={302 + i * 6}
                width="40"
                height="4.4"
                fill="var(--color-primary)"
                opacity={running ? 0.6 : 0.18}
                stroke={ring("pump") ? "var(--color-primary)" : "var(--color-border)"}
                strokeWidth={ring("pump") ? 1.2 : 0.6}
              />
            ))}
          </g>
          {label(206, 296, "Pump discharge")}
          {label(206, 322, `Multistage pump · ${well.stages} stages`)}
          {label(206, 334, `${well.oem} ${well.pumpModel}`)}
        </g>

        {/* intake / gas handling */}
        <g opacity={dim("intake")}>
          <rect
            x="140"
            y="352"
            width="40"
            height="18"
            fill="var(--color-opportunity)"
            opacity="0.32"
            stroke={ring("intake") ? "var(--color-primary)" : "var(--color-opportunity)"}
            strokeWidth={ring("intake") ? 1.8 : 1}
          />
          {/* free-gas bubbles rising in the annulus when GVF is elevated */}
          {running &&
            well.gvfPct > 12 &&
            Array.from({ length: 4 }).map((_, i) => (
              <circle
                key={i}
                className="esp-anim esp-flow-up"
                cx={128 + (i % 2) * 4}
                cy={360}
                r="1.6"
                fill="var(--color-watch)"
                opacity="0.85"
                style={
                  {
                    "--esp-from": "0px",
                    "--esp-to": "-280px",
                    animationDuration: `${flowDur * 2}s`,
                    animationDelay: `${i * 0.6}s`,
                  } as React.CSSProperties
                }
              />
            ))}
          {label(206, 362, `${well.gasHandler} · intake`)}
          {label(206, 374, `GVF ${n1(well.gvfPct)}%`)}
        </g>

        {/* protector / seal */}
        <g opacity={dim("protector")}>
          <rect
            x="146"
            y="374"
            width="28"
            height="16"
            fill="var(--color-card)"
            stroke={ring("protector") ? "var(--color-primary)" : "var(--color-border)"}
            strokeWidth={ring("protector") ? 1.8 : 1}
          />
          {label(206, 388, "Protector / seal section")}
        </g>

        {/* motor */}
        <g opacity={dim("motor")}>
          <rect
            x="142"
            y="394"
            width="36"
            height="32"
            rx="2"
            fill="var(--color-chart-4)"
            opacity="0.28"
            stroke={ring("motor") ? "var(--color-primary)" : "var(--color-chart-4)"}
            strokeWidth={ring("motor") ? 1.8 : 1}
          />
          <g style={{ transformOrigin: "160px 410px" }} className={running ? "esp-anim esp-rotor" : undefined}>
            <circle cx="160" cy="410" r="8" fill="none" stroke="var(--color-chart-4)" strokeWidth="1.6" strokeDasharray="4 4" />
          </g>
          {label(206, 404, `Motor ${well.motorRatingHp} hp`)}
          {label(206, 416, `${running ? n1(well.amps) + " A" : "0 A"} · ${well.motorTempF ? well.motorTempF + " degF" : "no data"}`)}
        </g>

        {/* downhole sensor */}
        <g opacity={dim("gauge")}>
          <circle
            cx="160"
            cy="438"
            r="5"
            fill={
              well.gaugeStatus === "good"
                ? "var(--color-normal)"
                : well.gaugeStatus === "lost"
                  ? "var(--color-critical)"
                  : "var(--color-watch)"
            }
            stroke={ring("gauge") ? "var(--color-primary)" : "none"}
            strokeWidth="1.8"
          />
          {label(206, 441, `Downhole sensor — ${well.gaugeStatus}`)}
        </g>

        {/* perforations / inflow */}
        <g opacity={dim("perfs")}>
          {Array.from({ length: 5 }).map((_, i) => (
            <g key={i}>
              <line
                x1="200"
                y1={352 + i * 12}
                x2="212"
                y2={352 + i * 12}
                stroke={ring("perfs") ? "var(--color-primary)" : "var(--color-chart-3)"}
                strokeWidth="1.6"
              />
              {running && (
                <circle
                  className="esp-anim esp-inflow"
                  cx="212"
                  cy={352 + i * 12}
                  r="1.6"
                  fill="var(--color-chart-3)"
                  style={
                    {
                      "--esp-from": "0px",
                      "--esp-to": "-14px",
                      animationDuration: `${flowDur * 1.6}s`,
                      animationDelay: `${i * 0.25}s`,
                    } as React.CSSProperties
                  }
                />
              )}
            </g>
          ))}
          {label(4, 352, "Perforations / inflow")}
          {label(4, 366, `Pr ${n0(well.reservoirPsi)} psi`)}
          {label(4, 380, `Pwf ${n0(well.pwfPsi)} psi`)}
        </g>

        {/* hotspots */}
        {hotspots.map((h) => (
          <g
            key={h.key}
            tabIndex={0}
            role="button"
            aria-label={`${h.label}: ${h.value} ${h.unit}. ${h.design}. Status ${h.status}`}
            className="cursor-pointer outline-none focus-visible:opacity-100"
            onMouseEnter={() => setActive(h.key)}
            onMouseLeave={() => setActive((c) => (c === h.key ? null : c))}
            onFocus={() => setActive(h.key)}
            onBlur={() => setActive((c) => (c === h.key ? null : c))}
            onClick={() => setActive((c) => (c === h.key ? null : h.key))}
          >
            <circle
              cx={h.x}
              cy={h.y}
              r="6.5"
              fill="var(--color-background)"
              fillOpacity={active === h.key ? 0.9 : 0.55}
              stroke={toneStroke[h.tone]}
              strokeWidth={active === h.key ? 2 : 1.2}
            />
            <circle cx={h.x} cy={h.y} r="2" fill={toneStroke[h.tone]} />
          </g>
        ))}
      </svg>

      {hot && (
        <div
          className="pointer-events-none absolute z-10 w-[190px] -translate-y-1/2 rounded border border-border bg-popover/95 p-1.5 shadow-lg"
          style={{
            left: `${Math.min(72, (hot.x / VB_W) * 100 + 3)}%`,
            top: `${(hot.y / VB_H) * 100}%`,
          }}
        >
          <div className="text-[10.5px] font-semibold text-foreground">{hot.label}</div>
          <div className="num mt-0.5 text-[13px] text-foreground">
            {hot.value} <span className="text-[10px] text-muted-foreground">{hot.unit}</span>
          </div>
          <div className="text-[9.5px] text-muted-foreground">{hot.design}</div>
          <div className={cn("mt-0.5 text-[10px] font-medium", textTone[hot.tone])}>{hot.status}</div>
        </div>
      )}

      {labels && (
        <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
          <span className={cn("font-semibold", textTone[stateTone[well.state]])}>{stateLabels[well.state]}</span>
          <span>·</span>
          <span>Hover, click or tab a marker for value, design reference and status</span>
          <span>·</span>
          <span>Animation is a demo indication only — no control or write-back</span>
        </div>
      )}
    </div>
  );
}

/** Tiny static status glyph for dense table rows. */
export function EspStatusGlyph({ well }: { well: Well }) {
  const tone = stateTone[well.state];
  const c = toneStroke[tone];
  return (
    <svg
      width="12"
      height="16"
      viewBox="0 0 12 16"
      aria-label={`${well.id} ${stateLabels[well.state]}`}
      role="img"
      className="inline-block align-middle"
    >
      <line x1="0" y1="2.5" x2="12" y2="2.5" stroke="var(--color-border)" />
      <rect x="3.5" y="2.5" width="5" height="10" fill="none" stroke="var(--color-border)" />
      <rect x="4.5" y="6" width="3" height="4" fill={c} opacity={well.hz > 0 ? 0.9 : 0.35} />
      <circle cx="6" cy="14" r="1.6" fill={c} />
    </svg>
  );
}

/** Compact non-interactive miniature for asset / failure context. */
export function EspWellMini({ well, height = 96 }: { well: Well; height?: number }) {
  const tone = stateTone[well.state];
  const c = toneStroke[tone];
  return (
    <svg viewBox="0 0 60 120" height={height} role="img" aria-label={`${well.id} ESP string miniature`}>
      <line x1="0" y1="10" x2="60" y2="10" stroke="var(--color-border)" />
      <rect x="22" y="4" width="16" height="6" fill="var(--color-panel-header)" stroke="var(--color-border)" />
      <rect x="18" y="10" width="24" height="104" fill="none" stroke="var(--color-border)" />
      <rect x="25" y="10" width="10" height="58" fill="var(--color-background)" stroke="var(--color-border)" />
      {Array.from({ length: 5 }).map((_, i) => (
        <rect key={i} x="24" y={70 + i * 4} width="12" height="2.6" fill={c} opacity={well.hz > 0 ? 0.75 : 0.3} />
      ))}
      <rect x="24" y="92" width="12" height="6" fill="var(--color-opportunity)" opacity="0.35" stroke="var(--color-opportunity)" />
      <rect x="25" y="100" width="10" height="12" fill="var(--color-chart-4)" opacity="0.3" stroke="var(--color-chart-4)" />
      <circle cx="30" cy="116" r="2.4" fill={c} />
    </svg>
  );
}
