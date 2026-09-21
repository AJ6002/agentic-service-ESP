import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.stores.session_store import delete_pending, delete_session

_NONEXISTENT_WELL = "FS-9999"


@pytest.mark.anyio
async def test_op04_seal_q1_nominal():
    """OP04 Query 1 (Nominal): FS-17 health assessment passes with OK, visuals, and health band."""
    session_id = "test-op04-q1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Assess the health of well FS-17"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]
        assert "done" in types
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        # Check visual cards
        assert "visual" in types
        # Check advisory names health band
        advisory_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert advisory_frame is not None
        assessment = advisory_frame["advisory"]["assessment"].upper()
        assert any(b in assessment for b in ["HEALTHY", "DEGRADED", "CRITICAL"])

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op04_seal_q2_secondary_well():
    """OP04 Query 2 (Secondary Well): FS-91 health assessment passes with OK."""
    session_id = "test-op04-q2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Assess health status of well FS-91"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op04_seal_q3_definitional():
    """OP04 Query 3 (Definitional): Concept question routes to SIMPLE/OP07 with zero visuals."""
    session_id = "test-op04-q3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is an ESP health index and how is it scored?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        types = [l["type"] for l in lines]
        assert "visual" not in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op04_seal_q4_missing_asset():
    """OP04 Query 4 (Clarification): Query missing asset ID pauses for clarification."""
    session_id = "test-op04-q4"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Evaluate the health score and degradation"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "PAUSED"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op04_seal_q5_nonexistent_refusal():
    """OP04 Query 5 (Honest Refusal): Nonexistent well returns INSUFFICIENT."""
    session_id = "test-op04-q5"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": f"Assess the health of well {_NONEXISTENT_WELL}"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "INSUFFICIENT"
        types = [l["type"] for l in lines]
        assert "error" in types
        assert "visual" not in types

    delete_pending(session_id)
    delete_session(session_id)


# ==================== OP05 Tests ====================

@pytest.mark.anyio
async def test_op05_seal_q1_nominal():
    """OP05 Query 1 (Nominal): FS-17 early warning query passes with OK."""
    session_id = "test-op05-q1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Are there any early warning anomaly signs for FS-17?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        types = [l["type"] for l in lines]
        assert "visual" in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op05_seal_q2_secondary_well():
    """OP05 Query 2 (Secondary Well): FS-91 early warning query passes with OK."""
    session_id = "test-op05-q2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is the early warning risk on FS-91?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op05_seal_q3_definitional():
    """OP05 Query 3 (Definitional): Concept question routes to SIMPLE/OP07 with zero visuals."""
    session_id = "test-op05-q3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is early warning anomaly detection for an ESP?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        types = [l["type"] for l in lines]
        assert "visual" not in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op05_seal_q4_missing_asset():
    """OP05 Query 4 (Clarification): Query missing asset ID pauses for clarification."""
    session_id = "test-op05-q4"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Check early warning indicators"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "PAUSED"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op05_seal_q5_nonexistent_refusal():
    """OP05 Query 5 (Honest Refusal): Nonexistent well returns INSUFFICIENT."""
    session_id = "test-op05-q5"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": f"Check early warning signs on {_NONEXISTENT_WELL}"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "INSUFFICIENT"
        types = [l["type"] for l in lines]
        assert "error" in types
        assert "visual" not in types

    delete_pending(session_id)
    delete_session(session_id)


# ==================== OP14 Tests ====================

@pytest.mark.anyio
async def test_op14_seal_q1_nominal():
    """OP14 Query 1 (Nominal): FS-17 history within coverage passes with OK."""
    session_id = "test-op14-q1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Show operational history for FS-17 from 2026-09-18 to 2026-09-19",
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        types = [l["type"] for l in lines]
        assert "visual" in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op14_seal_q2_secondary_well():
    """OP14 Query 2 (Secondary Well): FS-91 history passes with OK."""
    session_id = "test-op14-q2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Provide operational history for FS-91 between 2026-09-18 and 2026-09-19",
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op14_seal_q3_definitional():
    """OP14 Query 3 (Definitional): Concept question routes to SIMPLE/OP07 with zero visuals."""
    session_id = "test-op14-q3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is operational history in ESP surveillance?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        types = [l["type"] for l in lines]
        assert "visual" not in types

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op14_seal_q4_missing_asset():
    """OP14 Query 4 (Clarification): History query missing asset ID pauses for clarification."""
    session_id = "test-op14-q4"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Review past operational runtime history"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "PAUSED"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op14_seal_q5_coverage_exceeded_refusal():
    """OP14 Query 5 (Honest Refusal on Coverage Exceeded): Window outside coverage refuses cleanly."""
    session_id = "test-op14-q5"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Show operational history for FS-17 from 2024-01-01 to 2024-01-05",
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "INSUFFICIENT"
        types = [l["type"] for l in lines]
        assert "error" in types
        assert "visual" not in types
        err = next(l for l in lines if l["type"] == "error")
        assert err["code"] == "INSUFFICIENT_EVIDENCE"

    delete_pending(session_id)
    delete_session(session_id)
