# governance.tsx Barrel Component Analysis

## Identity
- **File**: `src/components/esp/engineering/governance.tsx`
- **Exports**: `CalculationGradeBadge`, `isCalculationGrade`, `RELIABILITY_CLASSES`
- **Kind**: Helper & Badge Barrel Component

## Purpose & Description in Simple Words
This component exports status badges and utility logic for rating assembly data completeness:
- **Calculation Grade Ratings**:
  - `A1 / A2`: Full calculation grade (Green badge).
  - `B1 / B2`: Moderate calculation grade (Blue badge).
  - `C1 / D`: Data incomplete / digitized curves missing (Red/Amber badge).

## Used By
- All pages under `/engineering/` routes.
