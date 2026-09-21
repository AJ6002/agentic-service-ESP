# Complete Ultra-Detailed Page-by-Page Component Enumeration & View Map

This document provides a runtime-accurate, component-by-component analysis of all 26 pages in the **ADVAIT ESP-PMM** dashboard suite. Every page is broken down by its visual regions, rendered components, sample data values, and exact click triggers/navigation views. All explanations are written in simple, plain English without sacrificing any technical detail.

---

## 1. Executive Summary

- **Total Shared Layouts (`<Outlet/>`)**: 5
- **Total Functional Pages**: 26
- **Total Legacy Redirect Routes**: 4
- **Total Interactive Views & Tabs**: 22
- **Total Overlays (Modals & Drawers)**: 4
- **Total Distinct React Components**: 59

---

## 2. Shared Layout Shells

### L1: Global Application Shell (`__root__`)
- **File**: [`src/routes/__root.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/__root.tsx) -> [`src/components/esp/AppShell.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AppShell.tsx)
- **Wraps**: Every page in the application.
- **Rendered Components**:
  - **Top Bar Header**:
    - Logo Badge: `div` containing `"AD"`.
    - Application Title: `"ADVAIT ESP-PMM | ESP Performance Monitoring & Management"`.
    - Workspace Selector: Dropdown switching between `Operations` (`/`) and `Configuration` (`/engineering`).
    - Field Scope Selector (Operations Mode): Dropdown filtering `All fields (3)`, `Nardah North`, `Kalisto West`, or `Tamrin Deep`.
    - Status Badges: `StatusPill` for `OTConnex live · 2 s scan`, `StatusPill` for `{N} critical open`.
    - User Profile Pill: Avatar circle `"VK"` with role (`Ops Engineer` or `Configurator`).
  - **Left Collapsible Sidebar Rail**:
    - Mode Switcher: Toggles between 56px collapsed icon rail and 196px expanded text sidebar.
    - Navigation Groups: Operations (`Fleet Cockpit`, `Well Monitor`, `Exceptions`, `Troubleshooting`, `Reliability`, `Reports`) and Engineering (`Engineering Home`, `Equipment Catalog`, `Installed Fleet`, `Well Definition`, `Governance`, `Engineering Workbench`, `Design Cases`, `Administration`).

---

## 3. Ultra-Detailed Per-Page Component & View Breakdown

---

### P1: Fleet Cockpit — `/`
- **Page Title**: ESP Fleet Cockpit
- **Route**: `/`
- **File Path**: [`src/routes/index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/index.tsx)
- **Layout Used**: L1 (`AppShell`)

#### A. Rendered Components (Top → Bottom, Left → Right)
1. **`SectionHeader`**: Renders page title `"ESP Fleet Cockpit"`.
2. **Field Summary Chips Bar**: Renders 4 `StatusPill` summary badges:
   - `Nardah North — 9 wells — 6 off-normal`
   - `Kalisto West — 9 wells — 7 off-normal`
   - `Tamrin Deep — 7 wells — 4 off-normal`
   - `Inside recommended range 88%`
3. **Top KPI Summary Strip (7 `KpiCard` Instances)**:
   - `WELLS RUNNING`: `22 / 25` (Subtext: `3 down`)
   - `AVAILABILITY`: `88%` (Subtext: `Run status weighted, 24 h`)
   - `FLEET ESP HEALTH INDEX`: `65.7` (Subtext: `Weighted envelope + thermal`)
   - `OIL RATE`: `26,052 bopd` (Subtext: `Allocated, latest scan`)
   - `PRODUCTION DEFERMENT`: `4,676 bopd` (Subtext: `Vs expected from active cases`)
   - `OPTIMIZATION UPSIDE`: `190 bopd` (Subtext: `Illustrative scenario estimates`)
   - `VALUE AT STAKE`: `$330.9k /day` (Subtext: `Deferment + upside`)
4. **Needs Attention Now Table (Left Panel, 8 cols)**:
   - Header: `"NEEDS ATTENTION NOW — Ranked by severity then production impact"`.
   - Link: `"Open full queue >"` (Triggers navigation to `/exceptions`).
   - Columns: `SEV`, `WELL`, `CATEGORY`, `IMPACT BOPD`, `AGE`, `CONF.`, `OWNER`.
   - Sample Rows:
     - `critical` | `ESP-338` | `VSD / power trip` | `1,180 bopd` | `1 h` | `86%` | `Unassigned`
     - `critical` | `ESP-242` | `Unplanned stop` | `1,050 bopd` | `20 h` | `82%` | `M. Okafor (Ops)`
     - `critical` | `ESP-104` | `Suspected gas interference / unstable amps` | `168 bopd` | `12 h` | `74%` | `A. Rahman (Prod Eng)`
     - `critical` | `ESP-141` | `VSD / power trip` | `140 bopd` | `1 h` | `86%` | `A. Rahman (Prod Eng)`
     - `warning` | `ESP-097` | `Suspected pump wear / declining head` | `210 bopd` | `60 d` | `68%` | `L. Vieira (Reliability)`
5. **Optimization Opportunities Panel (Right Top Panel, 4 cols)**:
   - Header: `"OPTIMIZATION OPPORTUNITIES — Healthy wells with headroom"`.
   - Columns: `WELL`, `BASIS`, `UPSIDE`, `CONF.`.
   - Sample Rows:
     - `ESP-312` | `Inside ROR AND load < 70% AND thermal margin...` | `$6.5k/d` | `58%`
     - `ESP-307` | `Inside ROR AND choke restriction detected` | `$3.7k/d` | `54%`
6. **Open Exceptions By Category Panel (Right Bottom Panel, 4 cols)**:
   - Header: `"OPEN EXCEPTIONS BY CATEGORY — Where surveillance effort is concentrated"`.
   - Horizontal progress bar items: `Suspected gas interference (2)`, `High motor temp (2)`, `Suspected pump wear (2)`, `Gauge comms (2)`, `VSD trip (2)`, `Outside ROR (2)`, `Unplanned stop (2)`, `Optimization opportunity (2)`.

#### B. Possible Navigation Views & Click Triggers
- **Click Well ID (`ESP-104`, `ESP-338`, `ESP-312`)** -> Opens Single Well Monitor (`/wells/$wellId`).
- **Click `"Open full queue >"`** -> Opens Exceptions Queue (`/exceptions`).
- **Click Field Selector (`Nardah North`, `Kalisto West`, `Tamrin Deep`)** -> Filters all KPIs and table rows for that specific oilfield.
- **Click Optimization Well (`ESP-312`)** -> Opens Engineering Workbench (`/engineering/workbench`) to simulate pump curves.

---

### P2: Well Directory — `/wells`
- **Page Title**: Well Directory — Fleet Selection
- **Route**: `/wells`
- **File Path**: [`src/routes/wells.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.index.tsx)
- **Layout Used**: L1 (`AppShell`)

#### A. Rendered Components
1. **`SectionHeader`**: Title `"Well Directory — Fleet Selection"`.
2. **`FleetTable`**: Full-width operations data table for all 25 wells.
   - Columns: `Well Name`, `Field`, `Operating State`, `Frequency (Hz)`, `Current (A)`, `Intake Pressure (PIP, psi)`, `Discharge Pressure (psi)`, `Motor Temp (°F)`, `Run Life (days)`, `Health Index (%)`, `Actions`.
   - Sample Row: `ESP-101` | `Nardah North` | `Normal Running` | `55.0 Hz` | `62.0 A` | `340 psi` | `1,420 psi` | `185°F` | `412 days` | `92%` | `[View Monitor]`.

#### B. Possible Navigation Views & Click Triggers
- **Click `[View Monitor]`** -> Opens Single Well Monitor (`/wells/$wellId`).
- **Search Input Filter** -> Filters displayed well rows by well name or field name.

---

