# Reliability — `/reliability`

## Meta
- **Route**: `/reliability`
- **Title**: ESP Reliability & Teardown Analytics
- **Subtitle**: Run life metrics, MTBF statistics, bad actors ranking, and teardown failure mode findings.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 5 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Reliability Summary KPIs** — `grid grid-cols-1 md:grid-cols-4 gap-3 mb-3`
2. **Run Life & Failure Analytics Section** — `grid grid-cols-1 lg:grid-cols-12 gap-3 mb-3`
   - **Left (6 cols)**: Run Life Distribution Histogram (`Recharts Bar`)
   - **Right (6 cols)**: Failure Mode Breakdown Donut Chart (`Recharts Pie`)
3. **Bad Actors & Intervention Table** — `w-full border rounded-sm`

## Blocks

### Reliability Summary KPIs
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Fleet MTBF | KPI Card | Col 1 | 1 | `Mean Time Between Failures: 642 days` |
| Active Run Days | KPI Card | Col 2 | 1 | `Total Fleet Run Time: 12,450 days` |
| Pull Rate (Annualized) | KPI Card | Col 3 | 1 | `0.18 pulls / well / year` |
| Bad Actor Count | KPI Card | Col 4 | 1 | `4 wells with >2 pulls in 24 months` |

### Run Life & Failure Analytics
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Run Life Distribution | Bar Chart | Left (6 cols) | 1 | Days bucketed (`<100`, `100-300`, `300-600`, `600-1000`, `>1000`) |
| Failure Modes | Donut / Pie Chart | Right (6 cols) | 1 | Categories: `Electrical (35%)`, `Gas/Solids Wear (28%)`, `Scale (15%)`, `Mechanical (22%)` |

### Bad Actors Table
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Bad Actors Inventory | Data Table | Full Width | 1 table (10 rows) | Displays well ID, pull count, last failure mode, teardown cause, and recommended redesign |

## Content
| Element | Label / Column / Value |
|---|---|
| Bad Actor Row 1 | `ESP-204` — `Pulls: 3 in 18 mo` · `Failure Cause: Motor Winding Insulation Breakdown (Thermal)` |
| Teardown Finding | `"Excessive scale buildup around motor shroud restricted cooling flow."` |
| Action | `[Schedule Workover Redesign]`, `[View Teardown Report PDF]` |

## States
- **Teardown Modal State**: Clicking `View Teardown Report` opens a dialog modal with photos, lab findings, and failed component analysis.
- **Filter State**: Filter reliability statistics by Manufacturer (e.g. `Schlumberger`, `Baker Hughes`, `Borets`).
