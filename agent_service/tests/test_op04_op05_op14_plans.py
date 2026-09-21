import pytest
from datetime import datetime, timezone
from app.contracts.routing import RouteDecision
from app.routing.objective_registry import get_objective
from app.planning.plan_builder import build_plan
from app.policy.policy_gate import validate_plan
from app.visualization.planner import plan_visualization
from app.contracts.evidence import EvidencePack, EvidenceItem
from app.evidence.formatter import format_pack


def test_build_and_validate_op04():
    manifest = get_objective("OP04_HEALTH_ASSESSMENT")
    assert manifest is not None

    decision = RouteDecision(
        route="WORKFLOW",
        intent="health",
        objective_id="OP04_HEALTH_ASSESSMENT",
        args={"asset_id": "FS-17"},
        confidence=0.9,
    )
    plan = build_plan("run-op04-1", "sess-1", decision, manifest)
    tools = [c.tool for c in plan.calls]
    assert "get_asset_context" in tools
    assert "get_health_index" in tools
    assert "get_historian_aggregates" in tools

    policy_res = validate_plan(plan)
    assert policy_res.approved is True


def test_build_and_validate_op05():
    manifest = get_objective("OP05_EARLY_WARNING")
    assert manifest is not None

    decision = RouteDecision(
        route="WORKFLOW",
        intent="early_warning",
        objective_id="OP05_EARLY_WARNING",
        args={"asset_id": "FS-17"},
        confidence=0.9,
    )
    plan = build_plan("run-op05-1", "sess-1", decision, manifest)
    tools = [c.tool for c in plan.calls]
    assert "get_asset_context" in tools
    assert "get_anomaly" in tools
    assert "get_historian_aggregates" in tools

    policy_res = validate_plan(plan)
    assert policy_res.approved is True


def test_build_and_validate_op14():
    manifest = get_objective("OP14_OPERATIONAL_HISTORY")
    assert manifest is not None

    decision = RouteDecision(
        route="WORKFLOW",
        intent="history",
        objective_id="OP14_OPERATIONAL_HISTORY",
        args={"asset_id": "FS-17", "start": "2026-09-18T00:00:00Z", "end": "2026-09-19T00:00:00Z"},
        confidence=0.9,
    )
    plan = build_plan("run-op14-1", "sess-1", decision, manifest)
    tools = [c.tool for c in plan.calls]
    assert "get_asset_context" in tools
    assert "get_historian_window" in tools
    assert "get_historian_aggregates" in tools
    assert "get_events" in tools

    policy_res = validate_plan(plan)
    assert policy_res.approved is True


def test_op04_missing_asset_fails_policy():
    manifest = get_objective("OP04_HEALTH_ASSESSMENT")
    decision = RouteDecision(
        route="WORKFLOW",
        intent="health",
        objective_id="OP04_HEALTH_ASSESSMENT",
        args={},  # Missing asset_id
        confidence=0.9,
    )
    plan = build_plan("run-op04-err", "sess-1", decision, manifest)
    policy_res = validate_plan(plan)
    assert policy_res.approved is False
    assert any("asset_id" in v for v in policy_res.violations)


def test_visual_cards_selection_for_op04():
    # Test that degradation-trend and risk-trajectory qualify when their signals are present
    payload = {
        "well_id": "FS-17",
        "health_score": 72.0,
        "rate_per_day": 0.45,
        "projected_days_to_threshold": 48.0,
    }
    item = EvidenceItem(
        evidence_id="EV-op04-viz",
        tool="get_health_index",
        source_domain="ml",
        fetched_at=datetime.now(timezone.utc),
        payload=payload,
    )
    pack = EvidencePack(
        run_id="run-viz-1",
        version=1,
        items=[item],
        sealed=True,
    )
    fe = format_pack(pack)
    spec = plan_visualization("OP04_HEALTH_ASSESSMENT", pack, formatted_evidence=fe)
    assert "health-score" in spec.card_ids
    assert "degradation-trend" in spec.card_ids
    assert "risk-trajectory" in spec.card_ids
