# 📡 ESP Live MQTT Telemetry, VFM & Event Stream Specification

> **Source Broker**: `192.168.1.155:1883` (Server 1 — Eclipse Mosquitto)  
> **Active Fleet**: 13 Farha South Production Wells (`FNW-01`, `FNW-06`, `FWS-06`, `FWS-04`, `FWS-02`, `ULFA-5`, `FS-129`, `FS-121`, `FS-96`, `FS-17`, `FS-21`, `FS-06`, `FS-91`)  
> **Broadcast Cadence**: 1.00s per well  
> **Capture Timestamp**: September 2026  

---

## 1. Topic Hierarchy Overview

The live Mosquitto broker publishes five distinct topic streams across the fleet:

```text
esp/v1/
├── simulator/status                     <- Heartbeat & Liveness State (Retained)
├── {well_id}/telemetry                  <- 14-Channel SCADA VFD Sensor Telemetry (1 Hz)
├── {well_id}/vfm                        <- Virtual Flow Metering & Derived Physics (1 Hz)
├── {well_id}/asset                      <- Nameplate Equipment, Geometry & H-Q Curve Coefficients (Retained)
└── {well_id}/events                     <- State Changes, Alarms, Trips & Scenario Transitions (On-Change)
```

---

## 2. Topic: `esp/v1/{well_id}/events` (State, Alarms & Faults)

### 2.1 Broadcast Trigger Mechanism
* Emitted **on-change** whenever any of the following transitions occur:
  1. `operating_state` changes (`stopped` -> `starting` -> `running` -> `tripped`).
  2. `scenario` changes (e.g. `normal` -> `dry_well_pump_off`).
  3. `trip_cause` is set or cleared.
  4. Active `alarms` array changes (alarms appear or resolve).

### 2.2 Verbatim Event Payloads (Un-truncated)

#### Sample A: Active High Motor Overload Alarm
```json
{
  "schema_version": "1.0.0",
  "message_type": "esp_event",
  "timestamp": "2026-09-13T10:37:40.123456Z",
  "well_id": "FS-17",
  "operating_state": "running",
  "scenario": "motor_overload",
  "trip_cause": null,
  "alarms": [
    "OVERLOAD"
  ]
}
```

#### Sample B: Terminal Trip on Underload Pump-Off
```json
{
  "schema_version": "1.0.0",
  "message_type": "esp_event",
  "timestamp": "2026-09-13T10:39:15.890123Z",
  "well_id": "FNW-01",
  "operating_state": "tripped",
  "scenario": "dry_well_pump_off",
  "trip_cause": "UNDERLOAD_PUMP_OFF",
  "alarms": [
    "LOW_INTAKE_PRESSURE",
    "UNDERLOAD",
    "TRIP_UNDERLOAD_PUMP_OFF"
  ]
}
```

#### Sample C: Normal Operational Reset
```json
{
  "schema_version": "1.0.0",
  "message_type": "esp_event",
  "timestamp": "2026-09-13T10:40:02.456789Z",
  "well_id": "FNW-01",
  "operating_state": "running",
  "scenario": "normal",
  "trip_cause": null,
  "alarms": []
}
```

