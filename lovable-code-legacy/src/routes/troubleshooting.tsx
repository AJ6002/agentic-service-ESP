import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { troubleshootingCases, tripCodes } from "@/data/esp/troubleshooting";
import { wellById } from "@/data/esp/fleet";
import { buildEvents, buildSeries } from "@/data/esp/series";
import { TrendChart, trendCatalog } from "@/components/esp/charts";
import { Note, PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { EspWellVisual, type EspSubsystem } from "@/components/esp/EspWellVisual";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/troubleshooting")({
  head: () => ({
    meta: [
      { title: "Troubleshooting Assistant — ESP diagnostics | ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "Direction-of-change ESP diagnostics: signature tables for flow, current, intake and discharge pressure with ranked causes, verification steps and actions.",
      },
      { property: "og:title", content: "ESP Troubleshooting Assistant" },
      { property: "og:description", content: "Pattern-based ESP diagnostics with ranked causes and verification steps." },
    ],
  }),
  component: Troubleshooting,
});

const dirGlyph = { up: "▲", down: "▼", flat: "▬", erratic: "∿" } as const;
const dirTone = { up: "text-warning", down: "text-critical", flat: "text-muted-foreground", erratic: "text-watch" } as const;

/** Maps a diagnostic case to the ESP subsystem it implicates (presentation only). */
function caseSubsystem(title: string, tripCode?: string): EspSubsystem {
  const t = `${title} ${tripCode ?? ""}`.toLowerCase();
  if (t.includes("gas") || t.includes("slug") || t.includes("intake")) return "intake";
  if (t.includes("motor") || t.includes("overload") || t.includes("temperature") || t.includes("underload")) return "motor";
  if (t.includes("cable") || t.includes("ground") || t.includes("electric") || t.includes("power") || t.includes("trip")) return "cable";
  if (t.includes("gauge") || t.includes("comm") || t.includes("telemetry")) return "gauge";
  if (t.includes("shaft") || t.includes("wear") || t.includes("pump") || t.includes("vibration")) return "pump";
  if (t.includes("tubing") || t.includes("leak") || t.includes("recirc")) return "tubing";
  if (t.includes("choke") || t.includes("wellhead") || t.includes("backpressure")) return "wellhead";
  if (t.includes("perforation") || t.includes("inflow") || t.includes("reservoir")) return "perfs";
  return "pump";
}

