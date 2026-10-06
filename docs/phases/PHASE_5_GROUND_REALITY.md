# Phase 5 Ground Reality: Current State Audit of ESP APM Agent Service

This document provides a factual, read-only baseline audit of the ESP APM Agent Service codebase (`agent_service/`) regarding fleet-scope and multi-asset capabilities.

---

## 1. Current Objective Coverage

The objectives config folder (`agent_service/config/objectives/`) contains 9 YAML manifest files. None of them support fleet-scope queries.

1. **`OP01_CURRENT_STATUS.yaml`** (`config/objectives/OP01_CURRENT_STATUS.yaml:1-31`)
   - `objective_id`: `OP01_CURRENT_STATUS`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_live_telemetry]`
   - `optional_evidence`: `[get_events]`
   - `default_visuals`: `[working_status_smart_fault_card]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 30).

2. **`OP02.yaml`** (`config/objectives/OP02.yaml:1-33`)
   - `objective_id`: `OP02_PRODUCTION_DECLINE_RCA`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_historian_aggregates, get_events]`
   - `optional_evidence`: `[get_current_status, get_historian_window]`
   - `default_visuals`: `[production-decline, pressure-corridor]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 32).

3. **`OP03_FAULT_DIAGNOSIS.yaml`** (`config/objectives/OP03_FAULT_DIAGNOSIS.yaml:1-42`)
   - `objective_id`: `OP03_FAULT_DIAGNOSIS`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_live_telemetry, get_historian_window]`
   - `optional_evidence`: `[get_ml_results, search_knowledge, get_fault_taxonomy, trace_causal_graph, get_events, get_trips]`
   - `default_visuals`: `[working_status_smart_fault_card, subsystem_equalizer, multi_tag_live_trends, advisor_panel_item]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 41).

4. **`OP04.yaml`** (`config/objectives/OP04.yaml:1-33`)
   - `objective_id`: `OP04_HEALTH_ASSESSMENT`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_health_index, get_historian_aggregates]`
   - `optional_evidence`: `[get_current_status, get_anomaly, get_events]`
   - `default_visuals`: `[working_status_smart_fault_card, subsystem_equalizer]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 32).

5. **`OP05.yaml`** (`config/objectives/OP05.yaml:1-34`)
   - `objective_id`: `OP05_EARLY_WARNING`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_anomaly, get_historian_aggregates]`
   - `optional_evidence`: `[get_current_status, get_health_index, get_events, get_explanation]`
   - `default_visuals`: `[working_status_smart_fault_card, subsystem_equalizer]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 33).

6. **`OP06.yaml`** (`config/objectives/OP06.yaml:1-18`)
   - `objective_id`: `OP06_KNOWLEDGE_LOOKUP`
   - `scope`: `GLOBAL`
   - `required_evidence`: `[search_knowledge]`
   - `optional_evidence`: `[]`
   - `default_visuals`: `[]`
   - Scope mentions: `scope: GLOBAL` (line 4); no asset required.

7. **`OP07_GENERAL_INQUIRY.yaml`** (`config/objectives/OP07_GENERAL_INQUIRY.yaml:1-13`)
   - `objective_id`: `OP07_GENERAL_INQUIRY`
   - `scope`: `GLOBAL`
   - `required_evidence`: `[]`
   - `optional_evidence`: `[search_knowledge]`
   - `default_visuals`: `[]`
   - Scope mentions: `scope: GLOBAL` (line 4); empty `arg_schema`.

8. **`OP14.yaml`** (`config/objectives/OP14.yaml:1-34`)
   - `objective_id`: `OP14_OPERATIONAL_HISTORY`
   - `scope`: `ASSET`
   - `required_evidence`: `[get_asset_context, get_historian_window, get_historian_aggregates, get_events]`
   - `optional_evidence`: `[get_trips, get_historian_coverage]`
   - `default_visuals`: `[multi_tag_live_trends]`
   - Scope mentions: `scope: ASSET` (line 4); requires `asset_id` (line 33).

