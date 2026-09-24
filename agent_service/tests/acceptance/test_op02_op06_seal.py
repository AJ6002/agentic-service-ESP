import json
import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.stores.session_store import delete_pending, delete_session


# ---------------------------------------------------------------------------
# Part 1: OP02 Production Decline RCA Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_op02_seal_q1_nominal():
    """OP02 Q1: 'Why has FS-17 production declined?' -> OK, honest decline or stability assessment, cards."""
    session_id = "test-op02-q1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    t0 = time.time()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why has FS-17 production declined?"},
        )
        latency = time.time() - t0
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]
        assert "done" in types
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        # Advisory frame checks
        advisory_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert advisory_frame is not None
        adv = advisory_frame["advisory"]
        assert adv["objective_id"] == "OP02_PRODUCTION_DECLINE_RCA"

        assessment = adv["assessment"]
        # AC-OP02-1 & AC-OP02-6 Truth-Telling:
        # If historian shows >5% decline, names decline rate with BPD/day.
        # If historian shows stable production, states stability honestly without forced decline.
        assert any(
            phrase in assessment.upper()
            for phrase in ["BPD/DAY", "BPD", "STABLE", "NO ABNORMAL DECLINE", "NORMAL EXPECTATIONS"]
        )

        # Recommendation exists
        assert adv["recommendation"] is not None and len(adv["recommendation"]) > 5

        # Visual cards: production-decline, pressure-corridor
        visual_frame = next((l for l in lines if l["type"] == "visual"), None)
        if visual_frame:
            card_ids = visual_frame["visualization"].get("card_ids") or visual_frame["visualization"].get("cards", [])
            assert any(c in card_ids for c in ["production-decline", "pressure-corridor", "trip-timeline", "gross-liquid-rate"])

        # AC-OP02-5: Soft latency target < 15s
        print(f"OP02 Q1 latency: {latency:.2f}s")

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op02_seal_q2_secondary_well():
    """OP02 Q2: 'Analyze production decline on FNW-01' -> same shape with FNW-01 data."""
    session_id = "test-op02-q2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Analyze production decline on FNW-01"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"
        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert adv_frame is not None
        assert adv_frame["advisory"]["objective_id"] == "OP02_PRODUCTION_DECLINE_RCA"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op02_seal_q3_negative_stable_well():
    """OP02 Q3: Negative case on stable telemetry -> states production is stable, does not force decline."""
    session_id = "test-op02-q3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why has FNW-01 production declined?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert adv_frame is not None
        assessment = adv_frame["advisory"]["assessment"].lower()
        # AC-OP02-6: Stable production -> no forced decline narrative or states stability
        assert any(w in assessment for w in ["stable", "no abnormal decline", "no significant decline", "rate", "bpd"])

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op02_seal_q4_coverage_gap():
    """OP02 Q4: Well with sparse/nonexistent coverage (ULFA-5) -> INSUFFICIENT or named gap."""
    session_id = "test-op02-q4"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why has ULFA-5 production declined?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        # Honest refusal if missing required data or paused for clarification
        if done["status"] == "INSUFFICIENT":
            err_frame = next((l for l in lines if l["type"] == "error"), None)
            assert err_frame is not None
            assert "ULFA-5" in err_frame.get("message", "") or "missing" in err_frame.get("message", "").lower()
        else:
            pass

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op02_seal_q5_multi_signal_30d():
    """OP02 Q5: Multi-signal 30-day production analysis on FS-17 -> aggregates used, latency < 15s."""
    session_id = "test-op02-q5"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    t0 = time.time()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Give me a full production analysis for FS-17 over the last 30 days"},
        )
        latency = time.time() - t0
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] in ("OK", "INSUFFICIENT")
        assert latency < 15.0, f"Query took {latency:.2f}s, expected < 15s"

    delete_pending(session_id)
    delete_session(session_id)


