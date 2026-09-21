# EspWellVisual Component Analysis

## Identity
- **File**: `src/components/esp/EspWellVisual.tsx`
- **Export**: `EspWellVisual` (Named Export)
- **Kind**: SVG Graphic Component

## Props
| Prop | Type | Required | Default | Purpose in Simple Terms |
|---|---|---|---|---|
| `wellId` | `string` | Yes | N/A | ID of the well to render downhole string geometry for. |

## Purpose & Description in Simple Words
This component renders an interactive diagram showing what an Electric Submersible Pump looks like inside an oil well deep underground. It draws the outer casing pipe, inner tubing, pump intake, pump stages, protector seal, electric motor, and downhole pressure sensor.

## Render Hierarchy
```text
EspWellVisual
├── SVG Viewport Frame
│   ├── Wellhead Surface Tree (Top Graphic)
│   ├── Outer Casing Pipe Boundaries
│   ├── Production Tubing String
│   ├── ESP Pump Section (Multi-stage impellers)
│   ├── Pump Intake & Gas Separator Graphic
│   ├── Motor Protector Seal Section
│   ├── Submersible Electric Motor Section
│   └── Downhole Pressure & Temperature Sensor Card
```

## Data Source
- **Data File**: [`src/data/esp/fleet.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/fleet.ts)

## Used By
- [`src/routes/wells.$wellId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.$wellId.tsx)
