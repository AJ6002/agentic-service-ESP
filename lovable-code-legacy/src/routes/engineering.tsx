import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { getEngineeringCatalog } from "@/lib/esp-catalog/queries.functions";
import { StatusPill } from "@/components/esp/ui";

const SECTIONS = [
  { group: "Reference master", to: "/engineering", label: "Engineering Overview", exact: true },
  { group: "Reference master", to: "/engineering/catalog", label: "Equipment Catalog" },
  { group: "Installed fleet", to: "/engineering/installations", label: "Installed ESP Systems" },
  { group: "Installed fleet", to: "/engineering/definition", label: "Well Definition (revisions)" },
  { group: "Engineering analysis", to: "/engineering/workbench", label: "Engineering Workbench" },
  { group: "Engineering analysis", to: "/engineering/design-cases", label: "Design Cases" },
  { group: "Governance", to: "/engineering/governance/validation", label: "Validation & Readiness" },
  { group: "Governance", to: "/engineering/governance/sources", label: "Source / Provenance Registry" },
  { group: "Governance", to: "/engineering/governance/quality", label: "Data Quality & Reconciliation" },
  { group: "Governance", to: "/engineering/governance/import", label: "Import / Catalog Administration" },
] as const;

const GROUPS = ["Reference master", "Installed fleet", "Engineering analysis", "Governance"] as const;

export const Route = createFileRoute("/engineering")({
  loader: () => getEngineeringCatalog(),
  errorComponent: ({ error }) => (
    <div className="p-3 text-[11px] text-critical">Engineering catalog unavailable: {error.message}</div>
  ),
  notFoundComponent: () => <div className="p-3 text-[11px] text-muted-foreground">Definition not found.</div>,
  component: EngineeringLayout,
});

function EngineeringLayout() {
  const data = Route.useLoaderData();
  const blocking = data.issues.filter((i) => i.status === "Blocking").length;

  return (
    <div className="flex min-h-0 gap-2.5">
      <aside className="hidden w-[188px] shrink-0 xl:block">
        <div className="sticky top-[3.25rem] rounded-md border border-border bg-panel">
          <div className="border-b border-border bg-panel-header px-2 py-1.5">
            <div className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">
              ESP Engineering Configuration
            </div>
            <div className="text-[9px] text-muted-foreground/80">Asset ConneX governed master data</div>
          </div>
          {GROUPS.map((group) => (
            <div key={group} className="border-b border-border/60 p-1 last:border-b-0">
              <div className="px-2 pt-0.5 pb-1 text-[8.5px] font-semibold tracking-widest text-muted-foreground/80 uppercase">
                {group}
              </div>
              <ul>
                {SECTIONS.filter((s) => s.group === group).map((s) => (
                  <li key={s.to}>
                    <Link
                      to={s.to}
                      activeOptions={{ exact: "exact" in s && s.exact }}
                      className="block rounded-sm border-l-2 border-transparent px-2 py-1 text-[10.5px] leading-tight text-muted-foreground hover:bg-accent hover:text-foreground"
                      activeProps={{ className: "bg-primary/15 border-primary text-foreground" }}
                    >
                      {s.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <div className="border-t border-border px-2 py-1.5">
            <StatusPill tone={blocking ? "critical" : "normal"}>{blocking} blocking QA</StatusPill>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <div className="mb-2 flex flex-wrap gap-1 xl:hidden">
          {SECTIONS.map((s) => (
            <Link
              key={s.to}
              to={s.to}
              activeOptions={{ exact: "exact" in s && s.exact }}
              className="rounded-sm border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground"
              activeProps={{ className: "bg-primary/15 border-primary text-foreground" }}
            >
              {s.label}
            </Link>
          ))}
        </div>
        <Outlet />
      </div>
    </div>
  );
}
