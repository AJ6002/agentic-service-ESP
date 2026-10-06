# Sprint 3 Plan: Fleet Tools + Adapter Aggregation

```yaml
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
docs_root: docs
created_at: 2026-10-05
updated_at: 2026-10-05
```

---

## 1. Goal Capsule

Implement query-time PostgreSQL aggregation for all Phase 5 Fleet Tools in `agent_service`, replacing all hardcoded constants with real live database aggregates:
1. **`fetch_fleet_kpi`**: Aggregate production rate (`SUM(flow_rate_bpd)`), fleet health score (`AVG(health_score)`), and operational states (`COUNT` of running vs down wells) across active fleet assets.
2. **`fetch_fleet_health`**: Return per-well health scores ranked from worst to best with health bands (`CRITICAL`, `DEGRADED`, `HEALTHY`), asset count, and worst/best callouts.
3. **`fetch_fleet_events`**: Aggregate operational transitions, trips, and alarms across all wells in a time window from `events` and telemetry tables.
4. **Tool Gateway & Policy Gate Registration**: Register `get_fleet_kpi`, `get_fleet_health`, and `get_fleet_events` as authorized read-only tools exempt from `asset_id` requirement, integrate with QoD validation and Evidence Formatter.

---

## 2. Technical Context & Exact File References

- **KPI Adapter**: [`agent_service/app/gateway/adapters/kpi.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/kpi.py)
  - `fetch_kpi(well_id)` (lines 17-94)
  - `fetch_fleet_kpi()` (lines 96-118) — needs rewrite from hardcoded 88.5 / 15420.0 to live SQL aggregation.
  - `fetch_fleet_health()` — new function.
- **Events Adapter**: [`agent_service/app/gateway/adapters/events.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/events.py)
  - `fetch_events_timeline(well_id)` (lines 18-106)
  - `fetch_events_trips(well_id)` (lines 108-188)
  - `fetch_fleet_events(start, end, limit)` — new function querying across all wells.
- **Tool Gateway**: [`agent_service/app/gateway/tool_gateway.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/tool_gateway.py)
  - Exemption set from `asset_id` (lines 96-106).
  - Tool dispatch matchers (lines 115-310).
- **Policy Gate**: [`agent_service/app/policy/policy_gate.py`](file:///a:/TAS-AI/ESP/agent_service/app/policy/policy_gate.py)
  - `ALLOWED_TOOLS` set (lines 11-37).
- **QoD Engine**: [`agent_service/app/evidence/qod.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/qod.py)
  - `_REQUIRED_FIELDS` (lines 44-70) and `_TOOL_TO_DOMAIN` (lines 73-100).
