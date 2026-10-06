# Sprint 6 Plan: Fleet Visual Cards

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

Implement and register three new visual cards for fleet-level observability and executive monitoring:
1. **`fleet-health-table`**: Sortable table displaying every well's health score, health band (`HEALTHY` / `DEGRADED` / `CRITICAL`), operating state (`RUNNING` / `TRIPPED` / `STOPPED`), top alarming signal, and gross production rate.
2. **`fleet-opportunity-view`**: Ranked list prioritizing wells with high production recovery potential (deferred production BPD, degraded health, high anomaly scores, and actionable optimization guidance).
3. **`fleet-production-summary`**: Aggregate KPI ribbon presenting total gross liquid production (BPD), net oil production (BOPD), average water cut (%), fleet operational availability (%), and active vs. down well counts.
4. **Backend Implementation**: Card registry declaration with `required_signals: []`, PostgreSQL query generators in `app/gateway/adapters/cards.py`, alias mappings, and objective manifest wiring (`OP08`, `OP09`, `OP13`).
5. **Dashboard Repository Blueprint**: Detailed TypeScript interfaces, props, and component architecture for the user to integrate into the external Dashboard repository.

---

## 2. Technical Context & Exact File References

- **Card Registry**: [`agent_service/config/cards_registry.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/cards_registry.yaml)
  - Declare `fleet-health-table`, `fleet-opportunity-view`, `fleet-production-summary` with `required_signals: []`.
- **Card Adapter & Generators**: [`agent_service/app/gateway/adapters/cards.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/cards.py)
  - `_CARD_ALIAS_MAP`: register aliases (`fleet-health-table` -> `fleet_health_table`, etc.).
  - `_DASHBOARD_CATALOG`: add the 3 new canonical card IDs.
  - Implement `_query_fleet_health_table(cur)`, `_query_fleet_opportunity_view(cur)`, and `_query_fleet_production_summary(cur)`.
  - Wire into `fetch_card(well_id, card_id)`.
