# GovernedContextPanel Component Analysis

## Identity
- **File**: `src/components/esp/engineering/GovernedContextPanel.tsx`
- **Export**: `GovernedContextPanel` (Named Export)
- **Kind**: Context & Validation Guard Panel

## Purpose & Description in Simple Words
This component displays the underlying mathematical parameters used for engineering calculations (static lift, friction loss, Total Dynamic Head). It checks whether the selected well assembly is **Calculation Grade** (`A1`/`A2`). If data is missing (`C1`/`D`), it blocks calculation graphs and displays a warning banner.

## Used By
- [`src/routes/engineering.workbench.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.workbench.tsx)