### P3: Well Monitor — `/wells/$wellId`
- **Page Title**: `{wellId} — {field} · {pad}` (e.g. `ESP-319 — Tamrin Deep · TMR-Pad-B`)
- **Route**: `/wells/$wellId` (Sample IDs: `ESP-319`, `ESP-104`, `ESP-205`, `ESP-101`)
- **File Path**: [`src/routes/wells.$wellId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.$wellId.tsx)
- **Layout Used**: L1 (`AppShell`)
- **Overlay Present**: `ESP Advisor — preview` (`AdvisorPanel` collapsible side drawer)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Well Page Header (`PageHeader`)
- **Title**: `${well.id} — ${field} · ${well.padName}` (e.g. `"ESP-319 — Tamrin Deep · TMR-Pad-B"`).
- **Description**: Headline status sentence (e.g. `"Operating right of ROR — upthrust risk with motor load at 71%"`).
- **Status Pills & Meta Badges**:
  - `Operating State`: Coloured badge (e.g. `Outside ROR — high flow` in amber warning tone, `Normal` in green, `Gas interference` in red/critical).
  - `Field & Pad`: Grey pill (e.g. `Tamrin Deep · TMR-Pad-B`).
  - `Pump Model & Stages`: Grey pill (e.g. `Meridian Artificial Lift MR-700 · 118 stages`).
  - `Data Quality Badge`: Coloured pill (`Data good` in green, `Degraded` in amber).
  - `Last Event Pill`: Blue info pill (e.g. `Last event: Rate 3,180 bpd vs ROR maximum 3,024 bpd (2026-08-13 09:55)`).
- **Action Navigation Buttons (Top-Right)**:
  - `← {prevId}`: Button (e.g. `← ESP-205`) -> jumps directly to the previous well.
  - `{nextId} →`: Button (e.g. `ESP-101 →`) -> jumps directly to the next well.
  - `Open in Engineering Workbench`: Primary button -> opens `/engineering/workbench?well={wellId}` with this well preloaded.
  - `Governed asset definition`: Button -> opens `/engineering/installations` to view governed asset records.

##### 2. Top Telemetry KPI Summary Strip (`KpiStrip` — 7 Stat Tiles)
- `ESP HEALTH INDEX`: `55` (Subtext: `Band: warning`, dynamic color by health band).
- `FREQUENCY`: `59.5 Hz` (Subtext: `Design 55.0 Hz`).
- `MOTOR LOAD`: `71 %` (Subtext: `61.4 A of 87 A rated`, tone warning if > 70%, critical if > 75%).
- `MOTOR TEMPERATURE`: `262 degF` (Subtext: `Limit 285 degF`, tone warning if within 12°F of limit).
- `PIP / PDP`: `470 / 2,295 psi` (Subtext: `Design 586 / 2,354`).
- `LIQUID / OIL`: `3,180 / 1,431 bpd` (Subtext: `+35.2% vs design liquid`, tone warning if variance > 10%).
- `DEFERMENT`: `0 bopd` (Subtext: `$0/day`, tone warning if deferment > 0).

##### 3. Main Navigation Tab Bar (`tabs`)
Horizontal underline tab bar with 6 selectable views:
- **`Overview`** (Default)
- **`Trends`**
- **`Operating point`**
- **`Pressure profile`**
- **`ESP string`**
- **`Events & exceptions`**

---

#### B. Detailed Breakdown of Each Tabbed View

##### Tab 1: `Overview` View
1. **`ESP SYSTEM VISUALIZATION` Panel** (Left Column):
   - **Subtitle**: `"Live simulated values bound to the string — hover or tab a marker for design comparison"`
   - **Rendered Graphic (`EspWellVisual` variant="full")**:
     - Interactive SVG schematic showing the full vertical ESP downhole system:
       - Surface choke & flowline valve indicators
       - Production casing & production tubing
       - Pump discharge pressure tap
       - Multistage centrifugal pump (e.g. `Multistage pump · 118 stages / Meridian Artificial Lift MR-700`)
       - Gas handler / intake section (with intake pressure PIP callout)
       - Protector / seal section
       - Submersible electric motor (e.g. `Motor 140 hp / load 71.0% / 61.4 A · 262 degF`)
       - Downhole sensor package (e.g. `Downhole sensor — good`)
     - **Bottom State Callout**:
       - State Pill (e.g. `Outside ROR — high flow`)
       - Hint text: `"Hover, click or tab a marker for value, design reference and status. Animation is a demo indication only — no control or write-back"`
2. **`OPERATING STATE TIMELINE` Panel** (Middle Column):
   - **Subtitle**: `"Last 24 hours — how the well arrived at its current state"`
   - **24-Hour Horizontal Bar**: Segmented coloured bar spanning `-24 h`, `-12 h`, `now` showing time proportions in each state.
   - **Chronological State Table**:
     - Lists state episodes from latest to oldest with status pills and durations:
       - e.g. `High flow / overloaded` | `-9.0 h → now`
       - e.g. `Normal` | `-14.0 h → -9.0 h`
       - e.g. `Normal` | `-24.0 h → -14.0 h`
3. **`WHAT CHANGED` Panel** (Lower Grid):
   - **Subtitle**: `"Signals that moved before the current state — the operational story"`
   - **Columns**: `Signal`, `From`, `To`, `Window`.
   - **Sample Row**: `PIP` | `580 psi` | `470 psi` | `last 9 h`.
4. **`OPERATING ENVELOPE` Panel** (Lower Grid):
   - **Subtitle**: `"Actual rate vs recommended operating range"`
   - **Graphic Envelope Bar**: Visual bar showing recommended operating range (ROR min to max) in green, Best Efficiency Point (BEP) line in blue, and actual operating rate marker in green/amber.
   - **Metrics Grid**: `ROR min (bpd)`, `ROR max (bpd)`, `BEP (bpd)`, `Q/Q_BEP (ratio)`.
   - **Diagnostic Margin Note**: Explains whether the well is inside ROR or operating in upthrust/downthrust risk (e.g. `"Right of ROR by 156 bpd — upthrust and motor loading exposure."`).
5. **`OPERATING POINT VS PUMP CURVE` Panel** (Lower Grid):
   - **Subtitle**: `${pumpModel} at ${hz} Hz`
   - **Mini Head-Capacity Chart (`MiniOperatingPoint`)**: Compact H-Q pump curve rendering head vs flow rate at active frequency with the current operating point dot.
6. **`TOTAL DYNAMIC HEAD` Panel** (Lower Grid):
   - **Subtitle**: `"Deterministic engineering calculation"`
   - **Breakdown Table**:
     - `Vertical / dynamic lift`: ft
     - `Tubing friction`: ft
     - `Wellhead backpressure`: ft
     - `Total dynamic head`: ft (bold summary)
     - `Design TDH`: ft
     - `Head per stage (actual)`: ft
     - `Head per stage (design)`: ft

---

##### Tab 2: `Trends` View
1. **`MULTI-TAG TREND` Panel**:
   - **Subtitle**: `"{Range} · event bands mark trips, setpoint changes and degradation onset"`
   - **Time Range Selector Buttons (Top Right)**:
     - `24h` | `7d` | `30d` | `60d`
   - **Signal Tag Toggle Buttons**:
     - Buttons to activate/deactivate overlaid signals: `Amps (A)`, `Hz (Hz)`, `PIP (psi)`, `PDP (psi)`, `Motor temp (°F)`, `Liquid (bpd)`, `Oil (bopd)`, `Motor load (%)`, `WHP (psi)`, `Vibration (g)`.
   - **Primary Trend Chart (`TrendChart`)**:
     - 300px height interactive multi-line chart with dual Y-axes, hover tooltips, and vertical event lines marking alarms and trips.
   - **Secondary Comparison Grid**:
     - 2 side-by-side sub-charts (200px height): PIP vs PDP hydraulic trend, Motor Temp vs Load thermal trend.
   - **Footer Note**: Description of OTConnex and Asset ConneX signal normalization.

---

##### Tab 3: `Operating point` View
1. **`OPERATING POINT DETAIL` Panel**:
   - **Subtitle**: `"Actual vs design at current frequency"`
   - **Large Pump Curve Plot (`MiniOperatingPoint`, height 280px)**:
     - Head (ft) vs Liquid Rate (bpd) curve, ROR shaded window, BEP line, and active operating point dot.
   - **Actual vs Design Comparison Table**:
     - **Columns**: `Parameter`, `Actual`, `Design`, `Variance`.
     - **Parameters**: `Frequency (Hz)`, `Liquid rate (bpd)`, `Oil rate (bopd)`, `PIP (psi)`, `PDP (psi)`, `Motor current (A)`, `TDH (ft)`.
     - Variance percentages flagged with amber warning pills if exceeding ±10%.

---

##### Tab 4: `Pressure profile` View
1. **`PRESSURE PROFILE` Panel**:
   - **Subtitle**: `"Reservoir → Pwf → PIP → pump ΔP → PDP → wellhead"`
   - **Vertical Pressure Traverse Chart (`PressureProfile`)**:
     - Y-axis: Depth (0 to total depth in ft TVD).
     - X-axis: Pressure (0 to 3,000+ psi).
     - Gradient plot connecting: Reservoir Pressure -> Flowing Bottomhole Pressure (Pwf) -> Pump Intake Pressure (PIP) -> Pump Boost (ΔP) -> Pump Discharge Pressure (PDP) -> Surface Wellhead Pressure (WHP).

---

##### Tab 5: `ESP string` View
1. **`ESP STRING VISUALIZATION` Panel** (Left Column, 300px):
   - Full-height graphical schematic of the installed downhole assembly with data-linked status callouts.
2. **`COMPONENT REGISTRY` Panel** (Right Column):
   - **Subtitle**: `"ESP is a system, not only a pump — configuration inherited from Asset ConneX"`
   - **Columns**: `Group`, `Component`, `Make / model`, `Specification`, `Tags`, `Source`, `Status`.
   - **Rows**: Iterates through all governed components in the string:
     - Tubing string, Check valve, Bleeder valve, Multistage pump, Gas handler/separator, Seal/protector, Induction motor, Downhole gauge instrument, Power cable / MLE.
     - Each component displays tag count, source system (`Asset ConneX`), and data quality badge (`Data good`).

---

##### Tab 6: `Events & exceptions` View
1. **`OPEN EXCEPTIONS FOR THIS WELL` Panel**:
   - **Subtitle**: `"Each item carries evidence, verification steps and a recommended action"`
   - **Exception Cards** (one card per active exception on this well):
     - **Header**: Severity pill (`critical`, `warning`, `opportunity`, `watch`), category title, exception ID, age (e.g. `12 h`), confidence percentage (e.g. `74%`).
     - **Observation**: Plain English description of the anomaly.
     - **Evidence**: Bulleted list of telemetry values triggering the rule.
     - **Verify**: Step-by-step checklist to confirm the condition in the field.
     - **Recommended Action**: Recommended operational or engineering mitigation.
   - **Empty State**: Renders `<Note>` if no open exceptions exist: `"No open exceptions. Well is inside envelope with stable electrical and thermal signals."`

---

#### C. Right-Rail Overlays & Persistent Panels (Visible Across All Tabs)

##### 1. `ESP ADVISOR — PREVIEW` (`AdvisorPanel`)
- **Type**: Collapsible Side Drawer / Rail Panel (width 330px).
- **Header Actions**:
  - Title: `"ESP Advisor — preview"`.
  - Subtitle: `"Decision support only. No control actions are issued from this module."`.
  - Button: `Collapse` -> Folds the panel into a slim vertical strip labelled `"ESP Advisor Preview"`. Clicking the collapsed strip expands it back.
- **Rendered Advisory Cards (`advisoriesFor(well)`)**:
  - **Header**: Advisory Kind pill (`Predictive`, `Optimization`, `Info`) + Confidence score (e.g. `confidence 82%`).
  - **Observation**: Diagnostic finding (e.g. `"Operating right of ROR — upthrust risk with motor load at 71%"`).
  - **Engineering Context**: Contextual rule explanation (e.g. `"Surveillance rules compare actual signals against the active design case and the recommended operating envelope."`).
  - **Assessment**: Impact evaluation (e.g. `"Evidence assembled from OTConnex tags and ESP-PMM calculations; engineer review required."`).
  - **Recommended Checks / Actions**: Bulleted action checklist (e.g. `"Verify field conditions before any setpoint change"`, `"Open the exception drawer for the full evidence chain"`).
  - **Evidence References**: Chip badges (e.g. `Operating point vs ROR`, `Actual vs expected table`, `Event history`).
- **Footer**: `"Advisory content is illustrative and evidence-referenced; engineering review is required before any setpoint change."`

##### 2. `ADVISOR ITEMS` Panel (Below Advisor Drawer)
- **Subtitle**: `"Evidence-backed, human-approved"`
- Compact list of active advisory cards displaying kind badges (`Predictive`, `Optimization`), confidence percentage, and concise assessment notes.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`← {prevId}`** (e.g. `← ESP-205`) | Header top right | Previous well's Well Monitor | `/wells/ESP-205` |
| **`{nextId} →`** (e.g. `ESP-101 →`) | Header top right | Next well's Well Monitor | `/wells/ESP-101` |
| **`Open in Engineering Workbench`** | Header top right (primary button) | Engineering Workbench with well pre-loaded | `/engineering/workbench?well=ESP-319` |
| **`Governed asset definition`** | Header top right | Governed Installed Fleet table | `/engineering/installations` |
| **`Overview` tab** | Main tab bar | Overview dashboard (Visual, timeline, envelope, TDH) | In-page tab switch (`Overview`) |
| **`Trends` tab** | Main tab bar | Multi-tag historical trend plots | In-page tab switch (`Trends`) |
| **`Operating point` tab** | Main tab bar | Detailed H-Q pump curve & variance table | In-page tab switch (`Operating point`) |
| **`Pressure profile` tab** | Main tab bar | Reservoir-to-wellhead pressure traverse | In-page tab switch (`Pressure profile`) |
| **`ESP string` tab** | Main tab bar | Detailed schematic & Asset ConneX registry | In-page tab switch (`ESP string`) |
| **`Events & exceptions` tab** | Main tab bar | Active well exceptions & evidence checklist | In-page tab switch (`Events & exceptions`) |
| **Time Range (`24h`, `7d`, `30d`, `60d`)** | `Trends` tab top right | Historical trend time window | In-page chart zoom/resample |
| **Signal Tags (`Amps`, `PIP`, `Hz`, etc.)** | `Trends` tab top bar | Overlaid signals on trend chart | In-page signal toggle |
| **`Collapse` / `ESP Advisor Preview`** | Advisor panel header | Toggles advisor right rail open/closed | In-page drawer collapse/expand |
| **`AD` Logo / `Fleet Cockpit`** | Global top bar & left sidebar | Global fleet overview | `/` |
| **`Exceptions`** | Global left sidebar | Fleet-wide exception triage queue | `/exceptions` |
| **`Troubleshooting`** | Global left sidebar | Guided diagnostic signature library | `/troubleshooting` |
| **`Reliability`** | Global left sidebar | Fleet run life, DIFA & bad actors | `/reliability` |
| **`Reports`** | Global left sidebar | Management scorecard | `/reports` |


---

### P4: Exceptions Queue — `/exceptions`
- **Page Title**: `Exception & Opportunity Queue — ADVAIT ESP-PMM`
- **Route**: `/exceptions`
- **File Path**: [`src/routes/exceptions.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/exceptions.tsx)
- **Layout Used**: L1 (`AppShell`)
- **Overlay Present**: None (Triage actions `Acknowledged`, `Assigned`, and `Closed` execute inline with immediate optimistic feedback)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Page Header (`PageHeader`)
- **Title**: `"Exception & Opportunity Queue"`
- **Description**: `"One prioritised list for the whole ESP fleet. Every item states what was observed, what evidence supports it, how to verify it and what action is recommended — so surveillance turns into decisions instead of alarm noise."`
- **Meta Status Pills**:
  - `Rules evaluated on normalised OTConnex signals` (Blue info pill)
  - `Confidence values are demo heuristics` (Muted grey pill)
