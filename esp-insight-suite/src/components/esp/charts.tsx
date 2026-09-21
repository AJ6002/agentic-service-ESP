import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { curveHeadAt, pumpCurve, tdhBreakdown } from "@/lib/esp/calc";
import type { Well } from "@/data/esp/types";
import type { EventBand, SeriesPoint } from "@/data/esp/series";
import { n0 } from "@/lib/esp/format";

const axis = {
  stroke: "var(--color-muted-foreground)",
  fontSize: 10,
  tickLine: false,
};

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-popover)",
    border: "1px solid var(--color-border)",
    borderRadius: 4,
    fontSize: 11,
  },
  labelStyle: { color: "var(--color-muted-foreground)", fontSize: 10 },
} as const;

const bandFill: Record<EventBand["tone"], string> = {
  critical: "var(--color-critical)",
  warning: "var(--color-warning)",
  watch: "var(--color-watch)",
  info: "var(--color-info)",
  stopped: "var(--color-stopped)",
};

export interface TrendDef {
  key: keyof SeriesPoint;
  label: string;
  unit: string;
  color: string;
}

export const trendCatalog: TrendDef[] = [
  { key: "hz", label: "Frequency", unit: "Hz", color: "var(--color-chart-1)" },
  { key: "amps", label: "Motor current", unit: "A", color: "var(--color-chart-4)" },
  { key: "pip", label: "Pump intake pressure", unit: "psi", color: "var(--color-chart-2)" },
  { key: "pdp", label: "Pump discharge pressure", unit: "psi", color: "var(--color-chart-5)" },
  { key: "whp", label: "Wellhead pressure", unit: "psi", color: "var(--color-opportunity)" },
  { key: "rate", label: "Liquid rate", unit: "bpd", color: "var(--color-chart-3)" },
  { key: "motorTemp", label: "Motor temperature", unit: "degF", color: "var(--color-critical)" },
  { key: "vib", label: "Vibration", unit: "g", color: "var(--color-watch)" },
  { key: "headPerStage", label: "Head per stage", unit: "ft", color: "var(--color-normal)" },
];

