from datetime import datetime
import pytest

from app.contracts import (
    UIContext,
    QueryRequest,
    DecisionRequest,
    Mentions,
    AssetBinding,
    TimeBinding,
    SessionSnapshot,
    ContextFrame,
    CandidateTool,
    RouterInput,
    RouteDecision,
    PendingInterrupt,
    RunState,
    StatusFrame,
    TextDeltaFrame,
    ClarificationFrame,
    InterruptFrame,
    AdvisoryFrame,
    VisualFrame,
    ErrorFrame,
    DoneFrame,
)

def test_api_contracts_roundtrip():
    ui = UIContext(selected_asset="FS-017", selected_time_range="last_24h")
    json_str = ui.model_dump_json()
    assert UIContext.model_validate_json(json_str) == ui

    qr = QueryRequest(session_id="S123", message="Why did FS-017 trip?", ui_context=ui)
    qr_json = qr.model_dump_json()
    assert QueryRequest.model_validate_json(qr_json) == qr

    dr = DecisionRequest(run_id="R456", action="APPROVE", token="tok-123", modified_args={"hz": 58})
    dr_json = dr.model_dump_json()
    assert DecisionRequest.model_validate_json(dr_json) == dr

def test_context_contracts_roundtrip():
    now = datetime.utcnow()
    mentions = Mentions(assets=["FS-017"], times=["10:42"], pronouns=["it"])
    asset = AssetBinding(id="FS-017", source="EXPLICIT", confidence=1.0, match_method="EXACT_ID")
    time_b = TimeBinding(instant=now, source="EXPLICIT", label="10:42", confidence=0.95)
    snapshot = SessionSnapshot(last_objective="OP03_FAULT_DIAGNOSIS", last_analysis_id="R455", turn_count=3)
    frame = ContextFrame(
        session_id="S123",
        raw_message="Why did FS-017 trip?",
        mentions=mentions,
        asset=asset,
        time=time_b,
        resolution="NEW",
        session_snapshot=snapshot
    )
    frame_json = frame.model_dump_json()
    reconstructed = ContextFrame.model_validate_json(frame_json)
    assert reconstructed.session_id == frame.session_id
    assert reconstructed.asset.id == "FS-017"
    assert reconstructed.asset.source == "EXPLICIT"

def test_routing_contracts_roundtrip():
    candidate = CandidateTool(tool="get_live_telemetry", score=0.89)
    assert CandidateTool.model_validate_json(candidate.model_dump_json()) == candidate

    r_in = RouterInput(
        raw_message="Why did FS-017 trip?",
        asset_id="FS-017",
        asset_source="EXPLICIT",
        turn_count=1,
        candidate_objectives=["OP03_FAULT_DIAGNOSIS"],
        candidate_tools=["get_live_telemetry"]
    )
    assert RouterInput.model_validate_json(r_in.model_dump_json()) == r_in

    r_dec = RouteDecision(
        route="WORKFLOW",
        intent="diagnose",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-017"},
        confidence=0.92,
        deferred_intents=["set_frequency"]
    )
    assert RouteDecision.model_validate_json(r_dec.model_dump_json()) == r_dec

def test_hitl_contracts_roundtrip():
    now = datetime.utcnow()
    pending = PendingInterrupt(
        run_id="R456",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-017", "FNW-01"],
        raised_at=now
    )
    p_json = pending.model_dump_json()
    rec_pending = PendingInterrupt.model_validate_json(p_json)
    assert rec_pending.run_id == "R456"
    assert rec_pending.reason == "CLARIFY"
    assert rec_pending.resume_at == "PLAN_BUILD"

    run = RunState(
        run_id="R456",
        session_id="S123",
        status="RUNNING",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-017"},
        turn_count=1
    )
    assert RunState.model_validate_json(run.model_dump_json()).run_id == "R456"

def test_events_frames_roundtrip():
    status = StatusFrame(run_id="R456", stage="context", progress=20, message="Resolving context")
    assert StatusFrame.model_validate_json(status.model_dump_json()) == status

    delta = TextDeltaFrame(run_id="R456", delta="Analyzing sensor signals...")
    assert TextDeltaFrame.model_validate_json(delta.model_dump_json()) == delta

    clarify = ClarificationFrame(
        run_id="R456",
        question="Which well would you like to inspect?",
        options=["FS-017", "FS-021"],
        slot="asset_id"
    )
    assert ClarificationFrame.model_validate_json(clarify.model_dump_json()) == clarify

    interrupt = InterruptFrame(
        run_id="R456",
        reason="APPROVE",
        pending_call={"tool": "set_operating_frequency", "args": {"hz": 58}}
    )
    assert InterruptFrame.model_validate_json(interrupt.model_dump_json()).reason == "APPROVE"

    err = ErrorFrame(run_id="R456", code="EMPTY_LLM_OUTPUT", message="No response produced")
    assert ErrorFrame.model_validate_json(err.model_dump_json()) == err

    done = DoneFrame(run_id="R456", status="OK")
    assert DoneFrame.model_validate_json(done.model_dump_json()) == done
