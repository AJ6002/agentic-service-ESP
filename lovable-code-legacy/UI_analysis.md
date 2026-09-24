# UI Analysis — ADVAIT ESP-PMM
# ESP Performance Monitoring & Management

> Screen-by-screen walkthrough of the running dashboard.
> Describes what a user sees and what they can do — not how it is built.

---

## 0. Summary

| | |
|---|---|
| Total pages | 8 |
| Total views (tabs / drill-downs / filters) | 19 |
| Total overlays (modals / drawers) | 1 |
| Entry page | `/` — ESP Fleet Cockpit |

### Page index

| # | Page | Route | Type | Parent | Views | Overlays |
|---|---|---|---|---|---|---|
| 1 | ESP Fleet Cockpit | `/` | PAGE | — | 1 (field filter) | 0 |
| 2 | Well Monitor | `/wells/$wellId` | DRILL-DOWN | Fleet Cockpit | 6 tabs | 1 drawer |
| 3 | Exception & Opportunity Queue | `/exceptions` | PAGE | — | 6 filter views | 0 |
| 4 | Troubleshooting Assistant | `/troubleshooting` | PAGE | — | 1 (case selector) | 0 |
| 5 | Reliability & Run Life | `/reliability` | PAGE | — | 5 tabs | 0 |
| 6 | Management Scorecard & Reports | `/reports` | PAGE | — | 0 | 0 |
| 7 | Administration & Platform Integration | `/administration` | PAGE | — | 0 | 0 |
| 8 | Engineering (all sub-pages) | `/engineering/**` | LAYOUT + children | — | see §8 | 0 |

### Page hierarchy (tree)

```
/ (ESP Fleet Cockpit)
├── click well link ──► /wells/$wellId (Well Monitor)
│                           └── tabs: Overview, Trends, Operating point,
│                                     Pressure profile, ESP string,
│                                     Events & exceptions
│                           └── right rail: Advisor drawer
├── "Open full queue →" ──► /exceptions (Exception Queue)
│                           └── filter bar: All, Critical, Warning,
│                                           Watch, Opportunities, Unassigned
├── left rail ──► /troubleshooting (Troubleshooting Assistant)
├── left rail ──► /reliability     (Reliability & Run Life)
│                           └── tabs: Run life, Failure analysis,
│                                     Bad actors, Interventions, DIFA records
├── left rail ──► /reports         (Management Scorecard & Reports)
├── left rail ──► /administration  (Administration)
└── "Engineering Configuration →" ──► /engineering/** (Engineering pages)
```

---

## 1. ESP Fleet Cockpit

**Route:** `/`
**Type:** PAGE — default landing screen
**Reached from:** any browser opening the app, or the logo in the top-left corner
**Source file:** `src/routes/index.tsx`

### What the user sees

The Fleet Cockpit is the first screen that appears when the app loads. It shows the health and production status of all 25 ESP wells across 3 fields in one view. Everything on this page is read-only; the user clicks through to individual wells or the exceptions queue to take action.

### Screen anatomy (top → bottom)

1. **Global top bar** — logo, workspace switcher, field scope dropdown, live-connection status pills, user profile
2. **Left sidebar** — icon navigation rail (collapsed by default; hover for tooltip; click arrow at bottom to expand labels)
3. **Page header** — page title, description, data-source pills
4. **Field summary strip** — one pill per field showing well count and off-normal count; inside-ROR percentage pill; link to Engineering Configuration
5. **KPI strip** — 7 numbered metric tiles across the full width
6. **Main body — two-column grid**
   - Left column: "Needs attention now" table
   - Right column: "Optimization opportunities" table + "Open exceptions by category" bar list
7. **Lower body — two-column grid**
   - Left column: "Fleet register" full-width well table
   - Right column: "Selected well visual" panel + "Deferment & upside by field" bar chart + "Worst actors — health index" table

---

### Components on this page

#### Global top bar (every page)

| Element | What the user reads | Notes |
|---|---|---|
| Logo badge | AD | click goes to `/` |
| Application title | ADVAIT ESP-PMM \| ESP Performance Monitoring & Management | always visible |
| Workspace dropdown | Operations — Operations & surveillance / Configuration — Engineering configuration & admin | switches left-rail nav groups |
| Field scope dropdown | All fields (3) / Nardah North / Kalisto West / Tamrin Deep | Operations workspace only; filters KPIs and table in place |
| Status pill | OTConnex live · 2 s scan | live connection indicator |
| Status pill | {N} critical open | dynamic alarm count |
| User profile pill | VK · Ops Engineer | initials + role |

#### Global left sidebar (every page)

**Operations workspace nav items** (visible when workspace = Operations)

| Label | Tooltip hint | Route |
|---|---|---|
| Fleet Cockpit | ESP fleet surveillance overview | `/` |
| Well Monitor | Per-well ESP operations detail | `/wells` |
| Exceptions | Exception & opportunity queue | `/exceptions` |
| Troubleshooting | Guided ESP diagnostics | `/troubleshooting` |
| Reliability | Run life, DIFA, interventions | `/reliability` |
| Reports | Scorecards & print views | `/reports` |

**Configuration workspace nav items** (visible when workspace = Configuration)

| Label | Tooltip hint | Route |
|---|---|---|
| Engineering Home | Governed ESP master data overview | `/engineering` |
| Equipment Catalog | OEM pumps, motors, components | `/engineering/catalog` |
| Installed Fleet | Installed ESP systems & well engineering | `/engineering/installations` |
| Well Definition | Per-well governed revisions & tags | `/engineering/definition` |
| Governance | Validation, sources, quality, import | `/engineering/governance/validation` |
| Engineering Workbench | Curves, TDH, scenarios | `/engineering/workbench` |
| Design Cases | Design vs current vs what-if | `/engineering/design-cases` |
| Administration | Integrations & configuration | `/administration` |

#### Page header

| Element | What the user reads |
|---|---|
| Title | ESP Fleet Cockpit |
| Description | Centralised surveillance across 3 fields and 25 ESP wells. Ranked by production impact and reliability risk so intervention effort goes where it pays — fewer preventable trips, fewer repeat field visits, faster reaction. |
| Pill | Signals: OTConnex (SCADA · historian · VSD · downhole gauges) |
| Pill | Asset model: Asset ConneX ESP templates |
| Pill | Scope: ESP artificial lift · 25 wells · 3 fields |
| Pill | Demo price deck $68/bbl |
| Link | Engineering Configuration → |

#### Field summary strip