export function TrendChart({
  data,
  events,
  tags,
  height = 220,
}: {
  data: SeriesPoint[];
  events: EventBand[];
  tags: TrendDef[];
  height?: number;
}) {
  const left = tags[0];
  const right = tags[1];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" vertical={false} />
        <XAxis dataKey="t" {...axis} minTickGap={40} />
        <YAxis
          yAxisId="l"
          {...axis}
          width={46}
          label={{
            value: left ? `${left.label} (${left.unit})` : "",
            angle: -90,
            position: "insideLeft",
            fontSize: 9,
            fill: "var(--color-muted-foreground)",
          }}
        />
        {right && (
          <YAxis
            yAxisId="r"
            orientation="right"
            {...axis}
            width={46}
            label={{
              value: `${right.label} (${right.unit})`,
              angle: 90,
              position: "insideRight",
              fontSize: 9,
              fill: "var(--color-muted-foreground)",
            }}
          />
        )}
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 10 }} />
        {events.map((e, i) => (
          <ReferenceArea
            key={i}
            yAxisId="l"
            x1={data[Math.min(e.idxStart, data.length - 1)]?.t ?? ""}
            x2={data[Math.min(e.idxEnd, data.length - 1)]?.t ?? ""}
            fill={bandFill[e.tone]}
            fillOpacity={0.13}
            stroke={bandFill[e.tone]}
            strokeOpacity={0.4}
            label={{ value: e.label, fontSize: 9, fill: "var(--color-muted-foreground)", position: "insideTop" }}
          />
        ))}
        {tags.map((t, i) => (
          <Line
            key={t.key as string}
            yAxisId={i === 1 ? "r" : "l"}
            type="monotone"
            dataKey={t.key as string}
            name={`${t.label} (${t.unit})`}
            stroke={t.color}
            strokeWidth={1.6}
            dot={false}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function PumpCurveChart({
  well,
  hz,
  actualFlow,
  actualHead,
  compareHz,
  height = 300,
  showPower = true,
}: {
  well: Well;
  hz: number;
  actualFlow: number;
  actualHead: number;
  compareHz?: number[];
  height?: number;
  showPower?: boolean;
}) {
  const speed = hz / well.ratedHz;
  const main = pumpCurve(well, hz);
  const extra = (compareHz ?? []).map((h) => ({ hz: h, pts: pumpCurve(well, h) }));
  const bepFlow = Math.round(well.bepRate * speed);
  const rorMin = Math.round(well.rorMin * speed);
  const rorMax = Math.round(well.rorMax * speed);
  const designFlow = Math.round(well.designLiquidBpd * (well.designHz / well.ratedHz) / (well.designHz / well.ratedHz));

  const merged = main.map((p, i) => {
    const row: Record<string, number> = {
      flow: p.flow,
      head: p.head,
      efficiency: p.efficiency,
      power: p.power,
    };
    extra.forEach((e) => {
      row[`head_${e.hz}`] = e.pts[i]?.head ?? 0;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={merged} margin={{ top: 10, right: 16, left: 4, bottom: 34 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" />
        <XAxis
          dataKey="flow"
          type="number"
          {...axis}
          domain={[0, "dataMax"]}
          label={{ value: "Liquid rate (bpd)", position: "insideBottom", offset: -26, fontSize: 10, fill: "var(--color-muted-foreground)" }}
        />
        <YAxis
          yAxisId="h"
          {...axis}
          width={50}
          label={{ value: "Head (ft)", angle: -90, position: "insideLeft", fontSize: 10, fill: "var(--color-muted-foreground)" }}
        />
        <YAxis yAxisId="e" orientation="right" {...axis} width={44} domain={[0, 100]} label={{ value: "Efficiency %", angle: 90, position: "insideRight", fontSize: 10, fill: "var(--color-muted-foreground)" }} />
        <YAxis yAxisId="p" orientation="right" hide domain={[0, "dataMax"]} />
        <Tooltip {...tooltipStyle} formatter={(v: number, k: string) => [n0(v), k]} />
        <Legend wrapperStyle={{ fontSize: 10, paddingTop: 6 }} verticalAlign="bottom" />

        <ReferenceArea
          yAxisId="h"
          x1={rorMin}
          x2={rorMax}
          fill="var(--color-normal)"
          fillOpacity={0.12}
          stroke="var(--color-normal)"
          strokeOpacity={0.35}
          label={{ value: "Recommended operating range", fontSize: 9, fill: "var(--color-normal)", position: "insideTop" }}
        />
        <ReferenceLine yAxisId="h" x={bepFlow} stroke="var(--color-chart-2)" strokeDasharray="4 3" label={{ value: `BEP ${n0(bepFlow)}`, fontSize: 9, fill: "var(--color-chart-2)", position: "top" }} />
        <Line yAxisId="h" type="monotone" dataKey="head" name={`Head @ ${hz} Hz`} stroke="var(--color-chart-1)" strokeWidth={2} dot={false} />
        {extra.map((e) => (
          <Line
            key={e.hz}
            yAxisId="h"
            type="monotone"
            dataKey={`head_${e.hz}`}
            name={`Head @ ${e.hz} Hz`}
            stroke="var(--color-chart-1)"
            strokeOpacity={0.4}
            strokeDasharray="4 3"
            strokeWidth={1.2}
            dot={false}
          />
        ))}
        <Line yAxisId="e" type="monotone" dataKey="efficiency" name="Efficiency (%)" stroke="var(--color-chart-3)" strokeWidth={1.4} dot={false} />
        {showPower && (
          <Line yAxisId="p" type="monotone" dataKey="power" name="BHP" stroke="var(--color-chart-5)" strokeWidth={1.2} strokeDasharray="3 3" dot={false} />
        )}
        <ReferenceDot
          yAxisId="h"
          x={Math.round(well.designLiquidBpd)}
          y={Math.round(curveHeadAt(well, well.designHz, well.designLiquidBpd))}
          r={4}
          fill="var(--color-chart-3)"
          stroke="var(--color-background)"
          label={{ value: "Design point", fontSize: 9, fill: "var(--color-chart-3)", position: "right" }}
        />
        <ReferenceDot
          yAxisId="h"
          x={Math.round(actualFlow)}
          y={Math.round(actualHead)}
          r={5}
          fill="var(--color-critical)"
          stroke="var(--color-background)"
          label={{ value: "Actual point", fontSize: 9, fill: "var(--color-critical)", position: "top" }}
        />
        <Scatter yAxisId="h" data={[]} />
        {designFlow < 0 && <Area yAxisId="h" dataKey="head" />}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function TdhWaterfall({ well, hz, height = 210 }: { well: Well; hz: number; height?: number }) {
  const rate = well.liquidRateBpd * (hz / Math.max(well.hz || hz, 1));
  const b = tdhBreakdown({
    pumpSettingFt: 6200,
    pipPsi: well.pipPsi,
    whpPsi: well.whpPsi,
    rateBpd: rate,
    tubingId: 2.441,
    sg: well.fluidSg,
  });
  const data = [
    { name: "Vertical / dynamic lift", value: Math.round(b.verticalLiftFt), fill: "var(--color-chart-1)" },
    { name: "Tubing friction", value: Math.round(b.frictionFt), fill: "var(--color-chart-4)" },
    { name: "Wellhead backpressure", value: Math.round(b.wellheadFt), fill: "var(--color-chart-3)" },
    { name: "Total dynamic head", value: Math.round(b.totalFt), fill: "var(--color-chart-2)" },
  ];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 40, left: 8, bottom: 4 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" horizontal={false} />
        <XAxis type="number" {...axis} label={{ value: "Head (ft)", position: "insideBottom", offset: -2, fontSize: 9, fill: "var(--color-muted-foreground)" }} />
        <YAxis type="category" dataKey="name" {...axis} width={140} />
        <Tooltip {...tooltipStyle} formatter={(v: number) => [`${n0(v)} ft`, "Head"]} />
        <Bar dataKey="value" radius={[0, 2, 2, 0]} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MiniOperatingPoint({ well, height = 130 }: { well: Well; height?: number }) {
  const speed = well.hz > 0 ? well.hz / well.ratedHz : well.designHz / well.ratedHz;
  const pts = pumpCurve(well, well.hz > 0 ? well.hz : well.designHz, 18);
  const head = curveHeadAt(well, well.hz > 0 ? well.hz : well.designHz, well.liquidRateBpd);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={pts} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" vertical={false} />
        <XAxis dataKey="flow" {...axis} tick={{ fontSize: 9 }} />
        <YAxis {...axis} width={38} tick={{ fontSize: 9 }} />
        <Tooltip {...tooltipStyle} />
        <ReferenceArea
          x1={Math.round(well.rorMin * speed)}
          x2={Math.round(well.rorMax * speed)}
          fill="var(--color-normal)"
          fillOpacity={0.12}
        />
        <Line type="monotone" dataKey="head" stroke="var(--color-chart-1)" strokeWidth={1.6} dot={false} name="Head (ft)" />
        <ReferenceDot x={well.liquidRateBpd} y={Math.round(head)} r={4} fill="var(--color-critical)" stroke="var(--color-background)" />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SimpleBar({
  data,
  xKey,
  bars,
  height = 220,
  layout = "horizontal",
  yWidth = 46,
}: {
  data: Record<string, string | number>[];
  xKey: string;
  bars: { key: string; label: string; color: string }[];
  height?: number;
  layout?: "horizontal" | "vertical";
  yWidth?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={layout} margin={{ top: 8, right: 16, left: 4, bottom: 4 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" />
        {layout === "horizontal" ? (
          <>
            <XAxis dataKey={xKey} {...axis} />
            <YAxis {...axis} width={yWidth} />
          </>
        ) : (
          <>
            <XAxis type="number" {...axis} />
            <YAxis type="category" dataKey={xKey} {...axis} width={yWidth} />
          </>
        )}
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 10 }} />
        {bars.map((b) => (
          <Bar key={b.key} dataKey={b.key} name={b.label} fill={b.color} radius={[2, 2, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ParetoChart({
  data,
  height = 260,
}: {
  data: { mode: string; count: number; cumulativePct: number }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 60 }}>
        <CartesianGrid stroke="var(--color-grid)" strokeDasharray="2 3" vertical={false} />
        <XAxis dataKey="mode" {...axis} interval={0} angle={-32} textAnchor="end" height={70} />
        <YAxis yAxisId="c" {...axis} width={34} label={{ value: "Pulls", angle: -90, position: "insideLeft", fontSize: 9, fill: "var(--color-muted-foreground)" }} />
        <YAxis yAxisId="p" orientation="right" {...axis} width={38} domain={[0, 100]} unit="%" />
        <Tooltip {...tooltipStyle} />
        <Bar yAxisId="c" dataKey="count" name="Failures" fill="var(--color-chart-4)" radius={[2, 2, 0, 0]} />
        <Line yAxisId="p" type="monotone" dataKey="cumulativePct" name="Cumulative %" stroke="var(--color-chart-1)" strokeWidth={1.6} dot={{ r: 2 }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