9. **`OP15_PLATFORM_GUIDE.yaml`** (`config/objectives/OP15_PLATFORM_GUIDE.yaml:1-21`)
   - `objective_id`: `OP15_PLATFORM_GUIDE`
   - `scope`: `GLOBAL`
   - `required_evidence`: `[]`
   - `optional_evidence`: `[lookup_ui_map_entry, search_ui_map]`
   - `default_visuals`: `[]`
   - Scope mentions: `scope: GLOBAL` (line 4); accepts `entry_id` or `query`.

**Summary:** 6 objectives are `ASSET` scope (single well only), and 3 objectives are `GLOBAL` scope (knowledge / platform text lookups). Zero objectives support fleet-scope queries.

---

## 2. Routing Contract — Scope Handling

- **`RouteDecision` Model (`agent_service/app/contracts/routing.py:23-34`)**:
  - `RouteDecision` has no `scope` field. The fields are: `route`, `intent`, `objective_id`, `args`, `confidence`, `deferred_intents`, `clarification_needed`, `clarify_reason`, `clarify_slot`, `clarify_options`.
- **Router Population**: `scope` is not populated by the router.
- **Downstream Consumption**: `scope` is not read by any downstream stage from `RouteDecision`.
- **Occurrences in Codebase**:
  - `agent_service/app/contracts/enums.py:8`: `Scope = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]`
  - `agent_service/app/contracts/objective_manifest.py:9`: `scope: Scope`
  - `agent_service/app/synthesis/identity_handler.py:105`: `scope = model_data.get("scope", {})` (reads `config/agent_identity.yaml:8`)
  - `agent_service/app/synthesis/identity_handler.py:110`: `f"I monitor the {scope.get('operational_fleet', {}).get('field', 'Farha South')} ESP fleet, "`
  - `agent_service/app/main.py:418`: comment: `# time-scoped calls (get_events, get_historian_window) as ISO-8601`
  - `agent_service/config/objectives/*.yaml:4`: `scope: ASSET` (OP01, OP02, OP03, OP04, OP05, OP14) and `scope: GLOBAL` (OP06, OP07, OP15)
  - `agent_service/tests/test_phase3_wireup.py:624`: mock test manifest fixture setting `scope="FLEET"`
  - `agent_service/tests/objectives/test_manifests.py:43`: `assert manifest.scope in ("ASSET", "GLOBAL")`

---

## 3. Router Behavior for Fleet Questions

- **Asset Routing Rules in Router Prompt (`agent_service/app/llm/prompts/router_v2.txt`)**:
  - Rule 2 (lines 46-54): `"WORKFLOW" is for questions about a SPECIFIC well's live status, sensor readings, decline, or fault events, OR for platform guide (OP15).`
  - Rule 4 (lines 72-75): `If an asset is required (e.g. "why did it trip?", "why has production dropped?") but asset_id is null/unresolved, route to "WORKFLOW" with the appropriate objective_id, args {"asset_id": null}, clarification_needed=true, clarify_slot="asset_id", and clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"].`
- **Fleet-Scope Prompt Rules**: Zero rules in `router_v2.txt` recognize fleet questions.
- **Deterministic Fallback Rules (`agent_service/app/routing/router.py:187-216`)**:
  ```python
  needs_asset_clarify = (
      router_input.asset_id is None
      and any(w in raw_lower for w in ["trip", "status", "vibration", "temp", "amps", "hz", "pressure", "why did", "health", "early warning", "warning", "anomaly", "history", "runtime"])
  )
  ```
- **Outcome for "which wells are underperforming"**:
  1. Context Resolver finds no asset ID in query; `router_input.asset_id` is `None`.
  2. Router LLM prompt (Rule 4) or keyword fallback (`needs_asset_clarify` matching "underperforming" / "performance") flags missing asset ID.
  3. Router returns `RouteDecision(route="WORKFLOW", intent="diagnose", objective_id="OP03_FAULT_DIAGNOSIS", args={"asset_id": None}, clarification_needed=True, clarify_slot="asset_id", clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"])`.
  4. The agent halts and emits a `ClarificationFrame` asking the user to choose one specific well (`FS-17`, `FS-91`, `FNW-01`, `FWS-06`) instead of inspecting the fleet.

---

## 4. KPI Adapter — Current Capabilities

File: `agent_service/app/gateway/adapters/kpi.py` (lines 1-119).

