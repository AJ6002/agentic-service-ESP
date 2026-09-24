import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Database,
  FileBarChart,
  Gauge,
  LayoutGrid,
  Settings2,
  Stethoscope,
  Wrench,
} from "lucide-react";
import { fields } from "@/data/esp/fleet";
import { needsAttention } from "@/data/esp/exceptions";
import { StatusPill } from "./ui";
import { cn } from "@/lib/utils";

type Workspace = "operations" | "configuration";

const WORKSPACES = {
  operations: {
    label: "Operations",
    persona: "Operations & surveillance",
    home: "/",
    groups: ["Operations"],
  },
  configuration: {
    label: "Configuration",
    persona: "Engineering configuration & admin",
    home: "/engineering",
    groups: ["Engineering", "Administration"],
  },
} as const;

const CONFIG_PREFIXES = ["/engineering", "/administration"];

const STORAGE_KEY = "advait.esp-pmm.workspace";

const nav = [
  { workspace: "operations", group: "Operations", to: "/", label: "Fleet Cockpit", hint: "ESP fleet surveillance overview", icon: LayoutGrid },
  { workspace: "operations", group: "Operations", to: "/wells", label: "Well Monitor", hint: "Per-well ESP operations detail", icon: Gauge },
  { workspace: "operations", group: "Operations", to: "/exceptions", label: "Exceptions", hint: "Exception & opportunity queue", icon: Activity },
  { workspace: "operations", group: "Operations", to: "/troubleshooting", label: "Troubleshooting", hint: "Guided ESP diagnostics", icon: Stethoscope },
  { workspace: "operations", group: "Operations", to: "/reliability", label: "Reliability", hint: "Run life, DIFA, interventions", icon: FileBarChart },
  { workspace: "operations", group: "Operations", to: "/reports", label: "Reports", hint: "Scorecards & print views", icon: FileBarChart },
  { workspace: "configuration", group: "Engineering", to: "/engineering", label: "Engineering Home", hint: "Governed ESP master data overview", icon: Database },
  { workspace: "configuration", group: "Engineering", to: "/engineering/catalog", label: "Equipment Catalog", hint: "OEM pumps, motors, components", icon: Database },
  { workspace: "configuration", group: "Engineering", to: "/engineering/installations", label: "Installed Fleet", hint: "Installed ESP systems & well engineering", icon: Database },
  { workspace: "configuration", group: "Engineering", to: "/engineering/definition", label: "Well Definition", hint: "Per-well governed revisions & tags", icon: ClipboardList },
  { workspace: "configuration", group: "Engineering", to: "/engineering/governance/validation", label: "Governance", hint: "Validation, sources, quality, import", icon: Settings2 },
  { workspace: "configuration", group: "Engineering", to: "/engineering/workbench", label: "Engineering Workbench", hint: "Curves, TDH, scenarios", icon: Wrench },
  { workspace: "configuration", group: "Engineering", to: "/engineering/design-cases", label: "Design Cases", hint: "Design vs current vs what-if", icon: ClipboardList },
  { workspace: "configuration", group: "Administration", to: "/administration", label: "Administration", hint: "Integrations & configuration", icon: Settings2 },
] as const;

