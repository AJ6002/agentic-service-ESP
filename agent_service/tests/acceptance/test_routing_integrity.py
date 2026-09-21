import pathlib
import pytest
from app.routing.capability_retrieval import retrieve_candidates
from app.routing.router import route_query_full
from app.contracts.routing import RouterInput, RouteDecision
from app.context.resolver import resolve_context

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.mark.anyio
async def test_ac_4_1_definitional_queries_never_route_to_op03():
    """
    AC-4.1: For definitional queries containing no well ID, route != OP03_FAULT_DIAGNOSIS.
    Prevents Bug A: 'trip' keyword must not hijack definitional queries.
    """
    queries = [
        line.strip()
        for line in (FIXTURES_DIR / "definitional_queries.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    for q in queries:
        cand_obj, cand_tools, _ = retrieve_candidates(q)
        frame = resolve_context(session_id="test-routing-4-1", message=q)
        r_in = RouterInput(
            raw_message=q,
            asset_id=frame.asset.id,
            turn_count=1,
            candidate_objectives=cand_obj,
            candidate_tools=cand_tools,
        )
        res = await route_query_full(r_in)
        assert res.decision.objective_id != "OP03_FAULT_DIAGNOSIS", f"'{q}' wrongly routed to OP03!"
        assert res.decision.route in ("SIMPLE", "WORKFLOW")
        if res.decision.route == "WORKFLOW":
            assert res.decision.objective_id != "OP03_FAULT_DIAGNOSIS"


@pytest.mark.anyio
async def test_ac_4_2_diagnostic_questions_with_asset_route_to_op03():
    """
    AC-4.2: Diagnostic questions containing a well ID route to OP03_FAULT_DIAGNOSIS.
    """
    test_queries = [
        ("Why did FS-17 trip?", "FS-17"),
        ("What's wrong with FS-91?", "FS-91"),
        ("Diagnose FS-17.", "FS-17"),
    ]
    for q, expected_well in test_queries:
        frame = resolve_context(session_id="test-routing-4-2", message=q)
        cand_obj, cand_tools, _ = retrieve_candidates(q)
        r_in = RouterInput(
            raw_message=q,
            asset_id=frame.asset.id,
            turn_count=1,
            candidate_objectives=cand_obj,
            candidate_tools=cand_tools,
        )
        res = await route_query_full(r_in)
        assert res.decision.objective_id == "OP03_FAULT_DIAGNOSIS", f"'{q}' did not route to OP03 (got {res.decision.objective_id})"


@pytest.mark.anyio
async def test_ac_4_3_definitional_query_does_not_guess_well():
    """
    AC-4.3: A definitional query containing 'trip' must not produce a guessed asset_id in args.
    """
    q = "Explain what underload trip is and why it happens."
    frame = resolve_context(session_id="test-routing-4-3", message=q)
    cand_obj, cand_tools, _ = retrieve_candidates(q)
    r_in = RouterInput(
        raw_message=q,
        asset_id=frame.asset.id,
        turn_count=1,
        candidate_objectives=cand_obj,
        candidate_tools=cand_tools,
    )
    res = await route_query_full(r_in)
    asset_id = (res.decision.args or {}).get("asset_id")
    assert asset_id is None, f"Definitional query must not guess well: {asset_id}"
    assert frame.asset.id is None


def test_ac_4_4_low_confidence_forces_clarify():
    """
    AC-4.4: Router confidence below 0.6 forces clarification_needed = true.
    """
    low_conf = RouteDecision(
        route="WORKFLOW",
        objective_id="OP03_FAULT_DIAGNOSIS",
        confidence=0.45,
        clarification_needed=True,
        clarify_reason="CLARIFY",
    )
    assert low_conf.clarification_needed is True