function Troubleshooting() {
  const [caseId, setCaseId] = useState(troubleshootingCases[0]!.id);
  const tc = troubleshootingCases.find((c) => c.id === caseId)!;
  const well = wellById(tc.wellId);
  const series = well ? buildSeries(well, "7d") : [];
  const events = well ? buildEvents(well, "7d") : [];

  return (
    <div className="space-y-3">
      <PageHeader
        title="Troubleshooting Assistant"
        description="ESP problems rarely show up as a single tag excursion. This workspace reads the pattern across flow, motor current, intake and discharge pressure, temperature and wellhead pressure, then ranks the causes that fit the whole signature."
        meta={
          <>
            <StatusPill tone="info">Direction-of-change library</StatusPill>
            <StatusPill tone="muted">Confidence values are demo heuristics for review, not automated decisions</StatusPill>
          </>
        }
      />

      <div className="grid gap-3 xl:grid-cols-[260px_minmax(0,1fr)]">
        <Panel title="Signature library" bodyClassName="p-0">
          <div className="divide-y divide-border">
            {troubleshootingCases.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCaseId(c.id)}
                className={cn(
                  "block w-full px-2.5 py-2 text-left hover:bg-accent/40",
                  c.id === caseId && "bg-primary/10",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="num text-[10px] text-muted-foreground">{c.id}</span>
                  <span className="num text-[10px] text-primary">{c.wellId}</span>
                </div>
                <div className="mt-0.5 text-[12px] font-medium">{c.title}</div>
                {c.tripCode && <div className="mt-0.5 num text-[10px] text-warning">{c.tripCode}</div>}
              </button>
            ))}
          </div>
        </Panel>

        <div className="space-y-3">
          <Panel
            title={tc.title}
            subtitle={tc.symptom}
            actions={
              well && (
                <Link to="/wells/$wellId" params={{ wellId: well.id }} className="text-[11px] text-primary hover:underline">
                  Open {well.id} →
                </Link>
              )
            }
          >
            <div className="grid gap-3 lg:grid-cols-2">
              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Diagnostic signature</div>
                <table className="mt-1 w-full border-collapse">
                  <thead>
                    <tr>
                      <Th>Signal</Th>
                      <Th>Direction</Th>
                      <Th>Expected behaviour</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {tc.signature.map((s, i) => (
                      <tr key={i}>
                        <Td>{s.tag}</Td>
                        <Td className={dirTone[s.direction]}>
                          {dirGlyph[s.direction]} {s.direction}
                        </Td>
                        <Td className="text-muted-foreground">{s.note}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Ranked causes</div>
                <div className="mt-1 space-y-1.5">
                  {tc.causes.map((c, i) => (
                    <div key={i} className="rounded border border-border bg-card p-2">
                      <div className="flex items-baseline justify-between">
                        <span className="text-[12px] font-medium">{c.cause}</span>
                        <span className="num text-[11px] text-muted-foreground">{(c.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="mt-1 h-1 rounded bg-background">
                        <div className="h-1 rounded bg-chart-1" style={{ width: `${c.confidence * 100}%` }} />
                      </div>
                      <p className="mt-1 text-[11px] text-muted-foreground">{c.rationale}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Verification sequence</div>
                <ul className="mt-1 space-y-1 text-[11px]">
                  {tc.verify.map((v, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="num text-muted-foreground">{i + 1}.</span>
                      <span>{v}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Recommended actions</div>
                <ul className="mt-1 space-y-1 text-[11px]">
                  {tc.actions.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-primary">→</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
                <Note>
                  Actions are advisory. Nothing in ESP-PMM writes to the drive; operations retains authority for every setpoint or restart decision.
                </Note>
              </div>
            </div>
          </Panel>

          {well && (
            <Panel
              title={`Implicated subsystem — ${well.id}`}
              subtitle="The ESP string with the subsystem in focus for this signature highlighted"
              bodyClassName="p-2"
            >
              <div className="grid gap-2 lg:grid-cols-[220px_minmax(0,1fr)]">
                <EspWellVisual well={well} variant="compact" highlight={caseSubsystem(tc.title, tc.tripCode)} />
                <div className="space-y-1 text-[11px] text-muted-foreground">
                  <div className="text-[10px] tracking-wider uppercase">Focus</div>
                  <div className="text-[12px] font-medium text-foreground">{caseSubsystem(tc.title, tc.tripCode)}</div>
                  <p>
                    Markers stay bound to the same simulated values used elsewhere in the demo. Hover or tab a marker to compare current and design
                    values for that node. Visualization only — no drive command is issued from this screen.
                  </p>
                </div>
              </div>
            </Panel>
          )}

          {well && (
            <Panel title={`Supporting evidence — ${well.id}`} subtitle="7-day window with event bands around the signature onset" bodyClassName="p-2">
              <div className="grid gap-2 lg:grid-cols-2">
                <TrendChart data={series} events={events} tags={[trendCatalog[1]!, trendCatalog[5]!]} height={200} />
                <TrendChart data={series} events={events} tags={[trendCatalog[2]!, trendCatalog[3]!]} height={200} />
              </div>
            </Panel>
          )}

          <Panel title="VSD trip code reference" subtitle="Common drive faults, typical causes and first response" bodyClassName="p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Code</Th>
                  <Th>Fault</Th>
                  <Th>Typical cause</Th>
                  <Th>First response</Th>
                </tr>
              </thead>
              <tbody>
                {tripCodes.map((t) => (
                  <tr key={t.code} className="hover:bg-accent/40">
                    <Td mono className="text-warning">{t.code}</Td>
                    <Td>{t.label}</Td>
                    <Td className="text-muted-foreground">{t.typicalCause}</Td>
                    <Td>{t.action}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      </div>
    </div>
  );
}
