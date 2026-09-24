# CurvePlot Component Analysis

## Identity
- **File**: `src/components/esp/engineering/CurvePlot.tsx`
- **Export**: `CurvePlot` (Named Export)
- **Kind**: Engineering Chart Component

## Purpose & Description in Simple Words
This component renders an interactive multi-axis engineering chart for evaluating ESP pump performance. It plots:
- **Head Curve ($H-Q$)**: Pump pressure lift versus fluid flow rate.
- **Power Curve ($P-Q$)**: Motor horsepower consumption versus fluid flow rate.
- **Efficiency Curve ($\eta-Q$)**: Pump efficiency percentage versus fluid flow rate.
- **Overlays**: Best Efficiency Point (BEP) and Recommended Operating Range (ROR).

## Used By
- [`src/routes/engineering.workbench.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.workbench.tsx)
- [`src/routes/engineering.catalog.pumps.$modelId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.catalog.pumps.$modelId.tsx)
