# Data Types & Contracts Inventory

This document explains all data interfaces and shapes in simple words.

---

## 1. Fleet & Operations Types (`src/data/esp/types.ts`)

- **`EspWellSummary`**: Represents one ESP well in the operations fleet.
  - Fields: `id`, `name`, `field`, `state`, `healthIndex`, `freqHz`, `currentA`, `pipPsi`, `pdpPsi`, `motorTempF`, `runLifeDays`.
- **`EspException`**: Represents an active problem or alarm on a well.
  - Fields: `id`, `wellId`, `wellName`, `severity` (`critical`/`warning`/`info`), `title`, `description`, `defermentBpd`, `defermentValueUsd`, `detectedAt`, `recommendedAction`.
- **`EspAdvisorRecommendation`**: Operational advice generated for a well.
  - Fields: `wellId`, `hypothesis`, `confidencePct`, `recommendedActions`, `urgency`.

---

## 2. Master Data & Asset Definition Types (`src/domain/esp/asset-definition.ts`)

- **`AssetDefinitionContract`**: 16-section master document tracking equipment specs, installation depth, fluid properties, and OT tag mappings for calculation-grade verification.
- **`CalculationGrade`**: Rating score (`A1`, `A2`, `B1`, `B2`, `C1`, `D`) indicating whether a well has complete digitized data for engineering math calculations.
