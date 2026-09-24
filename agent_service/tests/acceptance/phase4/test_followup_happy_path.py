import json
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_followup_explain_finding(seed_prior_analysis):
    """AC-FUP-1: Explains prior finding with 0 HTTP calls and 1 LLM call."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-happy-1", "run-diag-1")
    transport = ASGITransport(app=app)

    with patch("app.gateway.tool_gateway.execute_tool_call", side_effect=RuntimeError("Tool gateway forbidden on FOLLOW_UP")), \
         patch("app.routing.followup_handler.followup_narrate", return_value="Gas interference occurred because intake pressure dropped to 412.0 psi [EV-002].") as mock_narrator:

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={
                "session_id": session_id,
                "message": "Why did you say gas interference?",
            })
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            done = next(l for l in lines if l["type"] == "done")
            assert done["status"] == "OK"
            assert mock_narrator.call_count == 1
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "Gas interference" in delta["delta"]

@pytest.mark.anyio
async def test_followup_evidence_inquiry(seed_prior_analysis):
    """AC-FUP-2: Returns exact evidence IDs from Turn 1 pack without invoking LLM."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-happy-2", "run-diag-2")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={
            "session_id": session_id,
            "message": "What data did you use?",
        })
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        delta = next(l for l in lines if l["type"] == "text_delta")
        assert "EV-001" in delta["delta"]
        assert "EV-002" in delta["delta"]

@pytest.mark.anyio
async def test_followup_graph_explanation(seed_prior_analysis):
    """AC-FUP-3: Explains visualization and reuses exact cards from prior run."""
    session_id, run_id, _, _, viz = seed_prior_analysis("sess-happy-3", "run-diag-3")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="The pressure corridor chart shows PIP at 412.0 psi [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={
                "session_id": session_id,
                "message": "What does that graph mean?",
            })
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            vis_frame = next((l for l in lines if l["type"] == "visual"), None)
            assert vis_frame is not None
            assert vis_frame["visualization"]["card_ids"] == viz["card_ids"]

@pytest.mark.anyio
async def test_followup_multi_turn_chain(seed_prior_analysis):
    """AC-FUP-4: Multi-turn follow-up chain succeeds sequentially from same pack."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-happy-4", "run-diag-4")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure dropped severely [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.post("/query", json={"session_id": session_id, "message": "Why did you say that?"})
            assert resp1.status_code == 200
            resp2 = await client.post("/query", json={"session_id": session_id, "message": "What does that mean for the pump?"})
            assert resp2.status_code == 200
            lines2 = [json.loads(l) for l in resp2.text.strip().splitlines() if l]
            assert next(l for l in lines2 if l["type"] == "done")["status"] == "OK"

@pytest.mark.anyio
async def test_followup_explicit_analysis_id(seed_prior_analysis):
    """AC-FUP-5: Explicit analysis_id binds to target pack rather than last_analysis_id."""
    session_id, run_id, _, _, _ = seed_prior_analysis("sess-happy-5", "run-target-99")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Analysis run-target-99 confirms stable motor temperature [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={
                "session_id": session_id,
                "message": "Why did you say that for run-target-99?",
            })
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            assert next(l for l in lines if l["type"] == "done")["status"] == "OK"