- **Objective Manifests**:
  - [`agent_service/config/objectives/OP08_FLEET_INVENTORY.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/objectives/OP08_FLEET_INVENTORY.yaml)
  - [`agent_service/config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml)
  - [`agent_service/config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml`](file:///a:/TAS-AI/ESP/agent_service/config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml)
- **Visualization Planner**: [`agent_service/app/visualization/planner.py`](file:///a:/TAS-AI/ESP/agent_service/app/visualization/planner.py)
- **External Dashboard Repo**: Frontend widget dock and card renderer registry.

---

## 3. Implementation Units

### U1: Card Registry & Objective Manifests (Agent)
- **Files**:
  - `agent_service/config/cards_registry.yaml`
  - `agent_service/config/objectives/OP08_FLEET_INVENTORY.yaml`
  - `agent_service/config/objectives/OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml`
  - `agent_service/config/objectives/OP13_FLEET_EXECUTIVE_REPORT.yaml`
- **Changes**:
  1. Add to `cards_registry.yaml`:
     ```yaml
     fleet-health-table:
       component_id: FleetHealthTable
       unit: wells
       widget_type: table_card
       required_signals: []

     fleet-opportunity-view:
       component_id: FleetOpportunityView
       unit: ranking
       widget_type: ranked_list_card
       required_signals: []

     fleet-production-summary:
       component_id: FleetProductionSummary
       unit: BPD
       widget_type: kpi_ribbon_card
       required_signals: []
     ```
  2. Update Objective Manifests:
     - `OP08`: `allowed_visuals: [fleet-health, fleet-health-table, system_operational_summary]`, `default_visuals: [fleet-health-table, system_operational_summary]`
     - `OP09`: `allowed_visuals: [fleet-health, fleet-opportunity-view, fleet-production-summary, production-deferment, system_operational_summary]`, `default_visuals: [fleet-opportunity-view, fleet-production-summary]`
     - `OP13`: `allowed_visuals: [fleet-health, fleet-health-table, fleet-production-summary, system_operational_summary]`, `default_visuals: [fleet-production-summary, fleet-health-table, system_operational_summary]`

---

### U2: Card Payload Generators in `cards.py` (Agent)
- **File**: [`agent_service/app/gateway/adapters/cards.py`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/cards.py)
- **Changes**:
  1. Update `_CARD_ALIAS_MAP` and `_DASHBOARD_CATALOG` with `fleet_health_table`, `fleet_opportunity_view`, `fleet_production_summary`.
  2. Implement `_query_fleet_health_table(cur)`:
     - Queries `asset_registry`, `opg_well_telemetry`, and `esp_unified_assessments`.
     - Returns per-well `wellId`, `healthScore`, `healthBand`, `operatingState`, `topSignal`, `grossRateBpd`, `lastEvent`.
     - Returns summary counts: `totalWells`, `healthyCount`, `degradedCount`, `criticalCount`.
  3. Implement `_query_fleet_opportunity_view(cur)`:
     - Calculates deferred production BPD for down/tripped/degraded wells.
     - Ranks top opportunity candidates by potential production gain and anomaly risk.
     - Returns ranked list with `rank`, `wellId`, `opportunityType`, `deferredProductionBpd`, `healthScore`, `anomalyScore`, `recommendedAction`.
  4. Implement `_query_fleet_production_summary(cur)`:
     - Aggregates live gross production, net oil production, average water cut, active/down wells, availability %, and total deferment BPD.
  5. Connect handlers to `fetch_card(well_id, card_id)` dispatch switch.

---

### U3: Unit & Integration Test Suite for Fleet Visual Cards (Agent)
- **File**: `agent_service/tests/test_fleet_visual_cards.py`
- **Test Scenarios**:
  1. `test_cards_registry_declarations`: Ensure all 3 cards load with `required_signals: []`.
  2. `test_fetch_card_fleet_health_table`: Query `fetch_card("GLOBAL", "fleet-health-table")` against PostgreSQL, asserting real rows, valid health bands, and zero mock data.
  3. `test_fetch_card_fleet_opportunity_view`: Query `fetch_card("GLOBAL", "fleet-opportunity-view")`, asserting descending opportunity ranking and valid recommendation strings.
  4. `test_fetch_card_fleet_production_summary`: Query `fetch_card("GLOBAL", "fleet-production-summary")`, asserting positive aggregate production rates and consistent active + down counts.
  5. `test_visualization_planner_fleet_objectives`: Run `plan_visualization` for `OP08`, `OP09`, `OP13` with a sealed fleet pack and assert correct cards qualify.

---

### U4: External Dashboard Repository Blueprint (Instructions for Task 6.3)
- **Target**: External Dashboard / React Frontend Repository.
- **Components to Register**:
  1. **`FleetHealthTable` (`fleet-health-table`)**:
     - **TypeScript Interface**:
       ```typescript
       export interface FleetHealthTableProps {
         totalWells: number;
         healthyCount: number;
         degradedCount: number;
         criticalCount: number;
         wells: Array<{
           wellId: string;
           healthScore: number;
           healthBand: "HEALTHY" | "DEGRADED" | "CRITICAL";
           operatingState: "RUNNING" | "TRIPPED" | "STOPPED" | "MAINTENANCE";
           topSignal: string;
           grossRateBpd: number;
           lastEvent?: string;
         }>;
       }
       ```
     - **Widget UI**: Sortable table with clickable rows to navigate/filter by well, colored badge pills for `healthBand` and `operatingState`.
  2. **`FleetOpportunityView` (`fleet-opportunity-view`)**:
     - **TypeScript Interface**:
       ```typescript
       export interface FleetOpportunityViewProps {
         totalOpportunityBpd: number;
         candidateCount: number;
         rankedWells: Array<{
           rank: number;
           wellId: string;
           opportunityType: string;
           deferredProductionBpd: number;
           healthScore: number;
           anomalyScore: number;
           recommendedAction: string;
         }>;
       }
       ```
     - **Widget UI**: Ranked card list showing rank badge (#1, #2, #3), deferred production recovery metric in bold, anomaly badge, and expandable recommended action box.
  3. **`FleetProductionSummary` (`fleet-production-summary`)**:
     - **TypeScript Interface**:
       ```typescript
       export interface FleetProductionSummaryProps {
         totalGrossLiquidBpd: number;
         totalNetOilBopd: number;
         averageWaterCutPct: number;
         totalGasRateMscfd: number;
         activeWells: number;
         downWells: number;
         fleetAvailabilityPct: number;
         totalDefermentBpd: number;
       }
       ```
     - **Widget UI**: Multi-metric KPI ribbon / stat box bar displaying total gross rate (BPD), net oil (BOPD), water cut (%), and uptime availability (%).
  4. **Registration Hook**:
     - In the frontend widget mapper (e.g. `CardRenderer.tsx` / `WidgetDock.tsx`), map:
       - `"fleet_health_table"` / `"fleet-health-table"` -> `<FleetHealthTable {...card.payload} />`
       - `"fleet_opportunity_view"` / `"fleet-opportunity-view"` -> `<FleetOpportunityView {...card.payload} />`
       - `"fleet_production_summary"` / `"fleet-production-summary"` -> `<FleetProductionSummary {...card.payload} />`

---

## 4. Verification Contract & Definition of Done

1. **Card Fetch API Verification**:
   ```bash
   py -c "import asyncio; from app.gateway.adapters.cards import fetch_card; res = asyncio.run(fetch_card('GLOBAL', 'fleet-health-table')); print(res['status'], len(res['payload']['wells']))"
   ```
   **Pass Criteria**: `status == "OK"`, `len(wells) > 0`.
2. **Visualization Planner Verification**:
   ```python
   spec = plan_visualization("OP08_FLEET_INVENTORY", sealed_pack)
   assert "fleet-health-table" in spec.card_ids
   ```
3. **Automated Suite**:
   ```bash
   py -m pytest tests/test_fleet_visual_cards.py tests/test_fleet_narrator_prompts.py tests/test_multi_asset_evidence.py tests/test_fleet_tools.py tests/test_router_fleet_sprint1.py tests/objectives/test_manifests.py -v
   ```
   **Pass Criteria**: 100% green tests.
