# Shared Component Inventory — ADVAIT ESP-PMM

This document details all reusable UI components in `src/components/esp/` and `src/components/esp/engineering/`.

---

## 1. Primary ESP Domain Components (`src/components/esp/`)

| Component Name | File Path | Component Type | Purpose / Where Used |
| :--- | :--- | :--- | :--- |
| **`AppShell`** | [`AppShell.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AppShell.tsx) | Layout Shell | Global application chrome containing Topbar, Workspace Switcher, Left Nav Rail, and User Profile. |
| **`EspWellVisual`** | [`EspWellVisual.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/EspWellVisual.tsx) | SVG Schematic | Interactive downhole physical assembly rendering wellhead, casing, tubing, pump, protector, motor, and sensor. Used in `Well Monitor` (`/wells/$wellId`). |
| **`PressureProfile`** | [`PressureProfile.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/PressureProfile.tsx) | Area / Line Chart | Renders depth vs pressure gradient profile from reservoir to wellhead. Used in `Well Monitor` (`/wells/$wellId`). |
| **`FleetTable`** | [`FleetTable.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/FleetTable.tsx) | Data Table | Dense operational data table for 25 ESP wells. Used in `Fleet Cockpit` (`/`) and `Well Directory` (`/wells`). |
| **`AdvisorPanel`** | [`AdvisorPanel.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AdvisorPanel.tsx) | Side Drawer / Panel | Displays operational anomaly recommendations and 1-click execution actions. Used in `Well Monitor` (`/wells/$wellId`). |
| **`StatusPill`** | [`ui.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/ui.tsx) | Badge / Pill | Status indicator badge with tone colors (`normal`, `info`, `warning`, `critical`). Used globally in Topbar and tables. |
| **`KpiCard`** | [`ui.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/ui.tsx) | KPI Stat Card | Compact KPI card displaying title, metric value, unit, trend indicator, and tone. Used in Fleet Cockpit and Reliability. |
| **`TimeSeriesChart`** | [`charts.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/charts.tsx) | Recharts Plot | Time-series telemetry line chart for electrical, hydraulic, thermal, and vibration signals. Used in `Well Monitor`. |

---

## 2. Engineering Domain Components (`src/components/esp/engineering/`)

| Component Name | File Path | Component Type | Purpose / Where Used |
| :--- | :--- | :--- | :--- |
| **`CurvePlot`** | [`CurvePlot.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/engineering/CurvePlot.tsx) | Recharts Plot | Interactive multi-axis pump performance curve ($H-Q$, $P-Q$, $\eta-Q$) with BEP & ROR overlays. Used in `Engineering Workbench` (`/engineering/workbench`). |
| **`GovernedContextPanel`** | [`GovernedContextPanel.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/engineering/GovernedContextPanel.tsx) | Spec / Gate Panel | Displays static head, friction loss, TDH calculations, and blocks calculations for non-calc-grade assemblies (`C1/D`). Used in `Engineering Workbench`. |
| **`CalculationGradeBadge`** | [`governance.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/engineering/governance.tsx) | Status Pill | Renders calculation grade ratings (`A1`, `A2`, `B1`, `B2`, `C1`, `D`) with color codes and tooltips. Used across all Engineering views. |
