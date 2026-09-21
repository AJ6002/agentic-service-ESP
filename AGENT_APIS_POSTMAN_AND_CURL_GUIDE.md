# ESP APM Agent APIs — Postman & Testing Guide
**Server**: Server 184 (Edge / Data Services Engine)  
**Consumer**: ESP Agent Service (Server 191) & Operations Command Team  
**Base Protocol**: HTTP/1.1 REST, JSON responses  
**Unified Port**: `8000` (`http://127.0.0.1:8000` or `http://192.168.1.184:8000`)  
**Security / Auth**: Open access for development / internal network (IP-filtered for `192.168.1.191`)  
**Timestamp Format**: ISO-8601 UTC (`2026-09-13T10:37:40.123456Z`)  
**Canonical Well IDs**: `FS-17`, `FS-121`, `FNW-01`, `FNW-06`, `FWS-06`, `ULFA-5`, `FS-96`, `FS-21`, `FS-06`, `FS-91`, `FSWS-001-A`, `FS-014`, `FS-016`, `FS-031`

---

## 1. Postman Quick Setup

### Postman Environment Variables
Configure an Environment in Postman named `ESP Server 184` with the following keys:

| Variable | Initial Value | Current Value | Description |
| :--- | :--- | :--- | :--- |
| `baseUrl` | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` | Server 184 API host and unified port |
| `wellId` | `FS-17` | `FS-17` | Default canonical test well |
| `trippedWellId` | `FNW-01` | `FNW-01` | Known tripped / off-nominal well for anomaly testing |
| `startTs` | `2026-08-01T00:00:00Z` | `2026-08-01T00:00:00Z` | Window start timestamp |
| `endTs` | `2026-08-30T00:00:00Z` | `2026-08-30T00:00:00Z` | Window end timestamp |

### Common Headers
```http
Accept: application/json
Content-Type: application/json
```

---

## 2. API Catalog & Endpoint Directory

```
├── /historian
│   ├── GET /historian/health                # Health & DB attachment metrics
│   ├── GET /historian/window                # Bounded raw columnar time series
│   ├── GET /historian/latest                # Latest single reading per signal
│   ├── GET /historian/aggregates            # Downsampled time-bucketed aggregates
│   └── GET /historian/coverage              # Available time ranges and gaps
├── /live
│   ├── GET /live/health                     # MQTT connection & subscriber liveness
│   ├── GET /live/telemetry/{well_id}        # Latest telemetry packet with age_sec
│   ├── GET /live/telemetry/{well_id}/recent # Ring buffer of last N seconds
│   ├── GET /live/vfm/{well_id}              # Latest Virtual Flow Metering packet
│   ├── GET /live/asset/{well_id}            # Retained pump curves & nameplate specs
│   ├── GET /live/status                     # Simulator heartbeat status
│   └── GET /live/wells                      # List of all publishing wells
├── /events
│   ├── GET /events/health                   # Events DB status and row count
│   ├── GET /events/timeline                 # Chronological event window
│   ├── GET /events/trips                    # Filtered trip cause events
│   ├── GET /events/latest/{well_id}         # Latest event for a well
│   ├── GET /events/summary                  # Aggregated counts per well
│   └── GET /events/catalog                  # Canonical trip & alarm reference data
├── /ml
│   ├── GET /ml/health                       # ML backend liveness & loaded models
│   ├── GET /ml/anomaly/{well_id}            # Isolation Forest anomaly score & threshold
│   ├── GET /ml/fault/{well_id}              # Fault classification & top-k probabilities
│   ├── GET /ml/health/{well_id}             # Composite Health Index & contributors
│   ├── GET /ml/degradation/{well_id}        # Degradation trend & days-to-threshold
│   └── GET /ml/explain/{well_id}            # SHAP feature contributions
├── /plots
│   └── GET /plots/{well_id}/{plot_id}       # Pre-computed widget time-series series
├── /kpi
│   ├── GET /kpi/{well_id}                   # Holistic live KPI snapshot for dashboard
│   ├── GET /kpi/fleet                       # Fleet-wide multi-well KPI overview
│   └── GET /kpi/{well_id}/{metric}          # Dedicated individual metric sub-endpoints
└── /cards
    ├── GET /cards/catalog                   # Complete registry of all dashboard widgets
    └── GET /cards/{well_id}/{card_id}       # Granular card payload with UI plot metadata
