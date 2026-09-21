# Global App Shell — ADVAIT ESP-PMM

## Overview
The entire application is wrapped in a unified global layout component defined in [`src/components/esp/AppShell.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AppShell.tsx). It consists of a top sticky header bar, a left collapsible navigation rail/sidebar, and a main content viewport (`<main>`).

---

## Topbar (Header Chrome)
- **Height**: `44px` (`h-11`), sticky at top (`sticky top-0 z-30`).
- **Background**: `bg-panel-header`, border bottom `border-border`.
- **Elements (Left to Right)**:
  1. **Brand Badge**: Square logo badge containing `"AD"` with primary accent border (`border-primary/50 bg-primary/15 text-primary`).
  2. **Application Title & Subtitle**:
     - Title: `ADVAIT ESP-PMM | ESP Performance Monitoring & Management`
     - Subtitle: `ESP fleet surveillance & governed engineering definitions · Asset ConneX master data · OTConnex measurements`
  3. **Workspace Switcher Dropdown**:
     - Native HTML `<select>` allowing navigation between two primary workspaces:
       - **Operations**: `Operations — Operations & surveillance` (navigates to `/`)
       - **Configuration**: `Configuration — Engineering configuration & admin` (navigates to `/engineering`)
  4. **Field Scope Selector** *(Visible in Operations workspace)*:
     - Select dropdown containing: `All fields (3)`, `North Field`, `South Field`, `East Field`.
  5. **Role Badge** *(Visible in Configuration workspace)*:
     - `StatusPill`: `Editor / Configurator role` (`tone="info"`).
  6. **OTConnex System Status Pill**:
     - `StatusPill`: `OTConnex live · 2 s scan` (`tone="normal"`).
  7. **Critical Alarms Pill**:
     - `StatusPill`: `{N} critical open` (dynamic count from `needsAttention()` in `src/data/esp/exceptions.ts`).
  8. **User Profile Badge**:
     - Avatar circle with initials `"VK"`, displaying user role (`Ops Engineer` or `Configurator`).

---

## Left Sidebar / Navigation Rail
- **Position**: `sticky top-11 hidden md:flex`, height `calc(100vh - 2.75rem)`.
- **States**:
  - **Collapsed** (default width `56px`, `px-1`): Shows icons only with hover tooltips (`role="tooltip"`).
  - **Expanded** (width `196px`, `px-1.5`): Shows icon + title + secondary hint text.
  - **Toggle**: Bottom button with `<ChevronLeft>` / `<ChevronRight>` icon to expand/collapse.

### Navigation Groups & Items by Workspace

#### Operations Workspace Navigation (`workspace="operations"`)
- **Group: Operations**
  1. **Fleet Cockpit** (`/`): Icon `LayoutGrid` — *ESP fleet surveillance overview*
  2. **Well Monitor** (`/wells`): Icon `Gauge` — *Per-well ESP operations detail*
  3. **Exceptions** (`/exceptions`): Icon `Activity` — *Exception & opportunity queue*
  4. **Troubleshooting** (`/troubleshooting`): Icon `Stethoscope` — *Guided ESP diagnostics*
  5. **Reliability** (`/reliability`): Icon `FileBarChart` — *Run life, DIFA, interventions*
  6. **Reports** (`/reports`): Icon `FileBarChart` — *Scorecards & print views*

#### Configuration Workspace Navigation (`workspace="configuration"`)
- **Group: Engineering**
  1. **Engineering Home** (`/engineering`): Icon `Database` — *Governed ESP master data overview*
  2. **Equipment Catalog** (`/engineering/catalog`): Icon `Database` — *OEM pumps, motors, components*
  3. **Installed Fleet** (`/engineering/installations`): Icon `Database` — *Installed ESP systems & well engineering*
  4. **Well Definition** (`/engineering/definition`): Icon `ClipboardList` — *Per-well governed revisions & tags*
  5. **Governance** (`/engineering/governance/validation`): Icon `Settings2` — *Validation, sources, quality, import*
  6. **Engineering Workbench** (`/engineering/workbench`): Icon `Wrench` — *Curves, TDH, scenarios*
  7. **Design Cases** (`/engineering/design-cases`): Icon `ClipboardList` — *Design vs current vs what-if*
- **Group: Administration**
  8. **Administration** (`/administration`): Icon `Settings2` — *Integrations & configuration*

---

## Main Content Area
- **Container**: `<main className="min-w-0 flex-1 p-2.5">` rendering route outlets.
- **Scroll Behavior**: Native browser window vertical scroll; tables and charts feature internal horizontal/vertical overflow scrolling where required.
