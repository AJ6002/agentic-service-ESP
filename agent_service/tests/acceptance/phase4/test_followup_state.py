import json
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.stores.session_store import get_session

@pytest.mark.anyio
async def test_state_last_analysis_id_unchanged(seed_prior_analysis):
    """State 1: Follow-up turn does NOT overwrite or alter last_analysis_id."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-state-1", "run-diag-orig")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure dropped [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            session = get_session(session_id)
            assert session.last_analysis_id == "run-diag-orig"
            assert session.turn_count == 2

@pytest.mark.anyio
async def test_state_run_id_isolated(seed_prior_analysis):
    """State 2: Follow-up generates unique trace/run ID for audit."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-state-2", "run-diag-orig-2")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure dropped [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            done = next(l for l in lines if l["type"] == "done")
            assert done["run_id"] != "run-diag-orig-2"
            assert done["run_id"].startswith("R-")

@pytest.mark.anyio
async def test_state_cross_session_isolation(seed_prior_analysis):
    """State 3: Session A's pack is completely invisible to Session B."""
    seed_prior_analysis("sess-A", "run-A")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query on Session B asking follow-up
        resp = await client.post("/query", json={"session_id": "sess-B", "message": "Why did you say that?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        assert next(l for l in lines if l["type"] == "error")["code"] == "ANALYSIS_EXPIRED"

@pytest.mark.anyio
async def test_state_followup_after_clarify(seed_prior_analysis):
    """State 4: Pending clarification resolved cleanly before follow-up."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-state-4", "run-diag-4")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Raise clarify
        await client.post("/query", json={"session_id": session_id, "message": "Why did that happen?"})
        # Follow-up directly
        with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure dropped [EV-002]."):
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            assert next(l for l in lines if l["type"] == "done")["status"] == "OK"

@pytest.mark.anyio
async def test_state_ttl_boundary_check(seed_prior_analysis):
    """State 5: Active session succeeds on follow-up."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-state-5", "run-diag-5")
    transport = ASGITransport(app=app)
    with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure is 412.0 psi [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say that?"})
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            assert next(l for l in lines if l["type"] == "done")["status"] == "OK"