- **Exposed Functions**:
  1. `fetch_kpi(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]` (lines 17-94)
  2. `fetch_fleet_kpi(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]` (lines 96-118)
- **Aggregation Function & SQL**:
  - `fetch_fleet_kpi` runs:
    ```sql
    SELECT count(*), count(*) FILTER (WHERE is_active) FROM asset_registry;
    ```
- **Response Shapes**:
  - `fetch_kpi` response shape (lines 71-86):
    ```json
    {
      "well_id": "FS-17",
      "status": "OK",
      "gross_liquid_rate_bpd": 520.0,
      "net_oil_rate_bopd": 390.0,
      "water_cut_pct": 25.0,
      "motor_load_pct": 82.5,
      "health_score": 92.0,
      "intake_pressure_psi": 450.0,
      "discharge_pressure_psi": 1820.0,
      "motor_temp_c": 88.0,
      "vibration_g": 0.42,
      "frequency_hz": 50.0,
      "operating_state": "RUNNING",
      "source": "POSTGRESQL"
    }
    ```
  - `fetch_fleet_kpi` response shape (lines 106-113):
    ```json
    {
      "total_wells": 35,
      "running_wells": 32,
      "down_wells": 3,
      "fleet_health_score": 88.5,
      "total_production_bpd": 15420.0,
      "source": "POSTGRESQL"
    }
    ```
- **Storage / Aggregation Mode**: `fetch_fleet_kpi` only queries row counts from `asset_registry`. `fleet_health_score: 88.5` and `total_production_bpd: 15420.0` are hardcoded static constants (lines 110-111). It does not aggregate telemetry rows at query time.

---

## 5. Existing Fleet Tools — Any?

Occurrences in codebase:
- `agent_service/app/policy/policy_gate.py:33`: `"get_live_wells"` in `ALLOWED_TOOLS`
- `agent_service/app/gateway/tool_gateway.py:98`: `"get_fleet_kpi"` exempted from `asset_id` check
- `agent_service/app/gateway/tool_gateway.py:99`: `"get_live_wells"` exempted from `asset_id` check
- `agent_service/app/gateway/tool_gateway.py:126`: `elif tool == "get_live_wells": data = await live.fetch_live_wells(client=client)`
- `agent_service/app/gateway/adapters/live.py:177`: `async def fetch_live_wells(...) -> dict[str, Any]`
- `agent_service/app/gateway/adapters/kpi.py:96`: `async def fetch_fleet_kpi(...) -> dict[str, Any]`

**Tool Registration Status**:
- `get_live_wells` is registered and implemented (returns list of active well IDs from `asset_registry`).
- `get_fleet_kpi` is NOT in `ALLOWED_TOOLS` in `policy_gate.py` and has no execution dispatch handler in `tool_gateway.py` (would return `UNKNOWN_TOOL` if dispatched in a plan).
- Zero fleet ranking, filtering, sorting, or multi-well telemetry tools exist.

---

## 6. Evidence Pack — Multi-Asset Handling

File: `agent_service/app/contracts/evidence.py` (lines 1-56).

- **Asset Assumption**:
  - `EvidenceItem` has fields `evidence_id`, `tool`, `source_domain`, `fetched_at`, `freshness_sec`, `status`, `payload`, `unit_map`.
  - `EvidencePack` has fields `run_id`, `version`, `sealed`, `sealed_at`, `items`, `gaps`, `conflicts`.
- **Scope & Asset Count Fields**: Neither `EvidenceItem` nor `EvidencePack` has a `scope`, `asset_id`, or `asset_count` field.
- **Behavior with 13 Wells**:
  - In `agent_service/app/evidence/formatter.py:119-180`, `_extract_from_item` extracts signals from `payload["measurements"]` or flat keys into `FormattedValue` items.
  - `FormattedEvidence.by_signal(signal)` (`formatter.py:82-86`) maps 1:1 by signal name without a well dimension.
  - If a multi-well payload is passed, `formatter.py` either fails to extract values or collapses/overwrites measurements across wells.

---

## 7. XAI Prompt — Fleet Awareness