function workspaceForPath(pathname: string): Workspace {
  return CONFIG_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`)) ? "configuration" : "operations";
}

export function AppShell({ children }: { children: ReactNode }) {
  const openCritical = needsAttention().filter((e) => e.severity === "critical").length;
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const workspace = useMemo(() => workspaceForPath(pathname), [pathname]);
  const ws = WORKSPACES[workspace];

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, workspace);
    } catch {
      /* storage unavailable — non-critical */
    }
  }, [workspace]);

  const switchWorkspace = (next: Workspace) => {
    if (next === workspace) return;
    navigate({ to: WORKSPACES[next].home });
  };


  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-30 flex h-11 shrink-0 items-center gap-4 border-b border-border bg-panel-header px-2.5">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-sm border border-primary/50 bg-primary/15 text-[10px] font-bold text-primary">
            AD
          </div>
          <div className="leading-tight">
            <div className="text-[11.5px] font-semibold text-foreground">
              ADVAIT ESP-PMM <span className="text-muted-foreground">|</span> ESP Performance Monitoring &amp; Management
            </div>
            <div className="text-[9.5px] text-muted-foreground">
              ESP fleet surveillance & governed engineering definitions · Asset ConneX master data · OTConnex measurements
            </div>
          </div>
        </div>

        <label className="flex items-center gap-1.5 text-[10.5px] text-muted-foreground">
          Workspace
          <select
            aria-label="Switch workspace"
            className="rounded-sm border border-primary/40 bg-card px-1.5 py-0.5 text-[10.5px] font-medium text-foreground"
            value={workspace}
            onChange={(e) => switchWorkspace(e.target.value as Workspace)}
          >
            {(Object.keys(WORKSPACES) as Workspace[]).map((k) => (
              <option key={k} value={k}>
                {WORKSPACES[k].label} — {WORKSPACES[k].persona}
              </option>
            ))}
          </select>
        </label>

        <div className="ml-auto flex items-center gap-1.5">
          {workspace === "operations" ? (
            <label className="hidden items-center gap-1.5 text-[10.5px] text-muted-foreground lg:flex">
              Field scope
              <select className="rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px] text-foreground" defaultValue="all">
                <option value="all">All fields (3)</option>
                {fields.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <StatusPill tone="info">Editor / Configurator role</StatusPill>
          )}
          <StatusPill tone="normal">OTConnex live · 2 s scan</StatusPill>
          <StatusPill tone={openCritical ? "critical" : "normal"}>{openCritical} critical open</StatusPill>
          <div className="flex items-center gap-1.5 rounded-sm border border-border bg-card px-1.5 py-0.5 text-[10.5px]">
            <span className="size-4.5 rounded-full bg-primary/25 text-center text-[9px] leading-[1.15rem] text-primary">VK</span>
            <span className="text-muted-foreground">{workspace === "operations" ? "Ops Engineer" : "Configurator"}</span>
          </div>
        </div>

      </header>

      <div className="flex min-h-0 flex-1">
        <nav
          aria-label={`${ws.label} sections`}
          className={cn(
            "sticky top-11 hidden h-[calc(100vh-2.75rem)] shrink-0 flex-col border-r border-border bg-panel py-1.5 transition-[width] duration-150 md:flex",
            expanded ? "w-[196px] px-1.5" : "w-[56px] px-1",
          )}
        >
          <div
            className={cn(
              "pb-1 text-[9px] font-semibold tracking-widest text-muted-foreground uppercase",
              expanded ? "px-1.5" : "text-center",
            )}
          >
            {expanded ? `ADVAIT ESP-PMM · ${ws.label}` : ws.label.slice(0, 3)}
          </div>

          {ws.groups.map((group) => (
            <div key={group} className="pb-1">
              {expanded ? (
                <div className="px-1.5 pt-1 pb-0.5 text-[8.5px] font-semibold tracking-widest text-muted-foreground/80 uppercase">{group}</div>
              ) : (
                <div className="mx-auto my-1 h-px w-6 bg-border" aria-hidden />
              )}
              <ul className="space-y-0.5">
                {nav
                  .filter((n) => n.workspace === workspace && n.group === group)

                  .map((n) => {
                    const Icon = n.icon;
                    return (
                      <li key={n.to} className="group relative">
                        <Link
                          to={n.to}
                          activeOptions={{ exact: n.to === "/" }}
                          title={expanded ? undefined : `${n.label} — ${n.hint}`}
                          className={cn(
                            "flex items-center gap-2 rounded-sm border-l-2 border-transparent text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none",
                            expanded ? "px-2 py-1.5" : "h-9 justify-center",
                          )}
                          activeProps={{ className: "bg-primary/15 text-foreground border-primary" }}
                        >
                          <Icon size={16} strokeWidth={1.7} aria-hidden />
                          {expanded ? (
                            <span className="min-w-0 leading-tight">
                              <span className="block truncate text-[11.5px] font-medium">{n.label}</span>
                              <span className="block truncate text-[9px] text-muted-foreground/80">{n.hint}</span>
                            </span>
                          ) : (
                            <span className="sr-only">{n.label}</span>
                          )}
                        </Link>
                        {!expanded && (
                          <span
                            role="tooltip"
                            className="pointer-events-none absolute top-1/2 left-[52px] z-40 hidden -translate-y-1/2 rounded-sm border border-border bg-popover px-2 py-1 text-[10.5px] whitespace-nowrap text-foreground shadow-lg group-hover:block group-focus-within:block"
                          >
                            {n.label}
                            <span className="block text-[9px] text-muted-foreground">{n.hint}</span>
                          </span>
                        )}
                      </li>
                    );
                  })}
              </ul>
            </div>
          ))}

          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            aria-expanded={expanded}
            aria-label={expanded ? "Collapse navigation labels" : "Expand navigation labels"}
            className={cn(
              "mt-auto flex items-center gap-1.5 rounded-sm border border-border bg-card text-[10px] text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none",
              expanded ? "px-2 py-1" : "h-8 justify-center",
            )}
          >
            {expanded ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
            {expanded && <span>Collapse</span>}
          </button>
        </nav>

        <main className="min-w-0 flex-1 p-2.5">{children}</main>
      </div>
    </div>
  );
}
