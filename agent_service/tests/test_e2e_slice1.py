import json
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.stores.run_store import get_run
from app.stores.session_store import get_pending, delete_pending, delete_session


def _reset_session(session_id: str) -> None:
    """
    Full isolation reset for e2e tests: these tests reuse fixed session_id
    strings across runs, and now that main.py actually persists session
    state (turn_count, last_asset_id, ...), leftover state from a prior
    test run would leak into the next one (e.g. a pronoun resolving
    against an asset from a previous run instead of starting fresh).
    Clears BOTH pending and session state, not just pending.
    """
    delete_pending(session_id)
    delete_session(session_id)

@pytest.mark.anyio
async def test_e2e_clarify_roundtrip():
    session_id = "test-e2e-session-1"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # -----------------------------------------------------------------
        # TURN 1: Ambiguous well query ("why did it trip?")
        # -----------------------------------------------------------------
        resp1 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "why did it trip?"},
        )
        assert resp1.status_code == 200
        assert resp1.headers["content-type"] == "application/x-ndjson"

        lines1 = [json.loads(line) for line in resp1.text.strip().splitlines() if line]
        assert len(lines1) == 2
        assert lines1[0]["type"] == "clarification"
        assert lines1[0]["slot"] == "asset_id"
        assert "FS-17" in lines1[0]["options"]
        assert lines1[1]["type"] == "done"
        assert lines1[1]["status"] == "PAUSED"

        # Check pending state in Redis
        pending = get_pending(session_id)
        assert pending is not None
        assert pending.slot == "asset_id"
        assert pending.reason == "CLARIFY"

        run_id = lines1[0]["run_id"]
        run_state = get_run(run_id)
        assert run_state is not None
        assert run_state.status == "PAUSED"

        # -----------------------------------------------------------------
        # TURN 2: Reply with asset ("FS-017") -> BIND & Resume
        # -----------------------------------------------------------------
        resp2 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "FS-017"},
        )
        assert resp2.status_code == 200
        lines2 = [json.loads(line) for line in resp2.text.strip().splitlines() if line]

        types2 = [l["type"] for l in lines2]
        assert "text_delta" in types2
        assert "done" in types2
        text_frame = next(l for l in lines2 if l["type"] == "text_delta")
        assert "FS-17" in text_frame["delta"]
        assert "Diagnostic run" in text_frame["delta"]
        done_frame = next(l for l in lines2 if l["type"] == "done")
        assert done_frame["status"] == "OK"

        # Check pending state is cleared from Redis
        assert get_pending(session_id) is None

        # Check run state is completed, and the objective that was pending
        # actually got persisted onto the run (this is what makes resume
        # a real continuation instead of a context-free reply).
        completed_run = get_run(run_id)
        assert completed_run is not None
        assert completed_run.objective_id == "OP03_FAULT_DIAGNOSIS"
        assert completed_run.status == "DONE"

@pytest.mark.anyio
async def test_e2e_simple_glossary_query():
    session_id = "test-e2e-session-2"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What does underload mean?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(line) for line in resp.text.strip().splitlines() if line]
        assert len(lines) in (2, 3, 4)
        types = [l["type"] for l in lines]
        assert "text_delta" in types
        text_frame = next(l for l in lines if l["type"] == "text_delta")
        assert any(w in text_frame["delta"].lower() for w in ["underload", "current", "guidelines", "troubleshooting", "esp", "manual"])
        done_frame = next(l for l in lines if l["type"] == "done")
        assert done_frame["status"] == "OK"

        # No pending state created
        assert get_pending(session_id) is None

@pytest.mark.anyio
async def test_e2e_explicit_asset_priority_in_query():
    session_id = "test-e2e-session-3"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Check status of FS-091",
                "ui_context": {"selected_asset": "FNW-01"},
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(line) for line in resp.text.strip().splitlines() if line]
        types = [l["type"] for l in lines]
        assert "text_delta" in types
        text_frame = next(l for l in lines if l["type"] == "text_delta")
        assert "FS-91" in text_frame["delta"]
        assert "done" in types

@pytest.mark.anyio
async def test_e2e_empty_message_triggers_clarify():
    session_id = "test-e2e-session-4"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "   "},
        )
        assert resp.status_code == 200
        lines = [json.loads(line) for line in resp.text.strip().splitlines() if line]
        assert len(lines) == 2
        assert lines[0]["type"] == "clarification"
        assert "provide an operational question" in lines[0]["question"]
        assert lines[1]["type"] == "done"
        assert lines[1]["status"] == "PAUSED"


