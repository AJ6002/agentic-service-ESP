import json
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_stream_shape_single_done_frame(seed_prior_analysis):
    """Shape 1: Exactly one DoneFrame emitted per response stream."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-stream-1", "run-s1")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Gas interference occurred [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say gas interference?"})
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            done_frames = [l for l in lines if l["type"] == "done"]
            assert len(done_frames) == 1

@pytest.mark.anyio
async def test_stream_shape_expired_pack():
    """Shape 2: Expired path emits ErrorFrame + DoneFrame(INSUFFICIENT) only."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": "sess-empty-shape", "message": "Why did you say that?"})
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]
        assert "error" in types
        assert "done" in types
        assert types[-1] == "done"
        assert next(l for l in lines if l["type"] == "done")["status"] == "INSUFFICIENT"

@pytest.mark.anyio
async def test_stream_shape_valid_frame_types(seed_prior_analysis):
    """Shape 3: Only recognized FrameTypes emitted in stream."""
    session_id, _, _, _, _ = seed_prior_analysis("sess-stream-3", "run-s3")
    transport = ASGITransport(app=app)

    with patch("app.llm.calls.call_llm_chat", return_value="Intake was 412.0 psi [EV-002]."):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/query", json={"session_id": session_id, "message": "Why did you say that?"})
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            allowed_types = {"status", "text_delta", "advisory", "visual", "error", "done"}
            for l in lines:
                assert l["type"] in allowed_types, f"Unexpected frame type: {l['type']}"
