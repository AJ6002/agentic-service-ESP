# Flat Content & Label Inventory — ADVAIT ESP-PMM

This document provides a flat inventory of all UI labels, table columns, KPI titles, button labels, and units of measurement.

---

## 1. Units of Measurement & Engineering Acronyms

- **Frequency**: `Hz` (Hertz — Operating frequency, typical range: 30 Hz – 65 Hz)
- **Current**: `A` (Amperes — Motor current load)
- **Voltage**: `V` (Volts — Bus voltage, e.g. 4,160 V)
- **Pressure**: `psi` (Pounds per Square Inch — PIP, Discharge Pressure, Wellhead Pressure)
- **Temperature**: `°F` (Degrees Fahrenheit — Motor Temp, Reservoir Temp)
- **Flow Rate**: `bpd` (Barrels per Day — Total liquid rate)
- **Oil Production**: `bopd` (Barrels of Oil per Day)
- **Vibration**: `in/s` (Inches per Second — Radial & Axial vibration)
- **Head**: `ft` (Feet — Total Dynamic Head, Pump Stage Head)
- **Run Life**: `days` (Accumulated operating days)
- **PIP**: Pump Intake Pressure
- **Pdp**: Pump Discharge Pressure
- **BEP**: Best Efficiency Point
- **ROR**: Recommended Operating Range
- **TDH**: Total Dynamic Head
- **VSD**: Variable Speed Drive

---

## 2. Global Navigation & Workspace Labels

- **Operations Workspace**: `Fleet Cockpit`, `Well Monitor`, `Exceptions`, `Troubleshooting`, `Reliability`, `Reports`
- **Configuration Workspace**: `Engineering Home`, `Equipment Catalog`, `Installed Fleet`, `Well Definition`, `Governance`, `Engineering Workbench`, `Design Cases`, `Administration`
- **Scope Options**: `All fields (3)`, `North Field`, `South Field`, `East Field`

---

## 3. Key Button & Action Labels

- `[View Monitor]` — Navigates to well monitor view (`/wells/$wellId`)
- `[Investigate Well]` — Opens exception investigation detail
- `[Acknowledge Alarm]` — Silences operational exception alert
- `[Create Work Order]` — Opens work order assignment dialog
- `[Apply Frequency Adjustment]` — Sends VSD speed change command
- `[Export CSV]` — Downloads tabular dataset in CSV format
- `[Print / Export PDF]` — Generates printable summary PDF
- `[Test OTConnex Connection]` — Tests telemetry API connectivity
- `[Launch Import Wizard]` — Opens pump curve LAS/CSV file uploader

---

## 4. Main Table Column Headers

### Fleet Table (`/` & `/wells`)
`Well Name`, `Field`, `Operating State`, `Frequency (Hz)`, `Current (A)`, `Intake Pressure (PIP, psi)`, `Discharge Pressure (psi)`, `Motor Temp (°F)`, `Run Life (days)`, `Health Index (%)`, `Actions`

### Exceptions Queue Table (`/exceptions`)
`Severity`, `Well Name`, `Anomaly Category`, `Trigger Parameter`, `Production Deferment (bpd)`, `Value Loss ($/day)`, `Detected Time`, `Recommended Action`, `Action`

### Equipment Catalog Table (`/engineering/catalog`)
`OEM Manufacturer`, `Series / Model`, `Component Type`, `BEP Flow (bpd)`, `Head / Stage (ft)`, `Max Outer Diameter (in)`, `Digitization Status`, `Actions`

### Installed String Assembly Table (`/engineering/installations`)
`System ID`, `Well Name`, `Pump Model & Stages`, `Motor Rating (HP/V)`, `Protector / Separator`, `Cable Specification`, `Setting Depth (ft)`, `Calculation Grade`, `Actions`