- **Action Filter Toggle (`ToggleRow`)**:
  - 6 Selectable View Filters: `All` | `Critical` | `Warning` | `Watch` | `Opportunities` | `Unassigned`

##### 2. Top Summary KPI Strip (`KpiStrip` — 7 Stat Tiles)
- `CRITICAL`: `6` (Subtext: `Immediate action`, tone: `critical` red).
- `WARNING`: `8` (Subtext: `Same-shift review`, tone: `warning` orange).
- `WATCH`: `4` (Subtext: `Monitor trend`, tone: `watch` amber).
- `OPPORTUNITIES`: `5` (Subtext: `Upside candidates`, tone: `opportunity` green).
- `IMPACT AT RISK`: `4,676 bopd` (Subtext: `Sum of active impacts`, tone: `warning`).
- `UPSIDE IDENTIFIED`: `190 bopd` (Subtext: `Scenario estimates`, tone: `opportunity`).
- `VALUE AT STAKE`: `$330.9k /day` (Subtext: `Demo price deck`, unit: `/day`).

##### 3. Main Body — Split Two-Column Layout
- **Left Column (50% width)**: Scrollable prioritized exception queue table.
- **Right Column (50% width)**: Deep-dive investigation dossier and action card for the selected exception.

---

#### B. Detailed Breakdown of Each View & Panel

##### 1. View Filter Modes (`ToggleRow` Options)
- **`All`**: Displays all active exceptions sorted by severity rank (`critical` → `warning` → `watch` → `opportunity` → `info`) and descending production impact (`impactBopd`).
- **`Critical`**: Filters queue exclusively to `severity === "critical"` (immediate shutdown, power trip, or severe overload risks).
- **`Warning`**: Filters queue to `severity === "warning"` (intake degradation, high temperature, or ROR boundary breaches).
- **`Watch`**: Filters queue to `severity === "watch"` (emerging trends, data continuity issues).
- **`Opportunities`**: Filters queue to `severity === "opportunity"` (wells with hydraulic, thermal, and electrical headroom for rate uplift).
- **`Unassigned`**: Filters queue to unhandled exceptions where status is `"Open"`.

##### 2. Left Panel: `Queue — {N} items` Panel
- **Subtitle / Header**: Dynamic count matching active filter (e.g. `"Queue — 25 items"`).
- **Scroll Container**: High-density panel scroll with `maxHeight: calc(100vh - 330px)`.
- **Table Columns (6 Columns)**:
  1. `Sev`: Colored status badge (`critical` in red, `warning` in orange, `watch` in amber, `opportunity` in green, `info` in blue).
  2. `Well`: Monospace well ID link (e.g. `ESP-338`, `ESP-242`, `ESP-104`, `ESP-097`, `ESP-312`).
  3. `Category`: Operational anomaly category (truncated with ellipsis if > 190px).
  4. `Impact`: Production volume at risk in bopd (e.g. `1,180`, `1,050`, `210`, `168`, or `—` for opportunities).
  5. `Age`: Elapsed duration since event onset (e.g. `1 h`, `20 h`, `12 h`, `1 d 20 h`, `60 d`).
  6. `Status`: Status pill (`Open` in muted grey, `Acknowledged`, `Assigned`, or `Closed` in green).
- **Interactive Row Selection**:
  - Clicking any row highlights it with `bg-primary/10` and immediately populates the right panel with that exception's complete technical dossier.

##### 3. Right Panel: `{selected.id} — {selected.category}` (Investigation & Action Dossier)
- **Panel Header**:
  - Title: `${selected.id} — ${selected.category}` (e.g. `"EX-03 — Suspected gas interference / unstable amps"`).
  - Subtitle: `${selected.wellId} · ${fieldName(selected.fieldId)} · first seen ${selected.firstSeen}` (e.g. `"ESP-104 · Nardah North · first seen 2026-08-12 14:30"`).
  - **Triage Action Buttons (Top Right Header)**:
    - `[Acknowledged]`: Sets status to `Acknowledged` (highlights button in primary color).
    - `[Assigned]`: Sets status to `Assigned` (highlights button in primary color).
    - `[Closed]`: Sets status to `Closed` (highlights button in primary color).
- **Meta & Deep-Link Strip**:
  - `Severity Pill`: Colored tone badge (`critical`, `warning`, `opportunity`, `watch`).
  - `Owner Pill`: Grey badge e.g. `Owner: A. Rahman (Prod Eng)`.
  - `Status Pill`: Live status indicator (`Status: Open`, `Status: Acknowledged`, etc.).
  - `Confidence Pill`: Heuristic confidence score (e.g. `Confidence 74%`).
  - `Open Well Monitor →`: Primary link to `/wells/$wellId` for this well.
  - `Analyse in Workbench →`: Primary link to `/engineering/workbench?well=$wellId` preloaded for simulation.
- **Dossier Content Sections**:
  - **`RULE`**: Surveillance algorithm definition (e.g. `"Amp variability + PIP decline"`).
  - **`OBSERVATION`**: Plain English description of real-time operational symptoms (e.g. `"Motor current fluctuating across an 8.3 A band while pump intake pressure declined by 130 psi over the past 12 hours. Indicates free gas entering the pump stages causing cyclic gas loading."`).
  - **`EVIDENCE` (Left Column)**: Bulleted list of telemetry values triggering the rule:
    - `· Amp variability 8.3 A (band threshold 4 A)`
    - `· PIP declined from 340 psi to 210 psi over 12 h`
    - `· Liquid rate dropped 12% from previous stable period`
  - **`LIKELY CAUSES (RANKED)` (Right Column)**:
    - Ranked list of probable physical root causes with percentage weights and horizontal progress bars:
      - e.g. `Free gas ingestion at pump intake` | `72%` (Bar width: 72%)
      - e.g. `Declining reservoir pressure near wellbore` | `18%` (Bar width: 18%)
      - e.g. `Gas separator degradation or blockage` | `10%` (Bar width: 10%)
  - **`VERIFICATION STEPS`**: Numbered operational confirmation checklist:
    - `1. Check surface casing-tubing annulus pressure (CHP) for gas buildup.`
    - `2. Verify casing gas vent valve position and flowline backpressure.`
    - `3. Review latest PVT report for bubble point pressure relative to current PIP.`
  - **`RECOMMENDED ACTION`**: Numbered mitigation instructions:
    - `1. Open casing gas vent line to production separator to relieve annular gas pocket.`
    - `2. If hunting continues, reduce drive speed by 2.0 Hz to lower drawdown and stabilize intake.`
    - `3. Monitor PIP and motor amperage over the next 4 hours to verify stabilization.`
  - **`PRODUCTION IMPACT NOTE`**: Warning/Opportunity alert box:
    - e.g. `"Production impact: Deferred production from gas locking. Estimated value $21,760/day."`
  - **`AUDIT WORKFLOW NOTE`**: Informational banner explaining that state transitions integrate into ADVAIT notification and compliance audit trails.

---

#### C. Right-Rail Overlays & Modals
- **No blocking modals**: The entire triage and assignment workflow is inline within the right panel, maintaining continuous operational situational awareness.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`Queue Table Row`** | Left panel queue table | Selected exception investigation card | In-page row selection (`setSelectedId`) |
| **`Open Well Monitor →`** | Right panel meta row | Single Well Monitor for the selected well | `/wells/$wellId` (e.g. `/wells/ESP-104`) |
| **`Analyse in Workbench →`** | Right panel meta row | Engineering Workbench simulation | `/engineering/workbench?well=ESP-104` |
| **`[Acknowledged]`** | Right panel header top right | Updates status to Acknowledged | In-page optimistic state update |
| **`[Assigned]`** | Right panel header top right | Updates status to Assigned | In-page optimistic state update |
| **`[Closed]`** | Right panel header top right | Updates status to Closed | In-page optimistic state update |
| **`All` filter tab** | Header toggle row | Full prioritized exception queue | In-page filter (`All`) |
| **`Critical` filter tab** | Header toggle row | Critical exceptions only | In-page filter (`Critical`) |
| **`Warning` filter tab** | Header toggle row | Warning exceptions only | In-page filter (`Warning`) |
| **`Watch` filter tab** | Header toggle row | Watch exceptions only | In-page filter (`Watch`) |
| **`Opportunities` filter tab** | Header toggle row | Optimization opportunities only | In-page filter (`Opportunities`) |
| **`Unassigned` filter tab** | Header toggle row | Open unassigned items only | In-page filter (`Unassigned`) |
| **`AD` Logo / `Fleet Cockpit`** | Global top bar & left sidebar | Central fleet cockpit | `/` |
| **`Well Monitor`** | Global left sidebar | Well directory | `/wells` |
| **`Troubleshooting`** | Global left sidebar | Guided diagnostic assistant | `/troubleshooting` |
| **`Reliability`** | Global left sidebar | Run life & DIFA analytics | `/reliability` |
| **`Reports`** | Global left sidebar | Management scorecard | `/reports` |


---