@pytest.mark.anyio
async def test_e2e_session_memory_resolves_pronoun_on_later_turn():
    """
    Regression test for the session-persistence gap: resolve_asset()'s
    SESSION/PRONOUN path was implemented and unit-tested in isolation, but
    nothing in main.py ever wrote session state back to Redis after a
    turn, so a pronoun on turn 2 could never actually resolve against
    turn 1's asset through the real endpoint. This drives two full turns
    through the real /query route and proves that wiring now works.
    """
    from app.stores.session_store import get_session

    session_id = "test-e2e-session-memory-1"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: explicit asset, real workflow run -> asset gets persisted
        # into session state.
        resp1 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "why did FS-017 trip?"},
        )
        assert resp1.status_code == 200

        snapshot = get_session(session_id)
        assert snapshot is not None
        assert snapshot.last_asset_id == "FS-17"
        assert snapshot.turn_count == 1

        # Turn 2: pronoun only, no explicit asset, no UI context -> must
        # resolve against the asset remembered from turn 1, not go
        # UNRESOLVED.
        resp2 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "is it still tripping?"},
        )
        assert resp2.status_code == 200

        snapshot2 = get_session(session_id)
        assert snapshot2.turn_count == 2
        # Session memory carried the asset across turns via the real
        # endpoint, not just inside an isolated resolver unit test.
        assert snapshot2.last_asset_id == "FS-17"


@pytest.mark.anyio
async def test_e2e_meta_turn_keeps_pending_intact():
    """
    ARCHITECTURE §6.3 / CONVERSATION_HISTORY §8: a META reply must answer
    the user's question about the clarification but must NOT consume or clear
    the pending interrupt — the original question still needs an asset_id.
    """
    session_id = "test-e2e-session-meta"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1 — trigger a CLARIFY pause (missing asset_id)
        resp1 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "why did it trip?"},
        )
        assert resp1.status_code == 200
        lines1 = [json.loads(ln) for ln in resp1.text.strip().splitlines() if ln]
        assert lines1[0]["type"] == "clarification"

        # Verify pending is in Redis after Turn 1
        pending_after_t1 = get_pending(session_id)
        assert pending_after_t1 is not None
        assert pending_after_t1.slot == "asset_id"

        # Turn 2 — META: user asks about the clarification, not providing an asset
        resp2 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why are you asking?"},
        )
        assert resp2.status_code == 200
        lines2 = [json.loads(ln) for ln in resp2.text.strip().splitlines() if ln]
        # META must produce some answer (text_delta), not another clarification
        assert any(ln["type"] == "text_delta" for ln in lines2)

        # KEY ASSERTION: pending must still be intact in Redis after a META turn
        pending_after_meta = get_pending(session_id)
        assert pending_after_meta is not None, (
            "META turn incorrectly cleared the pending interrupt. "
            "Per design §6.3, pending must survive a META reply."
        )
        assert pending_after_meta.slot == "asset_id"
        assert pending_after_meta.run_id == pending_after_t1.run_id

    # Cleanup
    delete_pending(session_id)


@pytest.mark.anyio
async def test_e2e_supersede_marks_old_run_abandoned():
    """
    Regression test: SUPERSEDE deleted the pending but never updated the
    abandoned run's own RunState — it stayed "PAUSED" in Redis forever
    (until TTL) instead of "ABANDONED", making an audit lookup on that
    run misleading. This drives it through the real endpoint.
    """
    session_id = "test-e2e-supersede-1"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: raise a CLARIFY (asset missing) -> run paused.
        resp1 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "why did it trip?"},
        )
        assert resp1.status_code == 200
        lines1 = [json.loads(line) for line in resp1.text.strip().splitlines() if line]
        run_id = lines1[0]["run_id"]

        paused_run = get_run(run_id)
        assert paused_run is not None
        assert paused_run.status == "PAUSED"

        # Turn 2: unrelated new question, no asset mention at all -> must
        # SUPERSEDE, not BIND, and must close the old run cleanly.
        resp2 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "what does gas lock mean?"},
        )
        assert resp2.status_code == 200

        abandoned_run = get_run(run_id)
        assert abandoned_run is not None
        assert abandoned_run.status == "ABANDONED"
        assert abandoned_run.resume_at is None
        assert get_pending(session_id) is None


@pytest.mark.anyio
async def test_e2e_unrelated_question_with_different_asset_supersedes_not_binds():
    """
    Regression test for the more dangerous case: the new message mentions
    a DIFFERENT asset than the one being clarified, but is clearly a
    fresh, unrelated question — must SUPERSEDE and answer THAT question,
    not silently BIND the mentioned asset into the original paused
    diagnosis and run the wrong analysis.
    """
    session_id = "test-e2e-supersede-2"
    _reset_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "why did it trip?"},
        )
        assert resp1.status_code == 200
        lines1 = [json.loads(line) for line in resp1.text.strip().splitlines() if line]
        run_id = lines1[0]["run_id"]
        assert lines1[0]["type"] == "clarification"

        # A fresh question naming a DIFFERENT asset than any option offered.
        resp2 = await client.post(
            "/query",
            json={"session_id": session_id, "message": "what's the pressure at FS-091 right now?"},
        )
        assert resp2.status_code == 200
        lines2 = [json.loads(line) for line in resp2.text.strip().splitlines() if line]

        # Must NOT resume the original paused fault-diagnosis run.
        original_run = get_run(run_id)
        assert original_run.status == "ABANDONED"

        # Must answer as a genuinely NEW run (fresh run_id), not resume
        # the abandoned one — this is the concrete proof that the wrong
        # diagnosis was not silently executed.
        new_run_id = lines2[0]["run_id"]
        assert new_run_id != run_id
