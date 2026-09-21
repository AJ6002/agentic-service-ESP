import json
import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.contracts.evidence import EvidenceItem, EvidencePack
from app.contracts.events import DoneFrame, ErrorFrame
from app.contracts.visualization import VisualizationSpec
from app.evidence.formatter import FormattedEvidence, FormattedValue, format_pack
from app.visualization.planner import plan_visualization
from app.synthesis.response_assembler import ResponseAssembler
from app.stores.session_store import delete_pending, delete_session
from app.main import app


def test_bug_d_unsealed_pack_yields_no_cards():
    """
    Bug D: Visualization Planner must check pack.sealed == True before selecting any card.
    If pack.sealed is False, plan_visualization MUST return empty card_ids.
    """
    pack = EvidencePack(
        run_id="R-unsealed-test",
        version=1,
        sealed=False,
        items=[
            EvidenceItem(
                evidence_id="EV-1",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"vibration_g": 3.5, "motor_temp_c": 120.0},
                unit_map={},
            )
        ],
    )
    formatted = FormattedEvidence(
        run_id=pack.run_id,
        pack_version=pack.version,
        values=[
            FormattedValue(evidence_id="EV-1", signal="vibration_g", value_str="3.5", unit="g RMS"),
            FormattedValue(evidence_id="EV-1", signal="motor_temp_c", value_str="120.0", unit="degC"),
        ],
    )
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert spec.card_ids == [], "Unsealed pack must not select any cards"
    assert spec.evidence_ids == []


@pytest.mark.anyio
async def test_bug_c_and_e_assembler_insufficient_evidence():
    """
    Bug C & E: ResponseAssembler emits ErrorFrame with code INSUFFICIENT_EVIDENCE
    and DoneFrame with status INSUFFICIENT (NOT status OK, NOT text_delta).
    """
    err = ErrorFrame(
        run_id="R-err-insufficient",
        code="INSUFFICIENT_EVIDENCE",
        message="Diagnostic run for FS-17 could not be completed: required evidence missing.",
    )
    lines = []
    async for frame_line in ResponseAssembler.assemble_stream(
        run_id="R-err-insufficient",
        route="WORKFLOW",
        error=err,
        done_status="INSUFFICIENT",
    ):
        lines.append(json.loads(frame_line))

    assert len(lines) == 2
    assert lines[0]["type"] == "error"
    assert lines[0]["code"] == "INSUFFICIENT_EVIDENCE"
    assert "required evidence missing" in lines[0]["message"]
    
    assert lines[1]["type"] == "done"
    assert lines[1]["status"] == "INSUFFICIENT"
    
    # Must NOT emit text_delta or visual frames
    types = [l["type"] for l in lines]
    assert "text_delta" not in types
    assert "visual" not in types


@pytest.mark.anyio
async def test_bug_c_done_status_mapping():
    """
    Bug C DoneFrame status mapping:
    - OK for completed sealed run
    - PAUSED for clarification
    - INSUFFICIENT for insufficient evidence
    - FAILED for crashed / failed run
    """
    # 1. OK
    lines_ok = [
        json.loads(l)
        async for l in ResponseAssembler.assemble_stream(
            run_id="R-ok",
            route="SIMPLE",
            text="Everything normal",
            done_status="OK",
        )
    ]
    assert lines_ok[-1]["type"] == "done"
    assert lines_ok[-1]["status"] == "OK"

    # 2. PAUSED
    from app.contracts.events import ClarificationFrame
    lines_paused = [
        json.loads(l)
        async for l in ResponseAssembler.assemble_stream(
            run_id="R-paused",
            route="WORKFLOW",
            clarification=ClarificationFrame(run_id="R-paused", question="?", options=["A"], slot="asset_id"),
            done_status="PAUSED",
        )
    ]
    assert lines_paused[-1]["type"] == "done"
    assert lines_paused[-1]["status"] == "PAUSED"

    # 3. INSUFFICIENT
    lines_insufficient = [
        json.loads(l)
        async for l in ResponseAssembler.assemble_stream(
            run_id="R-insufficient",
            route="WORKFLOW",
            error=ErrorFrame(run_id="R-insufficient", code="INSUFFICIENT_EVIDENCE", message="Missing data"),
            done_status="INSUFFICIENT",
        )
    ]
    assert lines_insufficient[-1]["type"] == "done"
    assert lines_insufficient[-1]["status"] == "INSUFFICIENT"

    # 4. FAILED
    lines_failed = [
        json.loads(l)
        async for l in ResponseAssembler.assemble_stream(
            run_id="R-failed",
            route="WORKFLOW",
            error=ErrorFrame(run_id="R-failed", code="WORKFLOW_FAILED", message="Internal crash"),
            done_status="FAILED",
        )
    ]
    assert lines_failed[-1]["type"] == "done"
    assert lines_failed[-1]["status"] == "FAILED"


@pytest.mark.anyio
async def test_e2e_insufficient_run_emits_error_frame_and_insufficient_done():
    """
    End-to-end test of /query when diagnostic cannot complete due to missing required evidence:
    Verifies:
    1. ErrorFrame with code INSUFFICIENT_EVIDENCE is emitted (Bug E).
    2. No visual frame is emitted (Bug D).
    3. No text_delta frame is emitted (Bug E).
    4. DoneFrame has status INSUFFICIENT (Bug C).
    """
    session_id = "test-bug-c-d-e-e2e"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Why did FS-9999 trip?",
                # clarify_on_insufficient is False by default (operator direct question)
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(l) for l in resp.text.strip().splitlines() if l]

        types = [l["type"] for l in lines]
        # Must have ErrorFrame and DoneFrame
        assert "error" in types, f"Expected error frame, got: {types}"
        assert "done" in types, f"Expected done frame, got: {types}"

        # Bug D: Must NOT contain visual frame
        assert "visual" not in types, f"Visual frame should NOT be present on failed run: {types}"

        # Bug E: Must NOT contain text_delta frame
        assert "text_delta" not in types, f"TextDelta frame should NOT be present on failed run: {types}"

        # Find error frame
        err_frame = next(l for l in lines if l["type"] == "error")
        assert err_frame["code"] == "INSUFFICIENT_EVIDENCE"
        assert "required evidence missing" in err_frame["message"]

        # Find done frame
        done_frame = next(l for l in lines if l["type"] == "done")
        assert done_frame["status"] == "INSUFFICIENT", f"Expected DoneFrame status INSUFFICIENT, got {done_frame['status']}"

    delete_pending(session_id)
    delete_session(session_id)

