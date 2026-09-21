# FleetTable Component Analysis

## Identity
- **File**: `src/components/esp/FleetTable.tsx`
- **Export**: `FleetTable` (Named Export)
- **Kind**: Data Table Component

## Props
| Prop | Type | Required | Default | Purpose in Simple Terms |
|---|---|---|---|---|
| `wells` | `EspWellSummary[]` | Yes | N/A | List of well data objects to render in table rows. |
| `selectedField` | `string` | No | `"all"` | Filter criteria for displaying wells in a specific field. |

## Purpose & Description in Simple Words
This component renders the primary operations data table listing all 25 ESP wells. It displays operational status badges, electrical current, operating frequency, intake/discharge pressure, motor temperature, run life, health index, and quick links to open the single-well monitor view.

## Used By
- [`src/routes/index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/index.tsx)
- [`src/routes/wells.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.index.tsx)
