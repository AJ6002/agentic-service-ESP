# Governance Validation — `/engineering/governance/validation`

## Meta
- **Route**: `/engineering/governance/validation`
- **Title**: Governance Validation & Calculation-Grade Audit
- **Subtitle**: Automated audit matrix verifying calculation-grade (`A1-D`) assembly readiness, missing tags, and curve digitization completeness.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 11 (Configuration Workspace)

## Shell
- **Topbar Variant**: Configuration
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Governance Audit Summary** — `grid grid-cols-1 md:grid-cols-4 gap-3 mb-3`
2. **Audit Sub-Navigation Tabs** — `flex border-b mb-3`
3. **Validation Matrix & Exception Table** — `w-full border rounded-sm`

## Blocks

### Governance Audit Summary
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Calculation Grade (A1/A2) | KPI Card | Col 1 | 1 | `18 / 25 Assemblies Ready (72%)` |
| Missing Tag Bindings | KPI Card | Col 2 | 1 | `12 Tags Unbound` |
| Digitization Gaps | KPI Card | Col 3 | 1 | `3 Pump Models Missing HQ Curves` |
| Data Provenance Score | KPI Card | Col 4 | 1 | `94.2% Complete` |

### Audit Sub-Navigation Tabs
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Governance Sub-Routes | Tabs | Top | 4 tabs | `Validation Matrix`, `Data Sources`, `Data Quality`, `Import Wizard` |

### Validation Matrix Table
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Audit Grid | Data Table | Full Width | 1 table | Lists all 25 wells with breakdown of 16 provenance contract sections |

## Content
| Element | Label / Column / Value |
|---|---|
| Audit Checklist Items | 1. Pump OEM Model & Stages<br>2. Digitized Curve Data Points<br>3. Motor Electrical Specs<br>4. Fluid PVT Properties<br>5. Wellbore Trajectory<br>6. OT Tag Signal Mappings |
| Status Indicator | Green Checkmark (`Pass`), Yellow Warning (`Minor Gap`), Red X (`Blocking Exception`) |

## States
- **Block Gate State**: Shows explicit reason why engineering calculations are blocked for wells rated `C1` or `D`.
- **Import Wizard Modal State**: Navigating to `/engineering/governance/import` launches a 4-step file import wizard for uploading pump curves (CSV / LAS format).
