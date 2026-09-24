# Well Monitor — `/wells/$wellId`

## Meta
- **Route**: `/wells/$wellId` (Sample IDs: `ESP-101`, `ESP-104`, `ESP-201`)
- **Title**: Well Monitor — ESP Operational Telemetry
- **Subtitle**: Single-well physical schematic, electrical & hydraulic gauges, pressure profile, and AI advisor recommendations.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 2 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations (Field scope selector visible)
- **Sidebar State**: Collapsed by default (56px)

## Regions (render order)
1. **Well Header & Breadcrumb** — `flex items-center justify-between mb-3 border-b pb-2`
2. **Telemetry Gauge Strip** — `grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-3`
3. **Main Diagnostics Viewport** — `grid grid-cols-1 lg:grid-cols-12 gap-3 mb-3`
   - **Left Column (4 cols)**: Downhole Physical Schematic (`EspWellVisual`)
   - **Center Column (5 cols)**: Pressure Profile & Operating Trends
   - **Right Column (3 cols)**: Advisor Panel & Automated Action Recommendations
4. **Historical Telemetry Tabs & Trend Graphs** — `w-full border rounded-sm p-3`

## Blocks

### Telemetry Gauge Strip
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Operating Frequency | Gauge / Stat | Col 1 | 1 | Unit: `Hz` (e.g., `55.0 Hz`) |
| Motor Current | Gauge / Stat | Col 2 | 1 | Unit: `A` (e.g., `64.2 A`) |
| Voltage | Gauge / Stat | Col 3 | 1 | Unit: `V` (e.g., `4,160 V`) |
| Pump Intake Pressure (PIP)| Gauge / Stat | Col 4 | 1 | Unit: `psi` (e.g., `340 psi`) |
| Discharge Pressure | Gauge / Stat | Col 5 | 1 | Unit: `psi` (e.g., `1,420 psi`) |
| Motor Temperature | Gauge / Stat | Col 6 | 1 | Unit: `°F` (e.g., `185°F`) |
| Vibration | Gauge / Stat | Col 7 | 1 | Unit: `in/s` (e.g., `0.12 in/s`) |

### Main Diagnostics Viewport
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Downhole Assembly Schematic | Custom SVG Visual (`EspWellVisual`) | Col Span 4 | 1 | Visualizes surface tree, casing, tubing, intake, pump, protector, motor, and P/T gauge |
| Pressure Profile Graph | Area/Line Chart (`PressureProfile`) | Col Span 5 | 1 | Depth vs Pressure gradient (Reservoir -> PIP -> Discharge -> Wellhead) |
| Advisor Panel | Action Drawer / Panel (`AdvisorPanel`) | Col Span 3 | 1 | Displays current operating anomaly, root cause hypothesis, and 1-click recommended actions |

### Historical Telemetry Tabs & Trend Graphs
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Time-series Trends | Tabbed Recharts Plot (`charts.tsx`) | Full Width | 4 tabs | Tabs: `Electrical (Hz/A/V)`, `Hydraulic (PIP/Pdp)`, `Thermal (°F)`, `Vibration` |

## Content
| Element | Label / Column / Value |
|---|---|
| Well Header | `ESP-104 — South Field` · `Status: Suspected Gas Interference` · `Health: 68%` |
| Gauge 1 | Frequency: `52.5 Hz` (Target: `55.0 Hz`) |
| Gauge 2 | PIP: `210 psi` (Warning: `< 250 psi`) |
| Advisor Recommendation | `"Increase choke size by 5% or decrease frequency to 50 Hz to mitigate gas lock risk."` |
| Action Buttons | `[Acknowledge Alarm]`, `[Apply Frequency Adjustment]`, `[Open Troubleshooting Tree]` |

## States
- **Normal Running State**: All gauges rendered green, schematic indicates smooth fluid flow.
- **Gas Interference State**: PIP drops, motor current fluctuates wildly; schematic highlights gas bubbles at pump intake.
- **Motor Overload / High Temp State**: Temperature gauge turns red; advisor urges immediate current draw reduction.
- **VSD Trip State**: Gauges show `0 Hz`, `0 A`; status pill reads `TRIPPED — Code 42 (Overcurrent)`.