| Element | What the user reads | Notes |
|---|---|---|
| Label | ESP FLEET | section label |
| Pill per field | Nardah North · 9 wells · 6 off-normal | green or amber depending on ratio |
| Pill per field | Kalisto West · 9 wells · 7 off-normal | |
| Pill per field | Tamrin Deep · 7 wells · 4 off-normal | |
| Pill | Inside recommended range 88% | blue info pill |
| Link | Engineering Configuration → | navigates to `/engineering` |

#### KPI strip — 7 metric tiles

| KPI title | Sample value | Sub-label |
|---|---|---|
| Wells running | 22 / 25 | 3 down |
| Availability | 88 % | Run status weighted, 24 h |
| Fleet ESP health index | 65.7 | Weighted envelope + thermal + degradation |
| Oil rate | 26,052 bopd | Allocated, latest scan |
| Production deferment | 4,676 bopd | Vs expected from active cases |
| Optimization upside | 190 bopd | Illustrative scenario estimates |
| Value at stake | $330.9k /day | Deferment + upside |

#### Needs attention now (left panel)

Subtitle: *Ranked by severity then production impact — the operational queue for this shift*

Link in panel header: **Open full queue →** — navigates to `/exceptions`

**Attention queue table**

Columns (left → right): `Sev`, `Well`, `Category`, `Impact bopd`, `Age`, `Conf.`, `Owner`

Sample rows shown:
- critical · ESP-338 · VSD / power trip · 1,180 · 1 h · 86% · Unassigned
- critical · ESP-242 · Unplanned stop · 1,050 · 20 h · 82% · M. Okafor (Ops)
- critical · ESP-104 · Suspected gas interference / unstable amps · 168 · 12 h · 74% · A. Rahman (Prod Eng)
- critical · ESP-141 · VSD / power trip · 140 · 1 h · 86% · A. Rahman (Prod Eng)
- critical · ESP-219 · Suspected gas interference / unstable amps · 140 · 12 h · 74% · Unassigned
- critical · ESP-126 · Motor overload · 60 · 7 h · 77% · M. Okafor (Ops)
- warning · ESP-097 · Suspected pump wear / declining head per stage · 210 · 60 d · 68% · L. Vieira (Reliability)
- warning · ESP-271 · Suspected pump wear / declining head per stage · 130 · 60 d · 68% · Unassigned
- warning · ESP-285 · Outside ROR — low flow / downthrust · 120 · 1 d 20 h · 79% · M. Okafor (Ops)

Every well ID in the `Well` column is a clickable link that opens that well's Monitor page.

#### Optimization opportunities (right top panel)

Subtitle: *Healthy wells with envelope, thermal and electrical headroom*

**Opportunities table**

Columns: `Well`, `Basis`, `Upside`, `Conf.`

Sample rows:
- ESP-312 · Inside ROR AND load < 70% AND thermal margin... · $6.5k/d · 58%
- ESP-307 · Inside ROR AND choke restriction detected · $3.7k/d · 54%

Well IDs are clickable — they open the Engineering Workbench pre-loaded for that well.

#### Open exceptions by category (right bottom panel)

Subtitle: *Where surveillance effort is concentrated right now*

Horizontal progress bars, one per category, showing count. Categories seen on screen:
- Suspected gas interference / unstable amps · 2
- High motor temperature · 2
- Suspected pump wear / declining head per stage · 2
- Gauge communication / data quality · 2
- VSD / power trip · 2
- Outside ROR — low flow / downthrust · 2
- Unplanned stop · 2
- Optimization opportunity · 2

#### Fleet register (lower left panel)

Subtitle: *Actual vs envelope for every ESP well — click a well to open Well Monitor*

This is the main sortable well table. Every well ID is a link to `/wells/$wellId`.

**Fleet register table** — columns listed as they appear in `FleetTable`:

Columns: `Well`, `State`, `Field`, `Hz`, `Motor load %`, `Amps`, `PIP psi`, `PDP psi`, `Motor temp degF`, `Liquid bpd`, `Oil bopd`, `Health`, `ROR`, `Deferred bopd`

#### Selected well visual (lower right, top panel)

A compact animated ESP string diagram that shows the currently highlighted well from the Fleet register. A dropdown at the top right of the panel lets the user pick any well ranked by health index. Below the diagram, a status pill and an **Open Well Monitor →** link are shown.

**Deferment & upside by field (lower right, middle panel)**

**Deferment & upside by field chart**
- X axis: Field name (Nardah North, Kalisto West, Tamrin Deep)
- Y axis: Barrels per day
- Series: Deferred bopd (amber), Upside bopd (green)
- Tooltip shows: field name, deferred value, upside value

**Worst actors — health index (lower right, bottom panel)**

Columns: `Well`, `State`, `Health`, `Defer`

Shows the 8 wells with the lowest health index, each with a clickable well ID.

---

### Views on this page

| View | Trigger | What changes on screen |
|---|---|---|
| Field filter — Nardah North | select in topbar field dropdown | KPI strip, attention table, fleet register, and bar chart all update to show only that field's wells |
| Field filter — Kalisto West | same dropdown | same behaviour for Kalisto West wells |
| Field filter — Tamrin Deep | same dropdown | same behaviour for Tamrin Deep wells |
| Field filter — All fields (3) | same dropdown | returns to full 25-well view |
| Selected well visual | choose well in panel dropdown | ESP string diagram and status pill update to the chosen well |

### Overlays reachable from this page

None.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| Any well ID in "Needs attention now" | `/wells/ESP-xxx` | DRILL-DOWN |
| "Open full queue →" | `/exceptions` | PAGE |
| Any well ID in "Optimization opportunities" | `/engineering/workbench?well=ESP-xxx` | PAGE |
| Any well ID in Fleet register | `/wells/ESP-xxx` | DRILL-DOWN |
| Any well ID in "Worst actors" | `/wells/ESP-xxx` | DRILL-DOWN |
| "Open Well Monitor →" under visual | `/wells/ESP-xxx` | DRILL-DOWN |
| "Engineering Configuration →" in field strip | `/engineering` | PAGE |
| Topbar workspace → Configuration | `/engineering` | PAGE |
| Left rail nav item | corresponding page | PAGE |

### Notes

- The page title in the browser tab reads: **ESP Fleet Cockpit — ADVAIT ESP-PMM**
- The field scope dropdown only appears when the workspace is set to Operations.

---

## 2. Well Monitor

