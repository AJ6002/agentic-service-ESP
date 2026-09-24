import { createFileRoute } from "@tanstack/react-router";
import { wells } from "@/data/esp/fleet";
import { Note, PageHeader, Panel, StatusPill, Td, Th } from "@/components/esp/ui";

export const Route = createFileRoute("/administration")({
  head: () => ({
    meta: [
      { title: "Administration & Platform Integration — ADVAIT ESP-PMM" },
      {
        name: "description",
        content:
          "ESP-PMM configuration: OTConnex signal mapping, Asset ConneX hierarchy, surveillance rule thresholds, role permissions and AI advisor governance.",
      },
      { property: "og:title", content: "ESP-PMM Administration" },
      { property: "og:description", content: "Signal mapping, rule thresholds, roles and AI governance for ESP-PMM." },
    ],
  }),
  component: Administration,
});

const tagMap = [
  { tag: "ESP.FREQ_HZ", description: "Drive output frequency", unit: "Hz", source: "OTConnex → VSD", scan: "2 s", coverage: "25 / 25" },
  { tag: "ESP.MOTOR_AMPS", description: "Motor current", unit: "A", source: "OTConnex → VSD", scan: "2 s", coverage: "25 / 25" },
  { tag: "ESP.MOTOR_VOLTS", description: "Motor voltage", unit: "V", source: "OTConnex → VSD", scan: "5 s", coverage: "25 / 25" },
  { tag: "ESP.PIP_PSI", description: "Pump intake pressure", unit: "psi", source: "OTConnex → downhole gauge", scan: "10 s", coverage: "23 / 25" },
  { tag: "ESP.PDP_PSI", description: "Pump discharge pressure", unit: "psi", source: "OTConnex → downhole gauge", scan: "10 s", coverage: "23 / 25" },
  { tag: "ESP.MOTOR_TEMP_F", description: "Motor winding temperature", unit: "degF", source: "OTConnex → downhole gauge", scan: "10 s", coverage: "23 / 25" },
  { tag: "ESP.VIB_G", description: "Vibration", unit: "g", source: "OTConnex → downhole gauge", scan: "10 s", coverage: "21 / 25" },
  { tag: "WELL.WHP_PSI", description: "Wellhead pressure", unit: "psi", source: "OTConnex → SCADA", scan: "5 s", coverage: "25 / 25" },
  { tag: "WELL.LIQ_BPD", description: "Allocated liquid rate", unit: "bpd", source: "OTConnex → production allocation", scan: "1 h", coverage: "25 / 25" },
  { tag: "WELL.WCUT_PCT", description: "Water cut", unit: "%", source: "Well test / allocation", scan: "Weekly", coverage: "25 / 25" },
  { tag: "ESP.DRIVE_FAULT", description: "Drive fault code", unit: "code", source: "OTConnex → VSD", scan: "Event", coverage: "25 / 25" },
];

const rules = [
  { id: "R-01", rule: "Outside recommended operating range", basis: "Q vs ROR from pump curve at current Hz", threshold: "Any excursion sustained 30 min", severity: "warning" },
  { id: "R-02", rule: "Motor overload", basis: "Amps / nameplate amps", threshold: "> 75% for 15 min", severity: "critical" },
  { id: "R-03", rule: "High motor temperature", basis: "Motor temp vs limit", threshold: "Within 12 degF of limit", severity: "warning" },
  { id: "R-04", rule: "Suspected gas interference", basis: "Amp variability + PIP decline", threshold: "Band > 4 A with falling PIP", severity: "warning" },
  { id: "R-05", rule: "Pump degradation", basis: "Head per stage vs design", threshold: "> 10% decline over 30 days", severity: "warning" },
  { id: "R-06", rule: "Repeat drive trips", basis: "Fault-code count", threshold: "≥ 3 trips in 7 days", severity: "critical" },
  { id: "R-07", rule: "Gauge data quality", basis: "Signal continuity", threshold: "> 10% missing in 24 h", severity: "watch" },
  { id: "R-08", rule: "Optimization candidate", basis: "Envelope, thermal and electrical headroom", threshold: "All three margins positive", severity: "opportunity" },
];