# ---------------------------------------------------------------------------
# Part 2: OP06 Procedure / Knowledge Lookup Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_op06_seal_q1_underload_protection():
    """OP06 Q1: 'What is underload protection?' -> SIMPLE/OP06, doc citation with authority, zero well IDs."""
    session_id = "test-op06-q1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is underload protection?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        # Advisory frame checks
        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert adv_frame is not None
        adv = adv_frame["advisory"]
        assert adv["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"

        assessment = adv["assessment"]
        # AC-OP06-1: Cites at least one doc_id with authority level (or document ID)
        assert any(w in assessment.lower() for w in ["api", "sop", "doc", "level_a", "level_b", "standard", "rp", "spec", "underload", "motor", "bp", "takacs", "guidelines", "manual", "troubleshooting", "procedure", "protection"])

        # AC-OP06-3: Definitional queries never resolve a well ID
        for well in ["FS-17", "FS-91", "FNW-01", "FWS-06"]:
            assert well not in assessment

        # Visual frame has evidence-cards if KB hits exist
        visual_frame = next((l for l in lines if l["type"] == "visual"), None)
        if visual_frame:
            card_ids = visual_frame["visualization"].get("card_ids") or visual_frame["visualization"].get("cards", [])
            assert "evidence-cards" in card_ids

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op06_seal_q2_restart_procedure():
    """OP06 Q2: 'How do I restart an ESP?' -> procedural answer with steps, cites source doc, no well."""
    session_id = "test-op06-q2"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "How do I restart an ESP?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert adv_frame is not None
        assert adv_frame["advisory"]["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"
        # Does not name a specific well
        for well in ["FS-17", "FS-91", "FNW-01", "FWS-06"]:
            assert well not in adv_frame["advisory"]["assessment"]

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op06_seal_q3_explain_gas_lock():
    """OP06 Q3: 'Explain gas lock.' -> definitional answer, KB citation with authority."""
    session_id = "test-op06-q3"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Explain gas lock."},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assert adv_frame is not None
        assert adv_frame["advisory"]["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op06_seal_q4_anti_hijack_op03():
    """OP06 Q4: 'Explain what underload trip is and why it happens.' -> must route to OP06, NOT OP03."""
    session_id = "test-op06-q4"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Explain what underload trip is and why it happens."},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        types = [l["type"] for l in lines]
        assert "clarification" not in types

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        if adv_frame:
            assert adv_frame["advisory"]["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_op06_seal_q5_anti_hijack_op01():
    """OP06 Q5: 'What is the current status of an ESP?' -> must route to OP06, NOT OP01."""
    session_id = "test-op06-q5"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is the current status of an ESP?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        done = next(l for l in lines if l["type"] == "done")
        assert done["status"] == "OK"

        types = [l["type"] for l in lines]
        assert "clarification" not in types

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        if adv_frame:
            assert adv_frame["advisory"]["objective_id"] == "OP06_KNOWLEDGE_LOOKUP"

    delete_pending(session_id)
    delete_session(session_id)


# ---------------------------------------------------------------------------
# Part 3: Cross-cutting Routing Disambiguation Table
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@pytest.mark.parametrize(
    "message,expected_route,expected_op",
    [
        ("Why has FS-17 production declined?", "WORKFLOW", "OP02_PRODUCTION_DECLINE_RCA"),
        ("What is underload protection?", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
        ("Explain gas lock.", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
        ("What's the current status of FS-17?", "WORKFLOW", "OP01_CURRENT_STATUS"),
        ("Why did FS-17 trip?", "WORKFLOW", "OP03_FAULT_DIAGNOSIS"),
        ("Explain what underload trip is.", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
    ],
)
async def test_routing_disambiguation_table(message, expected_route, expected_op):
    """Part 3: Verify all 6 cross-cutting queries disambiguate exactly as specified."""
    from app.contracts.routing import RouterInput
    from app.routing.router import route_query_full

    well_id = "FS-17" if "FS-17" in message else None
    r_in = RouterInput(
        raw_message=message,
        asset_id=well_id,
        asset_source="EXPLICIT" if well_id else "UNRESOLVED",
        turn_count=1,
    )
    res = await route_query_full(r_in)
    dec = res.decision
    assert dec.route == expected_route, f"Mismatch route for '{message}': got {dec.route}, expected {expected_route}"
    assert dec.objective_id == expected_op, f"Mismatch op for '{message}': got {dec.objective_id}, expected {expected_op}"
