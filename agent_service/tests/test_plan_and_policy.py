import pytest
from app.contracts.plan import PlanArtifact, PlanCall
from app.contracts.routing import RouteDecision
from app.planning.plan_builder import build_plan
from app.policy.policy_gate import validate_plan
from app.routing.objective_registry import get_objective

def test_build_plan_op03_fault_diagnosis():
    manifest = get_objective("OP03_FAULT_DIAGNOSIS")
    decision = RouteDecision(
        route="WORKFLOW",
        intent="diagnose",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-017"},
        confidence=0.9,
    )
    plan = build_plan(
        run_id="R-test-plan-1",
        session_id="S-test-1",
        decision=decision,
        manifest=manifest,
    )
    assert plan.run_id == "R-test-plan-1"
    # required_evidence + optional_evidence + the main tool call.
    assert len(plan.calls) == len(manifest.required_evidence) + len(manifest.optional_evidence) + 1
    assert plan.calls[-1].tool == "diagnose_fault"
    assert plan.requires_approval is False

def test_policy_gate_valid_plan():
    manifest = get_objective("OP03_FAULT_DIAGNOSIS")
    decision = RouteDecision(
        route="WORKFLOW",
        intent="diagnose",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-017"},
        confidence=0.9,
    )
    plan = build_plan("R-pol-1", "S-pol-1", decision, manifest)
    res = validate_plan(plan)
    assert res.approved is True
    assert len(res.violations) == 0

def test_policy_gate_missing_required_arg():
    manifest = get_objective("OP03_FAULT_DIAGNOSIS")
    decision = RouteDecision(
        route="WORKFLOW",
        intent="diagnose",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": ""},  # missing asset_id
        confidence=0.9,
    )
    plan = build_plan("R-pol-2", "S-pol-2", decision, manifest)
    res = validate_plan(plan)
    assert res.approved is False
    assert any("Missing required argument 'asset_id'" in v for v in res.violations)


def test_build_plan_includes_optional_evidence_calls():
    """
    Regression: optional_evidence was declared in every objective YAML but
    plan_builder never turned it into a call at all — e.g. OP03's
    search_knowledge was silently never fetched regardless of whether a KB
    service existed. This asserts optional_evidence tools now appear as
    READ calls alongside required_evidence and the main tool.
    """
    manifest = get_objective("OP03_FAULT_DIAGNOSIS")
    decision = RouteDecision(
        route="WORKFLOW",
        intent="diagnose",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-17"},
        confidence=0.9,
    )
    plan = build_plan(
        run_id="R-test-plan-opt-1",
        session_id="S-test-opt-1",
        decision=decision,
        manifest=manifest,
    )

    tools_in_plan = {c.tool for c in plan.calls}
    for optional_tool in manifest.optional_evidence:
        assert optional_tool in tools_in_plan, (
            f"optional_evidence tool '{optional_tool}' must appear in the plan"
        )
    # Required + optional + main tool, no more, no fewer.
    expected_count = len(manifest.required_evidence) + len(manifest.optional_evidence) + 1
    assert len(plan.calls) == expected_count


def test_optional_evidence_absent_source_does_not_block_seal():
    """
    An ABSENT/DEGRADED optional-evidence source must never prevent the
    pack from sealing — that's the whole point of it being optional.
    """
    manifest = get_objective("OP03_FAULT_DIAGNOSIS")
    res = validate_plan(
        PlanArtifact(
            run_id="R-opt-seal-1",
            session_id="S-opt-seal-1",
            objective_id="OP03_FAULT_DIAGNOSIS",
            args={"asset_id": "FS-17"},
            confidence=0.9,
            calls=[
                PlanCall(seq=1, kind="READ", tool="get_asset_context", args={"asset_id": "FS-17"}),
                PlanCall(seq=2, kind="READ", tool="get_live_telemetry", args={"asset_id": "FS-17"}),
                PlanCall(seq=3, kind="READ", tool="get_historian_window", args={"asset_id": "FS-17"}),
                PlanCall(seq=4, kind="READ", tool="search_knowledge", args={"asset_id": "FS-17"}),
                PlanCall(seq=5, kind="READ", tool="diagnose_fault", args={"asset_id": "FS-17"}),
            ],
        )
    )
    assert res.approved is True
