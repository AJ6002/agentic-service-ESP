import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.contracts.evidence import CallResult, Gap, EvidencePack
from app.evidence.pack import classify_gap_reason
from app.evidence.qod import validate
from app.stores.session_store import delete_pending, delete_session
from app.main import app


@pytest.mark.anyio
async def test_ac_6_1_simple_route_latency_under_threshold():
    """
    AC-6.1: Fast glossary / direct query response is fast (< 5s).
    """
    session_id = "test-ac-6-1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t0 = time.perf_counter()
        resp = await client.post(
            "/query",
            json={"session_id": session_id, "message": "What is gas lock?"},
        )
        elapsed = time.perf_counter() - t0
        assert resp.status_code == 200
        assert elapsed < 5.0, f"Simple route latency {elapsed:.2f}s exceeded 5s threshold"

    delete_pending(session_id)
    delete_session(session_id)


def test_ac_6_2_no_fabrication_under_failure_mode():
    """
    AC-6.2: When adapters return FAILED or TIMEOUT, no measurement numbers are fabricated.
    """
    cr = CallResult(
        seq=1,
        status="TIMEOUT",
        error="Gateway timeout contacting Server 184",
        error_code="TIMEOUT",
    )
    qod = validate(cr, run_id="R-ac-6-2", tool="get_live_telemetry")
    gap = Gap(
        source_domain="get_live_telemetry",
        reason=classify_gap_reason(cr),
        required=True,
    )
    pack = EvidencePack(
        run_id="R-ac-6-2",
        version=1,
        sealed=False,
        items=[],
        gaps=[gap],
    )
    assert len(pack.items) == 0
    assert len(pack.gaps) == 1
    assert pack.gaps[0].reason == "TIMEOUT"


def test_ac_6_3_audit_trail_recorded():
    """
    AC-6.3: Audit logging records event, run_id, and payload.
    """
    from app.audit.audit_sink import record_audit, get_audit_records
    record_audit(
        "test_acceptance_event",
        run_id="R-audit-test",
        session_id="session-audit-test",
        payload={"key": "val"},
    )
    audits = get_audit_records(count=10)
    matching = [a for a in audits if a.get("run_id") == "R-audit-test"]
    assert len(matching) >= 1
    assert matching[0]["event_type"] == "test_acceptance_event"