```

---

## 3. Historian API (`/historian/*`)

### 3.1 Health Check
- **Method**: `GET`
- **URL**: `{{baseUrl}}/historian/health`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/historian/health" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "uptime_sec": 3840,
    "db_attached": true,
    "row_count": 425493,
    "backend": "duckdb"
  }
  ```

### 3.2 Time-Series Window
- **Method**: `GET`
- **URL**: `{{baseUrl}}/historian/window?well_id={{wellId}}&start={{startTs}}&end={{endTs}}&signals=amp_a,freq_hz,motor_temp_c,int_prs_psi&limit=100`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/historian/window?well_id=FS-17&start=2026-08-01T00:00:00Z&end=2026-08-30T00:00:00Z&signals=amp_a,freq_hz,motor_temp_c,int_prs_psi&limit=10" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "start": "2026-08-01T00:00:00Z",
    "end": "2026-08-30T00:00:00Z",
    "row_count": 10,
    "truncated": false,
    "columns": ["timestamp", "amp_a", "freq_hz", "motor_temp_c", "int_prs_psi"],
    "units": {
      "amp_a": "A",
      "freq_hz": "Hz",
      "motor_temp_c": "°C",
      "int_prs_psi": "PSI"
    },
    "rows": [
      ["2026-08-27T07:20:21.749959Z", 35.7, 53.1, 87.71, 395.4],
      ["2026-08-27T07:20:22.749959Z", 35.8, 53.1, 87.72, 395.1]
    ]
  }
  ```

### 3.3 Latest Signal Readings
- **Method**: `GET`
- **URL**: `{{baseUrl}}/historian/latest?well_id={{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/historian/latest?well_id=FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-08-27T07:20:21.749959Z",
    "values": {
      "int_prs_psi": 395.4,
      "disch_prs_psi": 1883.1,
      "int_temp_c": 64.53,
      "motor_temp_c": 87.71,
      "vibration_g": 0.082,
      "volt_v": 594.1,
      "amp_a": 35.7,
      "freq_hz": 53.1,
      "leak_current_ct": 15.0,
      "dhg_current_ma": 10.7,
      "whp_psi": 180.3,
      "flp_psi": 171.0,
      "ap_psi": 155.5,
      "vfd_sts": true
    }
  }
  ```

### 3.4 Aggregates (Downsampled Bucketing)
- **Method**: `GET`
- **URL**: `{{baseUrl}}/historian/aggregates?well_id={{wellId}}&start={{startTs}}&end={{endTs}}&signals=amp_a,motor_temp_c&bucket=1h&agg=avg`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/historian/aggregates?well_id=FS-17&start=2026-08-01T00:00:00Z&end=2026-08-30T00:00:00Z&signals=amp_a,motor_temp_c&bucket=1h&agg=avg" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "bucket": "1h",
    "agg": "avg",
    "start": "2026-08-01T00:00:00Z",
    "end": "2026-08-30T00:00:00Z",
    "columns": ["bucket", "amp_a", "motor_temp_c"],
    "units": { "amp_a": "A", "motor_temp_c": "°C" },
    "rows": [
      ["2026-08-27 07:00:00Z", 35.72, 87.68],
      ["2026-08-27 08:00:00Z", 35.81, 87.75]
    ]
  }
  ```

### 3.5 Telemetry Coverage
- **Method**: `GET`
- **URL**: `{{baseUrl}}/historian/coverage?well_id={{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/historian/coverage?well_id=FS-17" -H "Accept: application/json"
  ```

---

## 4. Live Data API (MQTT Facade) (`/live/*`)

> **Note on Strict Error Handling**: When the MQTT broker at `192.168.1.155:1883` is offline or disconnected, all `/live/telemetry/*` and `/live/vfm/*` endpoints immediately return **HTTP 503** with code `MQTT_DISCONNECTED`.

### 4.1 Live Health & Broker Liveness
- **Method**: `GET`
- **URL**: `{{baseUrl}}/live/health`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/live/health" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "mqtt_connected": true,
    "broker": "192.168.1.155:1883",
    "wells_subscribed": 14,
    "last_message_ts": "2026-09-13T10:37:40Z"
  }
  ```

### 4.2 Most Recent Telemetry Packet
- **Method**: `GET`
- **URL**: `{{baseUrl}}/live/telemetry/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/live/telemetry/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-09-13T10:37:40.270090Z",
    "age_sec": 0.82,
    "manufacturer": "Borets / Levare",
    "model_id": "B400-400",
    "measurements": {
      "int_prs_psi": 395.4,
      "disch_prs_psi": 1883.1,
      "int_temp_c": 64.53,
      "motor_temp_c": 87.71,
      "vibration_g": 0.082,
      "volt_v": 594.1,
      "amp_a": 35.7,
      "freq_hz": 53.1
    },
    "source": "mqtt",
    "schema_version": "1.0.0"
  }
  ```

### 4.3 Retained Asset Nameplate & Curve Coeffs
- **Method**: `GET`
- **URL**: `{{baseUrl}}/live/asset/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/live/asset/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-01-17T00:00:00Z",
    "asset": {
      "pump_type": "B400-400",
      "stages": 342,
      "motor_hp_50hz": 53.0,
      "volt_50hz": 1669.0,
      "rated_amp_a": 20.3,
      "cluster": "SB247",
      "vsd_model": "VECTOR PLUS",
      "pump_curve_coeffs": { "A": -0.00012, "B": -0.01, "C": -0.78, "D": 440.0 }
    }
  }
  ```

### 4.4 Publishing Wells List
- **Method**: `GET`
- **URL**: `{{baseUrl}}/live/wells`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/live/wells" -H "Accept: application/json"
  ```

---

## 5. Events API (`/events/*`)

### 5.1 Events Health
- **Method**: `GET`
- **URL**: `{{baseUrl}}/events/health`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/events/health" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "row_count": 370,
    "last_event_ts": "2026-09-13T10:39:15Z"
  }
  ```

### 5.2 Chronological Event Timeline
- **Method**: `GET`
- **URL**: `{{baseUrl}}/events/timeline?well_id={{trippedWellId}}&start=2026-09-01T00:00:00Z&end=2026-09-20T00:00:00Z&limit=10`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/events/timeline?well_id=FNW-01&start=2026-09-01T00:00:00Z&end=2026-09-20T00:00:00Z&limit=10" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FNW-01",
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-09-20T00:00:00Z",
    "event_count": 5,
    "events": [
      {
        "event_id": "EV-20260913-100000-1010",
        "timestamp": "2026-09-13T10:00:00Z",
        "well_id": "FNW-01",
        "operating_state": "tripped",
        "scenario": "dry_well_pump_off",
        "trip_cause": "UNDERLOAD_PUMP_OFF",
        "alarms": ["LOW_INTAKE_PRESSURE", "UNDERLOAD", "TRIP_UNDERLOAD_PUMP_OFF"],
        "event_type": "trip"
      }
    ]
  }
  ```

### 5.3 Filtered Trips Only
- **Method**: `GET`
- **URL**: `{{baseUrl}}/events/trips?well_id={{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/events/trips?well_id=FS-17" -H "Accept: application/json"
  ```

### 5.4 Events Summary by Well
- **Method**: `GET`
- **URL**: `{{baseUrl}}/events/summary`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/events/summary" -H "Accept: application/json"
  ```

### 5.5 Canonical Reference Catalog
- **Method**: `GET`
- **URL**: `{{baseUrl}}/events/catalog`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/events/catalog" -H "Accept: application/json"
  ```

---

## 6. ML Results & Plots API (`/ml/*`, `/plots/*`)

### 6.1 Anomaly Score
- **Method**: `GET`
- **URL**: `{{baseUrl}}/ml/anomaly/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ml/anomaly/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-09-13T10:37:38Z",
    "score": 0.72,
    "threshold": 0.65,
    "is_anomalous": true,
    "model_id": "isolation_forest_v2",
    "model_version": "2.1.0",
    "feature_version": "1.3.0",
    "confidence": 0.83
  }
  ```

### 6.2 Fault Classification & Probabilities
- **Method**: `GET`
- **URL**: `{{baseUrl}}/ml/fault/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ml/fault/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-09-13T10:37:38Z",
    "fault_class": "MOTOR_OVERLOAD",
    "probability": 0.78,
    "top_k": [
      { "fault_class": "MOTOR_OVERLOAD", "probability": 0.78 },
      { "fault_class": "OVERLOAD_SOLIDS", "probability": 0.15 },
      { "fault_class": "HIGH_VISCOSITY", "probability": 0.07 }
    ],
    "model_id": "fault_classifier_v3",
    "model_version": "3.0.1",
    "feature_version": "1.3.0",
    "confidence": 0.78
  }
  ```

### 6.3 Health Score & Contributors
- **Method**: `GET`
- **URL**: `{{baseUrl}}/ml/health/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ml/health/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-09-13T10:37:38Z",
    "health_score": 71.4,
    "band": "DEGRADED",
    "contributors": [
      { "signal": "motor_temp_c", "contribution": -0.18 },
      { "signal": "vibration_g", "contribution": -0.11 },
      { "signal": "amp_a", "contribution": -0.06 }
    ],
    "model_id": "health_v1",
    "model_version": "1.0.4",
    "confidence": 0.88
  }
  ```

### 6.4 Degradation Trajectory & RUL
- **Method**: `GET`
- **URL**: `{{baseUrl}}/ml/degradation/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ml/degradation/FS-17" -H "Accept: application/json"
  ```

### 6.5 SHAP Feature Contributions
- **Method**: `GET`
- **URL**: `{{baseUrl}}/ml/explain/{{wellId}}?output=fault`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ml/explain/FS-17?output=fault" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "output": "fault",
    "timestamp": "2026-09-13T10:37:38Z",
    "base_value": 0.20,
    "contributions": [
      { "feature": "amp_a", "value": 35.7, "shap": 0.31 },
      { "feature": "freq_hz", "value": 53.1, "shap": 0.09 },
      { "feature": "motor_temp_c", "value": 87.71, "shap": 0.18 }
    ],
    "model_version": "3.0.1",
    "confidence": 0.85
  }
  ```

### 6.6 Pre-Computed Dashboard Plots
- **Method**: `GET`
- **URL**: `{{baseUrl}}/plots/{{wellId}}/health_trajectory`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/plots/FS-17/health_trajectory" -H "Accept: application/json"
  ```

---

## 7. Holistic & Fleet KPI Endpoints (`/kpi/*`)

### 7.1 Single Well Holistic Headline KPI Snapshot
- **Method**: `GET`
- **URL**: `{{baseUrl}}/kpi/{{wellId}}`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/kpi/FS-17" -H "Accept: application/json"
  ```
- **Response**:
  ```json
  {
    "well_id": "FS-17",
    "timestamp": "2026-09-13T10:37:40Z",
    "kpis": {
      "oil_rate_bopd": 399.1,
      "water_cut_pct": 0.0,
      "liquid_rate_bpd": 399.1,
      "gas_rate_mscfd": 119.7,
      "motor_load_pct": 102.5,
      "energy_variance_pct": 29.23,
      "health_score": 71.4,
      "anomaly_score": 0.72
    },
    "status": "running",
    "alarm_count": 1
  }
  ```

### 7.2 Fleet-Wide Multi-Well KPI Overview
- **Method**: `GET`
- **URL**: `{{baseUrl}}/kpi/fleet`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/kpi/fleet" -H "Accept: application/json"
  ```

---

## 8. Granular Dashboard KPI Cards & Widget Endpoints

To give the AI Agent complete context on **when to call what** and **what each visual component represents**, every dashboard card is available as a dedicated API endpoint under both `/kpi/{well_id}/*` and `/cards/{well_id}/*`.

### Dashboard Card Catalog & Reasoning Guide Table

| Card ID | Component ID | Metric & Unit | Operational Representation | When Agent Must Call It |
| :--- | :--- | :--- | :--- | :--- |
| `gross-liquid-rate` | `section-production-kpi-liquid-rate` | Flow (BPD) | Total volumetric liquid rate (oil + water) lifted by the ESP. | Inflow analysis; sudden drop to 0 signals trip/severed shaft. |
| `net-oil-rate` | `section-production-kpi-oil-rate` | Crude (BOPD) | Net commercial crude oil recovery volume after water separation. | Economic triage and reservoir depletion monitoring. |
| `water-cut` | `section-production-kpi-water-cut` | Cut (%) & BPWD | Percentage fraction of formation water in the fluid stream. | Diagnosing fluid specific gravity increase & emulsion drag. |
| `associated-gas` | `section-production-kpi-associated-gas` | Gas (MSCFD) | Solution/casing gas breakout rate calculated from GOR. | Diagnosing pump gas locking, current hunting, or surging. |
| `production-deferment` | `section-production-kpi-deferment` | Lost (BPD) | Daily lost production volume due to trips or choke backpressure. | Quantifying production loss and downtime impact. |
| `energy-balance` | `section-production-kpi-energy-balance` | Variance (%) | Hydraulic power delivered vs electrical power absorbed. | Verifying VFM accuracy. Variance >15% signals sensor drift. |
| `health-score` | `section-summary-health-assessment` | Index (0-100) | Composite ESP health reflecting thermal, vib & electrical state. | Primary health indicator; <75 degraded, <50 trip danger. |
| `anomaly-score` | `section-intelligence-anomaly` | Score (0.0-1.0) | Multi-sensor divergence from statistical baseline. | Early warning indicator before hard alarms fire (>0.65). |
| `fault-classification` | `section-diagnosis-banner` | Categorical | Top root cause classification (e.g. MOTOR_OVERLOAD). | Diagnostic reasoning and operator mitigation plans. |
| `motor-load` | `section-stability-motor-load` | Current (%) | Motor amps draw relative to rated nameplate full-load current. | Electrical thermal stress; >105% risks winding burnout. |
| `motor-temperature` | `section-stability-motor-temp` | Temp (°C) | Downhole motor internal winding operating temperature. | Critical thermal protection; >110°C requires load reduction. |
| `vibration` | `section-stability-vibration` | Vib (G RMS) | Mechanical vibration acceleration measured downhole. | Mechanical integrity, cavitation, bearing wear, or bent shaft. |
| `intake-pressure` | `section-stability-intake-press` | Suction (PSI) | Reservoir fluid pressure at pump intake (PIP). | Drawdown & inflow analysis; <150 PSI causes cavitation. |
| `discharge-pressure` | `section-stability-disch-press` | Head (PSI) | Pressure generated at pump discharge head (PDP). | Computing Total Dynamic Head (TDH = PDP - PIP). |
| `vsd-advisor` | `section-vsd-advisor` | Speed (Hz) | Recommended operating frequency setpoint. | Evaluating frequency adjustments to optimize production. |
| `fleet-health` | `section-summary-fleet-health` | Fleet counts | Count of healthy vs anomalous wells across monitored field. | Fleet-wide prioritization and triage workflow. |
| `system-ingestion` | `section-summary-ingestion-rate` | Msg/s & count | Ingestion packet rate and total historical records stored. | System liveness and telemetry freshness validation. |

---

### 8.1 Card Catalog Endpoint
- **Method**: `GET`
- **URL**: `{{baseUrl}}/cards/catalog`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/catalog" -H "Accept: application/json"
  ```

---

### 8.2 Individual Card Endpoint Examples

#### Gross Liquid Rate Card
- **Endpoint 1**: `GET {{baseUrl}}/kpi/{{wellId}}/gross-liquid-rate`
- **Endpoint 2**: `GET {{baseUrl}}/cards/{{wellId}}/gross-liquid-rate`
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/gross-liquid-rate" -H "Accept: application/json"
  ```
- **Response**:
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

#### Net Oil Rate Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/net-oil-rate" -H "Accept: application/json"
  ```

#### Produced Water & Water Cut Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/water-cut" -H "Accept: application/json"
  ```

#### Production Deferment Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/production-deferment" -H "Accept: application/json"
  ```

#### Energy Balance Status & Variance Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/energy-balance" -H "Accept: application/json"
  ```

#### ESP Health Index Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/health-score" -H "Accept: application/json"
  ```

#### Motor Load Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/motor-load" -H "Accept: application/json"
  ```

#### Motor Temperature Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/motor-temperature" -H "Accept: application/json"
  ```

#### Pump Intake Pressure (PIP) Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/intake-pressure" -H "Accept: application/json"
  ```

#### Vibration Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/vibration" -H "Accept: application/json"
  ```

#### VSD Frequency Advisor Card
- **cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/cards/FS-17/vsd-advisor" -H "Accept: application/json"
  ```

---

## 9. Error Envelope & Status Codes

All endpoints follow the standard error contract:

```json
{
  "error": {
    "code": "WINDOW_TOO_LARGE",
    "message": "Requested window exceeds 30 days",
    "detail": {
      "requested_days": 45,
      "max_days": 30
    }
  }
}
```

| HTTP Status | Error Code | Meaning | Remediation |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | `WINDOW_TOO_LARGE` | Requested window span > 30 days | Shorten `start` and `end` window span |
| `400 Bad Request` | `LIMIT_EXCEEDED` | Requested `limit` > 50,000 rows | Lower requested `limit` parameter |
| `404 Not Found` | `WELL_NOT_FOUND` | Provided `well_id` is unknown | Check against `/live/wells` or canonical well list |
| `404 Not Found` | `NO_DATA` / `NO_EVENTS` | Well known but has zero rows in window | Check coverage via `/historian/coverage` |
| `404 Not Found` | `CARD_NOT_FOUND` | Unknown `card_id` | Call `/cards/catalog` for registered cards |
| `503 Service Unavailable` | `MQTT_DISCONNECTED` | MQTT broker at `192.168.1.155` unreachable | Verify network route to Server 1 / start Mosquitto |