const roles = [
  { role: "Control room operator", views: "Fleet Cockpit, Well Monitor, Exceptions, Troubleshooting", authority: "Acknowledge exceptions, log actions", restricted: "No setpoint writes, no case edits" },
  { role: "Production / artificial-lift engineer", views: "All operational views plus Workbench and Design Cases", authority: "Create what-if cases, propose setpoints", restricted: "Cannot approve rig work" },
  { role: "Maintenance / reliability engineer", views: "Reliability, DIFA, Interventions, Well Monitor", authority: "Raise interventions, record DIFA findings", restricted: "No design case approval" },
  { role: "Operations / asset manager", views: "Scorecard, Reports, Fleet Cockpit", authority: "Approve interventions and priorities", restricted: "Read-only on engineering calculations" },
  { role: "ESP-PMM administrator", views: "All views plus Administration", authority: "Tag mapping, rule thresholds, role assignment", restricted: "Change history is audited" },
];

function Administration() {
  return (
    <div className="space-y-3">
      <PageHeader
        title="Administration & Platform Integration"
        description="ESP-PMM extends the ADVAIT platform rather than duplicating it. Signals arrive through OTConnex, the asset hierarchy and ESP string configuration come from Asset ConneX, and workflow, notification and document services are reused as-is."
        meta={
          <>
            <StatusPill tone="normal">OTConnex connected · 11 template tags</StatusPill>
            <StatusPill tone="normal">Asset ConneX ESP template v2.3</StatusPill>
            <StatusPill tone="info">{wells.length} wells onboarded</StatusPill>
          </>
        }
      />

      <div className="grid gap-3 xl:grid-cols-2">
        <Panel title="Signal mapping" subtitle="ESP tag template resolved per well through OTConnex" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Tag</Th>
                <Th>Description</Th>
                <Th>Unit</Th>
                <Th>Source</Th>
                <Th align="right">Scan</Th>
                <Th align="right">Coverage</Th>
              </tr>
            </thead>
            <tbody>
              {tagMap.map((t) => (
                <tr key={t.tag} className="hover:bg-accent/40">
                  <Td mono className="text-primary">{t.tag}</Td>
                  <Td>{t.description}</Td>
                  <Td className="text-muted-foreground">{t.unit}</Td>
                  <Td className="text-muted-foreground">{t.source}</Td>
                  <Td align="right" mono>{t.scan}</Td>
                  <Td align="right" mono className={t.coverage.startsWith("25") ? "" : "text-watch"}>{t.coverage}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Surveillance rule configuration" subtitle="Deterministic thresholds behind every exception" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>ID</Th>
                <Th>Rule</Th>
                <Th>Engineering basis</Th>
                <Th>Threshold</Th>
                <Th>Severity</Th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-accent/40">
                  <Td mono>{r.id}</Td>
                  <Td>{r.rule}</Td>
                  <Td className="text-muted-foreground">{r.basis}</Td>
                  <Td mono>{r.threshold}</Td>
                  <Td>
                    <StatusPill tone={r.severity as "critical" | "warning" | "watch" | "opportunity"}>{r.severity}</StatusPill>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Roles and authority" subtitle="Same governed data, different views and permissions" bodyClassName="p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Role</Th>
                <Th>Views</Th>
                <Th>Authority</Th>
                <Th>Restrictions</Th>
              </tr>
            </thead>
            <tbody>
              {roles.map((r) => (
                <tr key={r.role} className="hover:bg-accent/40">
                  <Td>{r.role}</Td>
                  <Td className="text-muted-foreground">{r.views}</Td>
                  <Td>{r.authority}</Td>
                  <Td className="text-muted-foreground">{r.restricted}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="AI advisor governance" subtitle="How the ESP Advisor is allowed to behave">
          <div className="space-y-2 text-[12px]">
            <Note tone="info">
              The advisor is a supervised assistant. It reads deterministic calculations, trends, events, maintenance history and the ESP knowledge base,
              then proposes an explanation with the evidence it used.
            </Note>
            <ul className="space-y-1.5">
              {[
                "Engineering truth stays with the calculation engine — the advisor never replaces a computed value.",
                "Every assessment cites the calculations, trends and records it relied on.",
                "Operationally sensitive suggestions require explicit human confirmation.",
                "No closed-loop control: ESP-PMM does not write setpoints to the drive.",
                "Confidence values are advisory only and are shown alongside their basis.",
                "All advisor interactions are logged for audit and later model evaluation.",
              ].map((x, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-primary">→</span>
                  <span>{x}</span>
                </li>
              ))}
            </ul>
            <Note>
              Machine-learning anomaly detection and run-life prediction are staged for a later phase, once sufficient labelled fleet history has
              accumulated in the platform.
            </Note>
          </div>
        </Panel>
      </div>
    </div>
  );
}