**Route:** `/wells/$wellId` (e.g. `/wells/ESP-104`)
**Type:** DRILL-DOWN
**Reached from:** clicking any well link on the Fleet Cockpit, the Exception Queue, the Troubleshooting Assistant, or the Reliability page
**Source file:** `src/routes/wells.$wellId.tsx`

### What the user sees

A full engineering and operational snapshot of one ESP well. The top section stays constant regardless of which tab is selected (page header, KPI strip, tab bar). Below the tab bar, content changes per tab. On the right side of every tab, an Advisor panel shows automated recommendations for this well.

### Screen anatomy (top → bottom)

1. **Page header** — well ID, field, pad name, state pill, pump model pill, data quality badge, last event pill, and four action buttons
2. **KPI strip** — 7 live metric tiles for this specific well
3. **Tab bar** — 6 tabs: Overview, Trends, Operating point, Pressure profile, ESP string, Events & exceptions
4. **Tab content area** — changes based on selected tab
5. **Advisor panel** — always visible on the right side, showing automated surveillance findings for this well

---

### Components on this page

#### Page header

| Element | What the user reads | Notes |
|---|---|---|
| Title | ESP-104 — Nardah North · Pad-B | well ID, field, pad |
| Description | e.g. "Suspected gas interference. Amps erratic since 10:15. PIP declining." | one-line operational story |
| Pill | current state label e.g. Gas interference | coloured by severity |
| Pill | field · pad name | grey info pill |
| Pill | OEM pump model · N stages | grey info pill |
| Badge | data quality indicator | shows completeness of live signals |
| Pill | Last event: Gas slug detected (12 h ago) | blue info pill |
| Button | ← ESP-103 | navigates to previous well |
| Button | ESP-105 → | navigates to next well |
| Button | Open in Engineering Workbench | navigates to Workbench pre-loaded for this well |
| Button | Governed asset definition | navigates to `/engineering/installations` |

#### KPI strip — 7 metric tiles

| KPI title | Sample value | Sub-label |
|---|---|---|
| ESP health index | 62 | Band: watch |
| Frequency | 52.5 Hz | Design 55.0 Hz |
| Motor load | 73 % | 64.2 A of 85 A rated |
| Motor temperature | 198 degF | Limit 210 degF |
| PIP / PDP | 210 / 1,380 psi | Design 320 / 1,450 |
| Liquid / oil | 1,420 / 820 bpd | −12% vs design liquid |
| Deferment | 320 bopd | $21,760/day |

#### Tab bar

Six tabs in order: **Overview**, **Trends**, **Operating point**, **Pressure profile**, **ESP string**, **Events & exceptions**

The active tab is underlined in the primary colour.

---

### Tab: Overview

The default tab when the well first opens. Shows four sub-panels arranged in a grid.

**ESP system visualization panel**

Subtitle: *Live simulated values bound to the string — hover or tab a marker for design comparison*

A detailed animated ESP string diagram showing the wellhead, tubing, pump stages, intake, protector, motor, and downhole gauge — annotated with live parameter values at each component.

**Operating state timeline panel**

Subtitle: *Last 24 hours — how the well arrived at its current state*

A horizontal colour bar spanning 24 hours (from −24 h to now), divided into coloured segments per operating state. Below the bar, a table lists each state period with its time window.

| Column | What it shows |
|---|---|
| State pill | state label in its severity colour |
| Time window | e.g. 10.0 h → 12.0 h |

**What changed panel**

Subtitle: *Signals that moved before the current state — the operational story*

Columns: `Signal`, `From`, `To`, `Window`

Sample row: PIP · 340 psi → 210 psi · last 12 h

**Operating envelope panel**

Subtitle: *Actual rate vs recommended operating range*

A horizontal bar graphic showing:
- A green band = the Recommended Operating Range (ROR)
- A blue vertical line = the Best Efficiency Point (BEP)
- A small coloured marker = the current actual rate

Below the graphic, four values are shown: `ROR min`, `ROR max`, `BEP`, `Q/Q_BEP`

A note below explains the envelope position in plain language, e.g.:
*Left of ROR by 180 bpd — downthrust wear exposure on stages and thrust bearing.*

**Operating point vs pump curve panel**

Subtitle: pump model at current Hz

A small pump head curve (H-Q) chart with a dot marking the current operating point.

- X axis: Rate bpd
- Y axis: Head ft
- Overlays: BEP marker, ROR shaded region, current operating point dot

**Total dynamic head panel**

Subtitle: *Deterministic engineering calculation*

| Row label | Sample value |
|---|---|
| Vertical / dynamic lift | 3,820 ft |
| Tubing friction | 210 ft |
| Wellhead backpressure | 120 ft |
| **Total dynamic head** | **4,150 ft** |
| Design TDH | 4,000 ft |
| Head per stage (actual) | 34.6 ft |
| Head per stage (design) | 33.3 ft |

---

### Tab: Trends

Subtitle area shows time range toggle buttons: **24h**, **7d**, **30d**, **60d**

**Signal selector row**

A row of toggle buttons, one per available signal, lets the user pick up to 2 signals to compare on one chart:
`Amps`, `Hz`, `PIP psi`, `PDP psi`, `Motor temp degF`, `Liquid bpd`, `Oil bopd`, `Motor load %`, `WHP psi`, `Vibration g`

**Trend chart**

- X axis: time (width controlled by the selected range)
- Y axis: left = primary signal; right = secondary signal if a second is selected
- Series: up to 2 overlapping lines in contrasting colours
- Event markers: vertical lines for state changes, labelled on hover
- Tooltip shows: timestamp, values for both signals

A **"What changed"** table is shown below the chart listing signal movements that preceded the current state.

---

### Tab: Operating point

Shows the full-size pump head-curve chart with the current operating point overlaid.

**Head-efficiency-power curves**

- X axis: Rate (bpd)
- Y axis left: Head (ft)
- Y axis right: Efficiency (%)
- Y axis (second right): Power (HP)
- Series: Head curve, Efficiency curve, Power curve — all at the current frequency
- Overlays: ROR shaded band (green), BEP marker (blue line), current operating point (coloured dot)
- Tooltip shows: rate, head, efficiency, power at cursor position

Below the chart, an **Operating envelope** summary panel repeats the ROR / BEP values and the margin note.

---

### Tab: Pressure profile

Shows the vertical pressure traverse from reservoir to wellhead surface.

**Pressure profile chart**

- X axis: Pressure (psi)
- Y axis: Depth (ft TVD, positive = deeper)
- Series: pressure gradient line from reservoir → perforations → pump intake (PIP) → pump discharge (PDP) → wellhead
- Key labels on the curve: Reservoir, PIP, PDP, Wellhead
- Tooltip shows: depth and pressure at cursor

