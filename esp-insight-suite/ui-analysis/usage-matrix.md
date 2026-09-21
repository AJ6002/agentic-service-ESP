# Component Usage Matrix

This document lists every domain component and details where it is used across all routes.

| Component Name | File Location | Appears on Routes | Render Frequency | Usage Status |
| :--- | :--- | :--- | :--- | :--- |
| **`AppShell`** | `src/components/esp/AppShell.tsx` | All routes (via `__root.tsx`) | Global Layout Wrapper (100%) | ACTIVE |
| **`FleetTable`** | `src/components/esp/FleetTable.tsx` | `/`, `/wells` | 2 routes | ACTIVE |
| **`EspWellVisual`** | `src/components/esp/EspWellVisual.tsx` | `/wells/$wellId` | 1 route | ACTIVE |
| **`AdvisorPanel`** | `src/components/esp/AdvisorPanel.tsx` | `/wells/$wellId` | 1 route | ACTIVE |
| **`PressureProfile`** | `src/components/esp/PressureProfile.tsx` | `/wells/$wellId` | 1 route | ACTIVE |
| **`TimeSeriesChart`** | `src/components/esp/charts.tsx` | `/wells/$wellId` | 1 route | ACTIVE |
| **`CurvePlot`** | `src/components/esp/engineering/CurvePlot.tsx` | `/engineering/workbench`, `/engineering/catalog/pumps/$modelId` | 2 routes | ACTIVE |
| **`GovernedContextPanel`** | `src/components/esp/engineering/GovernedContextPanel.tsx` | `/engineering/workbench` | 1 route | ACTIVE |
| **`CalculationGradeBadge`** | `src/components/esp/engineering/governance.tsx` | All `/engineering/**` routes | 6 routes | ACTIVE |
| **`StatusPill`** | `src/components/esp/ui.tsx` | Global Header, `/`, `/wells`, `/exceptions` | 5+ routes | ACTIVE |
| **`KpiCard`** | `src/components/esp/ui.tsx` | `/`, `/reliability`, `/exceptions` | 3 routes | ACTIVE |

---

## Unused / Dead Item Flagging
- **Unused Components**: None detected. All custom domain components in `src/components/esp/` are imported and actively rendered by route components.
- **Primitive-Only / Simple Routes**:
  - `/asset-definition.tsx`: Performs immediate redirect to `/engineering/definition`.
  - `/asset-definitions.tsx`: Performs immediate redirect to `/engineering/definition`.
  - `/design-cases.tsx`: Performs immediate redirect to `/engineering/design-cases`.
  - `/workbench.tsx`: Performs immediate redirect to `/engineering/workbench`.
