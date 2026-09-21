# Reports — `/reports`

## Meta
- **Route**: `/reports`
- **Title**: Reports & Executive Field Scorecards
- **Subtitle**: Fleet availability, weekly performance scorecards, production deferment analysis, and printable reports.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 6 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Report Header & Controls** — `flex items-center justify-between mb-3`
2. **Field Availability & Deferment Grid** — `grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3`
3. **Weekly Field Scorecard Table** — `w-full border rounded-sm`

## Blocks

### Report Header & Controls
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Date Range Picker | Select / DatePicker | Top-Left | 1 | `Last 7 Days`, `Last 30 Days`, `Quarter-to-Date`, `Custom` |
| Export Controls | Button Group | Top-Right | 2 | `[Export CSV]`, `[Print / Export PDF]` |

### Field Availability & Deferment Grid
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Production Availability % | Gauge Card | Left | 1 | `96.4% Fleet Uptime` |
| Deferment Category Breakdown | Stacked Bar Chart | Right | 1 | `Unplanned Downtime vs Planned Maintenance vs Choke Curtailment` |

### Weekly Field Scorecard Table
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Field Scorecard | Data Table | Full Width | 1 table | Performance metrics breakdown grouped by `North Field`, `South Field`, and `East Field` |

## Content
| Element | Label / Column / Value |
|---|---|
| North Field Row | `Active Wells: 10` · `Target bpd: 15,000` · `Actual bpd: 14,250` · `Uptime: 95.0%` |
| South Field Row | `Active Wells: 8` · `Target bpd: 12,000` · `Actual bpd: 11,800` · `Uptime: 98.3%` |
| East Field Row | `Active Wells: 7` · `Target bpd: 9,500` · `Actual bpd: 9,100` · `Uptime: 95.7%` |
| Summary Total | `Fleet Total: 25 Wells` · `Target: 36,500 bpd` · `Actual: 35,150 bpd` · `Deferment: 1,350 bpd` |

## States
- **Print Preview State**: Triggering `[Print / Export PDF]` renders CSS print layout optimized for A4/Letter export.
