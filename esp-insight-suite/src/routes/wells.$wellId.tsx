import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useState } from "react";
import { fieldName, stateLabels, stateTone, wellById, wells } from "@/data/esp/fleet";
import { buildEvents, buildSeries, rangeConfig, stateTimeline, whatChanged, type Range } from "@/data/esp/series";
import { exceptionsForWell } from "@/data/esp/exceptions";
import { advisoriesFor } from "@/data/esp/advisor";
import { envelopePosition, healthBand, tdhBreakdown } from "@/lib/esp/calc";
import { hoursToDuration, n0, n1, n2, signed, usd } from "@/lib/esp/format";
import { MiniOperatingPoint, TrendChart, trendCatalog } from "@/components/esp/charts";
import { EspWellVisual } from "@/components/esp/EspWellVisual";
import { PressureProfile } from "@/components/esp/PressureProfile";
import { AdvisorPanel } from "@/components/esp/AdvisorPanel";
import {
  DataQualityBadge,
  KpiStrip,
  Metric,
  Note,
  PageHeader,
  Panel,
  StatusPill,
  Td,
  Th,
  ToggleRow,
  textTone,
} from "@/components/esp/ui";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/wells/$wellId")({
  loader: ({ params }) => {
    const well = wellById(params.wellId);
    if (!well) throw notFound();
    return { wellId: well.id, name: well.name, headline: well.headline };
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.wellId ?? "Well"} Monitor — ADVAIT ESP-PMM` },
      {
        name: "description",
        content: loaderData?.headline ?? "ESP well operating snapshot, state timeline, trends, operating point and recommendations.",
      },
      { property: "og:title", content: `${loaderData?.wellId ?? "Well"} ESP Monitor` },
      { property: "og:description", content: loaderData?.headline ?? "ESP well surveillance detail." },
    ],
  }),
  component: WellMonitor,
});

const tabs = ["Overview", "Trends", "Operating point", "Pressure profile", "ESP string", "Events & exceptions"] as const;
const ranges: Range[] = ["24h", "7d", "30d", "60d"];

function WellMonitor() {
  const { wellId } = Route.useParams();
  const well = wellById(wellId)!;
  const [tab, setTab] = useState<(typeof tabs)[number]>("Overview");
  const [range, setRange] = useState<Range>("7d");
  const [tagKeys, setTagKeys] = useState<string[]>(["amps", "pip"]);

  const series = buildSeries(well, range);
  const events = buildEvents(well, range);
  const timeline = stateTimeline(well);
  const changes = whatChanged(well);
  const env = envelopePosition(well);
  const exs = exceptionsForWell(well.id);
  const advisories = advisoriesFor(well);
  const tdh = tdhBreakdown({
    pumpSettingFt: 6200,
    pipPsi: well.pipPsi,
    whpPsi: well.whpPsi,
    rateBpd: well.liquidRateBpd,
    tubingId: 2.441,
    sg: well.fluidSg,
  });
  const idx = wells.findIndex((w) => w.id === well.id);
  const prev = wells[(idx - 1 + wells.length) % wells.length]!;
  const next = wells[(idx + 1) % wells.length]!;

  const activeTags = trendCatalog.filter((t) => tagKeys.includes(t.key as string)).slice(0, 2);
  const toggleTag = (k: string) =>
    setTagKeys((cur) => (cur.includes(k) ? cur.filter((c) => c !== k) : [...cur.slice(-1), k]));

  const rateDeltaPct = ((well.liquidRateBpd - well.designLiquidBpd) / well.designLiquidBpd) * 100;

  return (
    <div className="space-y-3">
      <PageHeader
        title={`${well.id} — ${fieldName(well.fieldId)} · ${well.padName}`}
        description={well.headline}
        meta={
          <>
            <StatusPill tone={stateTone[well.state]}>{stateLabels[well.state]}</StatusPill>
            <StatusPill tone="muted">{fieldName(well.fieldId)} · {well.padName}</StatusPill>
            <StatusPill tone="muted">{well.oem} {well.pumpModel} · {well.stages} stages</StatusPill>
            <DataQualityBadge quality={well.dataQuality} />
            <StatusPill tone="info">Last event: {well.lastEvent} ({well.lastEventAt})</StatusPill>
          </>
        }
        actions={
          <div className="flex items-center gap-2">
            <Link to="/wells/$wellId" params={{ wellId: prev.id }} className="rounded border border-border bg-card px-2 py-1 text-[11px] hover:bg-accent">
              ← {prev.id}
            </Link>
            <Link to="/wells/$wellId" params={{ wellId: next.id }} className="rounded border border-border bg-card px-2 py-1 text-[11px] hover:bg-accent">
              {next.id} →
            </Link>
            <Link to="/engineering/workbench" search={{ well: well.id }} className="rounded border border-primary/50 bg-primary/15 px-2 py-1 text-[11px] font-semibold text-primary hover:bg-primary/25">
              Open in Engineering Workbench
            </Link>
            <Link to="/engineering/installations" className="rounded border border-border bg-card px-2 py-1 text-[11px] hover:bg-accent">
              Governed asset definition
            </Link>
          </div>
        }
      />

      <KpiStrip>
        <Metric label="ESP health index" value={well.healthIndex} sub={`Band: ${healthBand(well.healthIndex)}`} tone={healthBand(well.healthIndex)} />
        <Metric label="Frequency" value={well.hz ? n1(well.hz) : "0.0"} unit="Hz" sub={`Design ${n1(well.designHz)} Hz`} />
        <Metric
          label="Motor load"
          value={well.hz ? `${well.motorLoadPct}` : "—"}
          unit="%"
          sub={`${n1(well.amps)} A of ${well.motorRatingA} A rated`}
          tone={well.motorLoadPct > 75 ? "critical" : well.motorLoadPct > 70 ? "watch" : "normal"}
        />
        <Metric
          label="Motor temperature"
          value={well.motorTempF ? well.motorTempF : "no data"}
          unit={well.motorTempF ? "degF" : ""}
          sub={`Limit ${well.motorTempLimitF} degF`}
          tone={well.motorTempF > well.motorTempLimitF - 12 ? "warning" : "normal"}
        />
        <Metric label="PIP / PDP" value={well.pipPsi ? `${n0(well.pipPsi)} / ${n0(well.pdpPsi)}` : "no data"} unit="psi" sub={`Design ${n0(well.designPipPsi)} / ${n0(well.designPdpPsi)}`} />
        <Metric label="Liquid / oil" value={`${n0(well.liquidRateBpd)} / ${n0(well.oilRateBopd)}`} unit="bpd" sub={`${signed(rateDeltaPct, 1)}% vs design liquid`} tone={Math.abs(rateDeltaPct) > 10 ? "warning" : "normal"} />
        <Metric label="Deferment" value={well.deferredBopd ? n0(well.deferredBopd) : "0"} unit="bopd" sub={usd(well.deferredBopd * 68) + "/day"} tone={well.deferredBopd ? "warning" : "normal"} />
      </KpiStrip>

      <div className="flex flex-wrap items-center gap-2 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              "-mb-px border-b-2 px-2.5 py-1.5 text-[12px]",
              tab === t ? "border-primary font-semibold text-foreground" : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-3">
          {tab === "Overview" && (
            <>
              <div className="grid gap-3 lg:grid-cols-[minmax(0,400px)_minmax(0,1fr)]">
                <Panel
                  title="ESP system visualization"
                  subtitle="Live simulated values bound to the string — hover or tab a marker for design comparison"
                  bodyClassName="p-2"
                >
                  <EspWellVisual well={well} variant="full" />
                </Panel>
                <Panel title="Operating state timeline" subtitle="Last 24 hours — how the well arrived at its current state">
                  <div className="space-y-2">
                    <div className="flex h-7 w-full overflow-hidden rounded border border-border">
                      {timeline.map((s, i) => (
                        <div
                          key={i}
                          title={`${s.state} · ${s.fromH.toFixed(1)} h → ${s.toH.toFixed(1)} h`}
                          style={{ width: `${((s.toH - s.fromH) / 24) * 100}%` }}
                          className={cn(
                            "flex items-center justify-center overflow-hidden text-[9px] whitespace-nowrap",
                            s.tone === "normal" && "bg-normal/25 text-normal",
                            s.tone === "watch" && "bg-watch/25 text-watch",
                            s.tone === "warning" && "bg-warning/30 text-warning",
                            s.tone === "critical" && "bg-critical/35 text-critical",
                            s.tone === "stopped" && "bg-stopped/30 text-stopped",
                            s.tone === "info" && "bg-info/25 text-info",
                          )}
                        >
                          {(s.toH - s.fromH) / 24 > 0.12 ? s.state : ""}
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>-24 h</span>
                      <span>-12 h</span>
                      <span>now</span>
                    </div>
                    <table className="w-full border-collapse">
                      <tbody>
                        {timeline.slice().reverse().map((s, i) => (
                          <tr key={i}>
                            <Td>
                              <StatusPill tone={s.tone}>{s.state}</StatusPill>
                            </Td>
                            <Td align="right" mono className="text-muted-foreground">
                              {s.fromH.toFixed(1)} h → {s.toH === 0 ? "now" : `${s.toH.toFixed(1)} h`}
                            </Td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              </div>

              <div className="grid gap-3 lg:grid-cols-2">
                <Panel title="What changed" subtitle="Signals that moved before the current state — the operational story">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <Th>Signal</Th>
                        <Th align="right">From</Th>
                        <Th align="right">To</Th>
                        <Th align="right">Window</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {changes.map((c, i) => (
                        <tr key={i}>
                          <Td>
                            <StatusPill tone={c.tone} dot={false}>{c.label}</StatusPill>
                          </Td>
                          <Td align="right" mono className="text-muted-foreground">{c.from}</Td>
                          <Td align="right" mono className={textTone[c.tone]}>{c.to}</Td>
                          <Td align="right" className="text-muted-foreground">{c.window}</Td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Panel>
              </div>

              <div className="grid gap-3 lg:grid-cols-3">
                <Panel title="Operating envelope" subtitle="Actual rate vs recommended operating range">
                  <div className="space-y-2">
                    <div className="relative h-9 rounded border border-border bg-card">
                      <div
                        className="absolute inset-y-0 bg-normal/25"
                        style={{
                          left: `${(well.rorMin / (well.rorMax * 1.35)) * 100}%`,
                          width: `${((well.rorMax - well.rorMin) / (well.rorMax * 1.35)) * 100}%`,
                        }}
                      />
                      <div className="absolute inset-y-0 w-px bg-info" style={{ left: `${(well.bepRate / (well.rorMax * 1.35)) * 100}%` }} />
                      <div
                        className={cn("absolute top-1 bottom-1 w-1 rounded", env.inside ? "bg-normal" : "bg-warning")}
                        style={{ left: `${Math.min((well.liquidRateBpd / (well.rorMax * 1.35)) * 100, 99)}%` }}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                      <span>ROR min <span className="num text-foreground">{n0(well.rorMin)}</span> bpd</span>
                      <span className="text-right">ROR max <span className="num text-foreground">{n0(well.rorMax)}</span> bpd</span>
                      <span>BEP <span className="num text-foreground">{n0(well.bepRate)}</span> bpd</span>
                      <span className="text-right">Q/Q<sub>BEP</sub> <span className="num text-foreground">{n2(env.bepRatio)}</span></span>
                    </div>
                    <Note tone={env.inside ? "normal" : "warning"}>
                      {env.inside
                        ? `Inside ROR with ${n0(env.lowMarginBpd)} bpd margin to downthrust and ${n0(env.highMarginBpd)} bpd to upthrust.`
                        : env.lowMarginBpd < 0
                          ? `Left of ROR by ${n0(Math.abs(env.lowMarginBpd))} bpd — downthrust wear exposure on stages and thrust bearing.`
                          : `Right of ROR by ${n0(Math.abs(env.highMarginBpd))} bpd — upthrust and motor loading exposure.`}
                    </Note>
                  </div>
                </Panel>

                <Panel title="Operating point vs pump curve" subtitle={`${well.pumpModel} at ${n1(well.hz || well.designHz)} Hz`} bodyClassName="p-2">
                  <MiniOperatingPoint well={well} height={170} />
                </Panel>

                <Panel title="Total dynamic head" subtitle="Deterministic engineering calculation">
                  <table className="w-full border-collapse">
                    <tbody>
                      {[
                        ["Vertical / dynamic lift", tdh.verticalLiftFt],
                        ["Tubing friction", tdh.frictionFt],
                        ["Wellhead backpressure", tdh.wellheadFt],
                        ["Total dynamic head", tdh.totalFt],
                      ].map(([label, v], i) => (
                        <tr key={i} className={i === 3 ? "font-semibold" : ""}>
                          <Td>{label as string}</Td>
                          <Td align="right" mono>{n0(v as number)} ft</Td>
                        </tr>
                      ))}
                      <tr>
                        <Td className="text-muted-foreground">Design TDH</Td>
                        <Td align="right" mono className="text-muted-foreground">{n0(well.designTdhFt)} ft</Td>
                      </tr>
                      <tr>
                        <Td className="text-muted-foreground">Head per stage (actual)</Td>
                        <Td align="right" mono>{n1(tdh.totalFt / well.stages)} ft</Td>
                      </tr>
                      <tr>
                        <Td className="text-muted-foreground">Head per stage (design)</Td>
                        <Td align="right" mono className="text-muted-foreground">{n1(well.headPerStage)} ft</Td>
                      </tr>
                    </tbody>
                  </table>
                </Panel>
              </div>
            </>
          )}

          {tab === "Trends" && (
            <Panel
              title="Multi-tag trend"
              subtitle={`${rangeConfig[range].label} · event bands mark trips, setpoint changes and degradation onset`}
              actions={<ToggleRow options={ranges} value={range} onChange={setRange} />}
              bodyClassName="p-2"
            >
              <div className="mb-2 flex flex-wrap gap-1">
                {trendCatalog.map((t) => (
                  <button
                    key={t.key as string}
                    type="button"
                    onClick={() => toggleTag(t.key as string)}
                    className={cn(
                      "rounded border px-1.5 py-0.5 text-[10px]",
                      tagKeys.includes(t.key as string)
                        ? "border-primary/60 bg-primary/15 text-foreground"
                        : "border-border bg-card text-muted-foreground hover:bg-accent",
                    )}
                  >
                    {t.label} ({t.unit})
                  </button>
                ))}
              </div>
              <TrendChart data={series} events={events} tags={activeTags.length ? activeTags : trendCatalog.slice(0, 2)} height={300} />
              <div className="mt-2 grid gap-2 lg:grid-cols-2">
                <TrendChart data={series} events={events} tags={[trendCatalog[2]!, trendCatalog[3]!]} height={200} />
                <TrendChart data={series} events={events} tags={[trendCatalog[6]!, trendCatalog[5]!]} height={200} />
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">
                Signals arrive through OTConnex from SCADA, the VSD and the downhole gauge, then are normalised against the Asset ConneX ESP tag template so every well presents the same measurement set.
              </p>
            </Panel>
          )}

          {tab === "Operating point" && (
            <Panel title="Operating point detail" subtitle="Actual vs design at current frequency" bodyClassName="p-2">
              <MiniOperatingPoint well={well} height={280} />
              <table className="mt-2 w-full border-collapse">
                <thead>
                  <tr>
                    <Th>Parameter</Th>
                    <Th align="right">Actual</Th>
                    <Th align="right">Design</Th>
                    <Th align="right">Variance</Th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Frequency (Hz)", well.hz, well.designHz],
                    ["Liquid rate (bpd)", well.liquidRateBpd, well.designLiquidBpd],
                    ["Oil rate (bopd)", well.oilRateBopd, well.designOilBopd],
                    ["PIP (psi)", well.pipPsi, well.designPipPsi],
                    ["PDP (psi)", well.pdpPsi, well.designPdpPsi],
                    ["Motor current (A)", well.amps, well.designAmps],
                    ["TDH (ft)", Math.round(tdh.totalFt), well.designTdhFt],
                  ].map(([label, a, d], i) => {
                    const delta = ((Number(a) - Number(d)) / Number(d)) * 100;
                    return (
                      <tr key={i}>
                        <Td>{label as string}</Td>
                        <Td align="right" mono>{n1(Number(a))}</Td>
                        <Td align="right" mono className="text-muted-foreground">{n1(Number(d))}</Td>
                        <Td align="right" mono className={Math.abs(delta) > 10 ? "text-warning" : "text-muted-foreground"}>
                          {signed(delta, 1)}%
                        </Td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === "Pressure profile" && (
            <Panel title="Pressure profile" subtitle="Reservoir → Pwf → PIP → pump ΔP → PDP → wellhead">
              <PressureProfile well={well} />
            </Panel>
          )}

          {tab === "ESP string" && (
            <div className="grid gap-3 lg:grid-cols-[300px_minmax(0,1fr)]">
              <Panel title="ESP string visualization" subtitle="Data-linked status callouts" bodyClassName="p-2">
                <EspWellVisual well={well} variant="full" />
              </Panel>
              <Panel title="Component registry" subtitle="ESP is a system, not only a pump — configuration inherited from Asset ConneX" bodyClassName="p-0">
                <div className="overflow-auto panel-scroll" style={{ maxHeight: 520 }}>
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <Th>Group</Th>
                        <Th>Component</Th>
                        <Th>Make / model</Th>
                        <Th>Specification</Th>
                        <Th align="right">Tags</Th>
                        <Th>Source</Th>
                        <Th>Status</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {well.components.map((c) => (
                        <tr key={c.id} className="hover:bg-accent/40">
                          <Td className="text-muted-foreground">{c.group}</Td>
                          <Td>{c.type}</Td>
                          <Td className="text-muted-foreground">{c.make} {c.model}</Td>
                          <Td className="max-w-[260px] truncate">{c.spec}</Td>
                          <Td align="right" mono>{c.tagCount}</Td>
                          <Td>
                            <StatusPill tone="info" dot={false}>{c.source}</StatusPill>
                          </Td>
                          <Td>
                            <DataQualityBadge quality={c.status} />
                          </Td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>
            </div>
          )}

          {tab === "Events & exceptions" && (
            <Panel title="Open exceptions for this well" bodyClassName="p-3" subtitle="Each item carries evidence, verification steps and a recommended action">
              <div className="space-y-3">
                {exs.length === 0 && <Note>No open exceptions. Well is inside envelope with stable electrical and thermal signals.</Note>}
                {exs.map((e) => (
                  <div key={e.id} className="rounded border border-border bg-card p-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill tone={e.severity === "critical" ? "critical" : e.severity === "warning" ? "warning" : e.severity === "opportunity" ? "opportunity" : "watch"}>
                        {e.severity}
                      </StatusPill>
                      <span className="text-[12px] font-semibold">{e.category}</span>
                      <span className="num ml-auto text-[11px] text-muted-foreground">
                        {e.id} · age {hoursToDuration(e.durationH)} · confidence {(e.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="mt-1.5 text-[12px]">{e.observation}</p>
                    <div className="mt-2 grid gap-2 lg:grid-cols-3">
                      <div>
                        <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Evidence</div>
                        <ul className="mt-1 space-y-0.5 text-[11px]">
                          {e.evidence.map((x, i) => <li key={i}>· {x}</li>)}
                        </ul>
                      </div>
                      <div>
                        <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Verify</div>
                        <ul className="mt-1 space-y-0.5 text-[11px]">
                          {e.verify.map((x, i) => <li key={i}>· {x}</li>)}
                        </ul>
                      </div>
                      <div>
                        <div className="text-[10px] tracking-wider text-muted-foreground uppercase">Recommended action</div>
                        <ul className="mt-1 space-y-0.5 text-[11px]">
                          {e.recommendedAction.map((x, i) => <li key={i}>· {x}</li>)}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>

        <div className="space-y-3">
          <AdvisorPanel well={well} />
          <Panel title="Advisor items" subtitle="Evidence-backed, human-approved" bodyClassName="p-2">
            <div className="space-y-2">
              {advisories.map((a) => (
                <div key={a.id} className="rounded border border-border bg-card p-2">
                  <div className="flex items-center justify-between">
                    <StatusPill tone={a.kind === "Optimization" ? "opportunity" : a.kind === "Predictive" ? "watch" : "info"}>{a.kind}</StatusPill>
                    <span className="num text-[10px] text-muted-foreground">{(a.confidence * 100).toFixed(0)}% conf.</span>
                  </div>
                  <p className="mt-1 text-[11px]">{a.assessment}</p>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
