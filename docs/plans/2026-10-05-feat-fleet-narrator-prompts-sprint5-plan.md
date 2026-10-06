# Sprint 5 Plan: Fleet Narrator Prompts

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

Implement domain-specialized XAI synthesizer prompts and wiring for the three Fleet objectives:
1. **OP08 (Fleet Inventory)**: Summarize total/running/down wells, health distribution, list top-attention wells (capped at top 5 unless full list requested), citing evidence IDs, within 150–250 words (up to 400 for full listings).
2. **OP09 (Fleet Production Optimization)**: Rank wells by opportunity (production deferred, degradation velocity, anomaly score), recommend top 3 focus wells with explicit ranking criteria and evidence citations.
3. **OP13 (Fleet Executive Reporting)**: High-level one-page executive summary covering fleet health & production posture, key metrics, top risks/trip events, and prioritized strategic recommendations.
4. **Prompt Wiring & Evidence Attribution**: Update `app/llm/calls.py` to route OP08/OP09/OP13 to their dedicated prompts, and enhance `app/synthesis/xai.py`'s `format_evidence_for_prompt` to surface `[Well: <well_id>]` attribution in prompt strings.

---

## 2. Technical Context & Exact File References

- **Prompts Directory**: [`agent_service/app/llm/prompts/`](file:///a:/TAS-AI/ESP/agent_service/app/llm/prompts/)
  - Create `narrator_fleet_inventory_v1.txt` (OP08)
  - Create `narrator_fleet_optimization_v1.txt` (OP09)
  - Create `narrator_fleet_executive_v1.txt` (OP13)
- **LLM Call Dispatcher**: [`agent_service/app/llm/calls.py:192-225`](file:///a:/TAS-AI/ESP/agent_service/app/llm/calls.py#L192-L225)
  - Map `OP08` -> `narrator_fleet_inventory_v1.txt`
  - Map `OP09` -> `narrator_fleet_optimization_v1.txt`
  - Map `OP13` -> `narrator_fleet_executive_v1.txt`
- **XAI Prompt Formatter**: [`agent_service/app/synthesis/xai.py:18-76`](file:///a:/TAS-AI/ESP/agent_service/app/synthesis/xai.py#L18-L76)
  - Include `Well: <well_id>` in event records and numeric measurements when `well_id` is populated on `FormattedValue` / `FormattedEventRecord`.
- **Advisory Contract**: [`agent_service/app/contracts/advisory.py`](file:///a:/TAS-AI/ESP/agent_service/app/contracts/advisory.py)
  - Schema: `objective_id`, `assessment`, `hypotheses`, `recommendation`, `verification_steps`, `troubleshooting_steps`, `confidence`, `cited_evidence_ids`.
- **Existing Manifests**:
  - `agent_service/config/objectives/OP08_FLEET_INVENTORY.yaml`
  - `agent_service/config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`
  - `agent_service/config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml`

---

## 3. Implementation Units

### U1: Create `narrator_fleet_inventory_v1.txt`
- **File**: `agent_service/app/llm/prompts/narrator_fleet_inventory_v1.txt`
- **Rules**:
  - Summarize total wells, running vs down counts, and health distribution (Healthy >=75, Degraded 50–74.9, Critical <50).
  - Rank and list wells needing attention by severity (worst health score first).
  - Unless user query explicitly asks for all/complete/full list, cap individual well breakdown at the top 5 worst wells.
  - Length constraint: 150–250 words for standard summary, up to 400 words for full listing queries.
  - Strict grounding: cite evidence IDs (e.g. `EV-...`) for every well and metric; refuse to invent wells.
  - JSON schema output conforming to `Advisory`.

### U2: Create `narrator_fleet_optimization_v1.txt`
- **File**: `agent_service/app/llm/prompts/narrator_fleet_optimization_v1.txt`
- **Rules**:
  - Identify production optimization opportunities across the fleet.
  - Rank wells by opportunity (health degradation, deferred rate, anomaly score, operating status).
  - Explicitly recommend the top 3 wells to investigate/optimize with technical rationale.
  - Cite ranking criteria and evidence IDs for all data points.
  - Actionable engineering recommendations (frequency adjustment, choke tuning, drawdown optimization).
  - JSON schema output conforming to `Advisory`.

### U3: Create `narrator_fleet_executive_v1.txt`
- **File**: `agent_service/app/llm/prompts/narrator_fleet_executive_v1.txt`
- **Rules**:
  - High-level executive synthesis (one-page format).
  - Sections/points for:
    1. Executive Assessment (fleet availability %, total rate BPD, fleet health index).
    2. Key Risks & Tripped/Down Wells (recent trip events and critical health assets).
    3. Prioritized Strategic & Operational Focus.
  - Use structured bullet points/comparisons.
  - Strict grounding with evidence ID citations; zero fabricated assets.
  - JSON schema output conforming to `Advisory`.

### U4: Update Prompt Formatter in `xai.py`
- **File**: [`agent_service/app/synthesis/xai.py`](file:///a:/TAS-AI/ESP/agent_service/app/synthesis/xai.py#L37-L58)
- **Changes**:
  - In `format_evidence_for_prompt`:
    - For `evidence.events`: include `Well: {ev.well_id} | ` when `ev.well_id` is present.
    - For `evidence.values`: include `[Well: {item.well_id}] ` when `item.well_id` is present.
- **Verification**: Formatted prompt string contains clear well attribution per measurement and event.

### U5: Wire Dispatch in `app/llm/calls.py`
- **File**: [`agent_service/app/llm/calls.py`](file:///a:/TAS-AI/ESP/agent_service/app/llm/calls.py#L199-L213)
- **Changes**:
  ```python
  if "OP04" in objective_id:
      system_prompt = load_prompt("narrator_health_v1.txt")
  elif "OP05" in objective_id:
      system_prompt = load_prompt("narrator_early_warning_v1.txt")
  elif "OP14" in objective_id:
      system_prompt = load_prompt("narrator_history_v1.txt")
  elif "OP02" in objective_id:
      system_prompt = load_prompt("narrator_decline_rca_v1.txt")
  elif "OP06" in objective_id:
      system_prompt = load_prompt("narrator_procedure_v1.txt")
  elif "OP15" in objective_id:
      system_prompt = load_prompt("narrator_platform_v1.txt")
  elif "OP08" in objective_id:
      system_prompt = load_prompt("narrator_fleet_inventory_v1.txt")
  elif "OP09" in objective_id:
      system_prompt = load_prompt("narrator_fleet_optimization_v1.txt")
  elif "OP13" in objective_id:
      system_prompt = load_prompt("narrator_fleet_executive_v1.txt")
  else:
      system_prompt = load_prompt("narrator_v1.txt")
  ```

### U6: Comprehensive Test Suite for Fleet Narrator Prompts
- **File**: `agent_service/tests/test_fleet_narrator_prompts.py`
- **Test Scenarios**:
  1. `test_prompt_files_exist_and_load`: Verify all three prompt files load cleanly via `load_prompt`.
  2. `test_xai_prompt_formatter_includes_well_ids`: Verify `format_evidence_for_prompt` includes `[Well: ...]` tags for multi-well values and events.
  3. `test_narrate_prompt_dispatch_mapping`: Verify `narrate` selects the correct prompt string for OP08, OP09, OP13.
  4. `test_e2e_fleet_synthesis_live_data`:
     - Run full real flow: fetch live PostgreSQL fleet data -> validate via QoD -> seal pack -> format -> synthesize Advisory with LLM.
     - Assert `advisory.objective_id` matches.
     - Assert `advisory.cited_evidence_ids` is non-empty.
     - Assert `advisory.assessment` mentions real fleet metrics and real well IDs without fabrication.

---

## 4. Verification Contract & Definition of Done

1. **Prompt Existence Check**:
   - `narrator_fleet_inventory_v1.txt`, `narrator_fleet_optimization_v1.txt`, and `narrator_fleet_executive_v1.txt` exist and pass schema validation.
2. **End-to-End Synthesis**:
   - Execute OP08, OP09, OP13 through `narrate()` and verify valid `Advisory` models returned.
3. **Automated Suite**:
   ```bash
   py -m pytest tests/test_fleet_narrator_prompts.py tests/test_multi_asset_evidence.py tests/test_fleet_tools.py tests/test_router_fleet_sprint1.py tests/objectives/test_manifests.py -v
   ```
   **Pass Criteria**: 100% green tests.
