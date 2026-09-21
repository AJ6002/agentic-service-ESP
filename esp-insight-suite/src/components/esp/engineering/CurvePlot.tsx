import type { CurvePoint, PumpModel } from "@/lib/esp-catalog/queries.functions";

/**
 * Plots ONLY digitised curve points that exist in the governed catalog.
 * Never synthesises a curve — callers must handle the empty case.
 */
export function CurvePlot({
  model,
  points,
  height = 230,
}: {
  model: PumpModel;
  points: CurvePoint[];
  height?: number;
}) {
  if (points.length === 0) return null;

  const hzGroups = [...new Set(points.map((p) => Number(p.reference_hz)))].sort((a, b) => b - a);
  const W = 520;
  const H = height;
  const pad = { l: 42, r: 46, t: 12, b: 26 };
  const maxFlow = Math.max(...points.map((p) => Number(p.flow_bpd))) * 1.05;
  const maxHead = Math.max(...points.map((p) => Number(p.head_ft_per_stage ?? 0))) * 1.15;
  const maxHp = Math.max(...points.map((p) => Number(p.power_hp_per_stage ?? 0))) * 1.3 || 1;

  const x = (f: number) => pad.l + (f / maxFlow) * (W - pad.l - pad.r);
  const yHead = (h: number) => H - pad.b - (h / maxHead) * (H - pad.t - pad.b);
  const yHp = (p: number) => H - pad.b - (p / maxHp) * (H - pad.t - pad.b);

  const colors = ["hsl(var(--chart-1, 200 90% 60%))", "hsl(var(--chart-2, 45 90% 60%))"];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`${model.model} pump curve`}>
      <rect x={pad.l} y={pad.t} width={W - pad.l - pad.r} height={H - pad.t - pad.b} className="fill-card stroke-border" strokeWidth={0.5} />

      {/* ROR band */}
      {model.ror_min_bpd != null && model.ror_max_bpd != null && (
        <rect
          x={x(Number(model.ror_min_bpd))}
          y={pad.t}
          width={Math.max(0, x(Number(model.ror_max_bpd)) - x(Number(model.ror_min_bpd)))}
          height={H - pad.t - pad.b}
          className="fill-normal/10 stroke-normal/40"
          strokeDasharray="2 2"
          strokeWidth={0.6}
        />
      )}

      {hzGroups.map((hz, gi) => {
        const g = points.filter((p) => Number(p.reference_hz) === hz).sort((a, b) => a.point_sequence - b.point_sequence);
        const head = g.filter((p) => p.head_ft_per_stage != null).map((p) => `${x(Number(p.flow_bpd))},${yHead(Number(p.head_ft_per_stage))}`).join(" ");
        const hp = g.filter((p) => p.power_hp_per_stage != null).map((p) => `${x(Number(p.flow_bpd))},${yHp(Number(p.power_hp_per_stage))}`).join(" ");
        return (
          <g key={hz}>
            <polyline points={head} fill="none" stroke={colors[gi % colors.length]} strokeWidth={1.6} />
            <polyline points={hp} fill="none" stroke={colors[gi % colors.length]} strokeWidth={1} strokeDasharray="4 3" opacity={0.75} />
            <text x={W - pad.r + 4} y={pad.t + 10 + gi * 11} className="fill-muted-foreground text-[8px]">{hz} Hz</text>
          </g>
        );
      })}

      {/* BEP marker */}
      {model.bep_flow_bpd != null && model.bep_head_ft_per_stage != null && (
        <g>
          <circle cx={x(Number(model.bep_flow_bpd))} cy={yHead(Number(model.bep_head_ft_per_stage))} r={3.5} className="fill-warning" />
          <text x={x(Number(model.bep_flow_bpd)) + 5} y={yHead(Number(model.bep_head_ft_per_stage)) - 5} className="fill-warning text-[8px]">BEP</text>
        </g>
      )}

      <text x={pad.l} y={H - 8} className="fill-muted-foreground text-[8px]">0</text>
      <text x={W - pad.r - 40} y={H - 8} className="fill-muted-foreground text-[8px]">{Math.round(maxFlow).toLocaleString()} BPD</text>
      <text x={4} y={pad.t + 8} className="fill-muted-foreground text-[8px]">ft/stage</text>
      <text x={4} y={H - pad.b} className="fill-muted-foreground text-[8px]">0</text>
    </svg>
  );
}