---

### Tab: ESP string

Full-size, detailed ESP string diagram — the same graphic as in the Overview tab but larger, with full-resolution callout labels for every component: wellhead, tubing OD, pump stages, pump intake, gas separator, protector, motor, and downhole gauge.

---

### Tab: Events & exceptions

**Events table**

Columns: `Time`, `Event`, `Value`, `Duration`

Sample rows:
- 12 h ago · State change: Gas interference · PIP < 250 psi · ongoing
- 1 d ago · Drive trip: Fault 42 · — · 35 min

**Open exceptions for this well table**

Columns: `Sev`, `Category`, `Impact bopd`, `Age`, `Status`

Each row lists one active exception for this specific well.

---

### Advisor panel (always visible on the right side)

**Advisor panel** — `src/components/esp/AdvisorPanel.tsx`

This panel is always shown next to the tab content. It reads the well's current state and displays:

| Element | What the user reads |
|---|---|
| Panel title | Advisor |
| State pill | current well state e.g. Gas interference |
| Advisory text | explanation of the problem and its operational impact |
| Action items list | numbered actions in priority order |
| Links | "Open in Workbench →" where relevant |

---

### Views on this page

| View | Trigger | What changes on screen |
|---|---|---|
| Overview tab | click "Overview" | ESP string visual, state timeline, what-changed, envelope, mini operating point, TDH breakdown |
| Trends tab | click "Trends" | time-range toggle, signal selector, trend chart, what-changed table |
| Operating point tab | click "Operating point" | full H-Q pump curve chart with current operating point |
| Pressure profile tab | click "Pressure profile" | pressure traverse chart from reservoir to wellhead |
| ESP string tab | click "ESP string" | full-size annotated downhole string diagram |
| Events & exceptions tab | click "Events & exceptions" | events table + exceptions table for this well |
| Time range | click 24h / 7d / 30d / 60d (Trends tab only) | trend chart x-axis updates |
| Signal selector | click signal button (Trends tab only) | overlays that signal on the trend chart |

### Overlays reachable from this page

| Overlay | Trigger | What it shows | Actions |
|---|---|---|---|
| Advisor panel (right rail) | always visible | current well diagnosis and action priorities | follow-up links only; no modal |

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| ← ESP-103 button | previous well monitor | DRILL-DOWN |
| ESP-105 → button | next well monitor | DRILL-DOWN |
| "Open in Engineering Workbench" | `/engineering/workbench?well=ESP-xxx` | PAGE |
| "Governed asset definition" | `/engineering/installations` | PAGE |
| Well link in Events table | same page, different well | DRILL-DOWN |
| "Open {well} →" in advisor | same page for referenced well | DRILL-DOWN |

### Notes

- If a wellId in the URL does not match any well in the dataset, a 404 "Screen not found" page is shown with a "Back to Fleet Cockpit" link.
- The data quality badge changes colour if fewer than all signals are available (e.g. if the downhole gauge is offline, PIP / PDP / motor temp show "no data").

---

## 3. Exception & Opportunity Queue

**Route:** `/exceptions`
**Type:** PAGE
**Reached from:** "Open full queue →" link on the Fleet Cockpit, or the left sidebar "Exceptions" item
**Source file:** `src/routes/exceptions.tsx`

### What the user sees

A two-panel screen: a scrollable ranked list of every open exception on the left, and the full detail card for the currently selected exception on the right. The user clicks a row in the list to load its detail. This is the shift triage screen — it gives operators everything they need to decide, act, or assign.

### Screen anatomy (top → bottom)

1. **Page header** — title, description, data-source pills, view filter toggle row
2. **KPI strip** — 7 tiles summarising the state of the queue
3. **Two-column body**
   - Left: scrollable "Queue" table
   - Right: detail panel for the selected exception

---

### Components on this page

#### Page header

| Element | What the user reads |
|---|---|
| Title | Exception & Opportunity Queue |
| Description | One prioritised list for the whole ESP fleet. Every item states what was observed, what evidence supports it, how to verify it and what action is recommended — so surveillance turns into decisions instead of alarm noise. |
| Pill | Rules evaluated on normalised OTConnex signals |
| Pill | Confidence values are demo heuristics |
| Filter bar | All · Critical · Warning · Watch · Opportunities · Unassigned |

#### KPI strip — 7 metric tiles

| KPI title | Sample value | Sub-label |
|---|---|---|
| Critical | 6 | Immediate action |
| Warning | 8 | Same-shift review |
| Watch | 4 | Monitor trend |
| Opportunities | 5 | Upside candidates |
| Impact at risk | 4,676 bopd | Sum of active impacts |
| Upside identified | 190 bopd | Scenario estimates |
| Value at stake | $330.9k /day | Demo price deck |

#### Queue table (left panel)

Panel title: **Queue — {N} items** (updates as the filter changes)

**Queue table**

Columns: `Sev`, `Well`, `Category`, `Impact`, `Age`, `Status`

Sample rows (when filter = All):
- critical · ESP-338 · VSD / power trip · 1,180 · 1 h · Open
- critical · ESP-242 · Unplanned stop · 1,050 · 20 h · Open
- critical · ESP-104 · Suspected gas interference / unstable amps · 168 · 12 h · Acknowledged
- warning · ESP-097 · Suspected pump wear / declining head per stage · 210 · 60 d · Open
- opportunity · ESP-312 · Optimization candidate · — · 3 d · Open

Clicking any row highlights it and loads its detail into the right panel.

#### Exception detail panel (right panel)

Panel title: **{exception id} — {category}**
Panel subtitle: **{wellId} · {field} · first seen {date}**

Three action buttons in the panel header:
- **Acknowledged** — marks the exception as acknowledged
- **Assigned** — marks it as assigned
- **Closed** — marks it as closed

Pressing one button highlights it in the primary colour. The status pill in the detail body updates immediately.

**Detail body sections (top → bottom within the panel):**

| Section label | What the user reads |
|---|---|
| Severity pill | e.g. critical |
| Owner pill | Owner: M. Okafor (Ops) |
| Status pill | Status: Open / Acknowledged / Assigned / Closed |
| Confidence pill | Confidence 74% |
| Link | Open Well Monitor → |
| Link | Analyse in Workbench → |
| RULE | text of the surveillance rule that fired |
| OBSERVATION | what was observed in plain language |
| EVIDENCE | bullet list of observed signal values that support the exception |
| LIKELY CAUSES (RANKED) | table of probable causes with confidence bars |
| VERIFICATION STEPS | numbered checklist of how to confirm the diagnosis at the well |
| RECOMMENDED ACTIONS | numbered list of what to do |
| EXPECTED OUTCOME | description of what should happen if the action is correct |

