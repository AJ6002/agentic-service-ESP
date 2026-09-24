import { createFileRoute, Link, Outlet } from "@tanstack/react-router";

const TABS = [
  { to: "/engineering/governance/validation", label: "Validation & readiness" },
  { to: "/engineering/governance/sources", label: "Sources / provenance" },
  { to: "/engineering/governance/quality", label: "Data quality" },
  { to: "/engineering/governance/import", label: "Import / administration" },
] as const;

export const Route = createFileRoute("/engineering/governance")({
  component: GovernanceLayout,
});

function GovernanceLayout() {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1 border-b border-border pb-1">
        {TABS.map((t) => (
          <Link
            key={t.to}
            to={t.to}
            className="rounded-sm border border-border px-2 py-0.5 text-[10.5px] text-muted-foreground hover:bg-accent hover:text-foreground"
            activeProps={{ className: "bg-primary/15 border-primary text-foreground" }}
          >
            {t.label}
          </Link>
        ))}
      </div>
      <Outlet />
    </div>
  );
}
