# Interaction States Inventory — ADVAIT ESP-PMM

This document details all interactive, conditional, and responsive UI states available in the application.

---

## 1. Global Shell States

- **Workspace Navigation State**:
  - `Operations Workspace`: Displays field scope filter dropdown (`All fields (3)`), operational navigation routes (`/`, `/wells`, `/exceptions`, `/troubleshooting`, `/reliability`, `/reports`).
  - `Configuration Workspace`: Displays `Editor / Configurator role` pill, master data navigation routes (`/engineering`, `/engineering/catalog`, `/engineering/installations`, `/engineering/workbench`, `/administration`).
- **Sidebar Collapse State**:
  - `Collapsed (56px)`: Displays icons with hover tooltips (`role="tooltip"`).
  - `Expanded (196px)`: Displays full labels, category headers, and hint text.

---

## 2. Operating State Conditionals (`src/data/esp/fleet.ts`)

| State Name | Status Pill Tone | Visual Indicator | Advisor Action Triggered |
| :--- | :--- | :--- | :--- |
| **Normal Running** | Green (`normal`) | Green flow animation | None (Optimal operation) |
| **Gas Interference** | Yellow (`warning`) | Bubbles at pump intake in `EspWellVisual` | Adjust choke / lower VSD frequency |
| **Pump Wear** | Yellow (`warning`) | Head curve degradation indicator | Schedule replacement / monitor slip |
| **Motor Overload** | Red (`critical`) | Red motor temperature glow | Reduce current / frequency immediately |
| **High Motor Temp** | Red (`critical`) | Temperature gauge > 200°F | Inspect cooling shroud / fluid rate |
| **VSD Trip** | Red (`critical`) | `0 Hz` / `0 A` status banner | Execute VSD trip code diagnostic flow |
| **Comm Loss** | Gray (`info`) | Dotted trend lines | Check downhole gauge surface card |

---

## 3. Engineering Calculation-Grade Gating (`GovernedContextPanel.tsx` & `governance.tsx`)

| Calculation Grade | Status | Engineering Workbench Behavior |
| :--- | :--- | :--- |
| **A1 — Calculation Grade** | Green | Full simulation allowed; $H-Q$, $P-Q$, $\eta-Q$ curves active; frequency scenario slider enabled. |
| **A2 — Minor Gaps** | Green | Full simulation allowed with minor uncertainty warnings. |
| **B1 / B2 — Moderate Grade** | Blue | Simulation enabled; fallback PVT properties noted. |
| **C1 — Unresolved Assembly** | Amber / Red | **Blocked**: Workbench displays warning banner. Simulation curves disabled. |
| **D — Zero Digitized Curves** | Red | **Blocked**: Digitization missing. Prompts user to open `Import Wizard`. |
