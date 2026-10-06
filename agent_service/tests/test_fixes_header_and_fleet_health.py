import pytest
from app.workflow.runner import _objective_header, run_workflow
from app.gateway.adapters.kpi import fetch_fleet_kpi
from app.routing.router import route_query
from app.contracts.routing import RouterInput


def test_fix1_objective_header_scope_awareness():
    """Verify _objective_header produces scope-aware header text."""
    # 1. ASSET scope
    h_asset_op01 = _objective_header("OP01_CURRENT_STATUS", asset_id="FS-17", scope="ASSET")
    assert h_asset_op01 == "Status check for FS-17:"

    h_asset_op03 = _objective_header("OP03_FAULT_DIAGNOSIS", asset_id="FS-17", scope="ASSET")
    assert h_asset_op03 == "Fault diagnosis for FS-17:"

    h_asset_fallback = _objective_header("OP99_CUSTOM", asset_id="FS-17", scope="ASSET")
    assert h_asset_fallback == "Diagnostic run for FS-17 (objective: OP99_CUSTOM):"

    # 2. FLEET scope
    h_fleet_op09 = _objective_header("OP09_FLEET_PRODUCTION_OPTIMIZATION", asset_id=None, scope="FLEET")
    assert h_fleet_op09.startswith("Fleet analysis (objective: OP09_FLEET_PRODUCTION_OPTIMIZATION):")

    h_fleet_op08 = _objective_header("OP08_FLEET_INVENTORY", asset_id=None, scope="FLEET")
    assert h_fleet_op08.startswith("Fleet analysis (objective: OP08_FLEET_INVENTORY):")

    h_fleet_op13 = _objective_header("OP13_FLEET_EXECUTIVE_REPORT", asset_id=None, scope="FLEET")
    assert h_fleet_op13.startswith("Fleet analysis (objective: OP13_FLEET_EXECUTIVE_REPORT):")

    # 3. GLOBAL scope
    h_global_op06 = _objective_header("OP06_KNOWLEDGE_LOOKUP", asset_id=None, scope="GLOBAL")
    assert h_global_op06 == "Knowledge lookup:"

    h_global_op15 = _objective_header("OP15_PLATFORM_GUIDE", asset_id=None, scope="GLOBAL")
    assert h_global_op15 == "Platform guide:"


@pytest.mark.anyio
async def test_fix1_workflow_fleet_query_header():
    """Verify live workflow execution for underperforming wells produces 'Fleet analysis (objective: OP09_...)' header."""
    res = await run_workflow(
        run_id="test-fix1-fleet-header",
        session_id="sess-fix1",
        objective_id="OP09_FLEET_PRODUCTION_OPTIMIZATION",
        args={},
        confidence=0.95,
        user_query="Which wells are underperforming?",
        scope="FLEET",
    )
    assert res.ok is True
    assert res.text.startswith("Fleet analysis (objective: OP09_FLEET_PRODUCTION_OPTIMIZATION):")
    assert "Diagnostic run for the selected asset" not in res.text


@pytest.mark.anyio
async def test_fix2_fleet_health_score_and_estimate():
    """Verify fetch_fleet_kpi returns honest fleet_health_estimate and method='bucketed_status'."""
    res = await fetch_fleet_kpi()
    assert res["status"] == "OK"
    assert "fleet_health_estimate" in res
    assert 0.0 <= res["fleet_health_estimate"] <= 100.0
    assert res["method"] == "bucketed_status"
    # Backward compatibility alias
    assert "fleet_health_score" in res
    assert res["fleet_health_score"] == res["fleet_health_estimate"]
