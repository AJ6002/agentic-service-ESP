# OTConnex / ADVAIT ESP-PMM — Master Component List (Page-by-Page & View-by-View)

**Target System:** ADVAIT ESP-PMM (Lovable Operations Frontend Suite)  
**Source Document:** [`x:\TAS\ESP_APM_server\esp-insight-suite\audit\enumeration.md`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/audit/enumeration.md)  
**Document Name:** `OT-Connex-Component-list.md`  
**Classification:** Complete Hierarchical UI Component & Micro-Widget Directory  

---

## Table of Contents

1. [Layout Shell L1: Global Application Shell (`__root__`)](#1-layout-shell-l1-global-application-shell-__root__)
2. [Page P1: Fleet Cockpit (`/`)](#2-page-p1-fleet-cockpit-)
3. [Page P2: Well Directory (`/wells`)](#3-page-p2-well-directory-wells)
4. [Page P3: Well Monitor (`/wells/$wellId`)](#4-page-p3-well-monitor-wellswellid)
   - [P3.1 Top Bar & Header Controls](#p31-top-bar--header-controls)
   - [P3.2 Top Telemetry KPI Summary Strip (7 Cards)](#p32-top-telemetry-kpi-summary-strip-7-cards)
   - [P3.3 Tab 1: Overview View](#p33-tab-1-overview-view)
   - [P3.4 Tab 2: Trends View](#p34-tab-2-trends-view)
   - [P3.5 Tab 3: Operating point View](#p35-tab-3-operating-point-view)
   - [P3.6 Tab 4: Pressure profile View](#p36-tab-4-pressure-profile-view)
   - [P3.7 Tab 5: ESP string View](#p37-tab-5-esp-string-view)
   - [P3.8 Tab 6: Events & exceptions View](#p38-tab-6-events--exceptions-view)
   - [P3.9 Right-Rail Persistent Overlay: ESP Advisor Drawer](#p39-right-rail-persistent-overlay-esp-advisor-drawer)
5. [Page P4: Exceptions Queue (`/exceptions`)](#5-page-p4-exceptions-queue-exceptions)
   - [P4.1 Header Bar & View Filter Tabs](#p41-header-bar--view-filter-tabs)
   - [P4.2 Top Summary KPI Strip (7 Cards)](#p42-top-summary-kpi-strip-7-cards)
   - [P4.3 Left Panel: Prioritized Queue Table](#p43-left-panel-prioritized-queue-table)
   - [P4.4 Right Panel: Investigation & Action Dossier Desk](#p44-right-panel-investigation--action-dossier-desk)
6. [Page P5: Troubleshooting Assistant (`/troubleshooting`)](#6-page-p5-troubleshooting-assistant-troubleshooting)
   - [P5.1 Header Bar & Status Badges](#p51-header-bar--status-badges)
   - [P5.2 Left Panel: Signature Library Case Selector](#p52-left-panel-signature-library-case-selector)
   - [P5.3 Right Top Panel: 4-Section Case Diagnostic Card](#p53-right-top-panel-4-section-case-diagnostic-card)
   - [P5.4 Right Middle Panels: Implicated Subsystem Visualizer & 7-Day Trend Canvas](#p54-right-middle-panels-implicated-subsystem-visualizer--7-day-trend-canvas)
   - [P5.5 Right Bottom Panel: VSD Trip Code Reference Table](#p55-right-bottom-panel-vsd-trip-code-reference-table)
7. [Page P6: Reliability & Run Life (`/reliability`)](#7-page-p6-reliability--run-life-reliability)
   - [P6.1 Header Bar, Tab Switcher & Status Badges](#p61-header-bar-tab-switcher--status-badges)
   - [P6.2 Top Reliability KPI Summary Strip (7 Cards)](#p62-top-reliability-kpi-summary-strip-7-cards)
   - [P6.3 Tab 1: Run life View (Distribution, Field Durability, Pump Family, Influencing Factors)](#p63-tab-1-run-life-view)
   - [P6.4 Tab 2: Failure analysis View (Pareto & Failures by Component)](#p64-tab-2-failure-analysis-view)
   - [P6.5 Tab 3: Bad actors View (Mini Visual Cards & Bad Actor Ranking)](#p65-tab-3-bad-actors-view)
   - [P6.6 Tab 4: Interventions View (Planned Interventions Table)](#p66-tab-4-interventions-view)
   - [P6.7 Tab 5: DIFA records View (Teardown Inspection Logs Table)](#p67-tab-5-difa-records-view)
8. [Page P7: Management Scorecard & Reports (`/reports`)](#8-page-p7-management-scorecard--reports-reports)
   - [P7.1 Header Bar & Status Pills](#p71-header-bar--status-pills)
   - [P7.2 Top Executive KPI Strip (7 Cards)](#p72-top-executive-kpi-strip-7-cards)
   - [P7.3 Top Row: Field Scorecard Table & Deferment/Upside Grouped Bar Chart](#p73-top-row-field-scorecard-table--defermentupside-grouped-bar-chart)
   - [P7.4 Bottom Row: Focus This Week Table, Field Run Life Chart & Failure Pareto Table](#p74-bottom-row-focus-this-week-table-field-run-life-chart--failure-pareto-table)
9. [Cross-Reference: Governed Engineering Workspace (`/engineering/*`)](#9-cross-reference-governed-engineering-workspace-engineering)

---

# 1. Layout Shell L1: Global Application Shell (`__root__`)

- **Root Component File:** [`src/routes/__root.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/__root.tsx) -> [`src/components/esp/AppShell.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/components/esp/AppShell.tsx)
- **Visual Structure (Top to Bottom, Left to Right):**

### A. Top Global Header Bar
1. `LogoBadge` (Navy square with white `"AD"` monogram).
2. `ApplicationTitle` (`"ADVAIT ESP-PMM | ESP Performance Monitoring & Management"`).
3. `WorkspaceSelectorDropdown` (Dropdown to switch between `Operations` mode and `Configuration` mode).
4. `FieldScopeSelectorDropdown` (Dropdown filtering: `All fields (3)`, `Nardah North`, `Kalisto West`, `Tamrin Deep`).
5. `TelemetryLiveStatusPill` (`StatusPill` tone="info" displaying `"OTConnex live · 2 s scan"`).
6. `CriticalExceptionsBadge` (`StatusPill` tone="critical" displaying `"{N} critical open"`).
7. `UserProfileAvatar` (Circular badge with initials `"VK"` and role indicator `"Ops Engineer"`).

### B. Left Collapsible Navigation Rail
1. `SidebarRailToggle` (Button to switch between 56px collapsed icon rail and 196px expanded text rail).
2. `NavigationGroup: Operations`:
   - `NavButton: Fleet Cockpit` (Link to `/`).
   - `NavButton: Well Monitor` (Link to `/wells`).
   - `NavButton: Exceptions` (Link to `/exceptions`).
   - `NavButton: Troubleshooting` (Link to `/troubleshooting`).
   - `NavButton: Reliability` (Link to `/reliability`).
   - `NavButton: Reports` (Link to `/reports`).
3. `NavigationGroup: Engineering Master Data`:
   - `NavButton: Engineering Home` (Link to `/engineering`).
   - `NavButton: Equipment Catalog` (Link to `/engineering/catalog`).
   - `NavButton: Installed Fleet` (Link to `/engineering/installations`).
   - `NavButton: Well Definition` (Link to `/engineering/definition`).
   - `NavButton: Engineering Workbench` (Link to `/engineering/workbench`).
   - `NavButton: Design Cases` (Link to `/engineering/design-cases`).
   - `NavButton: Governance & Validation` (Link to `/engineering/governance/validation`).

---

# 2. Page P1: Fleet Cockpit (`/`)

- **Route:** `/`
- **Component File:** [`src/routes/index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/index.tsx)
- **Top-to-Bottom Component Sequence:**

1. `SectionHeader` (Title `"ESP Fleet Cockpit"`).
2. `FieldSummaryChipsBar` (4 Horizontal Status Badges):
   - `FieldChip 1`: `Nardah North — 9 wells — 6 off-normal`
   - `FieldChip 2`: `Kalisto West — 9 wells — 7 off-normal`
   - `FieldChip 3`: `Tamrin Deep — 7 wells — 4 off-normal`
   - `FieldChip 4`: `Inside recommended range 88%`
3. `TopKpiSummaryStrip` (7 `KpiCard` Widgets):
   - Card 1: `WELLS RUNNING` (`22 / 25` | `3 down`)
   - Card 2: `AVAILABILITY` (`88%` | `Run status weighted, 24 h`)
   - Card 3: `FLEET ESP HEALTH INDEX` (`65.7` | `Weighted envelope + thermal`)
   - Card 4: `OIL RATE` (`26,052 bopd` | `Allocated, latest scan`)
   - Card 5: `PRODUCTION DEFERMENT` (`4,676 bopd` | `Vs expected from active cases`)
   - Card 6: `OPTIMIZATION UPSIDE` (`190 bopd` | `Illustrative scenario estimates`)
   - Card 7: `VALUE AT STAKE` (`$330.9k /day` | `Deferment + upside`)
4. `MainDashboardSplitGrid` (2 Columns: Left 1.3fr, Right 1fr):
   - **Left Column:**
     - `NeedsAttentionNowPanel` (Table of anomalous wells):
       - Header: `"NEEDS ATTENTION NOW — Ranked by severity then production impact"`
       - Quick Link: `"Open full queue >"` (routes to `/exceptions`)
       - Table: 7 Columns (`SEV`, `WELL`, `CATEGORY`, `IMPACT BOPD`, `AGE`, `CONF.`, `OWNER`)
   - **Right Column:**
     - `OptimizationOpportunitiesPanel` (Table of upside candidate wells):
       - Header: `"OPTIMIZATION OPPORTUNITIES — Healthy wells with headroom"`
       - Table: 4 Columns (`WELL`, `BASIS`, `UPSIDE`, `CONF.`)
     - `OpenExceptionsByCategoryPanel` (Horizontal category bar chart):
       - Header: `"OPEN EXCEPTIONS BY CATEGORY — Where surveillance effort is concentrated"`
       - Category Bars: Gas interference, High motor temp, Pump wear, Gauge comms, VSD trip, Outside ROR, Unplanned stop, Optimization.

---

# 3. Page P2: Well Directory (`/wells`)

- **Route:** `/wells`
- **Component File:** [`src/routes/wells.index.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.index.tsx)
- **Top-to-Bottom Component Sequence:**

1. `SectionHeader` (Title `"Well Directory — Fleet Selection"`).
2. `WellSearchAndFilterBar` (Search text input + Field selector pills).
3. `FleetTable` (Full-width 14-column operational grid):
   - Table Columns:
     1. `Well Name` (Link to `/wells/$wellId`)
     2. `Field` (Field name string)
     3. `Operating State` (Coloured status badge)
     4. `Frequency Hz` (Monospace frequency)
     5. `Current A` (Monospace motor current)
     6. `Intake Pressure PIP` (Monospace psi)
     7. `Discharge Pressure PDP` (Monospace psi)
     8. `Motor Temp °F` (Monospace °F with alarm styling)
     9. `Liquid Flow bpd` (Monospace liquid rate)
     10. `Oil Rate bopd` (Monospace oil rate)
     11. `Run Life days` (Monospace days)
     12. `Envelope %` (Monospace compliance %)
     13. `Health Index` (0–100 score + progress bar)
     14. `Actions` (`[View Monitor]` primary link)

---

# 4. Page P3: Well Monitor (`/wells/$wellId`)

- **Route:** `/wells/$wellId` (Dynamic parameterized route)
- **Component File:** [`src/routes/wells.$wellId.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/wells.$wellId.tsx)
- **Top-to-Bottom Component Sequence:**

### P3.1 Top Bar & Header Controls
1. `PageHeader`:
   - Title: `${well.id} — ${field} · ${well.padName}`
   - Description: Headline diagnostic status string
   - Status Pills: `Operating State`, `Field & Pad`, `Pump Model & Stages`, `Data Quality Badge`, `Last Event Pill`.
   - Top-Right Action Buttons:
     - `← {prevId}` (Button to jump to previous well)
     - `{nextId} →` (Button to jump to next well)
     - `Open in Engineering Workbench` (Primary button routing to `/engineering/workbench?well={wellId}`)
     - `Governed asset definition` (Button routing to `/engineering/installations`)

### P3.2 Top Telemetry KPI Summary Strip (7 Cards)
1. `ESP HEALTH INDEX` (Score + Band tone: normal/warning/critical)
2. `FREQUENCY` (Live Hz vs Design Hz)
3. `MOTOR LOAD` (Load % and live Amps vs rated Amps)
4. `MOTOR TEMPERATURE` (Live °F vs limit °F)
5. `PIP / PDP` (Intake and discharge psi vs design)
6. `LIQUID / OIL` (bpd vs design liquid)
7. `DEFERMENT` (bopd and daily financial loss)

### P3.3 Tab Navigation Bar (6 Tabs)
- `Tab 1: Overview`
- `Tab 2: Trends`
- `Tab 3: Operating point`
- `Tab 4: Pressure profile`
- `Tab 5: ESP string`
- `Tab 6: Events & exceptions`

---

### P3.4 Tab 1: Overview View
1. `EspSystemVisualizationPanel` (Left Column):
   - Subtitle: `"Live simulated values bound to the string..."`
   - `EspWellVisual` (Full vertical interactive SVG schematic):
     - Surface choke & flowline valve indicators
     - Production casing & production tubing
     - Pump discharge pressure tap
     - Multistage centrifugal pump stages
     - Gas handler / intake section with PIP tap
     - Protector / seal section
     - Submersible electric motor with temperature & current callout
     - Downhole gauge sensor package
   - Bottom State Pill & Disclaimer Hint.
2. `OperatingStateTimelinePanel` (Middle Column):
   - Subtitle: `"Last 24 hours — how the well arrived at its current state"`
   - 24-Hour Coloured Segmented Bar (`-24h` $\to$ `-12h` $\to$ `now`).
   - Chronological State Table (State episodes, time ranges, and durations).
3. `WhatChangedPanel` (Lower Grid):
   - Table: 4 Columns (`Signal`, `From`, `To`, `Window`).
4. `OperatingEnvelopePanel` (Lower Grid):
   - Graphical Envelope Bar (ROR min, ROR max, BEP line, Operating rate marker).
   - Metrics: `ROR min`, `ROR max`, `BEP`, `Q/Q_BEP`.
   - Diagnostic Margin Narrative Note.
5. `OperatingPointVsPumpCurvePanel` (Lower Grid):
   - `MiniOperatingPoint` (Compact H-Q pump curve at active frequency).
6. `TotalDynamicHeadPanel` (Lower Grid):
   - Calculation Breakdown Table (Vertical lift, Friction, Backpressure, TDH, Design TDH, Head/stage actual, Head/stage design).

---

### P3.5 Tab 2: Trends View
1. `MultiTagTrendPanel`:
   - Time Window Selector Buttons (`24h`, `7d`, `30d`, `60d`).
   - Signal Tag Toggle Buttons (`Amps`, `Hz`, `PIP`, `PDP`, `Motor temp`, `Liquid`, `Oil`, `Load`, `WHP`, `Vibration`).
   - Primary `TrendChart` Canvas (300px dual Y-axes chart with event lines).
   - Secondary Side-by-Side Comparison Charts:
     - Sub-chart A: PIP vs PDP Hydraulic Trend.
     - Sub-chart B: Motor Temp vs Load Thermal Trend.

---

### P3.6 Tab 3: Operating point View
1. `OperatingPointDetailPanel`:
   - Large H-Q Performance Curve Canvas (`MiniOperatingPoint`, height 280px).
   - Actual vs. Design Comparison Table (7 Parameters: `Frequency`, `Liquid rate`, `Oil rate`, `PIP`, `PDP`, `Current`, `TDH` with variance percentages).

---

### P3.7 Tab 4: Pressure profile View
1. `PressureProfilePanel`:
   - Vertical Pressure Traverse Canvas (`PressureProfile`):
     - X-axis: Pressure (0 to 3,000+ psi).
     - Y-axis: Depth (0 to total depth in ft TVD).
     - Gradient line connecting Reservoir $\to$ Pwf $\to$ PIP $\to$ Pump Boost $\to$ PDP $\to$ Surface WHP.

---

### P3.8 Tab 5: ESP string View
1. `EspStringVisualizationPanel` (Left Column, 300px schematic).
2. `ComponentRegistryPanel` (Right Column):
   - Table: 7 Columns (`Group`, `Component`, `Make / model`, `Specification`, `Tags`, `Source`, `Status`).
   - Governed Rows: Tubing, Check valve, Bleeder valve, Multistage pump, Gas handler, Seal/protector, Motor, Gauge, Cable/MLE.

---

### P3.9 Tab 6: Events & exceptions View
1. `OpenExceptionsForThisWellPanel`:
   - Active Exception Cards (Severity pill, Category, ID, Age, Confidence).
   - `Observation` Text Box.
   - `Evidence` Bullet List.
   - `Verify` Step-by-Step Checklist.
   - `Recommended Action` Mitigation Box.
   - Empty State `<Note>` when no exceptions exist.

---

### P3.10 Right-Rail Persistent Overlay: ESP Advisor Drawer
1. `AdvisorPanel` (330px Collapsible Slide-Out Rail):
   - Header: `"ESP Advisor — preview"` + Collapse/Expand Toggle Button.
   - Subtitle: `"Decision support only. No control actions are issued from this module."`
   - Active Advisory Cards:
     - Header: Advisory Kind pill (`Predictive`, `Optimization`, `Info`) + Confidence score.
     - `Observation` Box.
     - `Engineering Context` Box.
     - `Assessment` Box.
     - `Recommended Checks / Actions` Bulleted List.
     - `Evidence References` Chips.
2. `AdvisorItemsCompactPanel` (Summary badge stream below drawer).

---

# 5. Page P4: Exceptions Queue (`/exceptions`)

- **Route:** `/exceptions`
- **Component File:** [`src/routes/exceptions.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/exceptions.tsx)
- **Top-to-Bottom Component Sequence:**

### P4.1 Header Bar & View Filter Tabs
1. `PageHeader` (Title `"Exception & Opportunity Queue"`, governance description, metadata pills).
2. `ToggleRow` (6 Filter Tabs): `All`, `Critical`, `Warning`, `Watch`, `Opportunities`, `Unassigned`.

### P4.2 Top Summary KPI Strip (7 Cards)
1. `CRITICAL` (Count, critical red tone)
2. `WARNING` (Count, warning orange tone)
3. `WATCH` (Count, watch amber tone)
4. `OPPORTUNITIES` (Count, opportunity green tone)
5. `IMPACT AT RISK` (Total bopd volume at risk)
6. `UPSIDE IDENTIFIED` (Total potential bopd uplift)
7. `VALUE AT STAKE` (Total financial exposure in $/day)

### P4.3 Main Triage Split Workspace (50% / 50%)
- **Left Panel (`Queue — {N} items`):**
  - High-density scrollable table with 6 columns:
    1. `Sev` (Colored status tone pill)
    2. `Well` (Clickable well ID link)
    3. `Category` (Anomaly title string)
    4. `Impact` (Production volume in bopd)
    5. `Age` (Time elapsed since trigger)
    6. `Status` (Open / Acknowledged / Assigned / Closed)
- **Right Panel (`Investigation & Action Dossier Desk`):**
  - Header: Exception Title + Well ID + Field Name + Timestamp.
  - Triage Action Buttons: `[Acknowledged]`, `[Assigned]`, `[Closed]`.
  - Meta Deep Links: `Open Well Monitor →`, `Analyse in Workbench →`.
  - `RULE` Algorithm Card.
  - `OBSERVATION` Operational Narrative Card.
  - `EVIDENCE` Telemetry Bullet List (Left Sub-column).
  - `LIKELY CAUSES (RANKED)` Probability Table with Progress Bars (Right Sub-column).
  - `VERIFICATION STEPS` Field Checklist.
  - `RECOMMENDED ACTION` Operational Instructions.
  - `PRODUCTION IMPACT NOTE` Financial Alert Box.
  - `AUDIT WORKFLOW NOTE` Compliance Banner.

---

# 6. Page P5: Troubleshooting Assistant (`/troubleshooting`)

- **Route:** `/troubleshooting`
- **Component File:** [`src/routes/troubleshooting.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/troubleshooting.tsx)
- **Top-to-Bottom Component Sequence:**

### P5.1 Header Bar & Status Badges
1. `PageHeader` (Title `"Troubleshooting Assistant"`, description, direction-of-change badges).

### P5.2 Main Diagnostic Split Layout (260px / Flex 1)
- **Left Panel (`Signature library`):**
  - Scrollable list of pre-built failure signature cases (`troubleshootingCases`):
    - Case ID (`TS-01` to `TS-12`)
    - Associated Well ID link
    - Descriptive Fault Pattern Title
    - VSD Trip Code Badge (`F42`, `F12`, `F01`, etc.)
- **Right Column (Active Diagnostic Dossier & Supporting Evidence):**
  - **Top Panel (`Active Case Diagnostic Card`):**
    - Subtitle: Primary observed symptom + `"Open {well.id} →"` link.
    - 2x2 Diagnostic Grid:
      1. `DIAGNOSTIC SIGNATURE` Table (Columns: `Signal`, `Direction` with glyphs `▲`, `▼`, `▬`, `∿`, `Expected behaviour`).
      2. `RANKED CAUSES` Cards (Probable causes, confidence %, progress bars, physical explanations).
      3. `VERIFICATION SEQUENCE` (Numbered field confirmation steps).
      4. `RECOMMENDED ACTIONS` (Operational corrective mitigation steps + decision support note).
  - **Middle Left Panel (`Implicated subsystem — {well.id}`):**
    - `EspWellVisual` with the failing component dynamically highlighted in glowing outline (`intake`, `motor`, `cable`, `pump`, etc.).
  - **Middle Right Panel (`Supporting evidence — {well.id}`):**
    - Dual 7-Day Trend Charts: Chart 1 (Frequency & Oil rate) + Chart 2 (PIP & PDP hydraulic divergence).
  - **Bottom Panel (`VSD trip code reference`):**
    - Full-width reference table (Columns: `Code`, `Fault`, `Typical cause`, `First response` for `F01`, `F02`, `F12`, `F18`, `F23`, `F42`, `F51`).

---

# 7. Page P6: Reliability & Run Life (`/reliability`)

- **Route:** `/reliability`
- **Component File:** [`src/routes/reliability.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/reliability.tsx)
- **Top-to-Bottom Component Sequence:**

### P6.1 Header Bar, Tab Switcher & Status Badges
1. `PageHeader` (Title `"Reliability & Run Life"`, description, metadata pills).
2. `ToggleRow` (5 Tabs): `Run life`, `Failure analysis`, `Bad actors`, `Interventions`, `DIFA records`.

### P6.2 Top Reliability KPI Summary Strip (7 Cards)
1. `MEAN RUN LIFE` (`842 days`)
2. `REPEAT FAILURE RATE` (`29%` | warning tone)
3. `RECORDED PULLS` (`34 pulls`)
4. `INTERVENTION SPEND` (`$4.1M`)
5. `DEFERRED VOLUME` (`186,000 bbl` | warning tone)
6. `HIGH-RISK WELLS` (`4 wells` | critical tone)
7. `PLANNED INTERVENTIONS` (`7 queued`)

---

### P6.3 Tab 1: Run life View
1. `RunLifeDistributionByFieldPanel` (`SimpleBar` 6-bucket chart: `0–180d` to `900–1200d` grouped by field).
2. `RunLifeByFieldTablePanel` (Table: `Field`, `Pulls`, `Mean d`, `Median d`, `Shortest d`, `Repeat %`).
3. `MeanRunLifeByPumpFamilyPanel` (Horizontal bar chart plotting durability by OEM pump series).
4. `RunLifeInfluencingFactorsPanel` (Weighted model table: 10 Factors, Weights %, Why it matters).

---

### P6.4 Tab 2: Failure analysis View
1. `FailureModeParetoPanel` (`ParetoChart` dual-axis chart: Pull counts by failure mode + Cumulative % curve).
2. `FailuresByComponentPanel` (Horizontal bar chart: `Pump`, `Motor`, `Cable / MLE`, `Seal section`, `Gas separator`, `Downhole gauge`).

---

### P6.5 Tab 3: Bad actors View
1. `AssetContextPanel` (Horizontal strip of 8 mini well cards with `EspWellMini` visual, Well ID, and Risk Score badge).
2. `BadActorRankingTablePanel` (11-Column Table: `Well`, `Field`, `Risk score`, `Health`, `Run life d`, `Prior run d`, `Pulls`, `Repeat`, `Dominant factor`, `Indicative RUL d`, `Defer bopd`).
3. `MachineLearningRulDisclaimerNote` (`<Note>` stating RUL criteria).

---

### P6.6 Tab 4: Interventions View
1. `InterventionPlanTablePanel` (Table: 9 Columns: `ID`, `Well`, `Type`, `Priority`, `Window`, `Reason`, `Impact bopd`, `Risk`, `Status`).

---

### P6.7 Tab 5: DIFA records View
1. `PullAndDifaHistoryTablePanel` (Table: 9 Columns: `Record`, `Well`, `Pulled`, `Run life d`, `Component`, `Failure mode`, `Root-cause factor`, `DIFA summary`, `Cost kUSD` covering all 34 historical teardown records).

---

# 8. Page P7: Management Scorecard & Reports (`/reports`)

- **Route:** `/reports`
- **Component File:** [`src/routes/reports.tsx`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/src/routes/reports.tsx)
- **Top-to-Bottom Component Sequence:**

### P7.1 Header Bar & Status Pills
1. `PageHeader` (Title `"Management Scorecard & Reports"`, description, reporting period pill, demo price deck pill).

### P7.2 Top Executive KPI Strip (7 Cards)
1. `FLEET AVAILABILITY` (`88%`)
2. `FLEET HEALTH INDEX` (`65.7`)
3. `ENVELOPE COMPLIANCE` (`76%` | warning tone)
4. `DEFERMENT` (`4,676 bopd` | `$317,968/day`)
5. `IDENTIFIED UPSIDE` (`190 bopd` | `$12,920/day`)
6. `REPEAT / AVOIDABLE PULLS` (`10` of 34 | critical tone)
7. `RIG WORK QUEUED` (`5 candidates`)

### P7.3 Main Multi-Column Grid
- **Top Row (Two-Column Asymmetric Grid):**
  1. `FieldScorecardTablePanel` (9 Columns: `Field`, `Wells`, `Avail %`, `Health`, `Oil bopd`, `Defer bopd`, `Upside bopd`, `Envelope %`, `Open exc.`).
  2. `DefermentAndUpsideByFieldChartPanel` (Grouped bar chart comparing lost bopd vs upside bopd per field).
- **Bottom Row (Three-Column Balanced Grid):**
  1. `WhereToFocusThisWeekTablePanel` (Top 8 bad-actor wells with Risk, Defer bopd, Dominant factor).
  2. `RunLifeByFieldChartPanel` (Grouped bar chart: Mean days vs Median days per field).
  3. `TopFailureModesTablePanel` (Pareto table of top failure mechanisms with cumulative %) + Scheduled reporting PDF export note.

---

# 9. Cross-Reference: Governed Engineering Workspace (`/engineering/*`)

The governed master data catalog and simulation tools are documented in the companion specification [`Enumeration-Engineering_Configuration.md`](file:///x:/TAS/ESP_APM_server/esp-insight-suite/Enumeration-Engineering_Configuration.md):

- **P1: Engineering Home / Asset Definition Overview** (`/engineering`)
- **P2: Master Equipment Catalog** (`/engineering/catalog/`)
- **P3: OEM Pump Specification & Curve Viewer** (`/engineering/catalog/pumps/$modelId`)
- **P4: Installed ESP Systems Fleet** (`/engineering/installations/`)
- **P5: Installed System Detail View** (`/engineering/installations/$systemId`)
- **P6: String Assembly Specification** (`/engineering/installations/assembly`)
- **P7: Wellbore & Completion Definition** (`/engineering/installations/well`)
- **P8: Fluid PVT Properties** (`/engineering/installations/fluid`)
- **P9: Operating & Design Limits** (`/engineering/installations/limits`)
- **P10: Well Definition Revisions** (`/engineering/definition/`)
- **P11: Single Well Provenance Dossier** (`/engineering/definition/$wellId`)
- **P12: Engineering Workbench (Curve & Frequency Simulator)** (`/engineering/workbench`)
- **P13: Design Cases vs. Operating Points** (`/engineering/design-cases`)
- **P14: Engineering Validation & Readiness Matrix** (`/engineering/governance/validation`)
- **P15: Source & Provenance Registry** (`/engineering/governance/sources`)
- **P16: Data Quality & Reconciliation Queue** (`/engineering/governance/quality`)
- **P17: Import & Catalog Administration Pipeline** (`/engineering/governance/import`)
