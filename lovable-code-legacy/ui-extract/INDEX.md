# ADVAIT ESP-PMM — UI Route Index & Page Map

This document serves as the master navigation map and page index for the **ADVAIT ESP-PMM** (*ESP Performance Monitoring & Management*) mock frontend suite.

---

## Workspace Route Map

```text
ADVAIT ESP-PMM (Global Shell)
├── Workspace: Operations
│   ├── /                             Fleet Cockpit (Operations Surveillance Overview)
│   ├── /wells                        Well Directory (Fleet List View)
│   ├── /wells/:wellId                Well Monitor (Single Well Telemetry & Downhole Schematic)
│   ├── /exceptions                   Exceptions (Operational Anomaly & Opportunity Queue)
│   ├── /troubleshooting              Troubleshooting (Guided Diagnostics & VSD Trip Lookup)
│   ├── /reliability                  Reliability (Run Life, Bad Actors & Teardown Analysis)
│   └── /reports                      Reports (Field Scorecards & Deferment Summaries)
└── Workspace: Configuration
    ├── /engineering                  Engineering Home (Master Data Overview)
    ├── /engineering/catalog          Equipment Catalog (OEM Pumps, Motors & Digitized Curves)
    ├── /engineering/catalog/pumps/:id Pump Model Detail (Performance Specifications & Curves)
    ├── /engineering/installations    Installed Fleet (ESP System Assembly Inventory)
    ├── /engineering/installations/:id Installation Detail (String Assembly & Calculation Grade)
    ├── /engineering/definition       Well Definition (Governed Revisions & Tag Mapping)
    ├── /engineering/governance/val   Governance Validation (A1-D Calculation Readiness)
    ├── /engineering/workbench        Engineering Workbench (Curve Plotting & Scenario Simulations)
    ├── /engineering/design-cases     Design Cases (Design vs Operating Point Comparison)
    └── /administration               Administration (OTConnex & Asset ConneX Integrations)
```

---

## Page Summaries

| Page / Route | Workspace | Description | Key Components |
| :--- | :--- | :--- | :--- |
| **[Fleet Cockpit](pages/fleet-cockpit.md)** (`/`) | Operations | Real-time surveillance dashboard for the entire 25-well ESP fleet across 3 fields. | `FleetKpiRow`, `ExceptionCounters`, `FleetTable`, `FieldSummaryCard` |
| **[Well Monitor](pages/well-monitor.md)** (`/wells/$wellId`) | Operations | Deep-dive single-well telemetry, downhole physical assembly schematic, and advisor. | `EspWellVisual`, `GaugeRow`, `PressureProfile`, `AdvisorPanel`, `TrendCharts` |
| **[Exceptions Queue](pages/exceptions.md)** (`/exceptions`) | Operations | Operational exception and opportunity triage queue for wells with alarms or trips. | `ExceptionCard`, `SeverityFilterTabs`, `ActionDialog`, `DefermentBadge` |
| **[Troubleshooting](pages/troubleshooting.md)** (`/troubleshooting`) | Operations | Interactive diagnostic decision trees, root cause isolation, and VSD trip code lookup. | `DiagnosticFlowchart`, `TripCodeLookupTable`, `GuidedStepsList` |
| **[Reliability](pages/reliability.md)** (`/reliability`) | Operations | MTBF statistics, run life distributions, teardown findings, and bad actor well analysis. | `MtbfKpiCard`, `RunLifeDistributionChart`, `TeardownTable`, `InterventionPlanner` |
| **[Reports](pages/reports.md)** (`/reports`) | Operations | Executive scorecards, weekly field performance summaries, and printable reports. | `FieldScorecardTable`, `DefermentBarChart`, `ExportButton`, `SummaryGrid` |
| **[Engineering Workbench](pages/engineering-workbench.md)** (`/engineering/workbench`) | Configuration | Curve plotting ($H-Q, P-Q, \eta-Q$), TDH calculation, and frequency scenario simulation. | `CurvePlot`, `OperatingPointOverlay`, `FrequencySlider`, `TdhCalculator` |
| **[Equipment Catalog](pages/engineering-catalog.md)** (`/engineering/catalog`) | Configuration | Master equipment catalog for OEM pumps, motors, gas separators, and cables. | `CatalogGrid`, `PumpModelCard`, `DigitizationBadge`, `CurveCompletenessIndicator` |
| **[Installed Fleet](pages/engineering-installations.md)** (`/engineering/installations`) | Configuration | Installed ESP string assembly inventory and component specification breakdown. | `InstallationTable`, `AssemblySpecList`, `CalculationGradeBadge` |
| **[Governance Validation](pages/engineering-governance.md)** (`/engineering/governance/validation`) | Configuration | Audit matrix verifying calculation-grade (`A1-D`) assembly readiness and missing tags. | `ValidationMatrixTable`, `MissingTagAlert`, `DigitizationAuditCard` |
| **[Administration](pages/administration.md)** (`/administration`) | Configuration | Platform integration settings (OTConnex tag mappings, Asset ConneX template links). | `IntegrationStatusCard`, `TagMappingTable`, `ThresholdOverrideForm` |