Prompts inspected: `narrator_v1.txt`, `narrator_health_v1.txt`, `narrator_early_warning_v1.txt`, `narrator_decline_rca_v1.txt`, `narrator_history_v1.txt`, `narrator_procedure_v1.txt`, `narrator_platform_v1.txt`.

- **Fleet / Ranking / Aggregation Mentions**: Zero narrator prompts mention fleet, multi-well ranking, or multi-well triage.
  - Exception: `narrator_procedure_v1.txt:12` mentions "Authority Ranking" (referring to Level A vs Level B standard documents).
- **Current Presentation Instructions (`narrator_v1.txt:4-13`)**:
  - Rules instruct the model to report single-equipment condition: `"assessment": "<high-level summary of equipment condition and observations citing specific evidence>"`.
- **Outcome with Fleet Pack**: The narrator would treat all data points as belonging to a single unspecified asset or output an unranked narrative paragraph without structured comparative ranking.

---

## 8. Card Registry — Fleet Cards

File: `agent_service/config/cards_registry.yaml` (lines 1-223).

- **Registered Card IDs (31 total)**:
  `gross-liquid-rate`, `net-oil-rate`, `water-cut`, `associated-gas`, `production-deferment`, `energy-balance`, `health-score`, `anomaly-score`, `fault-classification`, `motor-load`, `motor-temperature`, `vibration`, `intake-pressure`, `discharge-pressure`, `vsd-advisor`, `fleet-health`, `system-ingestion`, `degradation-trend`, `risk-trajectory`, `production-decline`, `pressure-corridor`, `trip-timeline`, `evidence-cards`, `working_status_smart_fault_card`, `subsystem_equalizer`, `pump_curve_operating_point`, `esp_well_schematic`, `multi_tag_live_trends`, `vfm_production_ribbon`, `system_operational_summary`, `advisor_panel_item`.
- **Fleet-Level Cards**:
  - `fleet-health` (lines 114-119) / `system_operational_summary` (lines 211-216): Configured with `unit: "Fleet"`, `widget_type: system_summary_card`.
  - Implementation in `agent_service/app/gateway/adapters/cards.py:361-379` (`_query_system_summary`) returns a single object containing `totalWells`, `runningWells`, `downWells`, and hardcoded `fleetHealth: 91.5`.
- **Ranking / Multi-Well Table Cards**: Zero cards exist for tabular multi-well lists, ranked anomaly matrices, or fleet-wide comparison charts.

---

## 9. Fleet List — Where Is It?

1. **Config File**:
   - `agent_service/config/wells_canonical.yaml:1-33`: Static YAML listing 14 production wells (`FNW-01`, `FS-17`, `FS-121`, `FNW-06`, `FWS-06`, `ULFA-5`, `FS-96`, `FS-21`, `FS-06`, `FS-91`, `FSWS-001-A`, `FS-014`, `FS-016`, `FS-031`).
   - `agent_service/config/asset_aliases.yaml:1-42`: Static alias mappings for 4 primary wells (`FS-17`, `FS-91`, `FNW-01`, `FWS-06`).
2. **PostgreSQL Database Table**:
   - Database table: `asset_registry` in `esp_apm_db` (contains 35 wells with 3-digit zero-padded IDs, e.g., `FS-017`, `FNW-001`).
3. **Runtime Query Tool & Code**:
   - Tool name: `get_live_wells`
   - Adapter code: `agent_service/app/gateway/adapters/live.py:177-194`
   - SQL executed:
     ```sql
     SELECT well_id, cluster, is_active FROM asset_registry ORDER BY well_id;
     ```

---

## 10. Storage — What Fleet Runs Would Write

File: `agent_service/app/stores/run_store.py` (lines 1-134).

- **Redis Key Patterns**:
  - `esp:run:{run_id}`: Serialized `RunState` JSON (`save_run`, line 25)
  - `esp:run:{run_id}:pack:v{version}`: Serialized `EvidencePack` JSON (`save_pack`, line 66)
  - `esp:run:{run_id}:pack:latest_version`: String version number (`save_pack`, line 68)
  - `esp:run:{run_id}:artifacts`: Serialized `Advisory` & `VisualizationSpec` JSON (`save_run_artifacts`, line 115)
