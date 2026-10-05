import pytest
from app.contracts.routing import RouterInput
from app.routing.router import route_query, route_query_full
from app.routing.objective_registry import load_objective_registry, clear_objective_registry


@pytest.fixture(autouse=True)
def reload_registry():
    clear_objective_registry()
    load_objective_registry(force_reload=True)


@pytest.mark.anyio
async def test_route_1_working_status_page():
    r_in = RouterInput(raw_message="what is the working status page")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP15", "OP15_PLATFORM_GUIDE")


@pytest.mark.anyio
async def test_route_2_subsystem_equalizer():
    r_in = RouterInput(raw_message="what does the subsystem equalizer show")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP15", "OP15_PLATFORM_GUIDE")


@pytest.mark.anyio
async def test_route_3_navigation_how_to_get_to():
    r_in = RouterInput(raw_message="how do I get to reliability")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP15", "OP15_PLATFORM_GUIDE")


@pytest.mark.anyio
async def test_route_4_explain_chart_with_route_context():
    r_in = RouterInput(
        raw_message="explain this chart",
        selected_route="/working-status",
    )
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP15", "OP15_PLATFORM_GUIDE")


@pytest.mark.anyio
async def test_route_5_gas_lock_concept():
    r_in = RouterInput(raw_message="What is gas lock?")
    decision = await route_query(r_in)
    assert decision.route == "SIMPLE"
    assert decision.objective_id in ("OP06", "OP06_KNOWLEDGE_LOOKUP")


@pytest.mark.anyio
async def test_route_6_tdh_concept():
    r_in = RouterInput(raw_message="What is TDH?")
    decision = await route_query(r_in)
    assert decision.route == "SIMPLE"
    assert decision.objective_id in ("OP06", "OP06_KNOWLEDGE_LOOKUP")


@pytest.mark.anyio
async def test_route_7_fs17_trip():
    r_in = RouterInput(raw_message="Why did FS-17 trip?", asset_id="FS-17")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP03", "OP03_FAULT_DIAGNOSIS")


@pytest.mark.anyio
async def test_route_8_identity():
    r_in = RouterInput(raw_message="What are you?")
    decision = await route_query(r_in)
    assert decision.route == "IDENTITY"


@pytest.mark.anyio
async def test_route_9_current_status_fs17():
    r_in = RouterInput(raw_message="What is the current status of FS-17?", asset_id="FS-17")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id in ("OP01", "OP01_CURRENT_STATUS")
