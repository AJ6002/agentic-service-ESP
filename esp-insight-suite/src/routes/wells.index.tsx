import { createFileRoute } from "@tanstack/react-router";
import { FleetTable } from "@/components/esp/FleetTable";
import { PageHeader, Panel, StatusPill } from "@/components/esp/ui";

export const Route = createFileRoute("/wells/")({
  head: () => ({
    meta: [
      { title: "Well Monitor — select an ESP well | ADVAIT ESP-PMM" },
      {
        name: "description",
        content: "Select an ESP well to open live operating snapshot, state timeline, trends, operating point and recommendations.",
      },
      { property: "og:title", content: "Well Monitor — ADVAIT ESP-PMM" },
      { property: "og:description", content: "Per-well ESP surveillance: snapshot, state timeline, trends and recommendations." },
    ],
  }),
  component: WellIndex,
});

function WellIndex() {
  return (
    <div className="space-y-3">
      <PageHeader
        title="Well Monitor"
        description="Choose a well to open its operating snapshot, state timeline, event history, operating point and recommendations. All signals are supplied by OTConnex; the ESP string and tag mapping come from Asset ConneX templates."
        meta={<StatusPill tone="info">25 wells · 3 fields · 2 s scan class</StatusPill>}
      />
      <Panel title="ESP well register" bodyClassName="p-0">
        <FleetTable maxHeight="calc(100vh - 250px)" />
      </Panel>
    </div>
  );
}