### P5: Troubleshooting Assistant — `/troubleshooting`
- **Page Title**: `Troubleshooting Assistant — ESP diagnostics | ADVAIT ESP-PMM`
- **Route**: `/troubleshooting`
- **File Path**: [`src/routes/troubleshooting.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/troubleshooting.tsx)
- **Layout Used**: L1 (`AppShell`)
- **Overlay Present**: None (All diagnostics, signal trend overlays, and downhole subsystem callouts render inline)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Page Header (`PageHeader`)
- **Title**: `"Troubleshooting Assistant"`
- **Description**: `"ESP problems rarely show up as a single tag excursion. This workspace reads the pattern across flow, motor current, intake and discharge pressure, temperature and wellhead pressure, then ranks the causes that fit the whole signature."`
- **Meta Status Pills**:
  - `Direction-of-change library` (Blue info pill)
  - `Confidence values are demo heuristics for review, not automated decisions` (Muted grey pill)

##### 2. Main Architecture — Asymmetric Two-Column Diagnostic Workspace
- **Left Column (260px width)**: High-density `Signature library` case selector.
- **Right Column (Flex 1, minmax(0, 1fr))**: Comprehensive four-panel diagnostic workbench:
  - Top: Active Case Diagnostic Card (Signature table, ranked causes, verification, actions).
  - Middle Left/Right: Implicated Subsystem Visualizer (`EspWellVisual` with highlighted component).
  - Middle: Supporting 7-Day Multi-Tag Trend Evidence (`TrendChart` dual grid).
  - Bottom: Global VSD Trip Code Reference Table.

---

#### B. Detailed Breakdown of Each View & Panel

##### 1. Left Panel: `Signature library` Panel
- **Panel Header**: `"Signature library"`
- **Interactive Case Cards (`troubleshootingCases`)**:
  - Rendered as vertical stack of border-divided selection buttons.
  - **Card Content**:
    - Top row: Monospace Case ID (e.g. `TS-01`, `TS-02`, `TS-03`) on left, linked Well ID in primary color (e.g. `ESP-104`, `ESP-338`, `ESP-285`) on right.
    - Title: Descriptive fault pattern (e.g. `"Gas interference — slug behaviour"`, `"VSD trip on overcurrent"`, `"Flowline / choke restriction"`, `"Pump wear / stage degradation"`, `"Tubing leak / recirculating flow"`).
    - Trip Code Pill: Monospace trip code badge in warning color if applicable (e.g. `F42 Overcurrent`, `F12 Underload`, `F01 DC Bus Overvoltage`).
  - **Selection Interaction**:
    - Clicking any case highlights it with `bg-primary/10` and immediately re-binds all diagnostic panels, trend charts, and downhole schematics in the right column.

##### 2. Right Top Panel: `{tc.title}` Case Diagnostic Card
- **Panel Header**:
  - Title: Selected case title (e.g. `"Gas interference — slug behaviour"`).
  - Subtitle: Primary observed symptom (e.g. `"Motor current hunting with falling intake pressure"`).
  - Action Link: `"Open {well.id} →"` (e.g. `"Open ESP-104 →"`) -> deep-links directly to `/wells/$wellId`.
- **Four-Section Diagnostic Grid (2x2 Layout)**:
  1. **`DIAGNOSTIC SIGNATURE` Table (Top-Left)**:
     - Columns: `Signal`, `Direction`, `Expected behaviour`.
     - Direction Glyphs & Colors:
       - `▲ up` (Amber warning tone): Parameter rising abnormally.
       - `▼ down` (Red critical tone): Parameter dropping unexpectedly.
       - `▬ flat` (Muted grey tone): Parameter uncharacteristically unresponsive.
       - `∿ erratic` (Amber watch tone): Parameter hunting/oscillating.
     - Sample Rows:
       - `Motor amps` | `∿ erratic` | `Hunting across 6–10 A band as gas slugs enter stages`
       - `Pump intake pressure (PIP)` | `▼ down` | `Steadily declining below bubble point`
       - `Liquid rate` | `▼ down` | `Reduced liquid volume displaced during slugging`
       - `Wellhead pressure (WHP)` | `▲ up` | `Gas pockets collecting at surface tree`
  2. **`RANKED CAUSES` Cards (Top-Right)**:
     - Cards showing probable root causes ordered by confidence:
       - Header: Cause description + confidence percentage (e.g. `Free gas ingestion at pump intake` | `78%`).
       - Progress Bar: Horizontal colored bar (`bg-chart-1`) scaled to confidence percentage.
       - Rationale: Physical explanation of why the observed signature fits this failure mechanism.
  3. **`VERIFICATION SEQUENCE` (Bottom-Left)**:
     - Numbered step-by-step checklist to confirm condition in the field:
       - `1. Inspect casing-tubing annulus pressure gauge for gas cap accumulation.`
       - `2. Check casing gas vent check valve for mechanical binding or scale.`
       - `3. Compare downhole gauge intake pressure against fluid bubble point.`
       - `4. Verify VSD output frequency stability against supervisory setpoint.`
  4. **`RECOMMENDED ACTIONS` (Bottom-Right)**:
     - Bulleted operational mitigation procedure:
       - `→ Vent annular gas cap to production line or low-pressure header.`
       - `→ Lower drive frequency by 1.5–2.0 Hz to stabilize pump intake head.`
       - `→ If hunting persists, initiate casing chemical flush for foam clearing.`
     - **Advisory Note**: `<Note>` reminding operators that actions are decision-support only and do not execute automated setpoint writes.

##### 3. Right Middle Panel: `Implicated subsystem — {well.id}`
- **Subtitle**: `"The ESP string with the subsystem in focus for this signature highlighted"`
- **Subsystem Auto-Mapping (`caseSubsystem`)**:
  - Dynamically detects and highlights the implicated downhole component: `intake`, `motor`, `cable`, `gauge`, `pump`, `tubing`, `wellhead`, or `perfs`.
- **Layout (Grid 220px schematic + narrative)**:
  - Left: `EspWellVisual` compact schematic with the target subsystem highlighted in glowing outline.
  - Right: Description of the affected node, design tolerances, and telemetry sensor bindings.

##### 4. Right Middle Panel: `Supporting evidence — {well.id}`
- **Subtitle**: `"7-day window with event bands around the signature onset"`
- **Dual Trend Graph Grid (2 Columns, 200px Height Each)**:
  - Chart 1 (`TrendChart`): Plots `Frequency (Hz)` and `Oil rate (bopd)` over 7 days with vertical alarm bands.
  - Chart 2 (`TrendChart`): Plots `Pump Intake Pressure (PIP)` and `Pump Discharge Pressure (PDP)` over the same 7-day window to show hydraulic divergence.

##### 5. Lower Full-Width Panel: `VSD trip code reference`
- **Subtitle**: `"Common drive faults, typical causes and first response"`
- **Reference Table (4 Columns)**:
  - Columns: `Code`, `Fault`, `Typical cause`, `First response`.
  - Sample Rows:
    - `F01` | `DC Bus Overvoltage` | `Regenerative power during rapid deceleration or grid surge` | `Verify deceleration ramp time and dynamic braking resistors`
    - `F02` | `DC Bus Undervoltage` | `Utility feeder sag or loose incoming line connection` | `Inspect supply transformer taps and incoming phase balance`
    - `F12` | `Underload / Pump Off` | `Pump gas locked, shaft broken, or fluid level pumped off` | `Check PIP trend; do not restart if shaft shear is suspected`
    - `F18` | `Ground Fault / Earth Leakage` | `Cable insulation breakdown or downhole motor winding fault` | `Perform Megger insulation resistance test before reset`
    - `F23` | `Motor Overtemperature` | `Insufficient fluid flow past motor or heavy scale deposition` | `Confirm production flow rate meets motor cooling velocity (0.5 ft/s)`
    - `F42` | `Overcurrent / Locked Rotor` | `Solids in pump stages, heavy sand ingestion, or mechanical lock` | `Attempt rocking restart at low frequency; check amps balance`
    - `F51` | `Drive Overheat` | `Enclosure cooling fan failure or blocked air filters in MCC` | `Check enclosure ambient temp and clean air filters`

---

#### C. Right-Rail Overlays & Modals
- **No blocking overlays**: The entire diagnostic workflow is contained in a single split-view screen with continuous visibility into the signature library and VSD trip codes.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`Signature Library Item`** | Left panel case list | Selected diagnostic case dossier | In-page case selection (`setCaseId`) |
| **`Open {well.id} →`** | Diagnostic panel header | Single Well Monitor for the affected well | `/wells/$wellId` (e.g. `/wells/ESP-104`) |
| **`Well Visual Markers`** | Implicated subsystem panel | Displays design vs actual comparison | In-page marker hover tooltip |
| **`AD` Logo / `Fleet Cockpit`** | Global top bar & left sidebar | Central fleet cockpit | `/` |
| **`Well Monitor`** | Global left sidebar | Well directory | `/wells` |
| **`Exceptions`** | Global left sidebar | Prioritized exception queue | `/exceptions` |
| **`Reliability`** | Global left sidebar | Run life & failure analysis | `/reliability` |
| **`Reports`** | Global left sidebar | Executive scorecard | `/reports` |
| **`Workspace Switcher`** | Global top bar header | Switches to Engineering configuration | `/engineering` |


---

### P6: Reliability & Run Life — `/reliability`
- **Page Title**: `Reliability & Run Life — ADVAIT ESP-PMM`
- **Route**: `/reliability`
- **File Path**: [`src/routes/reliability.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/reliability.tsx)
- **Layout Used**: L1 (`AppShell`)
- **Overlay Present**: None (Modal-free inline tabbed workspace)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Page Header (`PageHeader`)
- **Title**: `"Reliability & Run Life"`
- **Description**: `"Run life is the outcome of how wells were operated, not only of the equipment installed. This workspace links failure history and DIFA findings back to the operating factors ESP-PMM can influence — envelope compliance, temperature, free gas, abrasives and electrical integrity."`
- **Meta Status Pills**:
  - `34 pull records · 25 wells · 3 fields` (Blue info pill, `StatusPill tone="info"`)
  - `Cost and deferment figures are illustrative` (Muted grey pill, `StatusPill tone="muted"`)
- **Tab Navigation Controls (`ToggleRow`)**:
  - 5 Selectable Tabbed Views: `Run life` (Default) | `Failure analysis` | `Bad actors` | `Interventions` | `DIFA records`

##### 2. Top Reliability KPI Summary Strip (`KpiStrip` — 7 Stat Tiles)
- `MEAN RUN LIFE`: `842 days` (Subtext: `All recorded pulls`, unit: `days`, calculated across all 34 recorded failure pulls).
- `REPEAT FAILURE RATE`: `29%` (Subtext: `Same well within 2 runs`, unit: `%`, tone: `warning` as `repeatRate > 25%`, calculated from repeat failure flags).
- `RECORDED PULLS`: `34` (Subtext: `With DIFA summary`, total failure records tracked in system).
- `INTERVENTION SPEND`: `$4.1M` (Subtext: `Cumulative, illustrative`, calculated from sum of historical pull costs).
- `DEFERRED VOLUME`: `186,000 bbl` (Subtext: `Associated with failures`, unit: `bbl`, tone: `warning`, cumulative production volume lost to failures).
- `HIGH-RISK WELLS`: `4` (Subtext: `Risk score above 60`, tone: `critical`, count of bad actors exceeding risk threshold 60).
- `PLANNED INTERVENTIONS`: `7` (Subtext: `Proposed or scheduled`, active queued interventions excluding executed items).

---

#### B. Detailed Breakdown of Each Tabbed View

##### Tab 1: `Run life` View
1. **`Run-life distribution by field` Panel** (`SimpleBar`, height 260px):
   - **Subtitle**: `"Pull counts per run-life bucket"`
   - **Bucket Partitions (6 Categories)**: `0–180 d`, `180–360 d`, `360–540 d`, `540–720 d`, `720–900 d`, `900–1200 d`.
   - **Grouped Bars by Field**:
     - `Nardah North`: Blue bar (`var(--color-chart-1)`).
     - `Kalisto West`: Emerald bar (`var(--color-chart-2)`).
     - `Tamrin Deep`: Amber bar (`var(--color-chart-3)`).
2. **`Run life by field` Table Panel**:
   - **Header**: `"Run life by field"`
   - **Columns (6 Columns)**: `Field`, `Pulls`, `Mean d`, `Median d`, `Shortest d`, `Repeat %`.
   - **Column Alignment & Highlighting**:
     - `Field`: Left aligned.
     - `Pulls`: Right-aligned monospace.
     - `Mean d`: Right-aligned monospace (days formatted with `n0`).
     - `Median d`: Right-aligned monospace (days formatted with `n0`).
     - `Shortest d`: Right-aligned monospace, styled in `text-warning`.
     - `Repeat %`: Right-aligned monospace, styled in `text-warning` if exceeding 25%.
   - **Rows**:
     - `Nardah North` | `13` | `812` | `795` | `142` (warning) | `31` (warning)
     - `Kalisto West` | `12` | `854` | `830` | `188` (warning) | `25`
     - `Tamrin Deep` | `9` | `871` | `860` | `210` (warning) | `33` (warning)
3. **`Mean run life by pump family` Panel** (`SimpleBar`, vertical layout, height 280px, yWidth 170px):
   - **Header**: `"Mean run life by pump family"`
   - **Horizontal Bars**: Plots mean run life in days for each governed OEM pump line (`var(--color-chart-2)`):
     - `Vertek Lift VX-Series` (Mean run life: ~820 d, population: 7 wells)
     - `Corenta Systems CN-Flow` (Mean run life: ~890 d, population: 6 wells)
     - `Halcyon Downhole HD-Prime` (Mean run life: ~780 d, population: 6 wells)
     - `Meridian Artificial Lift MR-Stage` (Mean run life: ~860 d, population: 6 wells)
