# AppShell Component Analysis

## Identity
- **File**: `src/components/esp/AppShell.tsx`
- **Export**: `AppShell` (Named Export)
- **Kind**: Layout Shell Component

## Props
| Prop | Type | Required | Default | Purpose in Simple Terms |
|---|---|---|---|---|
| `children` | `ReactNode` | Yes | N/A | The active page content rendered inside the layout frame. |

## Imports
- **Primitives (`ui/`)**: Icons from `lucide-react`
- **Siblings (`esp/`)**: `StatusPill` from `@/components/esp/ui`
- **Data**: `fields` from `@/data/esp/fleet`, `needsAttention` from `@/data/esp/exceptions`

## Render Hierarchy
```text
AppShell
├── Header (Top Bar)
│   ├── Logo & Application Title
│   ├── Workspace Selector Dropdown
│   ├── Field Scope Selector Dropdown
│   └── System Status Pills & User Profile Badge
├── Outer Container (Flex Body)
│   ├── Navigation Sidebar Rail
│   │   ├── Navigation Links Group (Operations / Engineering)
│   │   └── Expand/Collapse Arrow Button
│   └── Main Viewport Container (<main>)
│       └── children (Active Route View)
```

## Regions (as seen on screen)
1. **Top Header**: Horizontal bar for title, workspace switching, and system badges.
2. **Left Navigation Rail**: Collapsible vertical menu.
3. **Main Content Region**: Central view area rendering current page.

## Data Source
- **Data Files**: [`src/data/esp/fleet.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/fleet.ts), [`src/data/esp/exceptions.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/exceptions.ts)

## Used By
- [`src/routes/__root.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/__root.tsx#L119)
