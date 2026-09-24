import json
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_provenance_clean_followup(seed_prior_analysis):
    """Provenance 1: Clean follow-up narrative passes provenance check."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-prov-1", "run-p1")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="The intake pressure was 412.0 psi [EV-002] and motor temp 88.4 C [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "Unverified" not in delta["delta"]
            assert next(l for l in lines if l["type"] == "done")["status"] == "OK"

@pytest.mark.anyio
async def test_provenance_injected_fake_number(seed_prior_analysis):
    """Provenance 2: Injected ungrounded number is flagged."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-prov-2", "run-p2")
    transport = ASGITransport(app=app)

    # Injected fake numbers 999.99 and 777.77 not in pack
    with patch("app.llm.calls.call_llm_chat", return_value="The pressure was 999.99 psi and frequency 777.77 Hz."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "Unverified numbers flagged" in delta["delta"]

@pytest.mark.anyio
async def test_provenance_regex_diff(seed_prior_analysis):
    """Provenance 3: Verify all numbers in clean follow-up exist in pack."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-prov-3", "run-p3")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Intake pressure is 412.0 psi and discharge is 1890.0 psi [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say that?"})
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            delta = next(l for l in lines if l["type"] == "text_delta")
            assert "412.0" in delta["delta"]
            assert "1890.0" in delta["delta"]
