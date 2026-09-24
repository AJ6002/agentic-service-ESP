# Global Page Shell Analysis

This document describes the common outer frame (header, sidebar, and layout container) that stays visible on screen across all pages.

---

## 1. What is the Global Shell?
The global shell is the main page layout defined in [`src/components/esp/AppShell.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AppShell.tsx#L63). It acts as a wrapper frame around every view in the application.

---

## 2. Top Bar (Header Chrome)
Located at the top of the screen (`src/components/esp/AppShell.tsx:87-142`).

- **Logo Badge** (`AppShell.tsx:89-91`): Displays `"AD"` inside a small square box.
- **Application Name** (`AppShell.tsx:93-95`): Displays `"ADVAIT ESP-PMM | ESP Performance Monitoring & Management"`.
- **Workspace Switcher Dropdown** (`AppShell.tsx:105-116`):
  - Lets the user switch between **Operations** (monitoring live wells) and **Configuration** (editing equipment and master data).
- **Field Scope Selector** (`AppShell.tsx:120-130`):
  - Lets the user filter data across **All fields (3)**, **North Field**, **South Field**, or **East Field**.
- **Live Status Pills** (`AppShell.tsx:134-135`):
  - Shows if telemetry connection is active (`OTConnex live · 2 s scan`).
  - Displays count of open critical alarms.
- **User Profile Pill** (`AppShell.tsx:136-139`):
  - Displays user avatar initials `"VK"` and active role (`Ops Engineer` or `Configurator`).

---

## 3. Left Navigation Rail (Sidebar)
Located on the left side of the screen (`src/components/esp/AppShell.tsx:145-225`).

- **Collapsed State** (default width 56 pixels): Shows icons only. Hovering over an icon displays a tooltip text bubble explaining the page.
- **Expanded State** (width 196 pixels): Expands when the user clicks the bottom arrow button to reveal text titles and short explanations.
- **Navigation Groups**:
  - **Operations Group**: Fleet Cockpit, Well Monitor, Exceptions, Troubleshooting, Reliability, Reports.
  - **Engineering Group**: Engineering Home, Equipment Catalog, Installed Fleet, Well Definition, Governance, Engineering Workbench, Design Cases.
  - **Administration Group**: Platform Administration.

---

## 4. Main Content Area (`<Outlet/>`)
Located in [`src/routes/__root.tsx:121`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/__root.tsx#L121).

- The `<Outlet/>` component from TanStack Router acts as a placeholder frame where the specific page content renders depending on the active URL path.
