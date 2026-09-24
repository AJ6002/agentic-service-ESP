# Data Type Consumers Matrix

This matrix maps each data type to the UI components and page routes that consume it.

| Data Type / Function | Source File | Consuming Components | Consuming Page Routes |
| :--- | :--- | :--- | :--- |
| `EspWellSummary` | `src/data/esp/fleet.ts` | `FleetTable`, `EspWellVisual`, `StatusPill` | `/`, `/wells`, `/wells/$wellId` |
| `EspException` | `src/data/esp/exceptions.ts` | `StatusPill`, `KpiCard` | `/`, `/exceptions` |
| `getAdvisorForWell()` | `src/data/esp/advisor.ts` | `AdvisorPanel` | `/wells/$wellId` |
| `getReliabilityData()` | `src/data/esp/reliability.ts` | `KpiCard` | `/reliability` |
| `getSeriesForWell()` | `src/data/esp/series.ts` | `TimeSeriesChart`, `PressureProfile` | `/wells/$wellId` |
| `CurveData` | `src/lib/esp-catalog/` | `CurvePlot`, `GovernedContextPanel` | `/engineering/workbench`, `/engineering/catalog/pumps/$modelId` |