**Evidence section example:**

- · Amp variability 8.3 A (band threshold 4 A)
- · PIP declined from 340 psi to 210 psi over 12 h
- · Liquid rate dropped 12% from previous stable period

**Likely causes table**

Columns: cause name, confidence bar, confidence percentage

**Verification steps example:**

1. Check surface choke position and wellhead back-pressure
2. Compare VSD output Hz to SCADA setpoint
3. Observe PIP trend over next 2 hours

---

### Views on this page

| View | Trigger | What changes on screen |
|---|---|---|
| All | click "All" in filter bar | queue shows every open exception, sorted by severity then impact |
| Critical | click "Critical" | queue filtered to critical-only rows |
| Warning | click "Warning" | queue filtered to warning-only rows |
| Watch | click "Watch" | queue filtered to watch-only rows |
| Opportunities | click "Opportunities" | queue filtered to optimization opportunities only |
| Unassigned | click "Unassigned" | queue filtered to exceptions with status = Open (not yet touched) |
| Row selection | click any table row | right panel updates to that exception's full detail |
| Status change | click Acknowledged / Assigned / Closed | status pill in right panel updates; row status column in queue updates |

### Overlays reachable from this page

None — status changes happen inline in the right panel without a modal.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| "Open Well Monitor →" in detail | `/wells/$wellId` | DRILL-DOWN |
| "Analyse in Workbench →" in detail | `/engineering/workbench?well=xxx` | PAGE |
| Left rail nav item | corresponding page | PAGE |

### Notes

- The Acknowledged / Assigned / Closed buttons are optimistic UI — they update the display immediately in the browser session. There is no backend persistence in this demo.
- The "Impact" column is blank (`—`) for opportunity exceptions; those rows show upside in the same column.

---

## 4. Troubleshooting Assistant

**Route:** `/troubleshooting`
**Type:** PAGE
**Reached from:** left sidebar "Troubleshooting" item
**Source file:** `src/routes/troubleshooting.tsx`

### What the user sees

A two-column workspace. The left column is a scrollable list called "Signature library" containing pre-built diagnostic cases. Clicking a case on the left loads its full analysis on the right. This is not a real-time diagnostic engine — it is a reference library of known ESP failure patterns with their signal signatures, ranked causes, and step-by-step actions.

### Screen anatomy (top → bottom)

1. **Page header** — title, description, data-source pills
2. **Two-column body**
   - Left (narrow): Signature library — scrollable list of diagnostic cases
   - Right (wide): Detail view of the selected case

---

### Components on this page

#### Page header

| Element | What the user reads |
|---|---|
| Title | Troubleshooting Assistant |
| Description | ESP problems rarely show up as a single tag excursion. This workspace reads the pattern across flow, motor current, intake and discharge pressure, temperature and wellhead pressure, then ranks the causes that fit the whole signature. |
| Pill | Direction-of-change library |
| Pill | Confidence values are demo heuristics for review, not automated decisions |

#### Signature library (left panel)

Each entry in the list shows:
- Case ID (e.g. TS-01)
- Associated well ID (e.g. ESP-104)
- Case title (e.g. Gas interference — slug behaviour)
- VSD trip code if applicable (e.g. F42 Overcurrent)

Clicking an entry highlights it and loads the right panel.

#### Case detail (right panel)

Panel title: the case title (e.g. Gas interference — slug behaviour)
Panel subtitle: the observed symptom description
Link: **Open ESP-xxx →** — navigates to that well's Well Monitor

**Signal signature table**

Shows the direction each signal moved before / during the event. Arrows used on screen:
- ▲ = rising (amber)
- ▼ = falling (red)
- ▬ = flat (grey)
- ∿ = erratic (amber)

Columns: `Signal`, `Direction`, `Comment`

Sample rows:
- Motor amps · ∿ erratic · Variability > 4 A band
- PIP · ▼ falling · Declining over 12 h
- Liquid rate · ▼ falling · Below design
- Motor temperature · ▲ rising · Secondary effect of gas load

**Likely causes table**

Columns: cause description, confidence bar, confidence percentage

Sample row: Free gas ingestion at pump intake · ████░░ · 72%

**Verification steps section**

Numbered list:
1. Verify annulus gas-vent valve is open
2. Compare VSD current to its trip threshold
3. Check PIP trend vs bubble-point pressure

**Recommended actions section**

Numbered list of specific operational steps.

**ESP string visual**

Below the text sections, an annotated ESP string diagram highlights the subsystem implicated by this case (e.g. the pump intake section is highlighted for a gas-interference case).

**Trend chart (when a well is linked to the case)**

When the case has a linked well, a 7-day trend chart appears showing the signals that changed around the event.

- X axis: Time (7-day window)
- Y axis left: primary signal (Amps or PIP)
- Y axis right: secondary signal
- Event markers: vertical lines at state change moments

---

### Views on this page

| View | Trigger | What changes on screen |
|---|---|---|
| Select a diagnostic case | click any entry in the Signature library | right panel loads that case's signature, causes, steps, and visual |

### Overlays reachable from this page

None.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| "Open ESP-xxx →" in case header | `/wells/ESP-xxx` | DRILL-DOWN |
| Left rail nav item | corresponding page | PAGE |

---

## 5. Reliability & Run Life

**Route:** `/reliability`
**Type:** PAGE
**Reached from:** left sidebar "Reliability" item
**Source file:** `src/routes/reliability.tsx`

### What the user sees

A tabbed analytics workspace covering the reliability history of the entire ESP fleet. The user switches between five tabs to explore run-life distributions, failure modes, bad actors, planned interventions, and individual DIFA (Downhole Inspection, Failure Analysis) records.

### Screen anatomy (top → bottom)

1. **Page header** — title, description, record count pills, tab bar (acts as page-level views)
2. **KPI strip** — 7 fleet-level reliability metric tiles
3. **Tab content area** — changes per tab

---

### Components on this page

#### Page header

| Element | What the user reads |
|---|---|
| Title | Reliability & Run Life |
| Description | Run life is the outcome of how wells were operated, not only of the equipment installed. This workspace links failure history and DIFA findings back to the operating factors ESP-PMM can influence — envelope compliance, temperature, free gas, abrasives and electrical integrity. |
| Pill | 34 pull records · 25 wells · 3 fields |
| Pill | Cost and deferment figures are illustrative |
| Tab bar | Run life · Failure analysis · Bad actors · Interventions · DIFA records |