4. **`Run-life influencing factors` Table Panel**:
   - **Subtitle**: `"Weighted model used for the ESP health index and risk score"`
   - **Columns (3 Columns)**: `Factor`, `Weight`, `Why it matters`.
   - **Model Factors Breakdown (10 Governed Influencing Factors)**:
     - `Proper sizing / envelope compliance` | `22%` | `Time outside ROR drives downthrust and upthrust wear`
     - `Bottomhole / operating temperature` | `15%` | `Insulation and elastomer life fall with sustained high temperature`
     - `Free gas at intake` | `14%` | `Gas cycling causes thrust and seal damage`
     - `Sand / foreign material` | `13%` | `Abrasive wear of stages and bearings`
     - `Corrosion` | `9%` | `CO2 / H2S exposure and material selection`
     - `Deposition / scale` | `8%` | `Head loss and mechanical drag`
     - `Fluid viscosity` | `7%` | `Head and efficiency correction; motor loading`
     - `Electrical failures` | `7%` | `Cable, MLE, splice and motor winding integrity`
     - `Operational problems` | `3%` | `Repeat restarts, nuisance trips, unstable operation`
     - `Age / accumulated cycles` | `2%` | `Baseline wear-out`

---

##### Tab 2: `Failure analysis` View
1. **`Failure-mode Pareto` Panel** (`ParetoChart`, height 320px):
   - **Subtitle**: `"Where reliability effort pays back first"`
   - **Dual-Axis Visualization**:
     - Left Axis (Bars): Number of pulls per failure mode.
     - Right Axis (Line): Cumulative percentage line spanning 0% to 100%.
   - **Ranked Failure Modes**:
     - `Stage / bearing wear (abrasives)`: 7 pulls (21% cum)
     - `Winding insulation failure`: 6 pulls (38% cum)
     - `Insulation degradation at splice`: 5 pulls (53% cum)
     - `Bag / labyrinth failure`: 4 pulls (65% cum)
     - `Shaft break`: 4 pulls (76% cum)
     - `Scale-induced lock-up`: 3 pulls (85% cum)
     - `Rotor wear`: 3 pulls (94% cum)
     - `Thermal overload`: 1 pull (97% cum)
     - `Comms / sensor failure`: 1 pull (100% cum)
2. **`Failures by component` Panel** (`SimpleBar`, vertical layout, height 320px, yWidth 130px):
   - **Header**: `"Failures by component"`
   - **Horizontal Pull Count Bars** (`var(--color-chart-4)`):
     - `Pump`: 14 pulls (Combined abrasives, shaft shears, and scale)
     - `Motor`: 7 pulls (Winding insulation failure and thermal overload)
     - `Cable / MLE`: 5 pulls (Splice and pothead insulation degradation)
     - `Seal section`: 4 pulls (Protector barrier bag and mechanical seal ingress)
     - `Gas separator`: 3 pulls (Rotor erosion and bearing cavitation wear)
     - `Downhole gauge`: 1 pull (Communication circuit and sensor loss)

---

##### Tab 3: `Bad actors` View
1. **`Asset context` Panel**:
   - **Subtitle**: `"Compact ESP string miniature per high-risk well — static reference view"`
   - **Mini ESP String Cards (`badActors.slice(0, 8)`)**:
     - Flex-wrapping strip of 8 interactive well cards (width: 86px, border, card background, hover highlight).
     - **Card Content**:
       - `EspWellMini`: Miniature vertical SVG schematic (height: 84px) representing downhole configuration and health status.
       - Well ID: Monospace text in primary blue (e.g. `ESP-242`, `ESP-338`, `ESP-104`).
       - Risk Score: Monospace badge (e.g. `risk 88`, `risk 84`, `risk 76`).
     - **Action Link**: Clicking any card routes directly to Single Well Monitor (`/wells/$wellId`).
2. **`Bad-actor ranking` Table Panel**:
   - **Subtitle**: `"Composite of health index, failure history, repeat pulls and operating state"`
   - **Scrollable Container**: `overflow-auto panel-scroll` with `maxHeight: calc(100vh - 300px)`.
   - **Columns (11 Columns)**: `Well`, `Field`, `Risk score`, `Health`, `Run life d`, `Prior run d`, `Pulls`, `Repeat`, `Dominant factor`, `Indicative RUL d`, `Defer bopd`.
   - **Column Alignment & Styling**:
     - `Well`: Clickable monospace link to `/wells/$wellId` styled with `text-primary hover:underline`.
     - `Field`: Muted text (`text-muted-foreground`).
     - `Risk score`: Monospace, colored `text-critical` if > 70, `text-warning` if > 50.
     - `Health`: Right-aligned monospace health index (0–100).
     - `Run life d`: Right-aligned monospace current operating days (`n0`).
     - `Prior run d`: Right-aligned monospace prior installation duration (`n0 text-muted-foreground`).
     - `Pulls`: Right-aligned monospace pulls recorded in last 12 months.
     - `Repeat`: Warning pill `<StatusPill tone="warning">Repeat</StatusPill>` if repeat failure, or `—` if false.
     - `Dominant factor`: Muted text explaining primary degradation driver.
     - `Indicative RUL d`: Right-aligned monospace estimated remaining useful life in days.
     - `Defer bopd`: Right-aligned monospace production volume deferred, styled in `text-warning` if > 0.
   - **Sample Rows**:
     - `ESP-242` | `Kalisto West` | `88` (critical) | `32` | `142` | `510` | `3` | `Repeat` (warning pill) | `Operational problems` | `96` | `1,050` (warning)
     - `ESP-338` | `Tamrin Deep` | `84` (critical) | `38` | `188` | `620` | `2` | `Repeat` (warning pill) | `Electrical failures` | `108` | `1,180` (warning)
     - `ESP-104` | `Nardah North` | `76` (critical) | `45` | `240` | `710` | `2` | `Repeat` (warning pill) | `Free gas at intake` | `132` | `168` (warning)
     - `ESP-097` | `Nardah North` | `72` (critical) | `48` | `310` | `840` | `2` | `Repeat` (warning pill) | `Sand / foreign material` | `144` | `210` (warning)
     - `ESP-271` | `Kalisto West` | `64` (warning) | `52` | `415` | `780` | `1` | `—` | `Sand / foreign material` | `168` | `130` (warning)
     - `ESP-118` | `Nardah North` | `62` (warning) | `55` | `490` | `650` | `1` | `—` | `Deposition / scale` | `174` | `110` (warning)
     - `ESP-205` | `Kalisto West` | `58` (warning) | `58` | `520` | `890` | `1` | `—` | `Envelope compliance` | `186` | `120` (warning)
     - `ESP-126` | `Nardah North` | `54` (warning) | `60` | `610` | `740` | `1` | `—` | `Bottomhole / operating temperature` | `198` | `60` (warning)
   - **Machine-Learning RUL Disclaimer Note (`<Note>`)**:
     - `"Remaining-useful-life values shown here are indicative placeholders produced by the demo risk model. Machine-learning RUL prediction is a later phase that requires accumulated fleet history and validated failure labels."`

---

##### Tab 4: `Interventions` View
1. **`Intervention plan` Table Panel**:
   - **Subtitle**: `"Recommended work ranked by impact and risk"`
   - **Columns (9 Columns)**: `ID`, `Well`, `Type`, `Priority`, `Window`, `Reason`, `Impact bopd`, `Risk`, `Status`.
   - **Column Alignment & Styling**:
     - `ID`: Monospace intervention ID (`INT-xxx`).
     - `Well`: Monospace link to `/wells/$wellId` styled with `text-primary hover:underline`.
     - `Type`: Intervention classification (`Workover / ESP replacement`, `VSD service`, `Redesign & resize`, `Chemical / scale treatment`, `Gauge repair`).
     - `Priority`: Right-aligned monospace priority code (`P1`, `P2`, `P3`).
     - `Window`: Monospace date window string (`YYYY-MM-DD → MM-DD` or date).
     - `Reason`: Truncated operational explanation (`max-w-[320px] truncate text-muted-foreground`).
     - `Impact bopd`: Right-aligned monospace deferred volume recovered, or `—` if zero.
     - `Risk`: Right-aligned monospace risk score, styled in `text-critical` if > 80.
     - `Status`: Colored status badge (`StatusPill` with `tone="normal"` for `Executed`, `tone="info"` for `Scheduled`, `tone="muted"` for `Proposed`).
   - **Complete Interventions Inventory (10 Items)**:
     - `INT-401` | `ESP-242` | `Workover / ESP replacement` | `P1` | `2026-08-22 → 08-27` | `Suspected broken shaft, well down, full deferment` | `1,050` | `96` (critical) | `Scheduled` (info pill)
     - `INT-402` | `ESP-338` | `VSD service` | `P1` | `2026-08-15` | `Repeat F-014 trips with lockout; electrical verification required` | `1,180` | `91` (critical) | `Scheduled` (info pill)
     - `INT-403` | `ESP-097` | `Workover / ESP replacement` | `P2` | `2026-09-08 → 09-13` | `Head-per-stage decline 17% over 60 days` | `210` | `78` | `Proposed` (muted pill)
     - `INT-404` | `ESP-271` | `Redesign & resize` | `P2` | `2026-09-19` | `Abrasive wear with chronic downthrust exposure; resize with abrasion-resistant stages` | `130` | `72` | `Proposed` (muted pill)
     - `INT-405` | `ESP-118` | `Chemical / scale treatment` | `P2` | `2026-08-19` | `Intake / perforation restriction suspicion with scale tendency` | `110` | `64` | `Proposed` (muted pill)
     - `INT-406` | `ESP-076` | `Gauge repair` | `P3` | `2026-08-26` | `Intermittent gauge comms reducing analytics confidence` | `—` | `41` | `Proposed` (muted pill)
     - `INT-407` | `ESP-331` | `Gauge repair` | `P3` | `2026-08-27` | `Gauge signal lost; surface-only surveillance` | `—` | `44` | `Proposed` (muted pill)
     - `INT-408` | `ESP-205` | `Redesign & resize` | `P3` | `2026-10-02` | `Pump oversized for current inflow; chronic left-of-ROR operation` | `120` | `58` | `Proposed` (muted pill)
     - `INT-409` | `ESP-126` | `Redesign & resize` | `P2` | `2026-09-25` | `Motor loading at 79% with rising water cut` | `60` | `69` | `Proposed` (muted pill)
     - `INT-410` | `ESP-133` | `Workover / ESP replacement` | `P3` | `Executed 2026-08-12` | `Planned flowline tie-in with ESP inspection` | `—` | `22` | `Executed` (normal green pill)

---

##### Tab 5: `DIFA records` View
1. **`Pull and DIFA history` Table Panel**:
   - **Subtitle**: `"Teardown findings linked to the operating factor that drove them"`
   - **Scrollable Container**: `overflow-auto panel-scroll` with `maxHeight: calc(100vh - 300px)`.
   - **Columns (9 Columns)**: `Record`, `Well`, `Pulled`, `Run life d`, `Component`, `Failure mode`, `Root-cause factor`, `DIFA summary`, `Cost kUSD`.
   - **Column Alignment & Styling**:
     - `Record`: Monospace pull record identifier (`DIFA-xxxx`).
     - `Well`: Monospace well identifier (`ESP-xxx`).
     - `Pulled`: Monospace date (`YYYY-MM-DD text-muted-foreground`).
     - `Run life d`: Right-aligned monospace days, styled in `text-warning` if < 300 days.
     - `Component`: Plain text failed assembly component (`Pump`, `Motor`, `Cable / MLE`, `Seal section`, `Gas separator`, `Downhole gauge`).
     - `Failure mode`: Specific mechanical or electrical failure mechanism.
     - `Root-cause factor`: Muted text linking failure back to one of the 10 governed operating factors.
     - `DIFA summary`: Muted truncated teardown inspection narrative (`max-w-[340px] truncate text-muted-foreground`).
     - `Cost kUSD`: Right-aligned monospace pull and replacement expense in thousands of USD.
   - **Sample Rows (Selected from 34 Tracked Teardown Records)**:
     - `DIFA-2100` | `ESP-101` | `2024-01-15` | `840` | `Pump` | `Stage / bearing wear (abrasives)` | `Sand / foreign material` | `Abrasive wear on impeller skirts and diffuser hubs; radial bearings within 60% of wear limit.` | `385`
     - `DIFA-2101` | `ESP-102` | `2024-02-05` | `210` (warning) | `Motor` | `Winding insulation failure` | `Electrical failures` | `Insulation resistance below limit at MLE splice; thermal ageing evident on winding sample.` | `510`
     - `DIFA-2102` | `ESP-103` | `2024-02-26` | `1,020` | `Pump` | `Shaft break` | `Operational problems` | `Teardown confirmed shaft failure at pump-protector coupling; heavy downthrust marking on lower stages.` | `420`
     - `DIFA-2103` | `ESP-104` | `2024-03-18` | `185` (warning) | `Seal section` | `Bag / labyrinth failure` | `Bottomhole / operating temperature` | `Elastomer degradation on upper barrier bag; wellbore fluid contamination in chamber 1.` | `340`
     - `DIFA-2104` | `ESP-105` | `2024-04-08` | `650` | `Pump` | `Scale-induced lock-up` | `Deposition / scale` | `Deposition on stage internals with reduced flow passage; chemistry consistent with carbonate scale.` | `290`
     - `DIFA-2105` | `ESP-106` | `2024-04-29` | `715` | `Gas separator` | `Rotor wear` | `Free gas at intake` | `Erosive blade thinning and casing cavitation pitting on gas intake separator.` | `315`

