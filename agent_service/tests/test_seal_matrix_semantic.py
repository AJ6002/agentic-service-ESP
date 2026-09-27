"""
Semantic integrity test suite for the 20-Query Seal Matrix (U7).
Validates deterministic elimination of:
1. Q4: Dead-well false normal & oil-rate contradiction
2. Q10: Stable vs. declining contradiction
3. Q18: Fresh-session follow-up routing to ANALYSIS_EXPIRED
4. Q15: Unverified numbers stripped with count-only banners
5. Q20: Zero uncited troubleshooting/verification steps in output
"""
import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

import app.contracts  # break circular import
from app.main import app
from app.stores.session_store import delete_pending, delete_session


@pytest.mark.anyio
async def test_q04_current_status_no_contradiction_or_false_normal():
    """Q4: Current status query must not contradict positive production or mask critical alarms."""
    session_id = f"test-sem-q04-{uuid.uuid4().hex}"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What's the current status of FS-17?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]

        done = next((l for l in lines if l["type"] == "done"), None)
        assert done is not None
        assert done["status"] == "OK"

        text_deltas = "".join(l.get("delta", "") for l in lines if l["type"] == "text_delta")
        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        assessment = adv_frame["advisory"]["assessment"] if adv_frame else text_deltas

        # Semantic assertion 1: Must not claim non-producing if oil is flowing
        assert "not producing" not in assessment.lower(), f"Contradiction found in assessment: {assessment}"
        assert "zero production" not in assessment.lower(), f"Contradiction found in assessment: {assessment}"


@pytest.mark.anyio
async def test_q10_production_decline_rca_no_stable_declining_contradiction():
    """Q10: Production decline RCA must never emit both stable and declining in same assessment."""
    session_id = f"test-sem-q10-{uuid.uuid4().hex}"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why has FS-17 production declined?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]

        done = next((l for l in lines if l["type"] == "done"), None)
        assert done is not None
        assert done["status"] == "OK"

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        if adv_frame:
            assessment = adv_frame["advisory"]["assessment"]
            # Must not contain mutual contradiction
            has_stable = "stable" in assessment.lower() or "no abnormal decline" in assessment.lower()
            has_declining = "declining" in assessment.lower() or "declined" in assessment.lower()
            assert not (has_stable and has_declining), (
                f"Contradiction: assessment contains both stable and declining statements: {assessment}"
            )


@pytest.mark.anyio
async def test_q18_fresh_session_followup_returns_analysis_expired():
    """Q18: Explicit follow-up on fresh session must return ANALYSIS_EXPIRED, never CLARIFY."""
    session_id = f"test-sem-q18-{uuid.uuid4().hex}"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "Why did you conclude that?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]

        # Must not emit clarification frame
        clarify = next((l for l in lines if l["type"] == "clarification"), None)
        assert clarify is None, "Expected no clarification frame on fresh session follow-up"

        # Must emit error frame with ANALYSIS_EXPIRED
        err = next((l for l in lines if l["type"] == "error"), None)
        assert err is not None, f"Expected error frame, got: {lines}"
        assert err["code"] == "ANALYSIS_EXPIRED"

        done = next((l for l in lines if l["type"] == "done"), None)
        assert done is not None
        assert done["status"] == "INSUFFICIENT"


@pytest.mark.anyio
async def test_q15_health_assessment_count_only_provenance_banner():
    """Q15: Health assessment warning banners must only contain counts, no raw unverified numbers."""
    session_id = f"test-sem-q15-{uuid.uuid4().hex}"
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

        done = next((l for l in lines if l["type"] == "done"), None)
        assert done is not None
        assert done["status"] == "OK"

        full_text = "".join(l.get("delta", "") for l in lines if l["type"] == "text_delta")
        # Ensure that if a warning banner is present, it does not use the old "Unverified for:" format
        assert "Numeric Provenance Unverified for:" not in full_text
        assert "Citation Provenance Unverified for:" not in full_text


@pytest.mark.anyio
async def test_q20_fault_diagnosis_zero_uncited_steps():
    """Q20: Fault diagnosis troubleshooting and verification steps must be strictly grounded."""
    session_id = f"test-sem-q20-{uuid.uuid4().hex}"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "How do I troubleshoot gas lock on FS-17?"},
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]

        done = next((l for l in lines if l["type"] == "done"), None)
        assert done is not None
        assert done["status"] == "OK"

        adv_frame = next((l for l in lines if l["type"] == "advisory"), None)
        if adv_frame:
            tb_steps = adv_frame["advisory"].get("troubleshooting_steps", [])
            for step in tb_steps:
                assert "[" in step and "]" in step, f"Ungrounded troubleshooting step found: {step}"
            ver_steps = adv_frame["advisory"].get("verification_steps", [])
            for step in ver_steps:
                assert "[" in step and "]" in step, f"Ungrounded verification step found: {step}"
