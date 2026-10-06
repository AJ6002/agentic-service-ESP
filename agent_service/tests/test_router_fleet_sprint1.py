import pytest
from app.contracts.routing import RouterInput
from app.routing.router import route_query, route_query_full
from app.routing.objective_registry import load_objective_registry, clear_objective_registry


@pytest.fixture(autouse=True)
def reload_registry():
    clear_objective_registry()
    load_objective_registry(force_reload=True)


@pytest.mark.anyio
async def test_case_1_which_wells_tripped():
    r_in = RouterInput(raw_message="which wells tripped")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "FLEET"
    assert decision.clarification_needed is False


@pytest.mark.anyio
async def test_case_2_list_all_wells():
    r_in = RouterInput(raw_message="list all wells")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "FLEET"
    assert decision.clarification_needed is False


@pytest.mark.anyio
async def test_case_3_rank_wells_by_health():
    r_in = RouterInput(raw_message="rank wells by health")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "FLEET"
    assert decision.clarification_needed is False


@pytest.mark.anyio
async def test_case_4_why_did_fs17_trip():
    r_in = RouterInput(raw_message="why did FS-17 trip", asset_id="FS-17")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "ASSET"
    assert decision.objective_id in ("OP03", "OP03_FAULT_DIAGNOSIS")


@pytest.mark.anyio
async def test_case_5_what_is_gas_lock():
    r_in = RouterInput(raw_message="What is gas lock")
    decision = await route_query(r_in)
    assert decision.route == "SIMPLE"
    assert decision.scope == "GLOBAL"
    assert decision.objective_id in ("OP06", "OP06_KNOWLEDGE_LOOKUP")


@pytest.mark.anyio
async def test_case_6_what_is_this_page():
    r_in = RouterInput(raw_message="What is this page", selected_route="/working-status")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "GLOBAL"
    assert decision.objective_id in ("OP15", "OP15_PLATFORM_GUIDE")


@pytest.mark.anyio
async def test_case_7_what_are_you():
    r_in = RouterInput(raw_message="What are you")
    decision = await route_query(r_in)
    assert decision.route == "IDENTITY"
    assert decision.scope == "GLOBAL"


@pytest.mark.anyio
async def test_case_8_show_me_fleet_summary():
    r_in = RouterInput(raw_message="Show me fleet summary")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "FLEET"
    assert decision.clarification_needed is False


@pytest.mark.anyio
async def test_case_9_how_many_wells_running():
    r_in = RouterInput(raw_message="How many wells running")
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.scope == "FLEET"
    assert decision.clarification_needed is False
