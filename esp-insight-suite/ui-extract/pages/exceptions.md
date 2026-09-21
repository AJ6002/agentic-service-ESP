# Exceptions — `/exceptions`

## Meta
- **Route**: `/exceptions`
- **Title**: Exception & Opportunity Queue
- **Subtitle**: Operational anomaly triage, severity classification, and financial opportunity recovery.
- **Auth**: None (Public / Client-side mock)
- **Nav Order**: 3 (Operations Workspace)

## Shell
- **Topbar Variant**: Operations
- **Sidebar State**: Collapsed (56px)

## Regions (render order)
1. **Header & Summary Banner** — `flex items-center justify-between mb-3`
2. **Filter & Search Bar** — `flex flex-wrap gap-2 mb-3`
3. **Exceptions Grid / Triage Cards** — `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3`

## Blocks

### Header & Summary Banner
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Summary Header | Stat Banner | Top | 1 | "8 Active Exceptions · Total Deferment: 1,450 bpd ($108,750/day)" |

### Filter & Search Bar
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Severity Tabs | Filter Tabs | Left | 4 | `All (8)`, `Critical (3)`, `Warning (4)`, `Info (1)` |
| Category Dropdown | Select | Center | 1 | Categories: `Electrical`, `Hydraulic`, `Thermal`, `Mechanical`, `Comm` |
| Search Input | Input | Right | 1 | Filter by well name or trip code |

### Exceptions Triage Cards
| Block | Type | Position | Count | Notes |
|---|---|---|---|---|
| Exception Card | Card | Grid Items | 8 cards | Detailed anomaly card per well |

## Content
| Element | Label / Column / Value |
|---|---|
| Card Header | `ESP-104` — `Gas Interference` · `Critical` |
| Metrics | `PIP: 180 psi` · `Deferment: 320 bpd` · `Value Loss: $24,000/day` |
| Trigger Time | `Detected 2 hours ago (10:15 AM)` |
| Recommended Action | `Reduce VSD frequency to 50 Hz or inject anti-foam agent.` |
| Card Actions | `[Investigate Well]`, `[Acknowledge]`, `[Create Work Order]` |

## States
- **Filter State**: Switching tabs filters exception cards by severity.
- **Action Modal State**: Clicking `Create Work Order` opens a dialog modal to assign maintenance teams.
- **Empty State**: Shows "No active exceptions matching criteria. All ESP systems running within envelope."
