import pytest

from app.workflow.runner import run_workflow


@pytest.mark.anyio
async def test_run_workflow_executes_real_plan_and_narrates_real_data():
    """
    This is the fix for the 'fake resume' bug: resuming a paused
    diagnosis must actually run Plan Builder -> Policy Gate -> Tool
    Gateway and narrate the real CallResult payloads, not discard the
    bound value and ask the LLM a generic question.
    """
    result = await run_workflow(
        run_id="R-wf-test-1",
        session_id="S-wf-test-1",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-017"},
        confidence=0.9,
    )
    assert result.ok is True
    assert result.plan is not None
    assert result.plan.objective_id == "OP03_FAULT_DIAGNOSIS"
    # One READ call per required_evidence entry + the main diagnose_fault call.
    assert len(result.plan.calls) >= 4
    # Real dispatch happened — call_results is populated, not skipped.
    assert len(result.call_results) > 0
    # Narration must reference the asset and be built from real results,
    # not a placeholder string like "System operational."
    assert "FS-017" in result.text
    assert "Diagnostic run" in result.text


@pytest.mark.anyio
async def test_run_workflow_rejects_plan_missing_required_arg():
    result = await run_workflow(
        run_id="R-wf-test-2",
        session_id="S-wf-test-2",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={},  # asset_id missing -> Policy Gate must reject
        confidence=0.9,
    )
    assert result.ok is False
    assert any("asset_id" in v for v in result.violations)


@pytest.mark.anyio
async def test_run_workflow_unknown_objective_fails_cleanly():
    result = await run_workflow(
        run_id="R-wf-test-3",
        session_id="S-wf-test-3",
        objective_id="OP99_DOES_NOT_EXIST",
        args={"asset_id": "FS-017"},
    )
    assert result.ok is False
    assert "unknown_objective" in result.violations[0]
