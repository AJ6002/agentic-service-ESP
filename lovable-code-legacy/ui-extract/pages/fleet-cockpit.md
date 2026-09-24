# Fleet Cockpit — `/`

## Meta
- **Route**: `/`
- **Title**: Fleet Cockpit
- **Subtitle**: ESP fleet surveillance & operating state overview across 3 fields and 25 ESP wells.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 1 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations (Field scope selector visible: `All fields (3)`)
- **Sidebar State**: Collapsed by default (56px) / Expandable (196px)

## Regions (render order)
1. **Header Toolbar** — `flex justify-between items-center mb-3`
2. **Fleet KPI Summary Strip** — `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-3`
3. **Exception & Alarm Counters Bar** — `flex flex-wrap gap-2 mb-3`
4. **Main Operations Fleet Table** — `w-full border rounded-sm overflow-hidden`

## Blocks

### Header Toolbar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Page Title & Subtitle | Header | Top-Left | 1 | "Fleet Cockpit — Real-time surveillance" |
| Field Selector | Select Dropdown | Top-Right | 1 | Filter by North, South, East Field |

### Fleet KPI Summary Strip
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Active Wells | KPI Card | Col 1 | 1 | "25 / 25" total monitored |
| Critical Exceptions | KPI Card | Col 2 | 1 | Count of wells in `critical` severity |
| Production Deferment | KPI Card | Col 3 | 1 | Total lost volume in `bpd` |
| Deferment Value | KPI Card | Col 4 | 1 | Financial opportunity loss in `$/day` |
| Mean Run Life | KPI Card | Col 5 | 1 | Average run time in `days` |
| Fleet Health Index | KPI Card | Col 6 | 1 | Composite percentage health (0–100%) |

### Exception & Alarm Counters Bar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Severity Filter Chips | Chip Row | Span Full | 4 | "All (25)", "Critical (3)", "Warning (5)", "Normal (17)" |

### Main Operations Fleet Table
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Fleet Operations Table | Data Table | Full Width | 1 table (25 rows) | Displays well status, electrical & hydraulic metrics |

## Content
| Element | Label / Column / Value |
|---|---|
| Column 1 | **Well Name & Field** (e.g. `ESP-101`, `North Field`) |
| Column 2 | **Status / State** (`Normal Running`, `Gas Interference`, `VSD Trip`, `Pump Wear`, `Motor Overload`) |
| Column 3 | **Frequency** (`Hz` — e.g. `55.0 Hz`) |
| Column 4 | **Current / Load** (`A` / `%` — e.g. `62 A / 85%`) |
| Column 5 | **PIP** (`Intake Pressure, psi` — e.g. `340 psi`) |
| Column 6 | **Discharge Pressure** (`psi` — e.g. `1,420 psi`) |
| Column 7 | **Motor Temp** (`°F` — e.g. `185°F`) |
| Column 8 | **Run Life** (`days` — e.g. `412 days`) |
| Column 9 | **Health Index** (`%` indicator pill — e.g. `92%`) |
| Column 10 | **Actions** (`View Monitor` link -> `/wells/$wellId`) |

## States
- **Field Filter State**: Interactively filters table rows by `North Field`, `South Field`, or `East Field`.
- **Severity Filter State**: Clicking severity chips filters the displayed wells by alert level.
- **Hover State**: Table rows highlight on hover; action buttons glow.
- **Empty State**: Displays "No wells found matching the selected filter criteria" if filters yield 0 rows.
