import { pressureProfile } from "@/lib/esp/calc";
import type { Well } from "@/data/esp/types";
import { n0 } from "@/lib/esp/format";

/**
 * Pressure-gradient visualisation: reservoir -> Pwf -> PIP -> pump ΔP -> PDP -> wellhead.
 * Drawn with SVG primitives so it can be annotated like an engineering plot.
 */
export function PressureProfile({ well }: { well: Well }) {
  const nodes = pressureProfile(well);
  const maxPsi = Math.max(...nodes.map((n) => n.psi), 100) * 1.12;
  const maxDepth = Math.max(...nodes.map((n) => n.depthFt), 1000);

  const W = 560;
  const H = 300;
  const padL = 54;
  const padR = 150;
  const padT = 18;
  const padB = 34;

  const x = (psi: number) => padL + (psi / maxPsi) * (W - padL - padR);
  const y = (depth: number) => padT + (depth / maxDepth) * (H - padT - padB);

  const order = [...nodes].sort((a, b) => b.depthFt - a.depthFt);
  const path = order.map((n, i) => `${i === 0 ? "M" : "L"}${x(n.psi)} ${y(n.depthFt)}`).join(" ");
  const pumpDp = well.pdpPsi - well.pipPsi;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Pressure gradient profile for ${well.id}`}>
      {[0, 0.25, 0.5, 0.75, 1].map((f) => (
        <g key={f}>
          <line x1={x(maxPsi * f)} y1={padT} x2={x(maxPsi * f)} y2={H - padB} stroke="var(--color-grid)" strokeDasharray="2 3" />
          <text x={x(maxPsi * f)} y={H - padB + 12} fontSize="8.5" textAnchor="middle" fill="var(--color-muted-foreground)">
            {n0(maxPsi * f)}
          </text>
        </g>
      ))}
      <text x={(W - padR) / 2} y={H - 6} fontSize="9" textAnchor="middle" fill="var(--color-muted-foreground)">
        Pressure (psi)
      </text>

      {[0, 0.25, 0.5, 0.75, 1].map((f) => (
        <g key={`d${f}`}>
          <line x1={padL} y1={y(maxDepth * f)} x2={W - padR} y2={y(maxDepth * f)} stroke="var(--color-grid)" strokeDasharray="2 3" />
          <text x={padL - 6} y={y(maxDepth * f) + 3} fontSize="8.5" textAnchor="end" fill="var(--color-muted-foreground)">
            {n0(maxDepth * f)}
          </text>
        </g>
      ))}
      <text x={12} y={padT + 8} fontSize="9" fill="var(--color-muted-foreground)">
        Depth (ft)
      </text>

      {/* pump ΔP band */}
      <rect
        x={x(well.pipPsi)}
        y={y(6260)}
        width={Math.max(x(well.pdpPsi) - x(well.pipPsi), 1)}
        height={y(6260) - y(6140) || 12}
        fill="var(--color-primary)"
        opacity="0.22"
      />
      <text x={x(well.pipPsi) + 4} y={y(6120)} fontSize="8.5" fill="var(--color-primary)">
        Pump ΔP {n0(pumpDp)} psi ({well.stages} stages)
      </text>

      <path d={path} fill="none" stroke="var(--color-chart-1)" strokeWidth="1.8" />

      {(() => {
        // Stagger callout labels so closely spaced nodes (PIP / PDP) stay readable.
        const sorted = [...nodes].sort((a, b) => a.depthFt - b.depthFt);
        let lastY = -100;
        return sorted.map((n) => {
          const labelY = Math.max(y(n.depthFt), lastY + 24);
          lastY = labelY;
          return (
            <g key={n.label}>
              <circle cx={x(n.psi)} cy={y(n.depthFt)} r="4" fill="var(--color-chart-1)" stroke="var(--color-background)" />
              <text x={W - padR + 8} y={labelY - 2} fontSize="9" fill="var(--color-foreground)">
                {n.label}
              </text>
              <text x={W - padR + 8} y={labelY + 9} fontSize="8.5" fill="var(--color-muted-foreground)">
                {n0(n.psi)} psi · {n.detail.slice(0, 34)}
              </text>
              <polyline
                points={`${x(n.psi)},${y(n.depthFt)} ${W - padR - 8},${y(n.depthFt)} ${W - padR + 4},${labelY - 5}`}
                fill="none"
                stroke="var(--color-border)"
                strokeDasharray="2 2"
              />
            </g>
          );
        });
      })()}

    </svg>
  );
}
