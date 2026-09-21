# ui.tsx Barrel Component Analysis

## Identity
- **File**: `src/components/esp/ui.tsx`
- **Exports**: `StatusPill`, `KpiCard`, `SectionHeader`, `SummaryBanner`
- **Kind**: Shared UI Element Barrel

## Purpose & Description in Simple Words
This file contains small reusable visual building blocks used across all pages in the app:
1. `StatusPill`: A small colored badge displaying system status (Green = normal, Yellow = warning, Red = critical, Gray = info).
2. `KpiCard`: A rectangular summary card showing key numbers like total active wells or daily deferment loss.
3. `SectionHeader`: Standardized title and description headers for page sections.

## Used By
- Almost every page in `src/routes/` and components in `src/components/esp/`.
