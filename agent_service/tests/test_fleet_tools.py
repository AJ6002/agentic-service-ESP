import pytest
from app.gateway.adapters.kpi import fetch_fleet_kpi, fetch_fleet_health
from app.gateway.adapters.events import fetch_fleet_events
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall, PlanArtifact
from app.policy.policy_gate import validate_plan

@pytest.mark.anyio
async def test_fetch_fleet_kpi_live_aggregation():
    """Verify fetch_fleet_kpi computes live Postgres aggregates with zero hardcoded values."""
    res = await fetch_fleet_kpi()
    assert res["status"] == "OK"
    assert res["source"] == "POSTGRESQL"
    assert res["total_wells"] > 0
    assert res["running_wells"] >= 0
    assert res["running_wells"] + res["down_wells"] == res["total_wells"]
    assert res["total_production_bpd"] > 0.0
    assert 0.0 <= res["fleet_health_estimate"] <= 100.0
    assert 0.0 <= res["fleet_health_score"] <= 100.0
    assert res["method"] == "bucketed_status"

@pytest.mark.anyio
async def test_fetch_fleet_health_ranking():
    """Verify fetch_fleet_health returns ranked wells from worst to best."""
    res = await fetch_fleet_health()
    assert res["status"] == "OK"
    assert res["source"] == "POSTGRESQL"
    assert res["count"] > 0
    wells = res["wells"]
    assert len(wells) == res["count"]
    
    assert res["worst"] == wells[0]["well_id"]
    assert res["best"] == wells[-1]["well_id"]
    
    # Assert ascending order of health scores
    for i in range(len(wells) - 1):
        assert wells[i]["health_score"] <= wells[i + 1]["health_score"]
        
    for w in wells:
        assert "well_id" in w
        assert "health_score" in w
        assert w["band"] in ("CRITICAL", "DEGRADED", "HEALTHY")

@pytest.mark.anyio
async def test_fetch_fleet_events_query():
    """Verify fetch_fleet_events aggregates events across all wells without requiring an asset_id."""
    res = await fetch_fleet_events()
    assert res["status"] == "OK"
    assert res["source"] == "POSTGRESQL"
    assert "events" in res
    assert res["count"] == len(res["events"])
    for ev in res["events"]:
        assert "well_id" in ev
        assert "timestamp" in ev
        assert "operating_state" in ev

@pytest.mark.anyio
async def test_tool_gateway_fleet_dispatch_without_asset_id():
    """Verify tool gateway dispatches get_fleet_kpi, get_fleet_health, get_fleet_events with zero asset_id."""
    for tool_name in ["get_fleet_kpi", "get_fleet_health", "get_fleet_events"]:
        call = PlanCall(seq=1, tool=tool_name, kind="READ", args={})
        call_res = await execute_tool_call(call)
        assert call_res.status == "OK", f"Tool {tool_name} failed: {call_res.error}"
        assert call_res.raw_response.get("status") == "OK"

def test_policy_gate_approves_fleet_tools():
    """Verify policy gate approves plans with fleet tools and zero asset_id for OP08, OP09, OP13."""
    plans = [
        PlanArtifact(
            run_id="run-op08",
            session_id="sess-08",
            objective_id="OP08_FLEET_INVENTORY",
            args={},
            confidence=0.95,
            calls=[PlanCall(seq=1, tool="get_live_wells", kind="READ", args={})],
        ),
        PlanArtifact(
            run_id="run-op09",
            session_id="sess-09",
            objective_id="OP09_FLEET_PRODUCTION_OPTIMIZATION",
            args={},
            confidence=0.95,
            calls=[
                PlanCall(seq=1, tool="get_fleet_kpi", kind="READ", args={}),
                PlanCall(seq=2, tool="get_fleet_health", kind="READ", args={}),
            ],
        ),
        PlanArtifact(
            run_id="run-op13",
            session_id="sess-13",
            objective_id="OP13_FLEET_EXECUTIVE_REPORT",
            args={},
            confidence=0.95,
            calls=[
                PlanCall(seq=1, tool="get_fleet_kpi", kind="READ", args={}),
                PlanCall(seq=2, tool="get_fleet_health", kind="READ", args={}),
                PlanCall(seq=3, tool="get_fleet_events", kind="READ", args={}),
            ],
        ),
    ]

    for p in plans:
        result = validate_plan(p)
        assert result.approved is True, f"Policy gate rejected {p.objective_id}: {result.violations}"
        assert len(result.violations) == 0