#### KPI strip — 7 metric tiles

| KPI title | Sample value | Sub-label |
|---|---|---|
| Mean run life | 842 days | All recorded pulls |
| Repeat failure rate | 29 % | Same well within 2 runs |
| Recorded pulls | 34 | With DIFA summary |
| Intervention spend | $4.1M | Cumulative, illustrative |
| Deferred volume | 186,000 bbl | Associated with failures |
| High-risk wells | 4 | Risk score above 60 |
| Planned interventions | 7 | Proposed or scheduled |

---

### Tab: Run life

**Run-life distribution by field chart**

- X axis: run-life bucket (e.g. 0-200 d, 200-400 d, 400-600 d, 600-800 d, 800+ d)
- Y axis: pull count
- Series: one bar series per field in different chart colours
- Tooltip shows: bucket, count per field

**Run life by field table**

Columns: `Field`, `Pulls`, `Mean d`, `Median d`, `Shortest d`, `Repeat %`

Sample rows:
- Nardah North · 12 · 810 · 780 · 145 · 33%
- Kalisto West · 13 · 870 · 850 · 190 · 23%
- Tamrin Deep · 9 · 860 · 840 · 210 · 33%

**Mean run life by pump family chart**

Horizontal bar chart.
- Y axis: pump family name
- X axis: mean run life (days)
- One bar per pump family

**Run-life influencing factors table**

Subtitle: *Weighted model used for the ESP health index and risk score*

Columns: `Factor`, `Weight`, `Why it matters`

Sample rows:
- Envelope compliance · 28% · Time outside ROR accelerates thrust bearing wear
- Gas ingestion frequency · 22% · Slug events stress stages and intake bushing
- Motor thermal margin · 18% · Operating near temp limit degrades winding insulation

---

### Tab: Failure analysis

**Failure-mode Pareto chart**

Pareto chart (bars descending left-to-right + cumulative % line).
- X axis: failure mode label
- Y axis left: count
- Y axis right: cumulative %
- Tooltip shows: failure mode, count, cumulative %

**Failures by component chart**

Horizontal bar chart.
- Y axis: component name (e.g. Motor, Pump stage, Cable, Protector)
- X axis: failure count

**Failure mode by field table**

Columns: `Failure mode`, one column per field showing count

**Well correlation table**

Subtitle: *Wells with multiple failure modes — repeat failure candidates*

Columns: `Well`, `Pulls`, `Modes`, `Risk score`

---

### Tab: Bad actors

**Bad actors table**

Columns: `Well`, `Field`, `Pulls`, `Mean run d`, `Last failure mode`, `Risk score`, `Recommended action`

Well IDs in this table are clickable links to the Well Monitor.

**Risk score distribution chart**

Bar chart of wells grouped by risk score band.
- X axis: risk score band (0-20, 20-40, 40-60, 60-80, 80-100)
- Y axis: well count

---

### Tab: Interventions

**Planned interventions table**

Columns: `Well`, `Field`, `Type`, `Priority`, `Estimated cost`, `Status`, `Target date`

- Type values seen: Workover, Pull & replace, Chemical treatment, VSD swap
- Status values seen: Proposed, Scheduled, Executed

Well IDs are clickable links to the Well Monitor.

**Intervention spend by type chart**

Horizontal bar chart showing cumulative cost split by intervention type.

---

### Tab: DIFA records

**DIFA records table** (Downhole Inspection & Failure Analysis)

Columns: `Pull ID`, `Well`, `Pull date`, `Run life d`, `DIFA finding`, `Root cause`, `Repeat`, `Cost $k`, `Deferred bbl`

- Repeat column shows a warning flag if the same failure mode occurred in the previous run.
- Each row is expandable to show the full DIFA finding text.

---

### Views on this page

| View | Trigger | What changes on screen |
|---|---|---|
| Run life tab | click "Run life" | distribution chart, field table, pump-family chart, influencing factors table |
| Failure analysis tab | click "Failure analysis" | Pareto chart, component chart, mode-by-field table, well correlation table |
| Bad actors tab | click "Bad actors" | bad-actor table, risk-score distribution chart |
| Interventions tab | click "Interventions" | planned interventions table, spend-by-type chart |
| DIFA records tab | click "DIFA records" | full DIFA record table |

### Overlays reachable from this page

None.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| Well ID in Bad actors table | `/wells/$wellId` | DRILL-DOWN |
| Well ID in Interventions table | `/wells/$wellId` | DRILL-DOWN |
| Left rail nav item | corresponding page | PAGE |

---

## 6. Management Scorecard & Reports

**Route:** `/reports`
**Type:** PAGE
**Reached from:** left sidebar "Reports" item
**Source file:** `src/routes/reports.tsx`

### What the user sees

A single-screen management summary designed for asset leadership. No tabs — everything is on one scroll. It shows how much production the fleet is losing, how much is avoidable, which fields are underperforming, which failure modes dominate, and which wells deserve rig or engineering attention this week.

### Screen anatomy (top → bottom)

1. **Page header** — title, description, reporting period pills
2. **KPI strip** — 7 fleet-level summary tiles
3. **Field scorecard table** (left) + **Deferment & upside by field chart** (right)
4. **Envelope compliance summary** (left) + **Run life by field table** (right)
5. **Failure-mode contribution chart** (left) + **Worst run-life wells table** (right)
6. **Avoidable failures & recommendations panel** (left) + **Intervention queue table** (right)
7. **Engineering & rig focus note**

---

### Components on this page

#### Page header

| Element | What the user reads |
|---|---|
| Title | Management Scorecard & Reports |
| Description | One page for asset leadership: how much production the ESP fleet is losing, how much of it is avoidable, where run life is short and which wells deserve engineering and rig attention this week. |
| Pill | Reporting period: last 24 hours and rolling 12 months |
| Pill | Demo price deck $68/bbl |

#### KPI strip — 7 metric tiles

| KPI title | Sample value | Sub-label |
|---|---|---|
| Fleet availability | 88 % | 22 of 25 running |
| Fleet health index | 65.7 | Weighted composite |
| Envelope compliance | 76 % | Running wells inside ROR |
| Deferment | 4,676 bopd | $318,000/day |
| Identified upside | 190 bopd | $12,920/day |
| Repeat / avoidable pulls | 10 | of 34 recorded pulls |
| Rig work queued | 5 | Workover candidates |

#### Field scorecard table (left panel)