### 2.3 Event Data Dictionary

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema_version` | String | Semantic contract version (`1.0.0`). |
| `message_type` | String | Discriminator tag: `esp_event`. |
| `timestamp` | String (ISO 8601) | Microsecond UTC timestamp of state transition. |
| `well_id` | String | Canonical well ID (`FNW-01`, `FS-17`). |
| `operating_state` | String | Discrete state: `running`, `starting`, `stopped`, `tripped`. |
| `scenario` | String | Active failure scenario (`normal` if healthy). |
| `trip_cause` | String / Null | Canonical failure reason causing physical shutdown. `null` if operating normally. |
| `alarms` | Array[String] | Active alarm flags currently violated. |

### 2.4 Complete Alarms Catalog

| Alarm Tag | Trigger Condition in Physics Engine | Physical Meaning |
| :--- | :--- | :--- |
| `LOW_INTAKE_PRESSURE` | `STD_INT_PRS_PSI` < 150.0 PSI | Pump intake pressure depleted; risk of gas flashing or dry run. |
| `UNDERLOAD` | Motor load < 55.0% while running | Current draw dropped; fluid flow lost or broken shaft. |
| `OVERLOAD` | Motor load > 115.0% | Current draw exceeds motor thermal capacity; rotor lock or heavy solids. |
| `HIGH_MOTOR_TEMPERATURE` | `STD_MOTOR_TEMP_C` > 135.0 °C | Winding temperature exceeds API RP 11S trip ceiling. |
| `HIGH_VIBRATION` | `STD_VIBRATION_G` > 2.0 g RMS | Severe mechanical vibration; damaged bearing or severe slugging. |
| `VOLTAGE_IMBALANCE` | Voltage imbalance > 5.0% | VFD phase imbalance; causes motor winding overheating. |
| `HIGH_GAS_FRACTION` | Gas volume fraction > 35.0% | High free gas in pump; leads to gas locking. |
| `OUTSIDE_RECOMMENDED_OPERATING_RANGE` | $Q < Q_{\min}(f)$ or $Q > Q_{\max}(f)$ | Flow rate operates outside pump hydraulic stability corridor (upthrust/downthrust). |
| `MOTOR_POWER_CAPACITY` | Pump shaft kW > $1.15 \times \text{Motor HP} \times 0.7457$ | Mechanical power required exceeds motor shaft rating. |
| `VSD_CAPACITY` | Apparent power kVA > $1.05 \times \text{VSD kVA}$ | Electrical draw exceeds surface drive rating. |
| `TRANSFORMER_CAPACITY` | Apparent power kVA > $1.05 \times \text{Transformer kVA}$ | Electrical draw exceeds step-up transformer capacity. |
| `TRIP_{cause}` | Operating state switches to `tripped` | Tag indicating hardware shutdown cause. |

### 2.5 Complete Trip Causes Catalog

| Trip Cause Tag | Trigger Scenario | Failure Mechanics |
| :--- | :--- | :--- |
| `UNDERLOAD_PUMP_OFF` | `dry_well_pump_off` | Reservoir inflow stops -> PIP drops -> fluid lost -> motor underload trip. |
| `GAS_LOCK_UNDERLOAD` | `gas_interference_to_lock` | Free gas fills impellers -> head lost -> flow drops to 0 -> underload trip. |
| `BROKEN_SHAFT_UNDERLOAD` | `broken_shaft` | Mechanical drive shaft shears -> impellers stop spinning -> motor unloads. |
| `MOTOR_OVERLOAD` | `motor_overload`, `high_viscosity_cold_start` | High mechanical drag or electrical stall -> current exceeds overcurrent trip limit. |
| `OVERLOAD_SOLIDS` | `sand_ingestion`, `scale_or_pump_wear` | Sand or scale deposits pack pump stages -> mechanical friction surge. |
| `HIGH_VIBRATION` | `bearing_degradation` | Bearing failure -> rotor eccentricity -> vibration exceeds safety shutdown threshold. |
| `UNDER_VOLTAGE` | `undervoltage` | Grid brownout / bus voltage drop below permissible inverter threshold. |
| `PHASE_IMBALANCE` | `phase_imbalance` | Phase angle / voltage delta exceeds safety relay limit. |
| `POWER_LOSS` | `power_loss` | Sudden power feed disconnection. |
| `HIGH_MOTOR_TEMPERATURE` | Internal thermal runaway | Insufficient motor fluid cooling velocity past motor housing (< 1.0 ft/s). |

---

## 3. Topic: `esp/v1/{well_id}/telemetry` (14 SCADA Channels)

### 3.1 Verbatim Raw JSON Payload
```json
{
  "schema_version": "1.0.0",
  "message_type": "esp_telemetry",
  "timestamp": "2026-09-13T10:37:40.270090Z",
  "well_id": "FNW-01",
  "manufacturer": "Borets / Levare",
  "model_id": "B400-400",
  "measurements": {
    "STD_INT_PRS_PSI": 395.4,
    "STD_DISCH_PRS_PSI": 1883.1,
    "STD_INT_TEMP_C": 64.53,
    "STD_MOTOR_TEMP_C": 87.71,
    "STD_VIBRATION_G": 0.082,
    "STD_VOLT_V": 594.1,
    "STD_AMP_A": 35.7,
    "STD_FREQ_HZ": 53.1,
    "STD_LEAK_CURRENT_CT": 15.0,
    "STD_DHG_CURRENT_MA": 10.7,
    "STD_WHP_PSI": 180.3,
    "STD_FLP_PSI": 171.0,
    "STD_AP_PSI": 155.5,
    "STD_VFD_STS": true
  }
}
```

### 3.2 Telemetry Data Dictionary

| Field | Type | Unit | Engineering Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | String | — | Semantic contract version (`1.0.0`). |
| `message_type` | String | — | Payload tag (`esp_telemetry`). |
| `timestamp` | String (ISO 8601) | UTC | Microsecond packet creation timestamp. |
| `well_id` | String | — | Primary identifier key (`FNW-01`, `FS-17`). |
| `measurements.STD_INT_PRS_PSI` | Float | PSI | Pump Intake Pressure (PIP). Liquid entry pressure. |
| `measurements.STD_DISCH_PRS_PSI` | Float | PSI | Pump Discharge Pressure (PDP). Exit pressure into tubing. |
| `measurements.STD_INT_TEMP_C` | Float | °C | Intake Fluid Temperature. Reservoir fluid temperature. |
| `measurements.STD_MOTOR_TEMP_C` | Float | °C | Motor Winding Temperature. Alarm at 115°C, trip at 135°C. |
| `measurements.STD_VIBRATION_G` | Float | g (RMS) | Radial mechanical vibration severity per ISO 10816. |
| `measurements.STD_VOLT_V` | Float | V (RMS) | VFD average 3-phase output voltage. |
| `measurements.STD_AMP_A` | Float | A (RMS) | Motor current draw. Primary load indicator. |
| `measurements.STD_FREQ_HZ` | Float | Hz | Operating drive speed frequency (35.0–65.0 Hz). |
| `measurements.STD_LEAK_CURRENT_CT` | Float | mA | Downhole cable insulation leakage current. |
| `measurements.STD_DHG_CURRENT_MA` | Float | mA | Downhole gauge instrumentation telemetry loop current. |
| `measurements.STD_WHP_PSI` | Float | PSI | Wellhead surface pressure upstream of choke. |
| `measurements.STD_FLP_PSI` | Float | PSI | Flowline surface pressure downstream of choke. |
| `measurements.STD_AP_PSI` | Float | PSI | Casing-tubing annulus gas blanket pressure. |
| `measurements.STD_VFD_STS` | Boolean | — | `true` = Energized / Running; `false` = Stopped / Tripped. |

---

## 4. Topic: `esp/v1/{well_id}/vfm` (Virtual Flow Metering)

### 4.1 Verbatim Raw JSON Payload
```json
{
  "schema_version": "1.0.0",
  "message_type": "esp_vfm",
  "timestamp": "2026-09-13T10:37:40.274900Z",
  "well_id": "FNW-01",
  "grad_mix_psi_ft": 0.3535,
  "sg_mix": 0.816,
  "water_cut_pct": 0.0,
  "oil_pct": 100.0,
  "head_per_stage_ft": 12.24,
  "head_normalized_ft": 10.94,
  "liquid_flow_rate_bpd": 399.1,
  "net_oil_rate_bpd": 399.1,
  "net_water_rate_bpd": 0.0,
  "gas_rate_mscfd": 119.7,
  "hydraulic_power_bhp": 25.46,
  "electrical_power_bhp": 35.98,
  "energy_balance_variance_pct": 29.23,
  "energy_balanced": false,
  "balance_status": "DIVERGENT",
  "derived_parameters": {
    "DRV_DIFF_PRS_PSI": 1480.1,
    "DRV_TOTAL_HEAD_FT": 4187.2,
    "DRV_STAGE_HEAD_FT": 12.24,
    "DRV_MIX_GRAD_PSI_FT": 0.3535,
    "DRV_MIX_SG": 0.816,
    "DRV_FLUID_LEVEL_FT": 1122.7,
    "DRV_APPARENT_POWER_KVA": 36.7,
    "DRV_ACTUAL_POWER_KW": 31.6,
    "DRV_V_PER_HZ": 11.16,
    "DRV_MOTOR_LOAD_PCT": 176.9
  },
  "higher_order_derived": {
    "HOD_NORM_HEAD_FT": 10.94,
    "HOD_FLOW_RATE_BPD": 399.1,
    "HOD_OIL_RATE_BOPD": 399.1,
    "HOD_WATER_RATE_BWPD": 0.0,
    "HOD_GAS_RATE_MSCFD": 119.7,
    "HOD_WATER_CUT_PCT": 0.0,
    "HOD_OIL_CUT_PCT": 100.0,
    "HOD_HYD_POWER_HP": 25.46,
    "HOD_ELEC_POWER_HP": 35.98,
    "HOD_ENERGY_VARIANCE_PCT": 29.23,
    "HOD_ENERGY_STATUS": "DIVERGENT"
  }
}
```

---

## 5. Topic: `esp/v1/{well_id}/asset` (Nameplate & Pump Curves)

### 5.1 Verbatim Raw JSON Payload (Retained: True)
```json
{
  "WELL": "FNW-01",
  "PUMP_TYPE": "B400-400",
  "STAGES": 342,
  "MOTOR_HP_50HZ": 53.0,
  "VOLT_50HZ": 1669.0,
  "AMP": 20.3,
  "CLUSTER": "SB247",
  "VSD_MODEL": "VECTOR PLUS",
  "VSD_KVA": 104.0,
  "TRANSFORMER_KVA": 160.0,
  "INSTALLATION_DATE": "2026-01-17",
  "COEFF_A": -0.00012,
  "COEFF_B": -0.01,
  "COEFF_C": -0.78,
  "COEFF_D": 440.0,
  "TVD_FT": 4800.0,
  "OIL_SG": 0.858,
  "WATER_SG": 1.072,
  "BO": 1.14,
  "cluster_wells": [
    "FNW-01",
    "FNW-02"
  ],
  "cluster_well_count": 2,
  "cluster_total_rated_amp": 43.9,
  "asset_properties": {
    "AP_TVD_FT": 4800.0,
    "AP_PUMP_STAGES": 342,
    "AP_PUMP_TYPE": "B400-400",
    "AP_MOTOR_HP": 53.0,
    "AP_MOTOR_VOLT_V": 1669.0,
    "AP_MOTOR_RATED_AMP_A": 20.3,
    "AP_PUMP_CURVE_COEFFS": {
      "A": -0.00012,
      "B": -0.01,
      "C": -0.78,
      "D": 440.0
    },
    "AP_OIL_SG": 0.858,
    "AP_WATER_SG": 1.072,
    "AP_FORMATION_VOL_FACTOR_BO": 1.14,
    "AP_GAS_OIL_RATIO_GOR_SCF_BBL": 300.0,
    "AP_VSD_KVA": 104.0,
    "AP_TRANSFORMER_KVA": 160.0
  }
}
```

---

## 6. Topic: `esp/v1/simulator/status` (Liveness)

```json
{
  "online": true
}
```
* Note: Mosquitto broker holds `{"online": false}` as MQTT Last Will and Testament (LWT). If the daemon on Server 1 crashes, Mosquitto immediately marks `online: false`.

---

## 7. End-to-End System Integration Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SERVER 1: Mosquitto MQTT (192.168.1.155:1883) & Twin API (Port 8080)                  │
└────────┬──────────────────────┬──────────────────────┬──────────────────┬──────────────┘
         │ .../telemetry (1 Hz) │ .../vfm (1 Hz)       │ .../events (IRQ) │ .../asset
         ▼                      ▼                      ▼                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SERVER 3: Edge Ingestion & ML Service (192.168.1.184)                                  │
│                                                                                        │
│ 1. Telemetry Historian (`unlabelled.db`):                                              │
│    • Ingests 14 SCADA channels into 34-column schema                                   │
│                                                                                        │
│ 2. Events Historian (`esp_events.db`):                                                 │
│    • Subscribes to `esp/v1/+/events`                                                   │
│    • Stores state transitions, alarm flags, and trip causes                            │
│                                                                                        │
│ 3. ML Engine & WebSocket Hub:                                                          │
│    • Isolation Forest anomaly scoring                                                  │
│    • Pushes live events & telemetry cards to React Dashboard                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SERVER 2: AI Specialist Multi-Agent Gateway (192.168.1.191:8090)                       │
│                                                                                        │
│ 1. Event Consumer:                                                                     │
│    • Triggers diagnostic investigation upon receiving critical event                   │
│                                                                                        │
│ 2. Synthesis Node:                                                                     │
│    • Cross-references event alarm against live telemetry and asset pump curves        │
│    • Generates operational mitigation recommendations                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
