import json
import pytest
from httpx import AsyncClient, ASGITransport

from app.contracts.events import DoneFrame, ErrorFrame
from app.contracts.evidence import EvidencePack
from app.synthesis.response_assembler import ResponseAssembler
from app.stores.session_store import delete_pending, delete_session
from app.main import app

_ALLOWED_DONE_STATUSES = {"OK", "PAUSED", "INSUFFICIENT", "FAILED"}

# A well ID that does not exist in the 184 database — all required evidence
# tools will return WELL_NOT_FOUND (Gap.reason == ABSENT) for it.
# Gap-Fill skips ABSENT gaps (permanent failures), so even after one retry
# round the pack is still INSUFFICIENT, and the honest refusal fires.
_NONEXISTENT_WELL = "FS-9999"


@pytest.mark.anyio
async def test_ac_1_1_failed_runs_must_not_return_status_ok():
    """
    AC-1.1: For any run where SealResult.status == INSUFFICIENT (after gap-fill
    exhausted), the terminal DoneFrame.status is INSUFFICIENT (not OK).

    Uses a nonexistent well so all required evidence tools return ABSENT
    (WELL_NOT_FOUND). Gap-Fill skips ABSENT gaps — no retry — and the honest
    refusal fires immediately after the first seal check.
    """
    session_id = "test-ac-1-1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": f"Why did {_NONEXISTENT_WELL} trip?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "INSUFFICIENT", f"Failed run must return INSUFFICIENT, got {done['status']}"
        assert done["status"] != "OK", "Failed run must NEVER return OK"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_ac_1_2_failed_runs_must_not_emit_visual_frames():
    """
    AC-1.2: If pack.sealed == false, the response stream contains zero VisualFrames.
    Uses a nonexistent well (all evidence ABSENT → INSUFFICIENT → no visuals).
    """
    session_id = "test-ac-1-2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": f"Diagnose {_NONEXISTENT_WELL}"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]
        assert "visual" not in types, f"Unsealed/failed run must not emit VisualFrame: {types}"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_ac_1_3_errors_must_use_error_frame_never_text_delta():
    """
    AC-1.3: For any failure outcome (INSUFFICIENT, etc.), the response contains an ErrorFrame
    with a code field. The failure is never delivered as text_delta.
    """
    session_id = "test-ac-1-3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": f"Why did {_NONEXISTENT_WELL} trip?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]

        assert "error" in types, f"Expected ErrorFrame on failure: {types}"
        assert "text_delta" not in types, f"Failure must NOT be delivered as text_delta: {types}"

        err = next(l for l in lines if l["type"] == "error")
        assert err["code"] == "INSUFFICIENT_EVIDENCE"
        assert len(err["message"]) > 0

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_ac_1_4_every_stream_ends_with_exactly_one_done_frame():
    """
    AC-1.4: count(frame.type == "done") == 1 for every run, regardless of outcome.
    """
    test_queries = [
        "What does gas lock mean in an ESP?",     # SIMPLE route
        "Why did it trip?",                        # CLARIFY route (missing asset)
        f"Why did {_NONEXISTENT_WELL} trip?",     # INSUFFICIENT route
    ]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for idx, q in enumerate(test_queries):
            session_id = f"test-ac-1-4-{idx}"
            delete_pending(session_id)
            delete_session(session_id)

            resp = await client.post("/query", json={"session_id": session_id, "message": q})
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            done_frames = [l for l in lines if l["type"] == "done"]
            assert len(done_frames) == 1, f"Expected exactly 1 DoneFrame for '{q}', got {len(done_frames)}"

            delete_pending(session_id)
            delete_session(session_id)


@pytest.mark.anyio
async def test_ac_1_5_done_frame_status_is_fixed_enum():
    """
    AC-1.5: done.status in {OK, PAUSED, INSUFFICIENT, FAILED}. No free strings.
    """
    test_queries = [
        ("What is gas lock?", "OK"),
        ("Why did it trip?", "PAUSED"),
        (f"Why did {_NONEXISTENT_WELL} trip?", "INSUFFICIENT"),
    ]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for idx, (q, expected_status) in enumerate(test_queries):
            session_id = f"test-ac-1-5-{idx}"
            delete_pending(session_id)
            delete_session(session_id)

            resp = await client.post("/query", json={"session_id": session_id, "message": q})
            assert resp.status_code == 200
            lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
            done = next(l for l in lines if l["type"] == "done")
            status = done.get("status")
            assert status in _ALLOWED_DONE_STATUSES, f"Invalid status '{status}' not in {_ALLOWED_DONE_STATUSES}"
            assert status == expected_status

            delete_pending(session_id)
            delete_session(session_id)