- **Fleet Run Differences**: Fleet runs would use the exact same key patterns keyed by `run_id`.
- **Constraints & TTL**:
  - Default TTL is 86,400 seconds (24 hours).
  - Multi-well payload for 13–35 wells (~50 KB to 200 KB) is well within Redis string limit (512 MB).

---

## 11. Dashboard Integration Points

Files: `agent_service/app/contracts/events.py`, `agent_service/app/contracts/api.py`, `agent_service/config/ui_map/ui_map.yaml`.

- **`scope` Field on Frames**: None of the 8 event frame models (`StatusFrame`, `TextDeltaFrame`, `ClarificationFrame`, `InterruptFrame`, `AdvisoryFrame`, `VisualFrame`, `ErrorFrame`, `DoneFrame`) in `events.py:1-60` contain a `scope` field.
- **`UIContext` Fields (`api.py:5-15`)**:
  - `fleet_filter: Optional[str] = None` (line 12)
  - `station_id: Optional[str] = None` (line 13)
  - `selected_route: Optional[str] = None` (line 14)
- **Fleet Route Identifiers in `ui_map.yaml`**:
  - `/working-status` (`route.working-status`): "Well Working Status & Model Fault Spectrum"
  - `/cockpit` (`route.cockpit`): "ESP Fleet Cockpit"
  - `/reports` (`route.reports`): "Automated Field Reports"
  - `/custom-testing` (`route.custom-testing`): "Custom Testing Studio"
  - `/engineering-overview` (`route.engineering-overview`): "Engineering Fleet Overview"

---

## 12. Existing Deferred Work

Searches across `agent_service/`:
- `TODO`: Not found (0 occurrences)
- `FIXME`: Not found (0 occurrences)
- `deferred_intents`: Present for actuation requests (e.g. `actuation_set_frequency` in `router.py:349`).
- `fleet` mentions in comments / code:
  - `app/visualization/planner.py:102`: `# Cards with empty required_signals (e.g. fleet-health or system-ingestion)`
  - `app/contracts/enums.py:8`: `Scope = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]`
  - `app/gateway/adapters/kpi.py:97`: `"""Fetch field-level fleet KPI summary."""`

---

## 13. What Phase 5 Needs — Gap List

The following elements do not exist today and are required to support fleet-scope objectives:

1. **Fleet Objective Manifests (Section 1)**: No objective manifests with `scope: FLEET` or `scope: MULTI_ASSET` exist in `config/objectives/`.
2. **Routing Contract Scope Field (Section 2)**: `RouteDecision` in `app/contracts/routing.py` lacks a `scope` attribute.
3. **Router Fleet Intent & Clarification Bypass (Section 3)**: `router_v2.txt` and `router.py` lack rules for fleet questions (e.g., "which wells tripped", "fleet health ranking"), routing all missing-asset questions to single-well `CLARIFY`.
4. **Adapter Multi-Well Batch Telemetry & Aggregation (Section 4)**: `kpi.py` contains static constants for fleet metrics; no adapter in `live.py`, `events.py`, `ml.py`, or `historian.py` supports multi-well batch queries.
5. **Tool Gateway Fleet Tool Registration (Section 5)**: `get_fleet_kpi` is not registered in `ALLOWED_TOOLS` (`policy_gate.py`) and is not dispatched in `tool_gateway.py`. No multi-well ranking or filtering tools exist.
6. **Evidence Formatter Multi-Asset Representation (Section 6)**: `EvidenceItem` and `FormattedEvidence` have no well dimension in signal indexing (`by_signal` is 1:1).
7. **Narrator Fleet Synthesis Prompts (Section 7)**: No narrator prompt exists for fleet ranking, comparative tables, or multi-well triage summaries.
8. **Fleet Visual Cards (Section 8)**: No visual cards exist for multi-well data tables, ranking lists, or fleet comparative charts.
9. **Well Identifier Consistency (Section 9)**: Discrepancy between unpadded IDs in `wells_canonical.yaml` (e.g. `FS-17`) and 3-digit padded IDs in PostgreSQL `asset_registry` (e.g. `FS-017`).
10. **Event Frame Scope Metadata (Section 11)**: Response frames in `app/contracts/events.py` lack a `scope` field.
