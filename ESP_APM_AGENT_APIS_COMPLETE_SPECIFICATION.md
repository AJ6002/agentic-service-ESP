# ESP APM Agent & Edge APIs — Complete Ground-Truth Specification & QoD Reference

> **Document Version**: 2.0.0 (Grounded in Verified Server 184 Implementation)  
> **Server Host**: `http://192.168.1.184:8090` (Unified Production Gateway) / Localhost `http://127.0.0.1:8090`  
> **Compliance Standard**: Quality of Data (QoD) Pipeline, Provenance Tracking, Agent Jane Autonomous Reasoning  
> **Telemetry Cadence**: 1.00s (1 Hz) | **Historian Engine**: Dual SQLite / DuckDB Scanner  

---

## 1. Authoritative Canonical Well Registry & Cross-Service Parity

### 1.1 The Single Source of Truth
The authoritative set of monitored assets consists of exactly **14 Farha South Production Wells**.
* **Validation Rule**: If an incoming query specifies any well ID outside this 14-well list, the API strictly returns `404 Not Found` (`WELL_NOT_FOUND`).
* **Runtime Verification**: Calling `GET /live/wells` dynamically returns this identical 14-well list with runtime liveness indicators.

```
Canonical Well IDs (14 Wells):
├── FNW-01      (Known Tripped / Off-Nominal Benchmark Well)
├── FS-17       (Canonical Baseline Running Well)
├── FS-121      (Running / Normal)
├── FNW-06      (Running / Normal)
├── FWS-06      (Running / Normal)
├── ULFA-5      (Running / Normal)
├── FS-96       (Running / Normal)
├── FS-21       (Running / Normal)
├── FS-06       (Running / Normal)
├── FS-91       (Running / Normal)
├── FSWS-001-A  (Running / Normal)
├── FS-014      (Running / Normal)
├── FS-016      (Running / Normal)
└── FS-031      (Running / Normal)
```

### 1.2 Cross-Service Parity Table
| Service Domain | Base Path | Data Source | Monitored Wells | Behavior for Healthy Well |
| :--- | :--- | :--- | :--- | :--- |
| **Historian** | `/historian/*` | `unlabelled.db` (`opg_well_telemetry`) | All 14 Canonical Wells | Returns historical rows (200 OK) |
| **Live Telemetry** | `/live/*` | MQTT (`esp/v1/#`) -> Memory Cache | All 14 Canonical Wells | Returns latest packet (200 OK) or 503 if broker disconnected |
| **Events** | `/events/*` | `esp_events.db` (`events`) | All 14 Canonical Wells | Returns `events: []` (200 OK) if no trips occurred |
| **ML Diagnostics** | `/ml/*` | `mlresults.db` + In-memory Pipeline | All 14 Canonical Wells | Returns anomaly score, fault class, health index (200 OK) |
| **Dashboard Plots** | `/plots/*` | SQLite aggregations & pre-computed trends | All 14 Canonical Wells | Returns time-series series (200 OK) |
| **KPI & Cards** | `/kpi/*`, `/cards/*` | Derived physics & KPI catalog | All 14 Canonical Wells | Returns card values, bands, thresholds, guidance (200 OK) |

---

## 2. Quality of Data (QoD) Freshness, Staleness & Timestamp Keys

To eliminate guessing for QoD freshness engines and provenance validators, the exact timestamp key, age tracking metric, and staleness tolerance are defined below:

