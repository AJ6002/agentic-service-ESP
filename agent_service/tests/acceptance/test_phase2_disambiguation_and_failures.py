import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
import httpx
from app.main import app
from app.stores.session_store import delete_pending, delete_session
from app.contracts.routing import RouterInput
from app.routing.router import route_query_full


# ---------------------------------------------------------------------------
# Phase Check 2: The One Test That Seals It (6 Disambiguation Queries)
# ---------------------------------------------------------------------------

SEALING_6_QUERIES = [
    ("Why has FS-17 production declined?", "OP02_PRODUCTION_DECLINE_RCA", "WORKFLOW"),
    ("What is underload protection?", "OP06_KNOWLEDGE_LOOKUP", "SIMPLE"),
    ("Explain gas lock.", "OP06_KNOWLEDGE_LOOKUP", "SIMPLE"),
    ("How healthy is FS-17?", "OP04_HEALTH_ASSESSMENT", "WORKFLOW"),
    ("Any early warnings for FS-17?", "OP05_EARLY_WARNING", "WORKFLOW"),
    ("Show me FS-17 history for the last 7 days", "OP14_OPERATIONAL_HISTORY", "WORKFLOW"),
]

@pytest.mark.anyio
@pytest.mark.parametrize("query,expected_op,expected_route", SEALING_6_QUERIES)
async def test_sealing_6_queries_disambiguation(query, expected_op, expected_route):
    """The one test that seals it: all 6 canonical queries route to exact expected OP."""
    well_id = "FS-17" if "FS-17" in query else None
    r_in = RouterInput(
        raw_message=query,
        asset_id=well_id,
        asset_source="EXPLICIT" if well_id else "UNRESOLVED",
        turn_count=1,
    )
    res = await route_query_full(r_in)
    dec = res.decision
    assert dec.route == expected_route, f"Query '{query}' route mismatch: {dec.route} != {expected_route}"
    assert dec.objective_id == expected_op, f"Query '{query}' op mismatch: {dec.objective_id} != {expected_op}"


# ---------------------------------------------------------------------------
# Phase Check 3: Slice 2 Non-Regression (OP01, OP03, OP07)
# ---------------------------------------------------------------------------

SLICE2_QUERIES = [
    ("What's the current status of FS-17?", "OP01_CURRENT_STATUS", "WORKFLOW"),
    ("Why did FS-17 trip?", "OP03_FAULT_DIAGNOSIS", "WORKFLOW"),
]

@pytest.mark.anyio
@pytest.mark.parametrize("query,expected_op,expected_route", SLICE2_QUERIES)
async def test_slice2_non_regression_routing(query, expected_op, expected_route):
    """Slice 2 objectives (OP01, OP03) route correctly without regression."""
    r_in = RouterInput(
        raw_message=query,
        asset_id="FS-17",
        asset_source="EXPLICIT",
        turn_count=1,
    )
    res = await route_query_full(r_in)
    dec = res.decision
    assert dec.route == expected_route
    assert dec.objective_id == expected_op


# ---------------------------------------------------------------------------
# Phase Check 4 & Per-Obj Check 5: Three Kill-Switch Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_kill_switch_server_184_down():
    """Kill switch 1: Server 184 down -> INSUFFICIENT ErrorFrame, status INSUFFICIENT, zero fake numbers."""
    session_id = "test-kill-184"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    # Simulate network failure to Server 184 (:8090)
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused to Server 184:8090")):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/query",
                json={"session_id": session_id, "message": "Why has FS-17 production declined?"},
            )
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            types = [l["type"] for l in lines]
            done = next(l for l in lines if l["type"] == "done")
            assert done["status"] == "INSUFFICIENT"
            # Must emit ErrorFrame with INSUFFICIENT_EVIDENCE
            assert "error" in types
            err = next(l for l in lines if l["type"] == "error")
            assert err["code"] == "INSUFFICIENT_EVIDENCE"
            # Must NOT emit AdvisoryFrame with fake decline claims
            assert "advisory" not in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_kill_switch_kb_down():
    """Kill switch 2: KB Service down (:8085) -> INSUFFICIENT ErrorFrame, status INSUFFICIENT, zero fake definitions."""
    session_id = "test-kill-kb"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    with patch("app.gateway.adapters.kb.search_kb", side_effect=httpx.ConnectError("KB service down")):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/query",
                json={"session_id": session_id, "message": "What is underload protection?"},
            )
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            types = [l["type"] for l in lines]
            done = next(l for l in lines if l["type"] == "done")
            assert done["status"] in ("INSUFFICIENT", "FAILED")
            assert "error" in types
            # Must NOT emit fabricated advisory
            assert "advisory" not in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_kill_switch_llm_down():
    """Kill switch 3: LLM gateway down -> ErrorFrame or deterministic fallback flag, never silent hallucination."""
    session_id = "test-kill-llm"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    from app.llm.client import LLMUnavailableError
    with patch("app.llm.client.call_llm_chat", side_effect=LLMUnavailableError("LLM cluster offline")):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/query",
                json={"session_id": session_id, "message": "Assess the health of well FS-17"},
            )
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            types = [l["type"] for l in lines]
            # Must signal fallback or outage via status frame or error frame
            has_status_flag = any(l.get("stage") == "llm_gateway" for l in lines if l.get("type") == "status")
            has_error_flag = "error" in types
            assert has_status_flag or has_error_flag

    delete_pending(session_id)
    delete_session(session_id)
