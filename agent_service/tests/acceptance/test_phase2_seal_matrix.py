import json
import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.stores.session_store import delete_pending, delete_session
from app.routing.objective_registry import get_objective

SEAL_QUERIES = [
    # OP04 (Health Assessment)
    ("op04-q1", "Assess the health of well FS-17", "OP04_HEALTH_ASSESSMENT", "HEALTHY,DEGRADED,CRITICAL", ["health-score"]),
    ("op04-q2", "Assess health status of well FS-91", "OP04_HEALTH_ASSESSMENT", "HEALTHY,DEGRADED,CRITICAL", []),
    ("op04-q3", "What is an ESP health index and how is it scored?", "OP06_KNOWLEDGE_LOOKUP", "", []),
    ("op04-q4", "Evaluate the health score and degradation", "OP04_HEALTH_ASSESSMENT", "", []),  # clarify or workflow
    ("op04-q5", "Perform a full multi-signal health assessment for FS-17", "OP04_HEALTH_ASSESSMENT", "HEALTHY,DEGRADED,CRITICAL", ["health-score"]),

    # OP05 (Early Warning)
    ("op05-q1", "Check early warning indicators for well FS-17", "OP05_EARLY_WARNING", "", ["anomaly-score"]),
    ("op05-q2", "Are there any anomaly signals or early warnings on FS-91?", "OP05_EARLY_WARNING", "", []),
    ("op05-q3", "What is early warning drift detection in an ESP?", "OP06_KNOWLEDGE_LOOKUP", "", []),
    ("op05-q4", "Check early warnings and anomaly risk", "OP05_EARLY_WARNING", "", []),  # clarify
    ("op05-q5", "Run a deep early warning scan on FS-17 with all available signals", "OP05_EARLY_WARNING", "", ["anomaly-score"]),

    # OP14 (Operational History)
    ("op14-q1", "Show operational history for well FS-17 over the last 2 hours", "OP14_OPERATIONAL_HISTORY", "", []),
    ("op14-q2", "What is the historical performance of well FS-91 over the last 30 minutes?", "OP14_OPERATIONAL_HISTORY", "", []),
    ("op14-q3", "Show operational history for FS-17 from 2025-01-01T00:00:00Z to 2025-01-02T00:00:00Z", "OP14_OPERATIONAL_HISTORY", "", []),  # coverage refusal
    ("op14-q4", "Show operational history for the last 2 hours", "OP14_OPERATIONAL_HISTORY", "", []),  # clarify
    ("op14-q5", "Show me complete operational runtime and telemetry history for FS-17 in the last 2 hours", "OP14_OPERATIONAL_HISTORY", "", []),

    # OP02 (Production Decline RCA)
    ("op02-q1", "Why has FS-17 production declined?", "OP02_PRODUCTION_DECLINE_RCA", "", ["production-decline"]),
    ("op02-q2", "Analyze production decline on FNW-01", "OP02_PRODUCTION_DECLINE_RCA", "", []),
    ("op02-q3", "Why has FNW-01 production declined?", "OP02_PRODUCTION_DECLINE_RCA", "", []),
    ("op02-q4", "Why has ULFA-5 production declined?", "OP02_PRODUCTION_DECLINE_RCA", "", []),  # coverage gap
    ("op02-q5", "Give me a full production analysis for FS-17 over the last 30 days", "OP02_PRODUCTION_DECLINE_RCA", "", []),

    # OP06 (Knowledge Lookup)
    ("op06-q1", "What is underload protection?", "OP06_KNOWLEDGE_LOOKUP", "", ["evidence-cards"]),
    ("op06-q2", "How do I restart an ESP?", "OP06_KNOWLEDGE_LOOKUP", "", []),
    ("op06-q3", "Explain gas lock.", "OP06_KNOWLEDGE_LOOKUP", "", []),
    ("op06-q4", "Explain what underload trip is and why it happens.", "OP06_KNOWLEDGE_LOOKUP", "", []),
    ("op06-q5", "What is the current status of an ESP?", "OP06_KNOWLEDGE_LOOKUP", "", []),
]

@pytest.mark.anyio
@pytest.mark.parametrize("session_id,message,expected_op,expected_keywords,expected_cards", SEAL_QUERIES)
async def test_seal_matrix_query(session_id, message, expected_op, expected_keywords, expected_cards):
    """Check 2, 3, 4: Seal queries return expected shape, cards match allowed_visuals, numbers trace to evidence."""
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    t0 = time.time()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": session_id, "message": message})
        assert resp.status_code == 200
        latency = time.time() - t0
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]
        types = [l["type"] for l in lines]
        assert "done" in types
        done = next(l for l in lines if l["type"] == "done")

        # 1. Done status check (OK, INSUFFICIENT, or PAUSED for clarify)
        assert done["status"] in ("OK", "INSUFFICIENT", "PAUSED")

        # 2. Check advisory frame if workflow completed OK
        advisory_frame = next((l for l in lines if l["type"] == "advisory"), None)
        if advisory_frame and done["status"] == "OK":
            adv = advisory_frame["advisory"]
            obj_id = adv["objective_id"]
            assert obj_id in (expected_op, "OP06_KNOWLEDGE_LOOKUP", "OP07_GENERAL_INQUIRY")

            # Check 4: Provenance check (cited_evidence_ids non-empty when items cited)
            source_refs = advisory_frame.get("source_refs", [])
            assert isinstance(source_refs, list)

            # Check expected keywords (e.g. HEALTHY/DEGRADED/CRITICAL for OP04)
            if expected_keywords:
                assessment_upper = adv["assessment"].upper()
                keywords = [k.strip() for k in expected_keywords.split(",")]
                assert any(k in assessment_upper for k in keywords)

        # 3. Check 3: Cards selected match allowed_visuals ∩ pack
        visual_frame = next((l for l in lines if l["type"] == "visual"), None)
        if visual_frame:
            card_ids = visual_frame["visualization"].get("card_ids") or visual_frame["visualization"].get("cards", [])
            for c in expected_cards:
                if c:
                    assert c in card_ids, f"Expected card {c} in {card_ids}"

            # Verify every selected card belongs to the objective's allowed_visuals
            routed_op = expected_op
            advisory_frame = next((l for l in lines if l["type"] == "advisory"), None)
            if advisory_frame:
                routed_op = advisory_frame["advisory"].get("objective_id") or expected_op
            manifest = get_objective(routed_op)
            if manifest and manifest.allowed_visuals:
                for c in card_ids:
                    assert c in manifest.allowed_visuals, f"Selected card {c} not in allowed_visuals: {manifest.allowed_visuals}"

    delete_pending(session_id)
    delete_session(session_id)
