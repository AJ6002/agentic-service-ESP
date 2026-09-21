import { createFileRoute, Link, getRouteApi } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";
import { ReliabilityBadge } from "@/components/esp/engineering/governance";
import { byId, oemName, sectionsForSystem } from "@/lib/esp-catalog/selectors";

const api = getRouteApi("/engineering");

export const Route = createFileRoute("/engineering/installations/")({
  head: () => ({
    meta: [
      { title: "Installed ESP fleet definitions — ADVAIT ESP-PMM" },
      { name: "description", content: "Governed installed ESP systems by field and pad: normalized pump, motor, gas handling, protector, cable, VSD and sensor selections with catalog match confidence." },
      { property: "og:title", content: "Installed ESP fleet definitions" },
      { property: "og:description", content: "Installed configuration and catalog match status for every ESP well." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: InstalledFleet,
});

function InstalledFleet() {
  const d = api.useLoaderData();
  const [field, setField] = useState("all");
  const [match, setMatch] = useState("all");
  const [q, setQ] = useState("");
  const blankRaw = d.installedSystems.filter((s) => (s.raw_designation ?? "").trim() === "").length;
  const secondaryOnly = d.installedSystems.filter((s) => s.match_status === "secondary-only").length;

  const rows = useMemo(
    () =>
      d.installedSystems
        .map((s) => {
          const well = byId(d.wells, s.well_id);
          const sections = sectionsForSystem(d, s.id);
          const pump = byId(d.pumpModels, s.normalized_pump_model_id ?? sections[0]?.pump_model_id ?? null);
          const motor = byId(d.motors, s.motor_model_id);
          return { s, well, sections, pump, motor };
        })
        .filter(
          (r) =>
            (field === "all" || r.well?.field_id === field) &&
            (match === "all" || r.s.match_status === match) &&
            (q === "" || `${r.well?.name} ${r.s.raw_designation ?? ""} ${r.pump?.model ?? ""}`.toLowerCase().includes(q.toLowerCase())),
        ),
    [d, field, match, q],
  );

  return (
    <div className="space-y-2.5">
      <PageHeader
        title="Installed Fleet"
        description="One governed record per installed ESP system. Raw CCED designations are normalized against the equipment catalog; unresolved constructions stay flagged rather than being guessed."
        meta={
          <>
            <StatusPill tone="info">{rows.length} of {d.installedSystems.length} CCED rows</StatusPill>
            <StatusPill tone={blankRaw ? "watch" : "normal"}>{blankRaw} blank raw designation</StatusPill>
            <StatusPill tone="watch">{secondaryOnly} secondary-only evidence</StatusPill>
            <StatusPill tone="muted">Engineering definition — no OT values</StatusPill>
          </>
        }
      />

      <Panel
        title="Installed ESP systems"
        subtitle="Field → pad → well → assembly; tapered assemblies show every pump section"
        bodyClassName="p-0"
        actions={
          <div className="flex flex-wrap items-center gap-1.5 text-[10.5px]">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search well / model"
              className="w-40 rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground placeholder:text-muted-foreground"
            />
            <select className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground" value={field} onChange={(e) => setField(e.target.value)}>
              <option value="all">All fields</option>
              {d.fields.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
            <select className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-foreground" value={match} onChange={(e) => setMatch(e.target.value)}>
              <option value="all">All match states</option>
              <option value="resolved">resolved</option>
              <option value="partial">partial</option>
              <option value="unresolved">unresolved</option>
              <option value="secondary-only">secondary-only</option>
            </select>
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Well</Th>
                <Th>Pad / Area</Th>
                <Th>Raw designation</Th>
                <Th>Normalized pump</Th>
                <Th>OEM</Th>
                <Th align="right">Sections</Th>
                <Th align="right">Stages</Th>
                <Th>Motor</Th>
                <Th>Assembly</Th>
                <Th>Match</Th>
                <Th>Evidence</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ s, well, sections, pump, motor }) => (
                <tr key={s.id} className="hover:bg-accent/40">
                  <Td>
                    <Link to="/engineering/installations/$systemId" params={{ systemId: s.id }} className="text-info hover:underline">
                      {well?.name ?? s.well_id}
                    </Link>
                  </Td>
                  <Td className="text-[10.5px] text-muted-foreground">{well?.pad_area ?? "—"}</Td>
                  <Td mono className="text-[10px] text-muted-foreground">
                    {(s.raw_designation ?? "").trim() !== "" ? s.raw_designation : <span className="text-warning">blank in source row</span>}
                  </Td>
                  <Td className="text-[10.5px]">{pump?.model ?? <span className="text-warning">unresolved</span>}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{pump ? oemName(d, pump.oem_id) : "—"}</Td>
                  <Td align="right" mono>{sections.length}</Td>
                  <Td align="right" mono>{s.total_stages ?? "—"}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{motor?.model ?? "—"}</Td>
                  <Td className="text-[10.5px] text-muted-foreground">{s.assembly_type}</Td>
                  <Td>
                    <StatusPill tone={s.match_status === "resolved" ? "normal" : s.match_status === "partial" || s.match_status === "secondary-only" ? "watch" : "critical"}>
                      {s.match_status}
                    </StatusPill>
                  </Td>
                  <Td>{pump ? <ReliabilityBadge code={pump.reliability_code} /> : <ReliabilityBadge code="D" />}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
