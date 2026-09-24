# Mock Data & Catalog Sources

This document describes all static mock data files powering the application.

---

## Data Files in `src/data/esp/`

1. [`fleet.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/fleet.ts):
   - Export: `wells` (Array of 25 wells across 3 fields), `fields` (Array of 3 field definitions: North, South, East Field).
2. [`exceptions.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/exceptions.ts):
   - Export: `needsAttention()` function returning wells with active alarms (gas lock, pump wear, VSD trips).
3. [`advisor.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/advisor.ts):
   - Export: `getAdvisorForWell(wellId)` returning AI/rule-based action recommendations.
4. [`reliability.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/reliability.ts):
   - Export: `getReliabilityData()` returning fleet MTBF, bad actor lists, and teardown failure modes.
5. [`series.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/series.ts):
   - Export: `getSeriesForWell(wellId)` returning historical time-series telemetry trends.
6. [`design-cases.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/design-cases.ts):
   - Export: `getDesignCases()` returning design vs actual operating point comparisons.
