import { Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { fieldName, stateLabels, stateTone, wells as allWells } from "@/data/esp/fleet";
import { envelopePosition, healthBand } from "@/lib/esp/calc";
import { n0, n1 } from "@/lib/esp/format";
import type { Well } from "@/data/esp/types";
import { SortHeader, StatusPill, Td, Th, textTone } from "./ui";
import { EspStatusGlyph } from "./EspWellVisual";
import { cn } from "@/lib/utils";

type SortField =
  | "id"
  | "field"
  | "state"
  | "health"
  | "hz"
  | "load"
  | "temp"
  | "pip"
  | "pdp"
  | "rate"
  | "oil"
  | "runlife"
  | "deferred";

const stateGroups = [
  "All states",
  "Needs attention",
  "Normal",
  "Outside ROR",
  "Gas interference",
  "Pump wear",
  "Motor / thermal",
  "VSD trip",
  "Data quality",
  "Stopped",
] as const;

function matchesGroup(w: Well, group: (typeof stateGroups)[number]) {
  switch (group) {
    case "All states":
      return true;
    case "Needs attention":
      return w.state !== "normal" && w.state !== "stopped-planned";
    case "Normal":
      return w.state === "normal";
    case "Outside ROR":
      return w.state === "outside-ror-low" || w.state === "outside-ror-high";
    case "Gas interference":
      return w.state === "gas-interference";
    case "Pump wear":
      return w.state === "pump-wear" || w.state === "vibration-warning";
    case "Motor / thermal":
      return w.state === "motor-overload" || w.state === "high-motor-temp";
    case "VSD trip":
      return w.state === "vsd-trip";
    case "Data quality":
      return w.state === "gauge-comms";
    case "Stopped":
      return w.hz === 0;
    default:
      return true;
  }
}

export function FleetTable({
  wells = allWells,
  maxHeight = "calc(100vh - 330px)",
  compact = false,
}: {
  wells?: Well[];
  maxHeight?: string;
  compact?: boolean;
}) {
  const [field, setField] = useState("all");
  const [group, setGroup] = useState<(typeof stateGroups)[number]>("All states");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<{ field: SortField; dir: "asc" | "desc" }>({ field: "health", dir: "asc" });

  const rows = useMemo(() => {
    const val = (w: Well): number | string => {
      switch (sort.field) {
        case "id":
          return w.id;
        case "field":
          return w.fieldId;
        case "state":
          return stateLabels[w.state];
        case "health":
          return w.healthIndex;
        case "hz":
          return w.hz;
        case "load":
          return w.motorLoadPct;
        case "temp":
          return w.motorTempF;
        case "pip":
          return w.pipPsi;
        case "pdp":
          return w.pdpPsi;
        case "rate":
          return w.liquidRateBpd;
        case "oil":
          return w.oilRateBopd;
        case "runlife":
          return w.runLifeDays;
        case "deferred":
          return w.deferredBopd;
      }
    };
    return wells
      .filter((w) => (field === "all" ? true : w.fieldId === field))
      .filter((w) => matchesGroup(w, group))
      .filter((w) => (q ? `${w.id} ${w.padName} ${w.oem} ${w.pumpModel}`.toLowerCase().includes(q.toLowerCase()) : true))
      .sort((a, b) => {
        const av = val(a);
        const bv = val(b);
        const cmp = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
        return sort.dir === "asc" ? cmp : -cmp;
      });
  }, [wells, field, group, q, sort]);

  const onSort = (f: SortField) =>
    setSort((s) => ({ field: f, dir: s.field === f && s.dir === "asc" ? "desc" : "asc" }));

  return (
    <div className="flex min-h-0 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-border bg-panel-header px-2 py-1.5">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter well, pad, pump…"
          className="w-44 rounded border border-border bg-card px-2 py-1 text-[11px] text-foreground placeholder:text-muted-foreground"
        />
        <select
          value={field}
          onChange={(e) => setField(e.target.value)}
          className="rounded border border-border bg-card px-1.5 py-1 text-[11px]"
        >
          <option value="all">All fields</option>
          <option value="NRD">Nardah North</option>
          <option value="KLS">Kalisto West</option>
          <option value="TMR">Tamrin Deep</option>
        </select>
        <select
          value={group}
          onChange={(e) => setGroup(e.target.value as (typeof stateGroups)[number])}
          className="rounded border border-border bg-card px-1.5 py-1 text-[11px]"
        >
          {stateGroups.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
        <span className="num ml-auto text-[11px] text-muted-foreground">{rows.length} wells</span>
      </div>

      <div className="min-h-0 overflow-auto panel-scroll" style={{ maxHeight }}>
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <SortHeader label="Well" field="id" sort={sort} onSort={onSort} />
              {!compact && <SortHeader label="Field / pad" field="field" sort={sort} onSort={onSort} />}
              <SortHeader label="Operating state" field="state" sort={sort} onSort={onSort} />
              <SortHeader label="Health" field="health" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="Hz" field="hz" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="Load %" field="load" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="Motor degF" field="temp" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="PIP psi" field="pip" sort={sort} onSort={onSort} align="right" />
              {!compact && <SortHeader label="PDP psi" field="pdp" sort={sort} onSort={onSort} align="right" />}
              <SortHeader label="Liquid bpd" field="rate" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="Oil bopd" field="oil" sort={sort} onSort={onSort} align="right" />
              <Th align="right">ROR</Th>
              <SortHeader label="Run life d" field="runlife" sort={sort} onSort={onSort} align="right" />
              <SortHeader label="Defer bopd" field="deferred" sort={sort} onSort={onSort} align="right" />
              {!compact && <Th>Headline exception</Th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((w) => {
              const env = envelopePosition(w);
              const band = healthBand(w.healthIndex);
              return (
                <tr key={w.id} className="group cursor-pointer hover:bg-accent/40">
                  <Td>
                    <span className="flex items-center gap-1.5">
                      <EspStatusGlyph well={w} />
                      <Link to="/wells/$wellId" params={{ wellId: w.id }} className="num font-semibold text-primary hover:underline">
                        {w.id}
                      </Link>
                    </span>
                  </Td>
                  {!compact && (
                    <Td className="text-muted-foreground">
                      {fieldName(w.fieldId)} · {w.padName}
                    </Td>
                  )}
                  <Td>
                    <StatusPill tone={stateTone[w.state]}>{stateLabels[w.state]}</StatusPill>
                  </Td>
                  <Td align="right" mono className={textTone[band]}>
                    {w.healthIndex}
                  </Td>
                  <Td align="right" mono>{w.hz ? n1(w.hz) : "—"}</Td>
                  <Td align="right" mono className={cn(w.motorLoadPct > 75 && "text-critical", w.motorLoadPct > 70 && w.motorLoadPct <= 75 && "text-watch")}>
                    {w.hz ? w.motorLoadPct : "—"}
                  </Td>
                  <Td align="right" mono className={cn(w.motorTempF > 268 && "text-critical", w.motorTempF > 255 && w.motorTempF <= 268 && "text-watch")}>
                    {w.motorTempF || "no data"}
                  </Td>
                  <Td align="right" mono>{w.pipPsi ? n0(w.pipPsi) : "no data"}</Td>
                  {!compact && <Td align="right" mono>{w.pdpPsi ? n0(w.pdpPsi) : "no data"}</Td>}
                  <Td align="right" mono>{n0(w.liquidRateBpd)}</Td>
                  <Td align="right" mono>{n0(w.oilRateBopd)}</Td>
                  <Td align="right">
                    {w.hz === 0 ? (
                      <span className="text-muted-foreground">—</span>
                    ) : (
                      <StatusPill tone={env.inside ? "normal" : "warning"} dot={false}>
                        {env.inside ? `in · ${env.bepRatio}×BEP` : env.lowMarginBpd < 0 ? "low flow" : "high flow"}
                      </StatusPill>
                    )}
                  </Td>
                  <Td align="right" mono>{n0(w.runLifeDays)}</Td>
                  <Td align="right" mono className={w.deferredBopd > 0 ? "text-warning" : ""}>
                    {w.deferredBopd ? n0(w.deferredBopd) : "—"}
                  </Td>
                  {!compact && <Td className="max-w-[340px] truncate text-muted-foreground">{w.headline}</Td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
