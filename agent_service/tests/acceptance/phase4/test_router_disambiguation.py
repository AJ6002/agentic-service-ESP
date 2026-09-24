import pytest
from app.contracts.routing import RouterInput
from app.routing.router import route_query_full

ROUTER_TEST_MATRIX = [
    ("Why did you say gas interference?", "FOLLOW_UP", False),
    ("What data did you use?", "FOLLOW_UP", False),
    ("What does that graph mean?", "FOLLOW_UP", False),
    ("Explain your reasoning on that diagnosis", "FOLLOW_UP", False),
    ("Why did you conclude that?", "FOLLOW_UP", False),
    ("Recheck with the last 2 hours", "WORKFLOW", False),
    ("What's the current status now?", "WORKFLOW", False),
    ("What is underload protection?", "SIMPLE", False),
    ("Explain gas lock.", "SIMPLE", False),
    ("Why did that happen?", "WORKFLOW", True),  # Ambiguous -> Clarify
]

@pytest.mark.anyio
@pytest.mark.parametrize("query,expected_route,expected_clarify", ROUTER_TEST_MATRIX)
async def test_router_heuristic_table(query, expected_route, expected_clarify):
    """Router 1: Heuristic fallback table accurately classifies intent."""
    r_in = RouterInput(
        raw_message=query,
        asset_id="FS-17",
        asset_source="SESSION",
        turn_count=2,
    )
    res = await route_query_full(r_in)
    dec = res.decision
    assert dec.route == expected_route, f"Query '{query}' expected route {expected_route}, got {dec.route}"
    assert dec.clarification_needed == expected_clarify, f"Query '{query}' expected clarify {expected_clarify}, got {dec.clarification_needed}"

@pytest.mark.anyio
async def test_router_past_vs_present_tense():
    """Router 2: Past-tense explanatory -> FOLLOW_UP; present-tense fresh -> WORKFLOW."""
    r_past = RouterInput(raw_message="Why did you say that?", asset_id="FS-17", turn_count=2)
    dec_past = (await route_query_full(r_past)).decision
    assert dec_past.route == "FOLLOW_UP"

    r_pres = RouterInput(raw_message="What is the telemetry now?", asset_id="FS-17", turn_count=2)
    dec_pres = (await route_query_full(r_pres)).decision
    assert dec_pres.route == "WORKFLOW"

@pytest.mark.anyio
async def test_router_why_trip_with_prior():
    """Router 3: 'Why did it trip?' with prior diagnosis routes to WORKFLOW (not FOLLOW_UP)."""
    r_in = RouterInput(raw_message="Why did it trip?", asset_id="FS-17", turn_count=2)
    dec = (await route_query_full(r_in)).decision
    assert dec.route == "WORKFLOW"
    assert dec.objective_id == "OP03_FAULT_DIAGNOSIS"

@pytest.mark.anyio
async def test_router_graph_query():
    """Router 4: 'What does the graph show?' routes to FOLLOW_UP."""
    r_in = RouterInput(raw_message="What does the graph show?", asset_id="FS-17", turn_count=2)
    dec = (await route_query_full(r_in)).decision
    assert dec.route == "FOLLOW_UP"

@pytest.mark.anyio
async def test_router_empty_session_handling():
    """Router 5: Follow-up question in turn 1 still routes to FOLLOW_UP (handled by handler expiration)."""
    r_in = RouterInput(raw_message="Why did you say gas interference?", asset_id=None, turn_count=1)
    dec = (await route_query_full(r_in)).decision
    assert dec.route == "FOLLOW_UP"