Columns: `Field`, `Wells`, `Avail %`, `Health`, `Oil bopd`, `Defer bopd`, `Upside bopd`, `Envelope %`, `Open exc.`

Sample rows:
- Nardah North · 9 · 89% · 64 · 9,240 · 1,820 · 70 · 78% · 7
- Kalisto West · 9 · 89% · 67 · 10,010 · 1,930 · 60 · 78% · 7
- Tamrin Deep · 7 · 86% · 66 · 6,802 · 926 · 60 · 71% · 3

#### Deferment & upside by field chart (right panel)

- X axis: Field name
- Y axis: Barrels per day
- Series: Deferred bopd (amber), Upside bopd (green)

#### Envelope compliance note

A coloured note box explaining how many running wells are inside their recommended operating range and what the implication is.

#### Run life by field table

Same table as in the Reliability page Run life tab. Columns: `Field`, `Pulls`, `Mean d`, `Median d`, `Shortest d`, `Repeat %`

#### Failure-mode contribution chart

Bar chart showing top failure modes by frequency. Same data as the Reliability Pareto but condensed to a simple bar for this summary view.

#### Worst run-life wells table

Columns: `Well`, `Field`, `Pulls`, `Mean run d`, `Last failure`, `Risk score`

Well IDs are clickable links to the Well Monitor.

#### Avoidable failures note

A highlighted note listing how many of the recorded pulls were repeats and the estimated cost of those avoidable failures.

#### Intervention queue table

Columns: `Well`, `Type`, `Priority`, `Status`, `Target date`

#### Engineering & rig focus note

A plain-language paragraph summarising which wells the page recommends prioritising this week, based on risk score, deferment, and envelope compliance.

---

### Views on this page

None — this page has no tabs. All content is on a single scroll.

### Overlays reachable from this page

None.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| Well ID in worst run-life table | `/wells/$wellId` | DRILL-DOWN |
| Well ID in intervention queue | `/wells/$wellId` | DRILL-DOWN |
| Left rail nav item | corresponding page | PAGE |

---

## 7. Administration & Platform Integration

**Route:** `/administration`
**Type:** PAGE
**Reached from:** left sidebar "Administration" item (Configuration workspace)
**Source file:** `src/routes/administration.tsx`

### What the user sees

A configuration reference page showing how ESP-PMM is connected to the rest of the ADVAIT platform. Four panels display the signal tag map, the surveillance rule thresholds, the user role matrix, and an AI advisor governance note. Nothing on this page requires user interaction in the demo — it is read-only.

### Screen anatomy (top → bottom)

1. **Page header** — title, description, connection status pills
2. **Two-column grid**
   - Left: Signal mapping table
   - Right: Surveillance rule configuration table
3. **Role matrix table** (full width)
4. **AI advisor governance note**

---

### Components on this page

#### Page header

| Element | What the user reads |
|---|---|
| Title | Administration & Platform Integration |
| Description | ESP-PMM extends the ADVAIT platform rather than duplicating it. Signals arrive through OTConnex, the asset hierarchy and ESP string configuration come from Asset ConneX, and workflow, notification and document services are reused as-is. |
| Pill | OTConnex connected · 11 template tags |
| Pill | Asset ConneX ESP template v2.3 |
| Pill | 25 wells onboarded |

#### Signal mapping table (left panel)

Panel subtitle: *ESP tag template resolved per well through OTConnex*

Columns: `Tag`, `Description`, `Unit`, `Source`, `Scan`, `Coverage`

All 11 tags shown:

| Tag | Description | Unit | Source | Scan | Coverage |
|---|---|---|---|---|---|
| ESP.FREQ_HZ | Drive output frequency | Hz | OTConnex → VSD | 2 s | 25 / 25 |
| ESP.MOTOR_AMPS | Motor current | A | OTConnex → VSD | 2 s | 25 / 25 |
| ESP.MOTOR_VOLTS | Motor voltage | V | OTConnex → VSD | 5 s | 25 / 25 |
| ESP.PIP_PSI | Pump intake pressure | psi | OTConnex → downhole gauge | 10 s | 23 / 25 |
| ESP.PDP_PSI | Pump discharge pressure | psi | OTConnex → downhole gauge | 10 s | 23 / 25 |
| ESP.MOTOR_TEMP_F | Motor winding temperature | degF | OTConnex → downhole gauge | 10 s | 23 / 25 |
| ESP.VIB_G | Vibration | g | OTConnex → downhole gauge | 10 s | 21 / 25 |
| WELL.WHP_PSI | Wellhead pressure | psi | OTConnex → SCADA | 5 s | 25 / 25 |
| WELL.LIQ_BPD | Allocated liquid rate | bpd | OTConnex → production allocation | 1 h | 25 / 25 |
| WELL.WCUT_PCT | Water cut | % | Well test / allocation | Weekly | 25 / 25 |
| ESP.DRIVE_FAULT | Drive fault code | code | OTConnex → VSD | Event | 25 / 25 |

#### Surveillance rule configuration table (right panel)

Panel subtitle: *Deterministic thresholds behind every exception*

Columns: `ID`, `Rule`, `Basis`, `Threshold`, `Severity`

All 8 rules shown:

| ID | Rule | Basis | Threshold | Severity |
|---|---|---|---|---|
| R-01 | Outside recommended operating range | Q vs ROR from pump curve at current Hz | Any excursion sustained 30 min | warning |
| R-02 | Motor overload | Amps / nameplate amps | > 75% for 15 min | critical |
| R-03 | High motor temperature | Motor temp vs limit | Within 12 degF of limit | warning |
| R-04 | Suspected gas interference | Amp variability + PIP decline | Band > 4 A with falling PIP | warning |
| R-05 | Pump degradation | Head per stage vs design | > 10% decline over 30 days | warning |
| R-06 | Repeat drive trips | Fault-code count | ≥ 3 trips in 7 days | critical |
| R-07 | Gauge data quality | Signal continuity | > 10% missing in 24 h | watch |
| R-08 | Optimization candidate | Envelope, thermal and electrical headroom | All three margins positive | opportunity |

#### Role permissions matrix (full-width panel)

Panel title: Role matrix

Columns: `Role`, `Views`, `Authority`, `Restricted`

