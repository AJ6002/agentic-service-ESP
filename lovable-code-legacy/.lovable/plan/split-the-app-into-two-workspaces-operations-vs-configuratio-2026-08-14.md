# Split the app into two workspaces: Operations vs Configuration

Today Operations screens and Engineering/Asset-Definition screens sit in one
mixed sidebar. This change separates them into two distinct workspaces with a
mode switcher in the top ribbon.

## Workspaces

**Operations (default, "user" view)**
- Performance Cockpit (`/`)
- Asset Monitor (`/wells`)
- Exceptions (`/exceptions`)
- Troubleshooting (`/troubleshooting`)
- Reliability (`/reliability`)
- Reports (`/reports`)

**Configuration (engineer / configurator view)**
- Engineering Configuration (`/engineering`)
- Engineering Workbench (`/workbench`)
- Design Cases (`/design-cases`)
- Data Readiness (`/engineering/readiness`)
- Asset Definition registry (`/asset-definition`)
- Administration (`/administration`)

## Behaviour

- A dropdown in the header ribbon labelled "Workspace" switches between
  **Operations** and **Configuration**, showing the persona under each
  ("Operations & surveillance" / "Engineering configuration & admin").
- The sidebar rail shows only the routes for the active workspace, so the two
  views never mix.
- The active workspace is derived from the current route: landing on any
  `/engineering*`, `/asset-definition*`, `/workbench`, `/design-cases`, or
  `/administration` URL selects Configuration automatically; everything else
  selects Operations. Manual selection persists in `localStorage` for the
  session.
- Switching workspace navigates to that workspace's home page
  (Operations → `/`, Configuration → `/engineering`).
- Configuration is marked as a privileged workspace with a small
  "Editor / Configurator role" badge in the ribbon; real permission
  enforcement is out of scope and handled later.
- All existing routes stay reachable by URL — nothing is removed or renamed.

## Technical notes

- Changes are confined to `src/components/esp/AppShell.tsx`: add a `workspace`
  field to the nav entries, derive the active workspace from
  `useRouterState().location.pathname`, add local state + `localStorage`
  persistence, and render a `<select>` in the header that navigates on change.
- Nav groups within each workspace stay as small section labels in the expanded
  rail (e.g. Configuration → "Engineering", "Administration").
- No data-layer, route-file, or domain-contract changes; no auth added.