---

#### C. Right-Rail Overlays & Modals
- **Modal-Free Tabbed Layout**: The entire reliability and teardown analytics workspace is delivered inline across 5 tabs without blocking popup modals or slide-over sheets. All forensic DIFA records, bad-actor tables, Pareto charts, and intervention workover schedules maintain continuous situational visibility.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`Run life` tab** | Header toggle row | Tab 1: Run-life distribution, field durability & factor weights | In-page tab switch (`setTab("Run life")`) |
| **`Failure analysis` tab** | Header toggle row | Tab 2: Dual-axis Pareto chart & failures by component | In-page tab switch (`setTab("Failure analysis")`) |
| **`Bad actors` tab** | Header toggle row | Tab 3: Mini string visuals, bad-actor ranking & RUL note | In-page tab switch (`setTab("Bad actors")`) |
| **`Interventions` tab** | Header toggle row | Tab 4: Prioritized intervention plan & workover candidates | In-page tab switch (`setTab("Interventions")`) |
| **`DIFA records` tab** | Header toggle row | Tab 5: Detailed teardown inspection history (34 records) | In-page tab switch (`setTab("DIFA records")`) |
| **`EspWellMini` Card** (e.g. `ESP-242`) | Bad actors panel (`Asset context`) | Single Well Monitor for the selected well | `/wells/$wellId` (e.g. `/wells/ESP-242`) |
| **`Well ID Link`** (e.g. `ESP-242`) | Bad-actor ranking table | Single Well Monitor for the bad-actor well | `/wells/$wellId` (e.g. `/wells/ESP-242`) |
| **`Well ID Link`** (e.g. `ESP-338`) | Intervention plan table | Single Well Monitor for the target well | `/wells/$wellId` (e.g. `/wells/ESP-338`) |
| **`AD` Logo / `Fleet Cockpit`** | Global top bar & left sidebar | Central fleet cockpit | `/` |
| **`Well Monitor`** | Global left sidebar | Well directory | `/wells` |
| **`Exceptions`** | Global left sidebar | Prioritized exception queue | `/exceptions` |
| **`Troubleshooting`** | Global left sidebar | Guided diagnostic assistant | `/troubleshooting` |
| **`Reports`** | Global left sidebar | Management scorecard | `/reports` |
| **`Workspace Switcher`** | Global top bar header | Switches to Engineering configuration | `/engineering` |


---

### P7: Management Scorecard & Reports — `/reports`
- **Page Title**: `Management Scorecard & Reports — ADVAIT ESP-PMM`
- **Route**: `/reports`
- **File Path**: [`src/routes/reports.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/reports.tsx)
- **Layout Used**: L1 (`AppShell`)
- **Overlay Present**: None (Single-page executive scorecard layout)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Page Header (`PageHeader`)
- **Title**: `"Management Scorecard & Reports"`
- **Description**: `"One page for asset leadership: how much production the ESP fleet is losing, how much of it is avoidable, where run life is short and which wells deserve engineering and rig attention this week."`
- **Meta Status Pills**:
  - `Reporting period: last 24 hours and rolling 12 months` (Blue info pill, `StatusPill tone="info"`)
  - `Demo price deck $68/bbl` (Muted grey pill, `StatusPill tone="muted"`)

##### 2. Top Executive KPI Strip (`KpiStrip` — 7 Stat Tiles)
- `FLEET AVAILABILITY`: `88%` (Subtext: `22 of 25 running`, unit: `%`, calculated as running wells divided by 25 total wells).
- `FLEET HEALTH INDEX`: `65.7` (Subtext: `Weighted composite`, tone: `watch`, fleet-wide weighted envelope and thermal health index).
- `ENVELOPE COMPLIANCE`: `76%` (Subtext: `Running wells inside ROR`, unit: `%`, tone: `warning` as `compliance < 80%`, calculated as 19 running wells inside recommended operating range).
- `DEFERMENT`: `4,676 bopd` (Subtext: `$317,968/day` evaluated at $68/bbl, unit: `bopd`, tone: `warning`, sum of production deferment against active design cases).
- `IDENTIFIED UPSIDE`: `190 bopd` (Subtext: `$12,920/day` evaluated at $68/bbl, unit: `bopd`, tone: `opportunity`, sum of production upside from healthy wells with headroom).
- `REPEAT / AVOIDABLE PULLS`: `10` (Subtext: `of 34 recorded pulls`, tone: `critical`, historical failures marked as repeat pulls on the same well within 2 runs).
- `RIG WORK QUEUED`: `5` (Subtext: `Workover candidates`, count of queued interventions specifying full workover rig deployment).

##### 3. Main Dashboard Grid (Structured Two-Tier Multi-Column Layout)
- **Top Row (Two-Column Asymmetric Grid `minmax(0, 1.2fr) minmax(0, 1fr)`)**:
  - Left: `Field scorecard` full-width asset performance table.
  - Right: `Deferment and upside by field` grouped bar chart.
- **Bottom Row (Three-Column Balanced Grid `xl:grid-cols-3`)**:
  - Left: `Where to focus this week` high-exposure bad-actor table.
  - Middle: `Run life by field` mean vs median comparative bar chart.
  - Right: `Top failure modes` Pareto frequency table with automated reporting note.

---

#### B. Detailed Breakdown of Panels

##### 1. Top Left Panel: `Field scorecard` Table Panel
- **Header**: `"Field scorecard"`
- **Table Columns (9 Columns)**: `Field`, `Wells`, `Avail %`, `Health`, `Oil bopd`, `Defer bopd`, `Upside bopd`, `Envelope %`, `Open exc.`
- **Column Alignment & Styling**:
  - `Field`: Left aligned field name.
  - `Wells`: Right-aligned monospace total wells on field.
  - `Avail %`: Right-aligned monospace runtime availability percentage.
  - `Health`: Right-aligned monospace average health index.
  - `Oil bopd`: Right-aligned monospace allocated gross oil rate (`n0`).
  - `Defer bopd`: Right-aligned monospace production deferment (`n0 text-warning`).
  - `Upside bopd`: Right-aligned monospace identified rate uplift potential (`n0 text-opportunity`).
  - `Envelope %`: Right-aligned monospace percentage of running wells operating within ROR, styled in `text-warning` if < 80%.
  - `Open exc.`: Right-aligned monospace active unresolved exceptions (`status !== "Closed"`).
- **Field Performance Breakdown (3 Operating Fields)**:
  - `Nardah North` | `9` | `89%` | `64` | `9,420` | `1,540` (warning) | `80` (opportunity) | `75%` (warning) | `8`
  - `Kalisto West` | `9` | `89%` | `68` | `10,112` | `1,820` (warning) | `70` (opportunity) | `75%` (warning) | `9`
  - `Tamrin Deep` | `7` | `86%` | `65` | `6,520` | `1,316` (warning) | `40` (opportunity) | `80%` | `5`

##### 2. Top Right Panel: `Deferment and upside by field` Chart Panel (`SimpleBar`, height 230px)
- **Header**: `"Deferment and upside by field"`
- **Chart Layout**: Horizontal grouped bar chart comparing production lost to downtime/degradation versus potential rate gain from envelope tuning.
- **Data Series (2 Bars per Field)**:
  - `Deferred bopd`: Amber warning bar (`var(--color-warning)`).
  - `Upside bopd`: Emerald opportunity bar (`var(--color-opportunity)`).
- **Field Comparison**:
  - `Nardah North`: 1,540 bopd deferred vs 80 bopd upside.
  - `Kalisto West`: 1,820 bopd deferred vs 70 bopd upside.
  - `Tamrin Deep`: 1,316 bopd deferred vs 40 bopd upside.

##### 3. Bottom Left Panel: `Where to focus this week` Table Panel
- **Subtitle**: `"Highest combined production and reliability exposure"`
- **Focus List**: Top 8 bad-actor wells ranked by composite risk score (`badActors.slice(0, 8)`).
- **Columns (4 Columns)**: `Well`, `Risk`, `Defer bopd`, `Dominant factor`.
- **Column Alignment & Styling**:
  - `Well`: Monospace well identifier (`mono`).
  - `Risk`: Right-aligned monospace composite risk score.
  - `Defer bopd`: Right-aligned monospace deferred volume (`n0`), or `—` if zero.
  - `Dominant factor`: Muted text description of physical degradation driver (`text-muted-foreground`).
- **Sample Focus Rows**:
  - `ESP-242` | `88` | `1,050` | `Operational problems`
  - `ESP-338` | `84` | `1,180` | `Electrical failures`
  - `ESP-104` | `76` | `168` | `Free gas at intake`
  - `ESP-097` | `72` | `210` | `Sand / foreign material`
  - `ESP-271` | `64` | `130` | `Sand / foreign material`
  - `ESP-118` | `62` | `110` | `Deposition / scale`
  - `ESP-205` | `58` | `120` | `Envelope compliance`
  - `ESP-126` | `54` | `60` | `Bottomhole / operating temperature`

##### 4. Bottom Middle Panel: `Run life by field` Chart Panel (`SimpleBar`, height 230px)
- **Header**: `"Run life by field"`
- **Chart Layout**: Grouped comparison bars per field comparing mean run life against median run life to reveal statistical skew from infant mortality.
- **Data Series (2 Bars per Field)**:
  - `Mean run life (d)`: Blue bar (`var(--color-chart-2)`).
  - `Median run life (d)`: Cyan bar (`var(--color-chart-1)`).
- **Field Metrics**:
  - `Nardah North`: Mean 812 days vs Median 795 days (Shortest: 142 d).
  - `Kalisto West`: Mean 854 days vs Median 830 days (Shortest: 188 d).
  - `Tamrin Deep`: Mean 871 days vs Median 860 days (Shortest: 210 d).

##### 5. Bottom Right Panel: `Top failure modes` Table Panel
- **Header**: `"Top failure modes"`
- **Columns (3 Columns)**: `Failure mode`, `Pulls`, `Cum %`.
- **Column Alignment & Styling**:
  - `Failure mode`: Left aligned forensic classification name.
  - `Pulls`: Right-aligned monospace pull count.
  - `Cum %`: Right-aligned monospace cumulative percentage in muted text (`text-muted-foreground`).
- **Top 7 Failure Modes (`failureModePareto.slice(0, 7)`)**:
  - `Stage / bearing wear (abrasives)` | `7` | `21%`
  - `Winding insulation failure` | `6` | `38%`
  - `Insulation degradation at splice` | `5` | `53%`
  - `Bag / labyrinth failure` | `4` | `65%`
  - `Shaft break` | `4` | `76%`
  - `Scale-induced lock-up` | `3` | `85%`
  - `Rotor wear` | `3` | `94%`
- **Scheduled Reporting & PDF Export Note (`<Note>`)**:
  - `"Reports in the delivered module are scheduled and distributed through the ADVAIT notification service, with export to PDF and Excel and a stored snapshot for each reporting period."`

---

#### C. Right-Rail Overlays & Modals
- **Modal-Free Layout**: The scorecard is structured as an executive single-view dashboard without intrusive dialogs or slide-over overlays, optimized for periodic asset management briefings, PDF exports, and executive reviews.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`AD` Logo / `Fleet Cockpit`** | Global top bar & left sidebar | Central fleet cockpit | `/` |
| **`Well Monitor`** | Global left sidebar | Fleet well directory | `/wells` |
| **`Exceptions`** | Global left sidebar | Prioritized exception triage queue | `/exceptions` |
| **`Troubleshooting`** | Global left sidebar | Guided diagnostic assistant | `/troubleshooting` |
| **`Reliability`** | Global left sidebar | Run life, bad actors & DIFA records | `/reliability` |
| **`Engineering Home`** | Global left sidebar | Governed master data portal | `/engineering` |
| **`Equipment Catalog`** | Global left sidebar | Equipment catalog | `/engineering/catalog` |
| **`Installed Fleet`** | Global left sidebar | Governed string assemblies | `/engineering/installations` |
| **`Engineering Workbench`** | Global left sidebar | Engineering simulation workbench | `/engineering/workbench` |
| **`Field Selector`** | Global top bar | Filters fleet view by oilfield | In-page filter |
| **`Workspace Switcher`** | Global top bar | Switches between Operations & Engineering | `/engineering` |

---

### P8: Engineering Home — `/engineering/`

> [!IMPORTANT]
> **Dedicated Engineering & Configuration Documentation Available**:
> The entire Engineering / Configuration Workspace is documented in depth in its dedicated master specification:
> 🔗 **[Enumeration-Engineering_Configuration.md](file:///x:/TAS/ESP_APM_server/esp-insight-suite/audit/Enumeration-Engineering_Configuration.md)** (alias: [`Enumeratin-Engineering_Configuration.md`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/audit/Enumeratin-Engineering_Configuration.md))
> In the dedicated document, this page is indexed as **Page 1 (P1: Engineering Home / Asset Definition Overview)** and includes exhaustive micro-component breakdowns, plain-English bracketed annotations, and live operational values from the operator's running environment.

- **Page Title**: `Asset Definitions overview — ADVAIT ESP-PMM`
- **Route**: `/engineering/` (Exact root route of Configuration workspace)
- **File Path**: [`src/routes/engineering.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.index.tsx)
- **Layout Used**: L2 (`src/routes/engineering.tsx` sub-navigation shell)
- **Overlay Present**: None (Governed master data portal with inline tree hierarchy, reliability grade mix, and reconciliation blocks)

