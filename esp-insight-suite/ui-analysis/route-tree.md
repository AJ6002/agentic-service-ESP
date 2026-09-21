# Route Tree & Navigation Graph

This document explains all pages and links in the app in simple, easy-to-understand terms.

---

## What is a Route?
A route is simply a web address (URL) that leads to a specific page inside the application.

---

## Overview of App Pages (36 Routes)

```text
/ (Root Layout: RootShell & AppShell)
├── /                                   Fleet Cockpit Page
├── /administration                     System Administration & Integration Settings Page
├── /asset-definition                   Redirect / Asset Definition Page
├── /asset-definitions                  Asset Definitions Overview Page
├── /design-cases                       Design Cases Redirect Page
├── /exceptions                         Exceptions & Alarms Triage Page
├── /reliability                        Fleet Reliability & Teardown Analytics Page
├── /reports                            Executive Scorecards & Reports Page
├── /troubleshooting                    Guided ESP Diagnostic Tree Page
├── /workbench                          Engineering Workbench Redirect Page
├── /wells                              Well Directory Page
│   └── /wells/$wellId                  Single Well Telemetry & Monitor Page
└── /engineering                        Engineering Master Layout
    ├── /engineering/                   Engineering Overview Page
    ├── /engineering/workbench          Engineering Workbench & Pump Curve Simulator Page
    ├── /engineering/design-cases       Engineering Design Cases Page
    ├── /engineering/catalog            Equipment Catalog Section
    │   ├── /engineering/catalog/       Catalog Main List Page
    │   └── /engineering/catalog/pumps/$modelId  Pump Model Specification Page
    ├── /engineering/installations      Installed Fleet Section
    │   ├── /engineering/installations/ Installed Systems List Page
    │   ├── /engineering/installations/$systemId System Assembly Detail Page
    │   ├── /engineering/installations/assembly Assembly Specification Page
    │   ├── /engineering/installations/fluid Fluid Properties Page
    │   ├── /engineering/installations/limits Well Operating Limits Page
    │   └── /engineering/installations/well Wellbore Trajectory Page
    ├── /engineering/definition         Well Definition Section
    │   ├── /engineering/definition/    Definitions Index Page
    │   └── /engineering/definition/$wellId Well Definition Detail Page
    └── /engineering/governance         Engineering Governance Section
        ├── /engineering/governance/    Governance Overview Page
        ├── /engineering/governance/import Pump Curve Import Wizard Page
        ├── /engineering/governance/quality Data Quality Audit Page
        ├── /engineering/governance/sources Data Sources Audit Page
        └── /engineering/governance/validation Assembly Calculation Grade Matrix Page
```

---

## Detailed Route List

| Path | Component File | Type | Parent Route | Description in Simple Terms |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `src/routes/index.tsx` | Page | Root (`__root.tsx`) | Main dashboard showing live operational status of all 25 wells across 3 fields. |
| `/wells` | `src/routes/wells.index.tsx` | Page | Root (`__root.tsx`) | List of all wells in the fleet for quick selection. |
| `/wells/$wellId` | `src/routes/wells.$wellId.tsx` | Page | Root (`__root.tsx`) | Detailed monitoring page for a single well showing gauges, pump drawing, and advisor. |
| `/exceptions` | `src/routes/exceptions.tsx` | Page | Root (`__root.tsx`) | List of open alarms and problems requiring immediate attention. |
| `/troubleshooting` | `src/routes/troubleshooting.tsx` | Page | Root (`__root.tsx`) | Step-by-step diagnostic guide and fault code lookup tool. |
| `/reliability` | `src/routes/reliability.tsx` | Page | Root (`__root.tsx`) | Statistics on pump life, failure reasons, and problem wells. |
| `/reports` | `src/routes/reports.tsx` | Page | Root (`__root.tsx`) | Summary reports and field performance scorecards. |
| `/engineering` | `src/routes/engineering.tsx` | Layout | Root (`__root.tsx`) | Main wrapper layout for all technical engineering pages. |
| `/engineering/workbench` | `src/routes/engineering.workbench.tsx` | Page | `/engineering` | Interactive graph showing pump performance curves and operating points. |
| `/engineering/catalog` | `src/routes/engineering.catalog.index.tsx` | Page | `/engineering` | Equipment catalog containing pump models, motors, and specs. |
| `/engineering/catalog/pumps/$modelId` | `src/routes/engineering.catalog.pumps.$modelId.tsx` | Page | `/engineering/catalog` | Specifications and curve data for a specific pump model. |
| `/engineering/installations` | `src/routes/engineering.installations.index.tsx` | Page | `/engineering` | List of installed pump assemblies inside active wells. |
| `/engineering/installations/$systemId` | `src/routes/engineering.installations.$systemId.tsx` | Page | `/engineering/installations` | Equipment breakdown for a specific installed pump assembly. |
| `/engineering/governance/validation` | `src/routes/engineering.governance.validation.tsx` | Page | `/engineering/governance` | Audit table checking if data is complete enough for math calculations. |
| `/administration` | `src/routes/administration.tsx` | Page | Root (`__root.tsx`) | Settings for data connections and alarm limits. |