| Endpoint Domain | Freshness Key Name | Age Key Name | Nominal Interval | Warning Staleness | Critical / Expired Staleness | QoD Invalidation Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/live/telemetry/*` | `timestamp` (ISO-8601 UTC) | `age_sec` (float) | 1.0 s | `age_sec > 5.0 s` | `age_sec > 30.0 s` | Flag telemetry STALE; trigger 503 fallback |
| `/live/vfm/*` | `timestamp` (ISO-8601 UTC) | `age_sec` (float) | 1.0 s | `age_sec > 5.0 s` | `age_sec > 30.0 s` | Flag flow meter ESTIMATE_DRIFTED |
| `/live/status` | `last_heartbeat` (ISO-8601) | N/A | 5.0 s | `now - ts > 15.0 s` | `now - ts > 60.0 s` | Simulator heartbeat lost |
| `/events/*` | `timestamp` (ISO-8601 UTC) | N/A | Event-driven (on change) | N/A (Event log is persistent) | N/A | Events are chronological point-in-time facts |
| `/ml/*` | `timestamp` (ISO-8601 UTC) | N/A | 5.0 s | `now - ts > 60.0 s` | `now - ts > 300.0 s` | Flag ML inference STALE |
| `/kpi/*`, `/cards/*` | `timestamp` (ISO-8601 UTC) | N/A | 1.0 s - 5.0 s | `now - ts > 30.0 s` | `now - ts > 120.0 s` | Re-compute card values from latest raw |
| `/historian/*` | `timestamp` (row array index 0) | N/A | Historical Archive | N/A (Immutable) | N/A | Historical records never stale; check `coverage` for gaps |

---

## 3. Signal Engineering Dictionary & Plausible Sanity Bounds

For QoD range-sanity validation, sensor values must fall within the physical operational envelope of ESP downhole and surface equipment. Any value outside `[Min Plausible, Max Plausible]` indicates sensor failure, telemetry corruption, or electrical open/short circuit.

| Signal Name | Database Column / JSON Key | Physical Meaning | Engineering Unit | Nominal Range | Min Plausible (Fail Low) | Max Plausible (Fail High) | Alarm Low | Alarm High |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Intake Pressure** | `int_prs_psi` / `STD_INT_PRS_PSI` | Pump Suction Intake Pressure (PIP) | PSI | 250.0 – 600.0 | **0.0** | **3,500.0** | < 150.0 | > 1,200.0 |
| **Discharge Pressure**| `disch_prs_psi` / `STD_DISCH_PRS_PSI`| Pump Discharge Head Pressure (PDP) | PSI | 1,400.0 – 2,200.0 | **0.0** | **5,000.0** | < 800.0 | > 3,200.0 |
| **Intake Temperature**| `int_temp_c` / `STD_INT_TEMP_C` | Reservoir Fluid Intake Temperature | °C | 55.0 – 75.0 | **0.0** | **140.0** | < 20.0 | > 105.0 |
| **Motor Temperature** | `motor_temp_c` / `STD_MOTOR_TEMP_C`| Downhole Motor Winding Temperature | °C | 75.0 – 95.0 | **0.0** | **160.0** | < 20.0 | > 125.0 (Trip 135) |
| **Vibration** | `vibration_g` / `STD_VIBRATION_G` | Downhole Mechanical Vibration RMS | g RMS | 0.04 – 0.15 | **0.0** | **10.0** | N/A | > 0.45 (Trip 2.0) |
| **Motor Voltage** | `volt_v` / `STD_VOLT_V` | VFD Phase-to-Phase Motor Voltage | V | 500.0 – 1,800.0 | **0.0** | **2,500.0** | < 380.0 | > 2,100.0 |
| **Motor Current** | `amp_a` / `STD_AMP_A` | Motor Phase Current Draw | A | 25.0 – 45.0 | **0.0** | **120.0** | < 15.0 | > 48.0 (Trip 55) |
| **Operating Frequency**| `freq_hz` / `STD_FREQ_HZ` | VFD Inverter Output Frequency | Hz | 45.0 – 58.0 | **20.0** | **70.0** | < 35.0 | > 62.0 |
| **Leakage Current** | `leak_current_ct` | Downhole Insulation Leakage | ct (mA) | 0.0 – 25.0 | **0.0** | **200.0** | N/A | > 50.0 |
| **DHG Current** | `dhg_current_ma` | Downhole Gauge Current Loop | mA | 8.0 – 16.0 | **0.0** | **50.0** | < 4.0 | > 24.0 |
| **Wellhead Pressure** | `whp_psi` | Surface Flowing Tubing Pressure | PSI | 120.0 – 280.0 | **0.0** | **1,500.0** | < 50.0 | > 600.0 |
| **Flowline Pressure** | `flp_psi` | Surface Flowline Gathering Pressure | PSI | 80.0 – 220.0 | **0.0** | **1,000.0** | < 30.0 | > 450.0 |
| **Annulus Pressure** | `ap_psi` | Casing-Tubing Annulus Gas Pressure | PSI | 50.0 – 250.0 | **0.0** | **1,200.0** | N/A | > 500.0 |
| **VFD Status** | `vfd_sts` | Discrete VFD Run Interlock (1=Run, 0=Stop) | discrete | 1 (Running) | **0** | **1** | N/A | 0 (Tripped) |
| **Liquid Production**| `liquid_rate_bpd` | Total Virtual Metered Liquid Rate | BPD | 200.0 – 600.0 | **0.0** | **5,000.0** | < 50.0 | > 2,500.0 |
| **Oil Production** | `oil_rate_bopd` | Net Commercial Crude Recovery Rate | BOPD | 100.0 – 450.0 | **0.0** | **3,000.0** | < 25.0 | > 1,500.0 |
| **Water Cut** | `water_cut_pct` | Formation Water Percentage in Stream | % | 0.0 – 85.0 | **0.0** | **100.0** | N/A | > 75.0 (High 92) |
| **Associated Gas** | `gas_rate_mscfd` | GOR Solution & Free Breakout Gas | MSCFD | 50.0 – 300.0 | **0.0** | **2,000.0** | N/A | > 250.0 (Trip 600) |
| **Health Index** | `health_score` | Composite Asset Health Rating | 0–100 index | 70.0 – 95.0 | **0.0** | **100.0** | < 75.0 (Degraded)| < 50.0 (Critical) |
| **Anomaly Score** | `anomaly_score` / `score` | Isolation Forest Statistical Divergence | 0.0–1.0 index | 0.05 – 0.35 | **0.0** | **1.0** | N/A | > 0.65 (Anomaly) |

---

## 4. Verbatim Endpoint Catalog, Field Guarantees & Units

Field status is rigorously annotated:
* `[REQ]`: **Guaranteed Present**. Always returned in every valid response.
* `[OPT]`: **Optional / Nullable**. Returned only when conditions are met; may be `null` or omitted.

---

### Domain 1: Historian API (`/historian/*`)

#### 1.1 `GET /historian/health`
* **Purpose**: Verifies SQLite/DuckDB engine attachment and total row inventory.
* **Empty / Error Behavior**: Always returns `200 OK` (with `status: "degraded"` and `db_attached: false` if file missing).
* **Verbatim Response**:
```json
{
  "status": "ok",                  // [REQ] String: "ok" | "degraded"
  "uptime_sec": 4210,              // [REQ] Integer: Seconds since gateway start (unit: seconds)
  "db_attached": true,             // [REQ] Boolean: True if unlabelled.db is successfully opened
  "row_count": 1991974,            // [REQ] Integer: Total stored telemetry rows across all wells
  "backend": "sqlite"              // [REQ] String: "duckdb" | "sqlite"
}
```

#### 1.2 `GET /historian/window`
* **Query Parameters**:
  * `well_id` [REQ]: Canonical well ID (e.g. `FS-17`)
  * `start` [REQ]: ISO-8601 start timestamp inclusive
  * `end` [REQ]: ISO-8601 end timestamp inclusive
  * `signals` [OPT]: Comma-separated signals (default: all 14 signals)
  * `limit` [OPT]: Maximum rows (default: 10000, max: 50000)
* **Empty / Error Behavior**:
  * Unknown well: `404 Not Found` (`WELL_NOT_FOUND`).
  * Valid well but 0 rows in requested time window: `200 OK` with `row_count: 0`, `rows: []`.
  * Time window > 30 days: `400 Bad Request` (`WINDOW_TOO_LARGE`).
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String: Canonical Well ID
  "start": "2026-08-01T00:00:00Z",                 // [REQ] String: ISO-8601 start window
  "end": "2026-08-30T00:00:00Z",                   // [REQ] String: ISO-8601 end window
  "row_count": 2,                                  // [REQ] Integer: Returned row count
  "truncated": false,                              // [REQ] Boolean: True if truncated by limit
  "columns": [                                     // [REQ] Array[String]: Exact ordered column headers
    "timestamp",
    "amp_a",
    "freq_hz",
    "motor_temp_c",
    "int_prs_psi"
  ],
  "units": {                                       // [REQ] Object: Explicit unit map for every column
    "amp_a": "A",
    "freq_hz": "Hz",
    "motor_temp_c": "°C",
    "int_prs_psi": "PSI"
  },
  "rows": [                                        // [REQ] Array[Array]: Parallel values matching columns
    ["2026-08-27T07:20:21.749959Z", 35.7, 53.1, 87.71, 395.4],
    ["2026-08-27T07:20:22.749959Z", 35.8, 53.1, 87.72, 395.1]
  ]
}
```

#### 1.3 `GET /historian/latest`
* **Query Parameters**: `well_id` [REQ], `signals` [OPT]
* **Empty / Error Behavior**:
  * Unknown well: `404 Not Found` (`WELL_NOT_FOUND`).
  * Valid well with 0 records in DB: `404 Not Found` (`NO_DATA`).
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-08-27T07:20:21.749959Z",      // [REQ] String: ISO-8601 UTC reading timestamp
  "values": {                                      // [REQ] Object: Latest readings dictionary
    "int_prs_psi": 395.4,                          // [REQ] Float: Intake pressure (unit: PSI)
    "disch_prs_psi": 1883.1,                       // [REQ] Float: Discharge pressure (unit: PSI)
    "int_temp_c": 64.53,                           // [REQ] Float: Intake fluid temp (unit: °C)
    "motor_temp_c": 87.71,                         // [REQ] Float: Motor winding temp (unit: °C)
    "vibration_g": 0.082,                          // [REQ] Float: Vibration RMS (unit: g)
    "volt_v": 594.1,                               // [REQ] Float: Motor voltage (unit: V)
    "amp_a": 35.7,                                 // [REQ] Float: Motor current (unit: A)
    "freq_hz": 53.1,                               // [REQ] Float: Operating frequency (unit: Hz)
    "leak_current_ct": 15.0,                       // [REQ] Float: Downhole leakage (unit: ct)
    "dhg_current_ma": 10.7,                        // [REQ] Float: Gauge loop current (unit: mA)
    "whp_psi": 180.3,                              // [REQ] Float: Wellhead pressure (unit: PSI)
    "flp_psi": 171.0,                              // [REQ] Float: Flowline pressure (unit: PSI)
    "ap_psi": 155.5,                               // [REQ] Float: Annulus pressure (unit: PSI)
    "vfd_sts": true                                // [REQ] Boolean: VFD running status (true=run)
  }
}
```

#### 1.4 `GET /historian/aggregates`
* **Query Parameters**: `well_id` [REQ], `start` [REQ], `end` [REQ], `signals` [OPT], `bucket` [OPT: "1h","1d"], `agg` [OPT: "avg","min","max","all"]
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "bucket": "1h",                                  // [REQ] String: Applied time bucket
  "agg": "avg",                                    // [REQ] String: Aggregation operator
  "start": "2026-08-01T00:00:00Z",                 // [REQ] String
  "end": "2026-08-30T00:00:00Z",                   // [REQ] String
  "columns": ["bucket", "amp_a", "motor_temp_c"],  // [REQ] Array[String]
  "units": { "amp_a": "A", "motor_temp_c": "°C" }, // [REQ] Object: Units map
  "rows": [                                        // [REQ] Array[Array]: Downsampled buckets
    ["2026-08-27 07:00:00Z", 35.72, 87.68],
    ["2026-08-27 08:00:00Z", 35.81, 87.75]
  ]
}
```

#### 1.5 `GET /historian/coverage`
* **Query Parameters**: `well_id` [REQ]
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "first_ts": "2026-08-01T00:00:00Z",              // [REQ] String: Earliest recorded timestamp
  "last_ts": "2026-09-13T10:37:40Z",               // [REQ] String: Most recent recorded timestamp
  "row_count": 425493,                             // [REQ] Integer: Total available rows for well
  "signals_present": [                             // [REQ] Array[String]: Channels with data
    "int_prs_psi", "disch_prs_psi", "int_temp_c", "motor_temp_c",
    "vibration_g", "volt_v", "amp_a", "freq_hz",
    "leak_current_ct", "dhg_current_ma", "whp_psi", "flp_psi", "ap_psi", "vfd_sts"
  ],
  "gaps": []                                       // [REQ] Array[Object]: Discovered telemetry dropouts
}
```

---

### Domain 2: Live Telemetry & MQTT Facade (`/live/*`)

#### 2.1 `GET /live/health`
* **Verbatim Response**:
```json
{
  "status": "ok",                  // [REQ] String: "ok" (connected) | "down" (disconnected)
  "mqtt_connected": true,          // [REQ] Boolean: TCP liveness to broker 192.168.1.155:1883
  "broker": "192.168.1.155:1883",  // [REQ] String: IP:Port of target MQTT broker
  "wells_subscribed": 14,          // [REQ] Integer: Total monitored wells in subscription scope
  "last_message_ts": "2026-09-17T12:32:34Z" // [REQ] String: ISO-8601 UTC timestamp of last ingested packet
}
```

#### 2.2 `GET /live/telemetry/{well_id}`
* **Error Behavior**: When MQTT is disconnected, immediately returns `503 Service Unavailable` with `MQTT_DISCONNECTED`.
* **Verbatim Response (200 OK)**:
```json
{
  "well_id": "FS-17",                              // [REQ] String: Canonical Well ID
  "timestamp": "2026-09-17T12:32:34.270090Z",      // [REQ] String: ISO-8601 UTC reading timestamp
  "age_sec": 0.82,                                 // [REQ] Float: Seconds elapsed since arrival (unit: s)
  "manufacturer": "Borets / Levare",               // [REQ] String: Equipment manufacturer
  "model_id": "B400-400",                          // [REQ] String: Pump model designation
  "measurements": {                                // [REQ] Object: 14 raw SCADA channels
    "STD_INT_PRS_PSI": 395.4,                      // [REQ] Float (unit: PSI)
    "STD_DISCH_PRS_PSI": 1883.1,                   // [REQ] Float (unit: PSI)
    "STD_INT_TEMP_C": 64.53,                       // [REQ] Float (unit: °C)
    "STD_MOTOR_TEMP_C": 87.71,                     // [REQ] Float (unit: °C)
    "STD_VIBRATION_G": 0.082,                      // [REQ] Float (unit: g RMS)
    "STD_VOLT_V": 594.1,                           // [REQ] Float (unit: V)
    "STD_AMP_A": 35.7,                             // [REQ] Float (unit: A)
    "STD_FREQ_HZ": 53.1,                           // [REQ] Float (unit: Hz)
    "STD_LEAK_CURRENT_CT": 15.0,                   // [REQ] Float (unit: ct)
    "STD_DHG_CURRENT_MA": 10.7,                    // [REQ] Float (unit: mA)
    "STD_WHP_PSI": 180.3,                          // [REQ] Float (unit: PSI)
    "STD_FLP_PSI": 171.0,                          // [REQ] Float (unit: PSI)
    "STD_AP_PSI": 155.5,                           // [REQ] Float (unit: PSI)
    "STD_VFD_STS": true                            // [REQ] Boolean (unit: discrete)
  },
  "source": "mqtt",                                // [REQ] String: "mqtt"
  "schema_version": "1.0.0"                        // [REQ] String
}
```

#### 2.3 `GET /live/telemetry/{well_id}/recent`
* **Query Parameters**: `seconds` [OPT: default 30, max 60]
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "seconds_requested": 30,                         // [REQ] Integer: Ring buffer depth in seconds
  "row_count": 30,                                 // [REQ] Integer: Number of 1-Hz samples returned
  "columns": [                                     // [REQ] Array[String]
    "timestamp", "amp_a", "freq_hz", "motor_temp_c", "int_prs_psi", "disch_prs_psi"
  ],
  "units": {                                       // [REQ] Object
    "amp_a": "A", "freq_hz": "Hz", "motor_temp_c": "°C", "int_prs_psi": "PSI", "disch_prs_psi": "PSI"
  },
  "rows": [                                        // [REQ] Array[Array]: Sequential 1-second records
    ["2026-09-17T12:32:04Z", 35.7, 53.1, 87.71, 395.4, 1883.1],
    ["2026-09-17T12:32:05Z", 35.8, 53.1, 87.72, 395.3, 1883.0]
  ]
}
```

#### 2.4 `GET /live/vfm/{well_id}`
* **Purpose**: Virtual Flow Metering (VFM) and derived downhole thermodynamic calculations.
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-17T12:32:34.270090Z",      // [REQ] String (ISO-8601 UTC)
  "age_sec": 0.82,                                 // [REQ] Float (unit: seconds)
  "flow_rates": {                                  // [REQ] Object: Volumetric flow estimates
    "liquid_rate_bpd": 399.1,                      // [REQ] Float (unit: BPD)
    "oil_rate_bopd": 399.1,                        // [REQ] Float (unit: BOPD)
    "water_rate_bpd": 0.0,                         // [REQ] Float (unit: BWPD)
    "water_cut_pct": 0.0,                          // [REQ] Float (unit: %)
    "gas_rate_mscfd": 119.7                        // [REQ] Float (unit: MSCFD)
  },
  "derived_physics": {                             // [REQ] Object: Mechanical & thermodynamic parameters
    "total_dynamic_head_ft": 4120.5,               // [REQ] Float: Total dynamic head developed (unit: ft)
    "hydraulic_power_hp": 34.8,                    // [REQ] Float: Hydraulic power delivered to fluid (unit: HP)
    "motor_load_pct": 102.5,                       // [REQ] Float: Electrical current load ratio (unit: %)
    "energy_variance_pct": 29.23,                  // [REQ] Float: Hydraulic vs Electrical power delta (unit: %)
    "fluid_density_sg": 0.858                      // [REQ] Float: Composite specific gravity (unit: SG water=1.0)
  },
  "status": "running",                             // [REQ] String: "running" | "tripped"
  "schema_version": "1.0.0"                        // [REQ] String
}
```

#### 2.5 `GET /live/asset/{well_id}`
* **Purpose**: Retained nameplate specifications and H-Q pump curve polynomial coefficients.
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-01-17T00:00:00Z",             // [REQ] String (Installation date)
  "asset": {                                       // [REQ] Object
    "pump_type": "B400-400",                       // [REQ] String: Manufacturer model code
    "stages": 342,                                 // [REQ] Integer: Number of impeller/diffuser stages
    "motor_hp_50hz": 53.0,                         // [REQ] Float: Rated motor horsepower (unit: HP)
    "volt_50hz": 1669.0,                           // [REQ] Float: Rated nameplate voltage (unit: V)
    "rated_amp_a": 20.3,                           // [REQ] Float: Rated full-load current (unit: A)
    "cluster": "SB247",                            // [REQ] String: Field gathering cluster ID
    "vsd_model": "VECTOR PLUS",                    // [REQ] String: Surface variable speed drive model
    "vsd_kva": 104.0,                              // [REQ] Float: Surface VFD electrical capacity (unit: kVA)
    "transformer_kva": 160.0,                      // [REQ] Float: Step-up transformer capacity (unit: kVA)
    "installation_date": "2026-01-17",             // [REQ] String: YYYY-MM-DD
    "tvd_ft": 4800.0,                              // [REQ] Float: True vertical setting depth (unit: ft)
    "oil_sg": 0.858,                               // [REQ] Float: Crude specific gravity (unit: SG)
    "water_sg": 1.072,                             // [REQ] Float: Produced water specific gravity (unit: SG)
    "bo": 1.14,                                    // [REQ] Float: Formation volume factor (unit: rb/stb)
    "pump_curve_coeffs": {                         // [REQ] Object: 3rd-order head curve $H(Q) = AQ^3 + BQ^2 + CQ + D$
      "A": -0.00012,                               // [REQ] Float
      "B": -0.01,                                  // [REQ] Float
      "C": -0.78,                                  // [REQ] Float
      "D": 440.0                                   // [REQ] Float: Shut-in zero-flow stage head (unit: ft/stage)
    }
  },
  "cluster": {                                     // [REQ] Object
    "cluster_id": "SB247",                         // [REQ] String
    "wells": ["FS-17"],                            // [REQ] Array[String]
    "well_count": 1,                               // [REQ] Integer
    "total_rated_amp": 20.3                        // [REQ] Float (unit: A)
  }
}
```

#### 2.6 `GET /live/status`
* **Verbatim Response**:
```json
{
  "online": true,                                  // [REQ] Boolean: Simulator execution state
  "last_heartbeat": "2026-09-17T12:32:34Z"         // [REQ] String: ISO-8601 UTC heartbeat timestamp
}
```

#### 2.7 `GET /live/wells`
* **Verbatim Response**:
```json
{
  "wells": [                                       // [REQ] Array[Object]: 14 Canonical Wells
    {
      "well_id": "FS-17",                          // [REQ] String: Canonical Well ID
      "last_seen": "2026-09-17T12:32:34Z",         // [REQ] String: ISO-8601 timestamp
      "online": true                               // [REQ] Boolean: Actively streaming telemetry
    },
    {
      "well_id": "FNW-01",
      "last_seen": "2026-09-17T12:32:34Z",
      "online": true
    }
  ]
}
```

---

### Domain 3: Events & Incident Management (`/events/*`)

#### 3.1 `GET /events/health`
* **Verbatim Response**:
```json
{
  "status": "ok",                  // [REQ] String
  "row_count": 370,                // [REQ] Integer: Total stored event transitions
  "last_event_ts": "2026-09-13T10:39:15Z" // [REQ] String: ISO-8601 timestamp of newest event
}
```

#### 3.2 `GET /events/timeline`
* **Query Parameters**: `well_id` [OPT], `start` [OPT], `end` [OPT], `limit` [OPT: default 100]
* **Empty Behavior**: If no events exist in the requested window, returns `200 OK` with `event_count: 0`, `events: []`.
* **Verbatim Response**:
```json
{
  "well_id": "FNW-01",                             // [OPT] String: Omitted if fleet query
  "start": "2026-09-01T00:00:00Z",                 // [REQ] String
  "end": "2026-09-30T00:00:00Z",                   // [REQ] String
  "event_count": 1,                                // [REQ] Integer
  "events": [                                      // [REQ] Array[Object]
    {
      "event_id": "EV-20260913-100000-1010",       // [REQ] String: Unique event primary key
      "timestamp": "2026-09-13T10:00:00Z",         // [REQ] String: Transition timestamp
      "well_id": "FNW-01",                         // [REQ] String: Canonical Well ID
      "operating_state": "tripped",                // [REQ] String: "running"|"starting"|"stopped"|"tripped"
      "scenario": "dry_well_pump_off",             // [REQ] String: Physics simulation scenario tag
      "trip_cause": "UNDERLOAD_PUMP_OFF",          // [OPT] String: Hardware trip cause (null if running)
      "alarms": [                                  // [REQ] Array[String]: Active alarm tags
        "LOW_INTAKE_PRESSURE",
        "UNDERLOAD",
        "TRIP_UNDERLOAD_PUMP_OFF"
      ],
      "event_type": "trip"                         // [REQ] String: "trip" | "alarm" | "state_change"
    }
  ]
}
```

#### 3.3 `GET /events/trips`
* **Query Parameters**: `well_id` [OPT], `start` [OPT], `end` [OPT], `limit` [OPT]
* **Empty Behavior**: If a well has 0 trip shutdowns (e.g. running healthy), returns `200 OK` with `event_count: 0`, `events: []`.
* **Verbatim Response**:
```json
{
  "event_count": 1,
  "events": [
    {
      "event_id": "EV-20260913-100000-1010",
      "timestamp": "2026-09-13T10:00:00Z",
      "well_id": "FNW-01",
      "operating_state": "tripped",
      "scenario": "dry_well_pump_off",
      "trip_cause": "UNDERLOAD_PUMP_OFF",
      "alarms": ["UNDERLOAD", "TRIP_UNDERLOAD_PUMP_OFF"],
      "event_type": "trip"
    }
  ]
}
```

#### 3.4 `GET /events/latest/{well_id}`
* **Empty Behavior**: Returns `200 OK` with the latest operational event; for stable wells with no trips, returns normal operation event (`operating_state: "running"`, `trip_cause: null`).
* **Verbatim Response**:
```json
{
  "event_id": "EV-20260913-101500-1011",           // [REQ] String
  "timestamp": "2026-09-13T10:15:00Z",             // [REQ] String
  "well_id": "FS-17",                              // [REQ] String
  "operating_state": "running",                    // [REQ] String
  "scenario": "normal",                            // [REQ] String
  "trip_cause": null,                              // [OPT] Null when operating normally
  "alarms": ["NORMAL_OPERATION"],                 // [REQ] Array[String]
  "event_type": "state_change"                     // [REQ] String
}
```

#### 3.5 `GET /events/summary`
* **Query Parameters**: `start` [OPT], `end` [OPT], `well_id` [OPT]
* **Verbatim Response**:
```json
{
  "start": "2026-09-01T00:00:00Z",                 // [REQ] String
  "end": "2026-09-13T11:00:00Z",                   // [REQ] String
  "wells": [                                       // [REQ] Array[Object]: Per-well aggregated metrics
    {
      "well_id": "FNW-01",                         // [REQ] String
      "trip_count": 1,                             // [REQ] Integer (unit: count)
      "alarm_count": 0,                            // [REQ] Integer (unit: count)
      "state_change_count": 0,                     // [REQ] Integer (unit: count)
      "scenario_change_count": 0                   // [REQ] Integer (unit: count)
    },
    {
      "well_id": "FS-17",
      "trip_count": 0,
      "alarm_count": 1,
      "state_change_count": 0,
      "scenario_change_count": 0
    }
  ]
}
```

#### 3.6 `GET /events/catalog`
* **Purpose**: Complete static reference catalog of supported hardware trip causes and alarm thresholds.
* **Verbatim Response**:
```json
{
  "trip_causes": [                                 // [REQ] Array[Object]
    {
      "tag": "UNDERLOAD_PUMP_OFF",                 // [REQ] String: Canonical trip cause tag
      "scenario": "dry_well_pump_off",             // [REQ] String: Underlying physics mechanism
      "meaning": "Reservoir inflow stops -> PIP drops -> fluid lost -> motor underload trip."
    },
    {
      "tag": "MOTOR_OVERLOAD",
      "scenario": "motor_overload",
      "meaning": "High mechanical drag -> current exceeds overcurrent trip limit."
    },
    {
      "tag": "BROKEN_SHAFT_ZERO_HEAD",
      "scenario": "broken_shaft",
      "meaning": "Mechanical coupling severance -> total loss of hydraulic lift -> low motor load."
    },
    {
      "tag": "GAS_LOCK_UNDERLOAD",
      "scenario": "gas_interference",
      "meaning": "Gas lock in pump intake stages -> head collapse and motor load hunting."
    },
    {
      "tag": "UNDER_VOLTAGE",
      "scenario": "undervoltage",
      "meaning": "Electrical bus voltage drops below VFD trip setpoint."
    }
  ],
  "alarms": [                                      // [REQ] Array[Object]
    {
      "tag": "LOW_INTAKE_PRESSURE",                // [REQ] String
      "threshold": "STD_INT_PRS_PSI < 150.0 PSI",  // [REQ] String: Evaluated rule
      "meaning": "Pump intake pressure depleted below minimum suction head."
    },
    {
      "tag": "OVERLOAD",
      "threshold": "Motor load > 115.0%",
      "meaning": "Current draw exceeds motor thermal design limit."
    },
    {
      "tag": "UNDERLOAD",
      "threshold": "Motor load < 30.0%",
      "meaning": "Current draw indicates pump cavitation or dry running."
    }
  ]
}
```

---

### Domain 4: Machine Learning Diagnostics (`/ml/*`)

#### 4.1 `GET /ml/health`
* **Verbatim Response**:
```json
{
  "status": "ok",                                  // [REQ] String
  "models_loaded": 4,                              // [REQ] Integer (Isolation Forest, Classifier, Health Index, SHAP)
  "last_inference_ts": "2026-09-17T11:28:47.329Z"  // [REQ] String: Timestamp of newest ML evaluation
}
```

#### 4.2 `GET /ml/anomaly/{well_id}`
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-17T11:28:47.329365Z",      // [REQ] String (ISO-8601 UTC)
  "score": 0.72,                                   // [REQ] Float: Anomaly score (unit: 0.0–1.0 index)
  "threshold": 0.65,                               // [REQ] Float: Binary threshold cutoff (unit: index)
  "is_anomalous": true,                            // [REQ] Boolean: True if score > threshold
  "model_id": "isolation_forest_v2",               // [REQ] String: Identifier of active ML model
  "model_version": "2.1.0",                        // [REQ] String: Semantic model version
  "feature_version": "1.3.0",                      // [REQ] String: Feature engineering matrix version
  "confidence": 0.83                               // [REQ] Float: Confidence probability (unit: 0.0–1.0)
}
```

#### 4.3 `GET /ml/fault/{well_id}`
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-17T11:28:47.329365Z",      // [REQ] String
  "fault_class": "MOTOR_OVERLOAD",                 // [REQ] String: Primary diagnostic classification
  "probability": 0.78,                             // [REQ] Float: Classification confidence (unit: 0.0–1.0)
  "top_k": [                                       // [REQ] Array[Object]: Differential diagnostic ranking
    { "fault_class": "MOTOR_OVERLOAD", "probability": 0.78 },
    { "fault_class": "OVERLOAD_SOLIDS", "probability": 0.15 },
    { "fault_class": "HIGH_VISCOSITY", "probability": 0.07 }
  ],
  "model_id": "fault_classifier_v3",               // [REQ] String
  "model_version": "3.0.1",                        // [REQ] String
  "feature_version": "1.3.0",                      // [REQ] String
  "confidence": 0.78                               // [REQ] Float
}
```

#### 4.4 `GET /ml/health/{well_id}`
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-17T11:28:47.329365Z",      // [REQ] String
  "health_score": 71.4,                            // [REQ] Float: Composite Health Score (unit: 0–100 index)
  "band": "DEGRADED",                              // [REQ] String: "HEALTHY" (>=75) | "DEGRADED" (50-74) | "CRITICAL" (<50)
  "contributors": [                                // [REQ] Array[Object]: Top negative penalty drivers
    { "signal": "motor_temp_c", "contribution": -0.18 }, // Float: Penalty fraction (unit: delta fraction)
    { "signal": "vibration_g", "contribution": -0.11 },
    { "signal": "amp_a", "contribution": -0.06 }
  ],
  "model_id": "health_v1",                         // [REQ] String
  "model_version": "1.0.4",                        // [REQ] String
  "confidence": 0.88                               // [REQ] Float
}
```

#### 4.5 `GET /ml/degradation/{well_id}`
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-17T11:28:47.329365Z",      // [REQ] String
  "trend": "increasing",                           // [REQ] String: "increasing" (degrading) | "stable"
  "rate_per_day": 0.42,                            // [REQ] Float: Daily health index decline rate (unit: points/day)
  "projected_days_to_threshold": 50,               // [REQ] Integer: Remaining Useful Life RUL (unit: days)
  "threshold": 50.0,                               // [REQ] Float: Critical trip threshold ceiling (unit: index)
  "confidence": 0.68,                              // [REQ] Float: Linear projection confidence (unit: 0.0–1.0)
  "model_version": "1.0.4"                         // [REQ] String
}
```

#### 4.6 `GET /ml/explain/{well_id}`
* **Query Parameters**: `output` [OPT: "fault"|"anomaly"|"health"]
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "output": "fault",                               // [REQ] String: Explained target variable
  "timestamp": "2026-09-17T11:28:47.329365Z",      // [REQ] String
  "base_value": 0.20,                              // [REQ] Float: SHAP expected baseline value (unit: index)
  "contributions": [                               // [REQ] Array[Object]: Feature attribution vector
    { "feature": "amp_a", "value": 35.7, "shap": 0.31 },         // value unit: A, shap: unitless weight
    { "feature": "freq_hz", "value": 53.1, "shap": 0.09 },       // value unit: Hz, shap: unitless weight
    { "feature": "motor_temp_c", "value": 87.71, "shap": 0.18 } // value unit: °C, shap: unitless weight
  ],
  "model_version": "3.0.1",                        // [REQ] String
  "confidence": 0.85                               // [REQ] Float
}
```

---

### Domain 5: Dashboard Plots API (`/plots/*`)

#### 5.1 `GET /plots/{well_id}/{plot_id}`
* **Supported `plot_id` Values**: `health_trajectory`, `anomaly_trend`, `pressure_corridor`, `motor_load_trend`, `production_decline`
* **Error Behavior**: Unknown `plot_id` returns `404 Not Found` (`PLOT_NOT_FOUND`).
* **Verbatim Response (`health_trajectory`)**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "plot_id": "health_trajectory",                  // [REQ] String
  "start": "2026-09-06T00:00:00Z",                 // [REQ] String
  "end": "2026-09-13T00:00:00Z",                   // [REQ] String
  "series": [                                      // [REQ] Array[Object]: Plottable data lines
    {
      "name": "health_score",                      // [REQ] String
      "unit": "0-100",                             // [REQ] String: Explicit engineering unit
      "points": [                                  // [REQ] Array[Array]: [ISO-8601 timestamp, float value]
        ["2026-09-06T00:00:00Z", 78.2],
        ["2026-09-07T00:00:00Z", 77.5],
        ["2026-09-08T00:00:00Z", 76.9],
        ["2026-09-09T00:00:00Z", 75.8],
        ["2026-09-10T00:00:00Z", 74.3],
        ["2026-09-11T00:00:00Z", 73.1],
        ["2026-09-12T00:00:00Z", 72.0],
        ["2026-09-13T00:00:00Z", 71.4]
      ]
    }
  ]
}
```

* **Verbatim Response (`pressure_corridor`)**:
```json
{
  "well_id": "FS-17",
  "plot_id": "pressure_corridor",
  "start": "2026-09-06T00:00:00Z",
  "end": "2026-09-13T00:00:00Z",
  "series": [
    {
      "name": "intake_pressure_psi",
      "unit": "PSI",
      "points": [["2026-09-06T00:00:00Z", 420.0], ["2026-09-13T00:00:00Z", 395.4]]
    },
    {
      "name": "discharge_pressure_psi",
      "unit": "PSI",
      "points": [["2026-09-06T00:00:00Z", 1920.0], ["2026-09-13T00:00:00Z", 1883.1]]
    }
  ]
}
```

---

### Domain 6: Holistic & Fleet KPIs (`/kpi/*`)

#### 6.1 `GET /kpi/{well_id}` (Single-Well Headline KPI Snapshot)
* **Verbatim Response**:
```json
{
  "well_id": "FS-17",                              // [REQ] String
  "timestamp": "2026-09-13T10:37:40Z",             // [REQ] String
  "kpis": {                                        // [REQ] Object: Multi-disciplinary KPI bundle
    "oil_rate_bopd": 399.1,                        // [REQ] Float: Net oil recovery rate (unit: BOPD)
    "water_cut_pct": 0.0,                          // [REQ] Float: Water fraction (unit: %)
    "liquid_rate_bpd": 399.1,                      // [REQ] Float: Total liquid discharge (unit: BPD)
    "gas_rate_mscfd": 119.7,                       // [REQ] Float: Solution gas breakout (unit: MSCFD)
    "motor_load_pct": 102.5,                       // [REQ] Float: Current load percentage (unit: %)
    "energy_variance_pct": 29.23,                  // [REQ] Float: Hydraulic vs electric variance (unit: %)
    "health_score": 71.4,                          // [REQ] Float: Composite health index (unit: 0-100)
    "anomaly_score": 0.72                          // [REQ] Float: Multi-parameter anomaly score (unit: 0.0-1.0)
  },
  "status": "running",                             // [REQ] String: "running" | "tripped"
  "alarm_count": 1                                 // [REQ] Integer: Number of active alarms
}
```

#### 6.2 `GET /kpi/fleet` (Fleet Overview)
* **Query Parameters**: `cluster` [OPT], `status` [OPT: "running"|"tripped"]
* **Verbatim Response**:
```json
{
  "timestamp": "2026-09-13T10:37:40Z",             // [REQ] String
  "well_count": 14,                                // [REQ] Integer: Count of matching wells
  "wells": [                                       // [REQ] Array[Object]: 14 wells summary
    {
      "well_id": "FS-17",                          // [REQ] String
      "status": "running",                         // [REQ] String: "running" | "tripped"
      "oil_rate_bopd": 399.1,                      // [REQ] Float (unit: BOPD)
      "health_score": 71.4,                        // [REQ] Float (unit: index)
      "alarm_count": 1                             // [REQ] Integer (unit: count)
    },
    {
      "well_id": "FNW-01",
      "status": "tripped",
      "oil_rate_bopd": 0.0,
      "health_score": 22.8,
      "alarm_count": 3
    }
  ]
}
```

#### 6.3 Dedicated Metric Sub-endpoints (`/kpi/{well_id}/{metric}`)
* Calling `/kpi/{well_id}/gross-liquid-rate`, `/kpi/{well_id}/net-oil-rate`, `/kpi/{well_id}/water-cut`, or `/kpi/{well_id}/motor-load` routes directly to the corresponding rich KPI Card object documented in Section 5.

---

## 5. Full 17-Card Catalog Dump & Agent Operational Reasoning Mapping

Every single card available in `GET /cards/catalog` and `GET /cards/{well_id}/{card_id}` is listed below verbatim.

### 5.1 Structure of an Individual Card Response (`GET /cards/{well_id}/{card_id}`)
Every card response is guaranteed to include:
```json
{
  "well_id": "FS-17",
  "timestamp": "2026-09-13T10:37:40Z",
  "card_id": "gross-liquid-rate",
  "component_id": "section-production-kpi-liquid-rate",
  "widget_title": "Gross Liquid Rate",
  "widget_type": "ribbon_card",
  "value": 399.1,
  "unit": "BPD",
  "status_band": "NOMINAL",
  "thresholds": {
    "low_critical": 50.0,
    "low_warning": 200.0,
    "high_warning": 2500.0,
    "high_critical": 3500.0
  },
  "representation": "Total virtual-metered volumetric liquid production rate (crude oil plus formation water) discharged by the pump.",
  "plot_style": "High-contrast cyan numeric display (1.65rem mono font) with BPD unit tag and subtitle 'Virtual Metered Total Flow'.",
  "agent_guidance": "Consult this card when evaluating well capacity, production deferment, or reservoir inflow issues. A sudden drop below 50 BPD indicates a pump trip, pump-off, or severed shaft."
}
```

### 5.2 The 17-Card Master Registry Table

| Index | `card_id` | `component_id` | Unit | Widget Type | Applicable Operational Objective | Required Data Sources | Agent Action Guidance |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `gross-liquid-rate` | `section-production-kpi-liquid-rate` | BPD | `ribbon_card` | `OP01_CURRENT_STATUS`, `OP05_PRODUCTION_OPTIMIZATION` | VFM flow model | Sudden drop < 50 BPD signals trip, broken shaft, or severe underload pump-off. |
| **02** | `net-oil-rate` | `section-production-kpi-oil-rate` | BOPD | `ribbon_card` | `OP05_PRODUCTION_OPTIMIZATION` | VFM flow + water cut | Use for commercial recovery and reservoir drainage monitoring. |
| **03** | `water-cut` | `section-production-kpi-water-cut` | BPWD / % | `ribbon_card` | `OP02_FAULT_DIAGNOSIS`, `OP05_PRODUCTION_OPTIMIZATION` | VFM + fluid analysis | High cut (>75%) increases fluid density (SG), elevating motor current and friction head. |
| **04** | `associated-gas` | `section-production-kpi-associated-gas` | MSCFD | `ribbon_card` | `OP02_FAULT_DIAGNOSIS` (Gas Lock) | VFM GOR calculation | High gas rate (>250 MSCFD) at low suction causes gas locking, cavitation, and current hunting. |
| **05** | `production-deferment` | `section-production-kpi-deferment` | BPD | `ribbon_card` | `OP01_CURRENT_STATUS` (Triage) | Trip status + capacity | When well trips, entire nominal capacity is registered as deferment until restart. |
| **06** | `energy-balance` | `section-production-kpi-energy-balance` | % / HP | `ribbon_card` | `OP04_SENSOR_VALIDATION` | Hydraulic HP vs Electric kW | Variance > 15% signals sensor drift, PVT property shift, or fluid calibration error. |
| **07** | `health-score` | `section-summary-health-assessment` | 0-100 | `gauge_card` | `OP01_CURRENT_STATUS`, `OP03_RUL_PREDICTION` | Composite ML Health Index | Primary health rating. <75 requires mitigation; <50 indicates imminent trip danger. |
| **08** | `anomaly-score` | `section-intelligence-anomaly` | 0.0-1.0 | `metric_box` | `OP02_FAULT_DIAGNOSIS` | Isolation Forest | Early warning before alarms trigger. Score > 0.65 indicates statistical divergence. |
| **09** | `fault-classification` | `section-diagnosis-banner` | discrete | `alert_banner` | `OP02_FAULT_DIAGNOSIS` | Random Forest / XGBoost | Primary diagnostic root cause source for operator troubleshooting. |
| **10** | `motor-load` | `section-stability-motor-load` | % | `stability_card` | `OP02_FAULT_DIAGNOSIS`, `OP05_PRODUCTION_OPTIMIZATION` | VFD current telemetry | >105% risks winding overheating; <30% indicates pump-off or sheared shaft. |
| **11** | `motor-temperature` | `section-stability-motor-temp` | °C | `stability_card` | `OP02_FAULT_DIAGNOSIS` (Thermal) | Downhole gauge RTD | >105°C requires immediate load reduction; >135°C is hard trip safety ceiling. |
| **12** | `vibration` | `section-stability-vibration` | g RMS | `stability_card` | `OP02_FAULT_DIAGNOSIS` (Mechanical) | Downhole accelerometer | >0.25 g indicates bearing wear or sand erosion; >0.45 g indicates severe rotor unbalance. |
| **13** | `intake-pressure` | `section-stability-intake-press` | PSI | `stability_card` | `OP01_CURRENT_STATUS`, `OP05_PRODUCTION_OPTIMIZATION` | Downhole intake gauge | Key drawdown indicator. Dropping below 150 PSI causes pump-off or gas breakout. |
| **14** | `discharge-pressure` | `section-stability-disch-press` | PSI | `stability_card` | `OP05_PRODUCTION_OPTIMIZATION` | Discharge pressure gauge | Difference between PDP and PIP determines developed Total Dynamic Head (TDH). |
| **15** | `vsd-advisor` | `section-vsd-advisor` | Hz | `advisor_card` | `OP05_PRODUCTION_OPTIMIZATION` | Head-capacity model | Recommended operating frequency setpoint to optimize flow within stability envelope. |
| **16** | `fleet-health` | `section-summary-fleet-health` | wells | `summary_box` | `OP01_CURRENT_STATUS` (Fleet Overview) | Fleet health roll-up | Monitored field tally. Use to prioritize which well needs immediate engineering action. |
| **17** | `system-ingestion` | `section-summary-ingestion-rate` | msg/s | `summary_box` | `OP04_SENSOR_VALIDATION` | Telemetry collector counter | Verifies telemetry stream liveness and historical archive integrity before reasoning. |

---

## 6. Empty vs Error Contract Matrix

This table clarifies how QoD pipelines must handle zero-data vs error conditions:

| Endpoint | Scenario | HTTP Status | Response Shape | QoD Engine Interpretation |
| :--- | :--- | :---: | :--- | :--- |
| `/historian/window` | Unknown `well_id` | **404** | `{"error": {"code": "WELL_NOT_FOUND"}}` | Asset unrecognized; abort pipeline |
| `/historian/window` | Valid well, 0 rows in window | **200** | `{"row_count": 0, "rows": []}` | Normal empty time range; no data loss |
| `/historian/window` | Window span > 30 days | **400** | `{"error": {"code": "WINDOW_TOO_LARGE"}}` | Parameter violation; shrink start/end |
| `/historian/window` | Limit > 50,000 rows | **400** | `{"error": {"code": "LIMIT_EXCEEDED"}}` | Parameter violation; reduce limit |
| `/live/telemetry/*` | MQTT Broker disconnected | **503** | `{"error": {"code": "MQTT_DISCONNECTED"}}` | Stream offline; DO NOT fabricate data |
| `/live/telemetry/*` | Valid well, packet age > 30s | **404** | `{"error": {"code": "NO_LIVE_DATA"}}` | Telemetry dropped out for this specific well |
| `/events/timeline` | Valid well, 0 events in window | **200** | `{"event_count": 0, "events": []}` | Well is completely stable; 0 alarms/trips |
| `/events/trips` | Healthy well (0 trips ever) | **200** | `{"event_count": 0, "events": []}` | Well is healthy; 0 hardware shutdowns |
| `/events/latest/{well}`| Healthy well with no trips | **200** | `{"operating_state": "running", "trip_cause": null, "alarms": ["NORMAL_OPERATION"]}` | Normal steady-state operation |
| `/cards/{well}/{card}` | Invalid/unknown `card_id` | **404** | `{"error": {"code": "CARD_NOT_FOUND"}}` | Card unregistered; check catalog |
| `/plots/{well}/{plot}` | Invalid/unknown `plot_id` | **404** | `{"error": {"code": "PLOT_NOT_FOUND"}}` | Plot type unsupported |

---

## 7. Architecture Flags & Limitations (Karpathy Audit)

> [!CAUTION]
> **Strict Verification Flags for Production Deployment:**
>
> 1. **Server 184 Historian Row Count**:
>    * During our live probe, `/historian/health` returned `row_count: 0`.
>    * **Reason**: `unlabelled.db` inside `C:\Server3_Deployment_Package\backend_service\data\` is currently empty.
>    * **Action Required**: Copy the populated 1.2 GB `unlabelled.db` (containing >704,000 records) into `backend_service\data\` on Server 184 so that `/historian/window` returns historical telemetry.
>
> 2. **Server 184 MQTT Broker Liveness**:
>    * The live API correctly enforces `HTTP 503 MQTT_DISCONNECTED` when telemetry cache is empty.
>    * TCP test to Server 1 (`192.168.1.155:1883`) passed.
>    * To have Server 184 stream continuously, ensure the background MQTT subscriber task is active in `gateway.py` lifespan and Server 1 simulator is actively transmitting.
>
> 3. **Canonical Well List Strictness**:
>    * All 14 canonical wells (`FS-17`, `FNW-01`, etc.) are recognized across all 8 domains.
>    * Do NOT query arbitrary or mock well IDs (e.g. `TEST-01`, `WELL-99`); they will be rejected with `404 WELL_NOT_FOUND`.