- **Evidence Formatter**: [`agent_service/app/evidence/formatter.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/formatter.py)
  - Attributed numeric facts (`FormattedValue`) and events (`FormattedEventRecord`).
- **PostgreSQL Database Tables**:
  - `opg_well_telemetry`: `well_id`, `flow_rate_bpd`, `operating_state`, `trip_cause`, `timestamp`.
  - `esp_unified_assessments`: `well_id`, `overall_status`, `anomaly_score`, `rul_hours`, `timestamp`.
  - `events`: `event_id`, `well_id`, `timestamp`, `operating_state`, `scenario`, `trip_cause`, `alarms`, `severity`.
  - `asset_registry`: `well_id`, `is_active`, `bep_rate_bpd`.

---

## 3. Implementation Units

### U1: Rewrite `fetch_fleet_kpi` with Live PostgreSQL Aggregation
- **File**: [`agent_service/app/gateway/adapters/kpi.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/kpi.py#L96-L118)
- **SQL Aggregation Design**:
  ```sql
  WITH latest_telem AS (
      SELECT DISTINCT ON (well_id) well_id, flow_rate_bpd, operating_state, timestamp
      FROM opg_well_telemetry
      ORDER BY well_id, timestamp DESC
  ),
  latest_ml AS (
      SELECT DISTINCT ON (well_id) well_id, overall_status, anomaly_score
      FROM esp_unified_assessments
      ORDER BY well_id, timestamp DESC
  )
  SELECT 
      COUNT(t.well_id) AS total_wells,
      COUNT(t.well_id) FILTER (WHERE LOWER(t.operating_state) = 'running') AS running_wells,
      COUNT(t.well_id) FILTER (WHERE LOWER(t.operating_state) != 'running') AS down_wells,
      COALESCE(SUM(t.flow_rate_bpd), 0.0) AS total_production_bpd,
      COALESCE(AVG(
          CASE 
              WHEN UPPER(m.overall_status) LIKE '%CRITICAL%' OR UPPER(m.overall_status) LIKE '%ALARM%' THEN 42.0
              WHEN UPPER(m.overall_status) LIKE '%WARN%' OR UPPER(m.overall_status) LIKE '%DEGRADED%' THEN 68.0
              ELSE 92.0
          END
      ), 90.0) AS avg_health_score
  FROM latest_telem t
  LEFT JOIN latest_ml m ON m.well_id = t.well_id;
  ```
- **Return Contract**:
  ```json
  {
    "status": "OK",
    "total_wells": 10,
    "running_wells": 9,
    "down_wells": 1,
    "fleet_health_score": 67.8,
    "total_production_bpd": 8560.5,
    "source": "POSTGRESQL"
  }
  ```
- **Verification**: Zero hardcoded values; returns actual calculated values from PostgreSQL.

---

### U2: Implement `fetch_fleet_health` Adapter
- **File**: [`agent_service/app/gateway/adapters/kpi.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/kpi.py)
- **SQL Ranking Design**:
  ```sql
  WITH latest_ml AS (
      SELECT DISTINCT ON (well_id) well_id, overall_status, anomaly_score, timestamp
      FROM esp_unified_assessments
      ORDER BY well_id, timestamp DESC
  )
  SELECT 
      well_id,
      CASE 
          WHEN UPPER(overall_status) LIKE '%CRITICAL%' OR UPPER(overall_status) LIKE '%ALARM%' THEN 42.0
          WHEN UPPER(overall_status) LIKE '%WARN%' OR UPPER(overall_status) LIKE '%DEGRADED%' THEN 68.0
          ELSE 92.0
      END AS health_score,
      CASE 
          WHEN UPPER(overall_status) LIKE '%CRITICAL%' OR UPPER(overall_status) LIKE '%ALARM%' THEN 'CRITICAL'
          WHEN UPPER(overall_status) LIKE '%WARN%' OR UPPER(overall_status) LIKE '%DEGRADED%' THEN 'DEGRADED'
          ELSE 'HEALTHY'
      END AS band
  FROM latest_ml
  ORDER BY health_score ASC, well_id ASC;
  ```
- **Return Contract**:
  ```json
  {
    "status": "OK",
    "wells": [
      {"well_id": "FS-006", "health_score": 42.0, "band": "CRITICAL"},
      {"well_id": "FNW-001", "health_score": 68.0, "band": "DEGRADED"},
      {"well_id": "FS-004", "health_score": 68.0, "band": "DEGRADED"}
    ],
    "count": 10,
    "worst": "FS-006",
    "best": "FS-018",
    "source": "POSTGRESQL"
  }
  ```
- **Verification**: Wells ordered by `health_score` ascending (worst first); `worst` and `best` correctly identify extreme wells.

---

### U3: Implement `fetch_fleet_events` Adapter
- **File**: [`agent_service/app/gateway/adapters/events.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/events.py)
- **Design**:
  - `fetch_fleet_events(start: Optional[str] = None, end: Optional[str] = None, limit: int = 100, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]`
  - Query explicit `events` table for window:
    ```sql
    SELECT event_id, well_id, timestamp, operating_state, scenario, trip_cause, alarms, severity
    FROM events
    WHERE timestamp >= %s AND timestamp <= %s
    ORDER BY timestamp DESC
    LIMIT %s;
    ```
  - If `events` table returns 0 rows, fallback to `opg_well_telemetry` for transitions:
    ```sql
    SELECT well_id, timestamp, operating_state, scenario, trip_cause, alarms
    FROM opg_well_telemetry
    WHERE timestamp >= %s AND timestamp <= %s
      AND (trip_cause IS NOT NULL AND trip_cause != '' OR operating_state IN ('tripped', 'stopped'))
    ORDER BY timestamp DESC
    LIMIT %s;
    ```
- **Return Contract**:
  ```json
  {
    "status": "OK",
    "events": [
      {
        "well_id": "FS-016",
        "event_id": "EV-20261004-185505-FS-016-130",
        "event_type": "trip",
        "operating_state": "tripped",
        "scenario": "GAS_INTERFERENCE",
        "trip_cause": "UNDERLOAD_PUMP_OFF",
        "alarms": ["UNDERLOAD"],
        "severity": "CRITICAL",
        "timestamp": "2026-10-05T00:25:04Z",
        "ts": "2026-10-05T00:25:04Z"
      }
    ],
    "count": 5,
    "temporal_meta": { ... },
    "source": "POSTGRESQL"
  }
  ```

---

### U4: Register Tools in Gateway, Policy Gate, QoD & Formatter
1. **Tool Gateway** ([`agent_service/app/gateway/tool_gateway.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/tool_gateway.py)):
   - Exemption check: Add `"get_fleet_kpi"`, `"get_fleet_health"`, `"get_fleet_events"` to the set of tools exempt from requiring `asset_id`.
   - Dispatch map:
     - `get_fleet_kpi`: `await kpi.fetch_fleet_kpi(client=client)`
     - `get_fleet_health`: `await kpi.fetch_fleet_health(client=client)`
     - `get_fleet_events`: `start`, `end`, `limit` extracted from `args`, `await events.fetch_fleet_events(start=start, end=end, limit=limit, client=client)`
2. **Policy Gate** ([`agent_service/app/policy/policy_gate.py`](file:///a:/TAS-AI/ESP/agent_service/app/policy/policy_gate.py)):
   - Add `"get_fleet_kpi"`, `"get_fleet_health"`, `"get_fleet_events"` to `ALLOWED_TOOLS`.
3. **QoD Engine** ([`agent_service/app/evidence/qod.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/qod.py)):
   - Add `"get_fleet_kpi": []`, `"get_fleet_health": []`, `"get_fleet_events": []` to `_REQUIRED_FIELDS`.
   - Add `"get_fleet_kpi": "kpi"`, `"get_fleet_health": "ml"`, `"get_fleet_events": "events"` to `_TOOL_TO_DOMAIN`.
4. **Evidence Formatter** ([`agent_service/app/evidence/formatter.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/formatter.py)):
   - Format numeric fleet values: `total_production_bpd`, `fleet_health_score`, `running_wells`, `down_wells`.
   - Format fleet events into `FormattedEventRecord` list.

---

### U5: Comprehensive Unit & Integration Tests
- **File**: `agent_service/tests/test_fleet_tools.py`
- **Test Scenarios**:
  1. `test_fetch_fleet_kpi_live_aggregation`: Verifies `fetch_fleet_kpi()` computes non-hardcoded aggregates from PostgreSQL (`total_wells > 0`, `total_production_bpd > 0`, `running_wells + down_wells == total_wells`).
  2. `test_fetch_fleet_health_ranking`: Verifies `fetch_fleet_health()` returns ranked list with `worst`, `best`, valid `health_score` (0-100), and valid `band`.
  3. `test_fetch_fleet_events_query`: Verifies `fetch_fleet_events()` returns event records with timestamps, well IDs, and trip causes.
  4. `test_tool_gateway_fleet_dispatch_without_asset_id`: Verifies `execute_tool_call` executes `get_fleet_kpi`, `get_fleet_health`, and `get_fleet_events` without `asset_id` and returns `status == "OK"`.
  5. `test_policy_gate_approves_fleet_tools`: Verifies `validate_plan()` approves `PlanArtifact` containing fleet calls for `OP08`, `OP09`, `OP13`.

---

## 4. Verification Contract & Definition of Done

1. **Adapter Level**:
   ```python
   kpi_res = await fetch_fleet_kpi()
   assert kpi_res["status"] == "OK"
   assert kpi_res["total_production_bpd"] > 0
   assert kpi_res["total_wells"] > 0
   
   health_res = await fetch_fleet_health()
   assert health_res["status"] == "OK"
   assert len(health_res["wells"]) > 0
   assert health_res["worst"] is not None
   
   events_res = await fetch_fleet_events()
   assert events_res["status"] == "OK"
   assert "events" in events_res
   ```
2. **Tool Gateway Level**:
   ```python
   res = await execute_tool_call(PlanCall(seq=1, tool="get_fleet_kpi", args={}))
   assert res.status == "OK"
   assert "MISSING_ASSET_ID" not in (res.error_code or "")
   ```
3. **Automated Suite**:
   ```bash
   pytest agent_service/tests/test_fleet_tools.py -v
   pytest agent_service/tests/objectives/test_manifests.py -v
   pytest agent_service/tests/test_router_fleet_sprint1.py -v
   ```
   **Pass Criteria**: All tests pass, 0 hardcoded constants, zero `asset_id` errors.
