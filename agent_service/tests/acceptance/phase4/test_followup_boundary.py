import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_boundary_trip_query_after_op03(seed_prior_analysis):
    """Boundary 1: 'Why did it trip?' after OP03 routes to WORKFLOW, not FOLLOW_UP."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-bound-1", "run-prev-1")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": session_id, "message": "Why did it trip?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        adv = next((l for l in lines if l["type"] == "advisory"), None)
        if adv:
            assert adv["advisory"]["objective_id"] == "OP03_FAULT_DIAGNOSIS"
        else:
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "OP03_FAULT_DIAGNOSIS" in delta["delta"]

@pytest.mark.anyio
async def test_boundary_recheck_time_window(seed_prior_analysis):
    """Boundary 2: 'Recheck with the last 2 hours' routes to WORKFLOW (fresh fetch)."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-bound-2", "run-prev-2")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": session_id, "message": "Recheck with the last 2 hours"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        # Must execute WORKFLOW
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        assert any(l["type"] == "visual" for l in lines)

@pytest.mark.anyio
async def test_boundary_ambiguous_query(seed_prior_analysis):
    """Boundary 3: Ambiguous 'Why did that happen?' routes to CLARIFY."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-bound-3", "run-prev-3")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": session_id, "message": "Why did that happen?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "PAUSED"
        clarify = next((l for l in lines if l["type"] == "clarification"), None)
        assert clarify is not None

@pytest.mark.anyio
async def test_boundary_no_prior_analysis():
    """Boundary 4: Follow-up question in empty session yields ANALYSIS_EXPIRED ErrorFrame."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": "sess-empty-fup", "message": "Why did you say that?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        err = next((l for l in lines if l["type"] == "error"), None)
        assert err is not None
        assert err["code"] == "ANALYSIS_EXPIRED"
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "INSUFFICIENT"

@pytest.mark.anyio
async def test_boundary_definitional_unaffected(seed_prior_analysis):
    """Boundary 5: 'What is underload protection?' after OP03 routes to OP06_KNOWLEDGE_LOOKUP."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-bound-5", "run-prev-5")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": session_id, "message": "What is underload protection?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        adv = next((l for l in lines if l["type"] == "advisory"), None)
        if adv:
            assert adv["advisory"]["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"
        else:
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "OP06_KNOWLEDGE_LOOKUP" in delta["delta"]

@pytest.mark.anyio
async def test_boundary_workflow_after_followup(seed_prior_analysis):
    """Boundary 6: Fresh WORKFLOW query after FOLLOW_UP executes full fresh pipeline."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-bound-6", "run-prev-6")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Follow-up turn
        await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
        # 2. Fresh status query
        resp = await client.post("/query", json={"session_id": session_id, "message": "What is the current status of FS-17?"})
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        adv = next((l for l in lines if l["type"] == "advisory"), None)
        if adv:
            assert adv["advisory"]["objective_id"] == "OP01_CURRENT_STATUS"
        else:
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "OP01_CURRENT_STATUS" in delta["delta"]
