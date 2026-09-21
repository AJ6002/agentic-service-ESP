# AdvisorPanel Component Analysis

## Identity
- **File**: `src/components/esp/AdvisorPanel.tsx`
- **Export**: `AdvisorPanel` (Named Export)
- **Kind**: Panel / Action Drawer

## Props
| Prop | Type | Required | Default | Purpose in Simple Terms |
|---|---|---|---|---|
| `wellId` | `string` | Yes | N/A | The unique name/ID of the well being inspected (e.g. `ESP-104`). |

## Imports
- **Primitives (`ui/`)**: None (uses raw HTML buttons and tags with Tailwind classes)
- **Siblings (`esp/`)**: `StatusPill` from `@/components/esp/ui`
- **Data**: `getAdvisorForWell` from `@/data/esp/advisor`

## Render Hierarchy
```text
AdvisorPanel
├── Header Region (Title: ESP Surveillance & Action Advisor)
├── Anomaly Status Banner (StatusPill + Well Name)
├── Root Cause Section (Hypothesis & Diagnostic Confidence score)
├── Action Recommendations List (Step-by-step instructions)
└── Action Buttons (Acknowledge Alarm / Execute Recommendation)
```

## Regions (as seen on screen)
1. **Advisor Header**: Shows panel title and well identifier.
2. **Diagnosis Banner**: Highlights active problem and confidence percentage.
3. **Recommended Actions List**: Numbered checklist of operational adjustments.

## Sub-elements
| Element | Type | Location | Labels / content in Simple Terms |
|---|---|---|---|
| Panel Header | Title | Top | "ESP Surveillance & Action Advisor" |
| Status Badge | StatusPill | Top Right | "Critical" or "Warning" badge |
| Confidence Rating | Text | Center | "85% Confidence — Diagnostic Match" |
| Action Button | Button | Bottom | "Apply Frequency Adjustment (50 Hz)" |

## States
| State | Trigger | Visual Effect |
|---|---|---|
| Normal | Well running smoothly | Green checkmark with "No active actions required." |
| Anomaly Active | Problem detected | Yellow/Red alert box with action recommendations. |

## Interactions
| Trigger | Handler | Effect |
|---|---|---|
| Click Action Button | `onClick` | Simulates sending an adjustment command to the well. |

## Data Source
- **Data File**: [`src/data/esp/advisor.ts`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/data/esp/advisor.ts)

## Used By
- [`src/routes/wells.$wellId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.$wellId.tsx)