#### A. Rendered Components (Top → Bottom, Left → Right)

##### 1. Sub-Navigation Sidebar Shell (`L2` in `engineering.tsx`)
- **Desktop Sidebar (188px sticky panel)**:
  - Header: `"ESP Engineering Configuration"` | `"Asset ConneX governed master data"`.
  - Group 1: `Reference master`
    - `Engineering Overview` (Active link `/engineering`)
    - `Equipment Catalog` (`/engineering/catalog`)
  - Group 2: `Installed fleet`
    - `Installed ESP Systems` (`/engineering/installations`)
    - `Well Definition (revisions)` (`/engineering/definition`)
  - Group 3: `Engineering analysis`
    - `Engineering Workbench` (`/engineering/workbench`)
    - `Design Cases` (`/engineering/design-cases`)
  - Group 4: `Governance`
    - `Validation & Readiness` (`/engineering/governance/validation`)
    - `Source / Provenance Registry` (`/engineering/governance/sources`)
    - `Data Quality & Reconciliation` (`/engineering/governance/quality`)
    - `Import / Catalog Administration` (`/engineering/governance/import`)
  - Footer Pill: `{blocking} blocking QA` (Red `critical` badge if blocking issues exist, else green `normal` — Live value: `2 blocking QA`).
- **Tablet / Mobile Ribbon**: Horizontal scrollable pill bar with links to all 10 sub-sections.

##### 2. Page Header (`PageHeader`)
- **Title**: `"Asset Definition Overview"`
- **Description**: `"Governed engineering master data (Asset ConneX concept). Every catalog value carries a source and reliability class; OT measurement remains in OTConnex and is never written here."`
- **Meta Status Pills**:
  - `Engineering configuration — read-only master data` (Blue info pill, `StatusPill tone="info"`)
  - `2 blocking issues` (Red critical pill, `StatusPill tone="critical"`)

##### 3. Top Master Data Metric Strip (`Metric` — 7 Stat Tiles)
- `CCED SOURCE ROWS`: `170` (Subtext: `169 with raw designation · 1 blank`, tone: `watch`).
- `WELLS`: `170` (Subtext: `1 fields · ESP lift`).
- `UNRESOLVED / PARTIAL MATCH`: `15` (Subtext: `excluded from calculations`, tone: `watch`).
- `PUMP MODELS`: `62` (Subtext: `31 CCED-priority · 56 calc-grade`).
- `DIGITISED CURVES`: `0` (Subtext: `0 points loaded`, tone: `warning`).
- `SECONDARY DISCOVERY`: `748` (Subtext: `of 751 reported (C1)`, tone: `watch`).
- `EVIDENCE SOURCES`: `15` (Subtext: `26 raw → normalized aliases`).

##### 4. Main Body — Asymmetric Two-Column Architecture (`1.1fr` vs `1fr`)
- **Left Column (1.1fr)**: Detailed tree view of the 13-tier governed engineering asset hierarchy.
- **Right Column (1fr)**: Catalog reliability classification mix and blocking reconciliation items.

---

#### B. Detailed Breakdown of Each Panel

##### 1. Left Panel: `Engineering asset hierarchy` Panel
- **Subtitle**: `"Enterprise → Field → Pad → Well → Artificial Lift System → ESP Assembly → components"`
- **13-Level Indented Tree List**:
  - Each row shows: indentation branch symbol (`└`), entity level title (with deep-links where available), underlying database table entity (`esp_*`), and instance count.
  1. `Enterprise / Customer`: `CCED` | count `1`
  2. `Field`: `esp_fields` | count `1`
  3. `Pad / Area`: `esp_wells.pad_area` | count `1`
  4. `Well` (Link: `/engineering/installations/well`): `esp_wells` | count `170`
  5. `Artificial Lift System`: `lift_method = ESP` | count `170`
  6. `ESP Assembly` (Link: `/engineering/installations/assembly`): `esp_installed_systems` | count `170`
  7. `Pump Section(s)`: `esp_installed_pump_sections` | count `170`
  8. `Intake / Gas handler`: `esp_gas_handling_models` | count `32`
  9. `Protector`: `esp_protector_models` | count `8`
  10. `Motor`: `esp_motor_models` | count `5`
  11. `Gauge / Sensor`: `esp_sensor_models` | count `0`
  12. `Cable / MLE`: `esp_cable_models` | count `0`
  13. `VSD / Transformer / Panel`: `esp_vsd_models` | count `0`

##### 2. Right Top Panel: `Catalog reliability mix` Panel
- **Subtitle**: `"Pump models by evidence class — C1/D are discovery only, never calculation input"`
- **Grade Breakdown List**:
  - `A1` (`ReliabilityBadge` green): OEM Factory Curve Sheet (Exact serial match) | `13 models` (Calculation-grade)
  - `A2` (`ReliabilityBadge` green): OEM Catalog Curve (Standard model curve) | `20 models` (Calculation-grade)
  - `B1` (`ReliabilityBadge` blue): Operator Digitized Archive (Verified curve points) | `1 model` (Calculation-grade)
  - `B2` (`ReliabilityBadge` blue): Multi-Well Field Test Calibrated Curve | `22 models` (Calculation-grade)
  - `C1` (`ReliabilityBadge` amber): Catalog Nameplate Only (No digitized curve points) | `3 models` (Discovery / not usable)
  - `D` (`ReliabilityBadge` red): Inferred / Unverified Model Designation | `3 models` (Discovery / not usable)

##### 3. Right Bottom Panel: `Blocking reconciliation items` Panel
- **Subtitle**: `"Must be resolved before the Engineering Workbench can compute against these installations"`
- **Blocking Items List**:
  - Item 1: `Hydraulic model missing` (red pill) | `Hydraulic model missing — PM family` | `Resolve from completion tally, pump serial/part number or OEM records; do not infer P4/P6/P10.` | `4 inst.`
  - Item 2: `Hydraulic model missing` (red pill) | `Hydraulic model missing — Flex35D` | `Resolve from installation/BHA/OEM record.` | `1 inst.`
  - Footer Action Link: `"Open Data Quality & Reconciliation →"` (navigates to `/engineering/governance/quality`).

---

#### C. Right-Rail Overlays & Modals
- **No blocking modals**: Pure read-only master data dashboard summarizing asset hierarchy, database tables, and curve digitizer readiness.

---

#### D. "From Where to Go — To Where" (Complete Navigation Triggers Map)

| On-Screen Trigger / Button | Visual Location | Destination Target | Target Route / Action |
|---|---|---|---|
| **`Well` level link** | Asset hierarchy tree row 4 | Governed Wellbore & Well Trajectory Tab | `/engineering/installations/well` |
| **`ESP Assembly` level link** | Asset hierarchy tree row 6 | Governed Installed Assembly Component Stack | `/engineering/installations/assembly` |
| **`Open Data Quality & Reconciliation →`** | Blocking items panel footer | Data Quality & Reconciliation page | `/engineering/governance/quality` |
| **`Equipment Catalog`** | Sub-nav sidebar / ribbon | Equipment catalog index | `/engineering/catalog` |
| **`Installed ESP Systems`** | Sub-nav sidebar / ribbon | Installed fleet register | `/engineering/installations` |
| **`Well Definition (revisions)`** | Sub-nav sidebar / ribbon | Well governance revision logs | `/engineering/definition` |
| **`Engineering Workbench`** | Sub-nav sidebar / ribbon | Curve & scenario simulator | `/engineering/workbench` |
| **`Design Cases`** | Sub-nav sidebar / ribbon | Design vs actual cases | `/engineering/design-cases` |
| **`Validation & Readiness`** | Sub-nav sidebar / ribbon | Calculation grade validation matrix | `/engineering/governance/validation` |
| **`Source / Provenance Registry`** | Sub-nav sidebar / ribbon | Source documents & evidence registry | `/engineering/governance/sources` |
| **`Import / Catalog Administration`** | Sub-nav sidebar / ribbon | Pump curve digitizer & CSV import wizard | `/engineering/governance/import` |
| **`Workspace Switcher`** | Global top bar header | Operations surveillance workspace | `/` |


---