| Role | Views | Authority | Restricted |
|---|---|---|---|
| Control room operator | Fleet Cockpit, Well Monitor, Exceptions, Troubleshooting | Acknowledge exceptions, log actions | No setpoint writes, no case edits |
| Production / artificial-lift engineer | All operational views plus Workbench and Design Cases | Create what-if cases, propose setpoints | Cannot approve rig work |
| Maintenance / reliability engineer | Reliability, DIFA, Interventions, Well Monitor | Raise interventions, record DIFA findings | No design case approval |
| Operations / asset manager | Scorecard, Reports, Fleet Cockpit | Approve interventions and priorities | Read-only on engineering calculations |
| ESP-PMM administrator | All views plus Administration | Tag mapping, rule thresholds, role assignment | Change history is audited |

#### AI advisor governance note

A highlighted note box explaining that advisor outputs are generated from deterministic surveillance rules and heuristic confidence scores — they are recommendations for human review, not automated control actions.

---

### Views on this page

None — single scroll, no tabs.

### Overlays reachable from this page

None.

### Where the user can go from here

| Trigger (what the user clicks) | Destination | Destination type |
|---|---|---|
| Left rail nav item | corresponding page | PAGE |

---

## 8. Engineering pages

**Routes:** `/engineering/**`
**Type:** LAYOUT + multiple child pages
**Reached from:** "Engineering Configuration →" link on Fleet Cockpit, or workspace switcher → Configuration
**Source file:** `src/routes/engineering.tsx` and its child files

### What the user sees

When the user switches workspace to Configuration, the left sidebar changes to show the Engineering group. The Engineering pages share a common sub-navigation and data loader. They cover governed equipment master data, pump catalog, installed assemblies, well definitions, governance audits, and engineering calculations.

These pages are primarily used by Artificial Lift Engineers and Reliability Engineers, not by control-room operators.

### Child pages under /engineering

| Page | Route | Purpose in one line |
|---|---|---|
| Engineering Home | `/engineering/` | Overview of governed master data — catalog models, installed systems, calculation-grade audit summary |
| Equipment Catalog | `/engineering/catalog/` | Searchable grid of OEM pumps, motors, protectors, separators, and cables with digitised curves |
| Pump model detail | `/engineering/catalog/pumps/$modelId` | Full rating curves and mechanical specs for one pump model |
| Installed Fleet | `/engineering/installations/` | Table of all 25 installed ESP string assemblies with grade badges |
| System Assembly Detail | `/engineering/installations/$systemId` | Full downhole component stack for one installed system |
| Assembly sub-pages | `/engineering/installations/assembly`, `/fluid`, `/limits`, `/well` | Tabbed sub-pages for assembly spec, fluid properties, operating limits, wellbore trajectory |
| Well Definition | `/engineering/definition/` | List of wells with their 16-section governed revision status |
| Well Definition Detail | `/engineering/definition/$wellId` | 16-section provenance accordion for one well |
| Governance Validation | `/engineering/governance/validation` | Calculation-grade audit matrix for all wells (A1 → D scoring) |
| Governance Data Quality | `/engineering/governance/quality` | Data completeness audit |
| Governance Sources | `/engineering/governance/sources` | Source document traceability |
| Curve Import Wizard | `/engineering/governance/import` | 4-step wizard for uploading digitised pump curves |
| Engineering Workbench | `/engineering/workbench` | Interactive pump curve simulator with frequency slider and operating point overlay |
| Design Cases | `/engineering/design-cases` | Design vs actual operating point comparison table |

> Full per-page breakdowns for Engineering pages follow the same template and can be added in a separate document when needed.

---

## Final Section — Cross-Page Map

### A. Navigation graph

```
/ (ESP Fleet Cockpit)
├── well ID link ─────────────────────────────► /wells/$wellId (Well Monitor)
│   └── "Open in Engineering Workbench" ──────► /engineering/workbench
│   └── "Governed asset definition" ──────────► /engineering/installations
│   └── ← / → buttons ────────────────────────► adjacent /wells/$wellId
├── "Open full queue →" ──────────────────────► /exceptions
│   └── "Open Well Monitor →" ──────────────► /wells/$wellId
│   └── "Analyse in Workbench →" ───────────► /engineering/workbench
├── optimization well link ───────────────────► /engineering/workbench
├── "Engineering Configuration →" ────────────► /engineering
├── left rail → Exceptions ───────────────────► /exceptions
├── left rail → Troubleshooting ──────────────► /troubleshooting
│   └── "Open ESP-xxx →" ──────────────────► /wells/$wellId
├── left rail → Reliability ──────────────────► /reliability
│   └── well ID link ───────────────────────► /wells/$wellId
├── left rail → Reports ──────────────────────► /reports
│   └── well ID link ───────────────────────► /wells/$wellId
└── workspace switcher → Configuration ──────► /engineering (and sub-pages)
    └── left rail → Administration ─────────► /administration
```

### B. Page hierarchy

- **Root landing**: `/` — Fleet Cockpit
- **Drill-down from root**: `/wells/$wellId` — Well Monitor (each of 25 wells)
- **Peer pages from root** (via left rail): `/exceptions`, `/troubleshooting`, `/reliability`, `/reports`, `/administration`
- **Cross-links from exceptions / reliability / troubleshooting**: drill into `/wells/$wellId`, navigate to `/engineering/workbench`
- **Engineering branch** (separate workspace): `/engineering/**` — 14 sub-pages with their own left-rail nav

### C. Component reuse across pages

| Visible element | Appears on |
|---|---|
| KPI strip (7 metric tiles) | Fleet Cockpit, Well Monitor, Exceptions, Reliability, Reports |
| Status pill (coloured badge) | Every page — used for state labels, data-source tags, severity indicators |
| Fleet register well table | Fleet Cockpit (full version), Well Directory |
| ESP string diagram | Fleet Cockpit (compact, in "Selected well visual"), Well Monitor (Overview tab full-size, ESP string tab), Troubleshooting Assistant |
| Operating envelope bar graphic | Well Monitor (Overview tab), Well Monitor (Operating point tab) |
| Head-curve chart with operating point | Well Monitor (Operating point tab), Engineering Workbench |
| "What changed" table | Well Monitor (Overview tab), Well Monitor (Trends tab) |
| Run life by field table | Reliability (Run life tab), Reports |
| Failure-mode chart | Reliability (Failure analysis tab), Reports |
| Bad actors table | Reliability (Bad actors tab), Reports |
| Intervention table | Reliability (Interventions tab), Reports |

### D. Entry points

- `/` — the default landing for any user opening the app
- `/wells/$wellId` — reachable as a deep link if the well ID is known
- `/exceptions` — reachable as a deep link; useful for shift-handover shared links
- `/engineering/workbench?well=$wellId` — reachable as a deep link from exception or well detail for engineering analysis
