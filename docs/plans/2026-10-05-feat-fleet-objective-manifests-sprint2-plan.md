# Sprint 2 Plan: Fleet Objective Manifests (OP08, OP09, OP13)

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

Implement and register the three Phase 5 fleet objective manifests in `agent_service/config/objectives/`:
1. **`OP08_FLEET_INVENTORY`**: Active fleet inventory and status reporting with `scope: FLEET`.
2. **`OP09_FLEET_PRODUCTION_OPTIMIZATION`**: Fleet-wide production KPI and health optimization with `scope: FLEET`.
3. **`OP13_FLEET_EXECUTIVE_REPORT`**: Executive summary combining fleet KPIs, health, and aggregate operational events with `scope: FLEET`.

All three manifests declare `scope: FLEET`, require zero `asset_id` arguments in `arg_schema`, load and validate against `ObjectiveManifest` Pydantic models, register cleanly in `objective_registry`, and pass all manifest validation and visual-card registration tests.

---

## 2. Technical Context & Exact File References

- **Objective Contract Model**: [`agent_service/app/contracts/objective_manifest.py`](file:///a:/TAS-AI/ESP/agent_service/app/contracts/objective_manifest.py#L5-L17)
  - `ObjectiveManifest` schema: `objective_id: str`, `tool: str`, `safety_class: SafetyClass`, `scope: Scope`, `required_evidence: list[str]`, `optional_evidence: list[str]`, `allowed_visuals: list[str]`, `default_visuals: Optional[list[str]]`, `arg_schema: dict[str, Any]`, `max_gapfill_rounds: int`.
- **Scope Enum**: [`agent_service/app/contracts/enums.py:8`](file:///a:/TAS-AI/ESP/agent_service/app/contracts/enums.py#L8)
  - `Scope = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]`
- **Existing Objectives Directory**: `agent_service/config/objectives/`
  - Manifest pattern: [`OP01_CURRENT_STATUS.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/objectives/OP01_CURRENT_STATUS.yaml), [`OP15_PLATFORM_GUIDE.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/objectives/OP15_PLATFORM_GUIDE.yaml)
- **Objective Registry Loader**: [`agent_service/app/routing/objective_registry.py:15-57`](file:///a:/TAS-AI/ESP/agent_service/app/routing/objective_registry.py#L15-L57)
  - Dynamically loads `config/objectives/*.yaml` and registers full IDs (`OP08_FLEET_INVENTORY`) and short IDs (`OP08`).
- **Cards Registry & Aliases**: [`agent_service/config/cards_registry.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/cards_registry.yaml#L114-L125), [`agent_service/app/gateway/adapters/cards.py:19-38`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/cards.py#L19-L38)
  - Registered cards: `fleet-health`, `production-deferment`, `system_operational_summary`.
- **Manifest Test Suite**: [`agent_service/tests/objectives/test_manifests.py:1-56`](file:///a:/TAS-AI/ESP/agent_service/tests/objectives/test_manifests.py#L1-L56)

---

## 3. Implementation Units

### U1: Create `OP08_FLEET_INVENTORY.yaml`
- **File**: `agent_service/config/objectives/OP08_FLEET_INVENTORY.yaml`
- **Specification**:
  ```yaml
  objective_id: OP08_FLEET_INVENTORY
  tool: get_live_wells
  safety_class: READ
  scope: FLEET
  max_gapfill_rounds: 0
  required_evidence:
    - get_live_wells
  optional_evidence:
    - get_fleet_kpi
  allowed_visuals:
    - fleet-health
    - system_operational_summary
  default_visuals:
    - fleet-health
  arg_schema:
    type: object
    properties: {}
    required: []
  ```
- **Verification**: YAML parses, validates against `ObjectiveManifest`, `scope == 'FLEET'`, `required == []`.

---

### U2: Create `OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`
- **File**: `agent_service/config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`
- **Specification**:
  ```yaml
  objective_id: OP09_FLEET_PRODUCTION_OPTIMIZATION
  tool: get_fleet_kpi
  safety_class: READ
  scope: FLEET
  max_gapfill_rounds: 0
  required_evidence:
    - get_fleet_kpi
    - get_fleet_health
  optional_evidence:
    - get_live_wells
  allowed_visuals:
    - fleet-health
    - production-deferment
    - system_operational_summary
  default_visuals:
    - fleet-health
    - production-deferment
  arg_schema:
    type: object
    properties: {}
    required: []
  ```
- **Verification**: YAML parses, validates against `ObjectiveManifest`, `scope == 'FLEET'`, `required == []`.

---

### U3: Create `OP13_FLEET_EXECUTIVE_REPORT.yaml`
- **File**: `agent_service/config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml`
- **Specification**:
  ```yaml
  objective_id: OP13_FLEET_EXECUTIVE_REPORT
  tool: get_fleet_kpi
  safety_class: READ
  scope: FLEET
  max_gapfill_rounds: 0
  required_evidence:
    - get_fleet_kpi
    - get_fleet_health
    - get_fleet_events
  optional_evidence:
    - get_live_wells
  allowed_visuals:
    - fleet-health
    - system_operational_summary
  default_visuals:
    - fleet-health
    - system_operational_summary
  arg_schema:
    type: object
    properties: {}
    required: []
  ```
- **Verification**: YAML parses, validates against `ObjectiveManifest`, `scope == 'FLEET'`, `required == []`.

---

### U4: Update Card Alias Map for Snake-Case & Kebab-Case
- **File**: [`agent_service/app/gateway/adapters/cards.py:19-38`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/cards.py#L19-L38)
- **Change**: Ensure both `fleet_health` and `fleet-health` map to canonical visual `system_operational_summary`:
  ```python
  "fleet_health": "system_operational_summary",
  "fleet-health": "system_operational_summary",
  ```
- **Verification**: `fetch_card(card_id='fleet_health')` and `fetch_card(card_id='fleet-health')` both resolve.

---

### U5: Update Manifest Validation Tests & Add OP08/OP09/OP13 Test Suite
- **File**: [`agent_service/tests/objectives/test_manifests.py`](file:///a:/TAS-AI/ESP/agent_service/tests/objectives/test_manifests.py)
- **Changes**:
  1. Update `test_manifests.py:43` scope assertion from `assert manifest.scope in ("ASSET", "GLOBAL")` to `assert manifest.scope in ("ASSET", "GLOBAL", "FLEET", "MULTI_ASSET")`.
  2. Add `OP08_FLEET_INVENTORY.yaml`, `OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`, `OP13_FLEET_EXECUTIVE_REPORT.yaml`, `OP15_PLATFORM_GUIDE.yaml` to `ALL_OBJECTIVES`.
  3. Add explicit test `test_fleet_manifests_no_asset_id_requirement`:
     - Checks `OP08`, `OP09`, `OP13` declare `scope == "FLEET"`.
     - Checks `len(manifest.arg_schema.get("required", [])) == 0` and `"asset_id"` not in `required`.
     - Checks all `allowed_visuals` and `default_visuals` exist in `cards_registry.yaml`.

---

## 4. Verification Contract & Definition of Done

1. **Manifest File Presence**:
   - `config/objectives/OP08_FLEET_INVENTORY.yaml` exists.
   - `config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml` exists.
   - `config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml` exists.
2. **Registry Introspection Check**:
   ```python
   from app.routing.objective_registry import get_objective, list_objectives
   for oid in ["OP08", "OP08_FLEET_INVENTORY", "OP09", "OP09_FLEET_PRODUCTION_OPTIMIZATION", "OP13", "OP13_FLEET_EXECUTIVE_REPORT"]:
       manifest = get_objective(oid)
       assert manifest is not None
       assert manifest.scope == "FLEET"
       assert "asset_id" not in manifest.arg_schema.get("required", [])
   ```
3. **Automated Test Suite**:
   ```bash
   pytest agent_service/tests/objectives/test_manifests.py -v
   pytest agent_service/tests/test_router_fleet_sprint1.py -v
   ```
   **Pass Criteria**: All tests green, 0 errors, 0 asset_id requirements on fleet objectives.