### P9: Engineering Workbench — `/engineering/workbench`
- **Page Title**: Engineering Workbench — Pump Curve Analysis
- **Route**: `/engineering/workbench`
- **File Path**: [`src/routes/engineering.workbench.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.workbench.tsx)
- **Layout Used**: L2 (`engineering.tsx`)

#### A. Rendered Components
1. **`SectionHeader`**: Title `"Engineering Workbench — Curve & Scenario Simulator"`.
2. **Controls Strip**:
   - System Dropdown: Select well assembly (e.g. `ESP-101 — REDA DN1750 120 stages`).
   - Frequency Slider: Drag slider `40.0 Hz` to `65.0 Hz` (Step `0.5 Hz`).
   - `CalculationGradeBadge`: Renders `A1 Verified` pill.
3. **Pump Performance Curve Plot (`CurvePlot`)**:
   - Recharts multi-axis chart plotting:
     - Head Curve ($H-Q$, ft vs bpd)
     - Power Curve ($P-Q$, HP vs bpd)
     - Efficiency Curve ($\eta-Q$, % vs bpd)
     - Overlays for Best Efficiency Point (BEP: 1,750 bpd @ 3,450 ft) and ROR (1,200 to 2,200 bpd).
4. **Governed Context Panel (`GovernedContextPanel`)**:
   - Static Lift: `4,200 ft`, Friction Loss: `180 ft`, Total Dynamic Head (TDH): `4,380 ft`.
   - Calculation Guard: If grade is `C1`/`D`, blocks simulation graphs and displays warning banner: `"Calculations Restricted: Missing digitized pump curve."`
5. **Frequency Scenario Comparison Table**:
   - Columns: `Frequency (Hz)`, `Rate (bpd)`, `TDH (ft)`, `Power (HP)`, `Efficiency (%)`, `Motor Load (%)`.
   - Rows: `45.0 Hz`, `50.0 Hz`, `55.0 Hz (Current)`, `60.0 Hz`.

#### B. Possible Navigation Views & Click Triggers
- **Drag Frequency Slider** -> Dynamically updates curves and affinity law calculations ($Q_2 = Q_1 \cdot \frac{f_2}{f_1}$, $H_2 = H_1 \cdot (\frac{f_2}{f_1})^2$).
- **Select Different Well Assembly** -> Loads new pump specifications and digitized curves.

---

### P10: Design Cases — `/engineering/design-cases`
- **Page Title**: ESP Design Cases vs Operating Points
- **Route**: `/engineering/design-cases`
- **File Path**: [`src/routes/engineering.design-cases.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.design-cases.tsx)
- **Layout Used**: L2 (`engineering.tsx`)

#### A. Rendered Components
1. **`SectionHeader`**: Title `"ESP Sizing Design Cases vs Current Performance"`.
2. **Design Case Comparison Table**:
   - Columns: `Well ID`, `Design Case Name`, `Design Rate (bpd)`, `Actual Rate (bpd)`, `Design Head (ft)`, `Actual Head (ft)`, `Match Status`.
   - Sample Row: `ESP-101` | `Initial Completion Sizing` | `1,800 bpd` | `1,740 bpd` | `3,600 ft` | `3,580 ft` | `Optimal Match (96.6%)`.

---

### P11: Equipment Catalog Index — `/engineering/catalog/`
- **Page Title**: Master Equipment Catalog
- **Route**: `/engineering/catalog/`
- **File Path**: [`src/routes/engineering.catalog.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.catalog.index.tsx)
- **Layout Used**: L3 (`engineering.catalog.tsx`)

#### A. Rendered Components
1. **Category Navigation Tabs**: `Pumps (42)`, `Motors (28)`, `Protectors (14)`, `Gas Separators (12)`, `Cables (18)`.
2. **Filter & Search Bar**: OEM Manufacturer selector (`All`, `Schlumberger`, `Baker Hughes`, `Borets`), Search box.
3. **Equipment Cards Grid**:
   - Card Example: **REDA DN1750** | `Schlumberger` | `BEP: 1,750 bpd` | `Head/Stage: 28.5 ft @ 60Hz` | `Digitized (21 Points)`.
   - Action Button: `[View Full Model Specs & Curve]`.

#### B. Possible Navigation Views & Click Triggers
- **Click Category Tabs (`Pumps`, `Motors`, `Protectors`)** -> Switches displayed equipment catalog grid.
- **Click `[View Full Model Specs]`** -> Navigates to `/engineering/catalog/pumps/DN1750`.

---

### P12: Pump Model Specification — `/engineering/catalog/pumps/$modelId`
- **Page Title**: OEM Pump Model Specification & Curve Data
- **Route**: `/engineering/catalog/pumps/$modelId` (Sample IDs: `DN1750`, `P100`, `J400`)
- **File Path**: [`src/routes/engineering.catalog.pumps.$modelId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.catalog.pumps.$modelId.tsx)
- **Layout Used**: L3 (`engineering.catalog.tsx`)

#### A. Rendered Components
1. **`SectionHeader`**: OEM pump title `"REDA DN1750 — Schlumberger 400 Series"`.
2. **`CurvePlot`**: Multi-axis digitized manufacturer performance curves.
3. **Mechanical Specs Table**: Outer Diameter (`4.00 in`), Shaft Diameter (`0.688 in`), Max Stages (`240`), Housing Material (`Monel / Ni-Resist`).

---

### P13: Installed Fleet List — `/engineering/installations/`
- **Page Title**: Installed ESP Systems & Assembly Fleet
- **Route**: `/engineering/installations/`
- **File Path**: [`src/routes/engineering.installations.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.installations.index.tsx)
- **Layout Used**: L4 (`engineering.installations.tsx`)

#### A. Rendered Components
1. **`SectionHeader`**: Title `"Installed ESP Systems & String Assemblies"`.
2. **Installation Assembly Data Table**:
   - Columns: `System ID`, `Well Name`, `Pump Model & Stages`, `Motor Rating`, `Setting Depth (ft)`, `Calculation Grade`, `Actions`.
   - Sample Row: `SYS-ESP-101` | `ESP-101` | `REDA DN1750 (120 stg)` | `Centrilift 150 HP` | `6,850 ft` | `A1 Verified` | `[Inspect Assembly]`.

#### B. Possible Navigation Views & Click Triggers
- **Click `[Inspect Assembly]`** -> Navigates to System Detail (`/engineering/installations/SYS-ESP-101`).

---

### P14–P18: Installation Detail Sub-Pages — `/engineering/installations/*`
- **Routes**:
  - `/engineering/installations/$systemId` (System Detail)
  - `/engineering/installations/assembly` (String Assembly Spec)
  - `/engineering/installations/fluid` (Fluid PVT Properties)
  - `/engineering/installations/limits` (Operating Limits)
  - `/engineering/installations/well` (Wellbore Trajectory)
- **File Paths**: `src/routes/engineering.installations.*.tsx`
- **Layout Used**: L4 (`engineering.installations.tsx`)
- **Rendered Components**:
  1. `SectionHeader` with tab links.
  2. Sub-assembly Cards & Spec Data Tables displaying gas oil ratio (GOR), fluid viscosity, deviation angle, and motor thermal limits.

---

### P19–P20: Well Definition Pages — `/engineering/definition/*`
- **Routes**: `/engineering/definition/`, `/engineering/definition/$wellId`
- **File Paths**: `src/routes/engineering.definition.index.tsx`, `src/routes/engineering.definition.$wellId.tsx`
- **Layout Used**: L2 (`engineering.tsx`)
- **Rendered Components**:
  1. **16-Section Provenance Accordion**: Equipment master data, sensor calibration, casing depth, tubing diameter, fluid PVT, and OT tag dictionary mappings.
  2. **Tag Mapping Table**: Canonical signal IDs (`ESP.PIP`, `ESP.PDP`, `ESP.FREQ`, `ESP.AMPS`, `ESP.TEMP`) mapped to OT tag paths.

---

### P21–P24: Governance Validation Pages — `/engineering/governance/*`
- **Routes**:
  - `/engineering/governance/` (Governance Overview)
  - `/engineering/governance/validation` (Validation Matrix)
  - `/engineering/governance/quality` (Data Quality Audit)
  - `/engineering/governance/sources` (Data Sources Audit)
- **File Paths**: `src/routes/engineering.governance.*.tsx`
- **Layout Used**: L5 (`engineering.governance.tsx`)
- **Rendered Components**:
  1. `ValidationMatrixTable`: Audit grid for all 25 wells listing calculation-grade scores (`A1` to `D`).
  2. `MissingTagAlert`: Warning banner showing unmapped tags and missing digitized curves.

---

### P25: Pump Curve Import Wizard — `/engineering/governance/import`
- **Page Title**: Digitized Pump Curve Import Wizard
- **Route**: `/engineering/governance/import`
- **File Path**: [`src/routes/engineering.governance.import.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/engineering.governance.import.tsx)
- **Layout Used**: L5 (`engineering.governance.tsx`)
- **Overlay Present**: `Import Wizard Modal`

#### A. Rendered Components
1. **4-Step Wizard Progress Bar**: `Step 1: Upload File` -> `Step 2: Column Mapping` -> `Step 3: Preview Curve` -> `Step 4: Save to Catalog`.
2. **File Dropzone (`DropZone`)**: File upload box accepting CSV or LAS digitized curve files.
3. **Preview Plot (`CurvePlot`)**: Live preview graph rendering uploaded data points before saving to catalog database.

---

### P26: Administration — `/administration`
- **Page Title**: Administration & Integration Settings
- **Route**: `/administration`
- **File Path**: [`src/routes/administration.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/administration.tsx)
- **Layout Used**: L1 (`AppShell`)

#### A. Rendered Components
1. **`SectionHeader`**: Title `"Administration & Integration Settings"`.
2. **Integration Endpoint Cards**:
   - Card 1: `OTConnex Service — https://otconnex.advait.internal/api/v2/telemetry (Status: Connected)`.
   - Card 2: `Asset ConneX Master Data — https://assetconnex.advait.internal/api/v1/hierarchy (Status: Synced)`.
3. **Global Alarm Threshold Form**:
   - Form Inputs: `Low PIP Limit (250 psi)`, `High Motor Temp Limit (210°F)`, `Overcurrent Trip Threshold (115%)`.
4. **Action Buttons**: `[Test OTConnex Connection]`, `[Save Threshold Settings]`.

---

## 4. Overlays (Modals & Drawers) Inventory

| Overlay Name | Type | Triggered From Page | File Source | Purpose in Simple Words |
| :--- | :--- | :--- | :--- | :--- |
| **`AdvisorPanel`** | Side Drawer | `/wells/$wellId` | `src/components/esp/AdvisorPanel.tsx` | Slide-over drawer displaying AI recommendations and 1-click execution actions. |
| **`Work Order Action Dialog`** | Modal Popup | `/exceptions` | `src/routes/exceptions.tsx` | Popup form for creating and assigning maintenance work orders. |
| **`Teardown Report Dialog`** | Modal Popup | `/reliability` | `src/routes/reliability.tsx` | Displays detailed photos and lab findings from failed pump teardowns. |
| **`Curve Import Wizard`** | Modal / Step-Wizard | `/engineering/governance/import` | `src/routes/engineering.governance.import.tsx` | 4-step wizard for uploading digitized pump curve data files. |

---

## 5. Duplicated & Repeated Components Analysis

1. **Raw Status Badges**:
   - `StatusPill` is central in [`src/components/esp/ui.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/ui.tsx#L18).
   - However, raw Tailwind status pills are manually re-created in [`FleetTable.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/FleetTable.tsx#L112) and [`exceptions.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/exceptions.tsx#L85) instead of reusing the central `StatusPill` component.
   - *Fix*: Standardize on `<StatusPill tone="...">`.

2. **Duplicate Stat Box Markup**:
   - `KpiCard` exists in [`src/components/esp/ui.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/ui.tsx#L45).
   - `reliability.tsx` and `reports.tsx` write custom `<div>` stat boxes instead of consuming `<KpiCard>`.

---

## 6. Dead Code & Legacy Infrastructure Wiring

1. **Legacy Redirect Routes**:
   - `src/routes/asset-definition.tsx` -> Redirects to `/engineering/definition`.
   - `src/routes/asset-definitions.tsx` -> Redirects to `/engineering/definition`.
   - `src/routes/design-cases.tsx` -> Redirects to `/engineering/design-cases`.
   - `src/routes/workbench.tsx` -> Redirects to `/engineering/workbench`.
2. **Unused Query Client Wiring**:
   - `QueryClient` is initialized in `src/router.tsx` and wrapped in `__root.tsx`, but no route calls `useQuery()`. Data is supplied by in-memory mock functions or TanStack Router loaders.
