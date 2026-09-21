# Installed Fleet — `/engineering/installations`

## Meta
- **Route**: `/engineering/installations`
- **Title**: Installed ESP Systems & Assembly Fleet
- **Subtitle**: Downhole string assemblies, motor HP ratings, stage counts, and calculation-grade readiness tracking.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 9 (Configuration Workspace)

## Shell
- **Topbar Variant**: Configuration
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Installed Fleet Summary Bar** — `flex items-center justify-between mb-3`
2. **Filter & Search Controls** — `flex flex-wrap gap-2 mb-3`
3. **Installation Assembly Data Table** — `w-full border rounded-sm`

## Blocks

### Installed Fleet Summary Bar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Installation Summary Stats | Banner | Top | 1 | `25 Active ESP Systems · 18 Calculation-Grade (A1/A2) · 7 Data Incomplete` |

### Filter & Search Controls
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Calculation Grade Filter | Select | Left | 1 | `All Grades`, `A1/A2 (Calculation Grade)`, `C1/D (Restricted)` |
| Field Selector | Select | Center | 1 | `North Field`, `South Field`, `East Field` |

### Installation Assembly Data Table
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Assembly Table | Data Table | Full Width | 1 table (25 rows) | System ID, Well Name, Pump Model, Stages, Motor HP, Cable Type, Grade |

## Content
| Element | Label / Column / Value |
|---|---|
| Column 1 | **System ID & Well** (e.g. `SYS-ESP-101`, `ESP-101`) |
| Column 2 | **Pump Model & Stages** (e.g. `REDA DN1750 — 120 stages`) |
| Column 3 | **Motor Rating** (e.g. `Centrilift 150 HP / 4,160 V / 60 A`) |
| Column 4 | **Protector / Separator** (e.g. `BSLB Shroud + Rotary Separator`) |
| Column 5 | **Cable Spec** (e.g. `#4 AWG Flat EPDM / Monel Armor`) |
| Column 6 | **Setting Depth** (e.g. `6,850 ft TVD`) |
| Column 7 | **Install Date** (e.g. `2024-03-15`) |
| Column 8 | **Calculation Grade** (`A1 Verified`, `A2 Minor Gaps`, `C1 Unresolved`) |
| Column 9 | **Actions** (`[Inspect Assembly Detail]`, `[Edit Specification]`) |

## States
- **Grade Badge Color States**:
  - `A1 / A2`: Green pill — Calculation grade ready.
  - `B1 / B2`: Blue pill — Moderate calculation grade.
  - `C1 / D`: Red/Amber pill — Restricted, engineering calculations blocked.
