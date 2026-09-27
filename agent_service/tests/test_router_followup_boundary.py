"""
Test router follow-up boundary and session isolation (U3 & U6).
Verifies that explicit FOLLOWUP_PATTERNS queries on fresh sessions route to FOLLOW_UP
(which returns ANALYSIS_EXPIRED) rather than CLARIFY on asset_id, while AMBIGUOUS_FOLLOWUP_PATTERNS
queries continue to ask for CLARIFY.
"""
import uuid
import pytest

import app.contracts  # break circular import
from app.contracts.routing import RouterInput
from app.routing.router import route_query_full
from app.routing.followup_handler import handle_followup


@pytest.mark.anyio
async def test_fresh_session_explicit_followup_routes_to_follow_up():
    """A fresh session with an explicit follow-up question routes to FOLLOW_UP."""
    session_id = f"test-fup-{uuid.uuid4().hex}"
    r_in = RouterInput(
        raw_message="Why did you conclude that?",
        session_id=session_id,
        asset_id=None,
        has_prior=False,
        turn_count=1,
    )
    res = await route_query_full(r_in)
    dec = res.decision

    assert dec.route == "FOLLOW_UP"
    assert not dec.clarification_needed
    assert dec.clarify_reason is None


@pytest.mark.anyio
async def test_fresh_session_followup_execution_returns_analysis_expired():
    """Executing follow-up on a fresh session with no prior analysis returns ANALYSIS_EXPIRED."""
    session_id = f"test-fup-{uuid.uuid4().hex}"
    res = await handle_followup(
        session_id=session_id,
        raw_message="Why did you conclude that?",
    )

    assert not res.ok
    assert res.code == "ANALYSIS_EXPIRED"
    assert "expired or not found" in res.message.lower()


@pytest.mark.anyio
async def test_fresh_session_ambiguous_followup_routes_to_clarify():
    """A fresh session with ambiguous follow-up ('Why did that happen?') routes to CLARIFY."""
    session_id = f"test-fup-{uuid.uuid4().hex}"
    r_in = RouterInput(
        raw_message="Why did that happen?",
        session_id=session_id,
        asset_id=None,
        has_prior=False,
        turn_count=1,
    )
    res = await route_query_full(r_in)
    dec = res.decision

    assert dec.route == "WORKFLOW"
    assert dec.clarification_needed
    assert dec.clarify_reason == "CLARIFY"
    assert dec.clarify_slot == "asset_id"


@pytest.mark.anyio
async def test_turn_count_accumulation_does_not_mask_routing():
    """Setting turn_count=7 on fresh session still routes explicit follow-up to FOLLOW_UP."""
    session_id = f"test-fup-{uuid.uuid4().hex}"
    r_in = RouterInput(
        raw_message="Why did you say that?",
        session_id=session_id,
        asset_id=None,
        has_prior=False,
        turn_count=7,
    )
    res = await route_query_full(r_in)
    dec = res.decision

    assert dec.route == "FOLLOW_UP"
    assert not dec.clarification_needed


@pytest.mark.anyio
async def test_q2_clarify_then_q3_bind_resumes_successfully():
    """Check 6: Q2 ('Explain that') triggers CLARIFY, then Q3 ('FS-17') binds and resumes."""
    import json
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.stores.session_store import delete_pending, delete_session

    session_id = f"test-bind-{uuid.uuid4().hex}"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: "Explain that" -> should raise CLARIFY for asset_id
        r1 = await client.post("/query", json={"session_id": session_id, "message": "Explain that"})
        assert r1.status_code == 200
        lines1 = [json.loads(l) for l in r1.text.strip().splitlines() if l]
        assert any(l["type"] == "clarification" for l in lines1), f"Expected clarification, got: {lines1}"
        done1 = next(l for l in lines1 if l["type"] == "done")
        assert done1["status"] == "PAUSED"

        # Turn 2: "FS-17" -> should BIND and resume execution
        r2 = await client.post("/query", json={"session_id": session_id, "message": "FS-17"})
        assert r2.status_code == 200
        lines2 = [json.loads(l) for l in r2.text.strip().splitlines() if l]
        # Must not clarify again
        assert not any(l["type"] == "clarification" for l in lines2), f"Unexpected second clarification: {lines2}"
        # Must have completed
        done2 = next((l for l in lines2 if l["type"] == "done"), None)
        assert done2 is not None
        assert done2["status"] == "OK"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "query",
    [
        "What data did you look at to figure that out?",
        "What data was used for that diagnosis?",
        "What data did you check?",
        "How did you figure that out?",
        "Explain your reasoning on that diagnosis",
    ],
)
async def test_conversational_data_inquiries_route_to_follow_up(query):
    """Conversational follow-up data queries route deterministically to FOLLOW_UP."""
    session_id = f"test-fup-{uuid.uuid4().hex}"
    r_in = RouterInput(
        raw_message=query,
        session_id=session_id,
        asset_id=None,
        has_prior=True,
        turn_count=2,
    )
    res = await route_query_full(r_in)
    dec = res.decision

    assert dec.route == "FOLLOW_UP"
    assert not dec.clarification_needed


