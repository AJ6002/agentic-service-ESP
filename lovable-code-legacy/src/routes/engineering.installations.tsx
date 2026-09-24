import { createFileRoute, Link, Outlet } from "@tanstack/react-router";

const TABS = [
  { to: "/engineering/installations", label: "Installed systems", exact: true },
  { to: "/engineering/installations/assembly", label: "ESP assembly" },
  { to: "/engineering/installations/well", label: "Well & completion" },
  { to: "/engineering/installations/fluid", label: "Fluid / PVT" },
  { to: "/engineering/installations/limits", label: "Operating & design limits" },
] as const;

export const Route = createFileRoute("/engineering/installations")({
  component: InstallationsLayout,
});

function InstallationsLayout() {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1 border-b border-border pb-1">
        {TABS.map((t) => (
          <Link
            key={t.to}
            to={t.to}
            activeOptions={{ exact: "exact" in t && t.exact }}
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
