# Engineering Workbench — `/engineering/workbench`

## Meta
- **Route**: `/engineering/workbench`
- **Title**: Engineering Workbench — Pump Curve & Envelope Analysis
- **Subtitle**: Digitized pump performance curves ($H-Q, P-Q, \eta-Q$), TDH calculations, and frequency scenario simulations.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 12 (Configuration Workspace)

## Shell
- **Topbar Variant**: Configuration (`Editor / Configurator role` pill active)
- **Sidebar State**: Collapsed (56px) / Expanded (196px)

## Regions (render order)
1. **Workbench Context Header** — `flex items-center justify-between mb-3 border-b pb-2`
2. **Interactive Controls Strip** — `flex flex-wrap gap-3 mb-3 p-2 bg-card rounded-sm border`
3. **Main Engineering Curve Workspace** — `grid grid-cols-1 lg:grid-cols-12 gap-3 mb-3`
   - **Left Panel (8 cols)**: Recharts Interactive Curve Plot (`CurvePlot.tsx`)
   - **Right Panel (4 cols)**: Operating Point & Hydraulic Calculations (`GovernedContextPanel.tsx`)
4. **Frequency Scenario Simulator** — `w-full border rounded-sm p-3`

## Blocks

### Interactive Controls Strip
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Well / System Selector | Dropdown | Left | 1 | Select well assembly (e.g., `ESP-101 — REDA DN1750 120 stages`) |
| Frequency Slider | Range Input | Center | 1 | Operating frequency (`40.0 Hz` to `65.0 Hz`, step `0.5 Hz`) |
| Calculation Grade Pill | Status Badge | Right | 1 | Shows readiness (`A1 Calculation-Grade` or `C1 Unresolved`) |

### Main Engineering Curve Workspace
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Pump Curve Plot | Custom Recharts Chart (`CurvePlot.tsx`) | Left (8 cols) | 1 | Plots Head ($H$), Power ($P$), and Efficiency ($\eta$) vs Rate ($Q$), overlaid with BEP & ROR |
| Governed Context Panel | Parameter Panel | Right (4 cols) | 1 | Displays static head, friction loss, TDH, operating point coordinates, and calculation gating |

### Frequency Scenario Simulator
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Frequency Comparison Table | Comparison Matrix | Full Width | 1 table | Performance metrics across `45 Hz`, `50 Hz`, `55 Hz`, `60 Hz` |

## Content
| Element | Label / Column / Value |
|---|---|
| Selected Pump | `REDA DN1750 — 120 Stages @ 60 Hz` |
| Best Efficiency Point (BEP) | `1,750 bpd @ 3,450 ft TDH (Efficiency: 68.5%)` |
| Recommended Operating Range (ROR) | `1,200 bpd to 2,200 bpd` |
| Current Operating Point | `1,420 bpd @ 3,820 ft TDH (Frequency: 55 Hz)` |
| Calculation Gating | `Calculation Grade: A1 (Digitized Curve & Complete Assembly Verified)` |

## States
- **Calculation Gated State**: If an assembly is rated `C1` or `D` (incomplete data), the workbench **blocks** simulation graphs and displays a warning banner: `"Engineering calculations restricted: Assembly data incomplete or missing digitized pump curve."`
- **Interactive Slider State**: Moving the frequency slider dynamically recalculates affinity laws ($Q_2 = Q_1 \cdot \frac{f_2}{f_1}$, $H_2 = H_1 \cdot (\frac{f_2}{f_1})^2$) and updates chart curves instantly.
