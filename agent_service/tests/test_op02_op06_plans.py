import pytest
from datetime import datetime, timezone
from app.routing.objective_registry import get_objective
from app.contracts.routing import RouteDecision
from app.contracts.evidence import EvidencePack, EvidenceItem
from app.planning.plan_builder import build_plan
from app.policy.policy_gate import validate_plan
from app.evidence.formatter import format_pack
from app.visualization.planner import plan_visualization


def test_op02_manifest_and_plan():
    op02 = get_objective("OP02_PRODUCTION_DECLINE_RCA")
    assert op02 is not None
    assert op02.safety_class == "READ"
    assert op02.scope == "ASSET"
    assert "production-decline" in op02.allowed_visuals
    assert "pressure-corridor" in op02.allowed_visuals
    assert "trip-timeline" in op02.allowed_visuals

    decision = RouteDecision(
        route="WORKFLOW",
        intent="decline_rca",
        objective_id="OP02_PRODUCTION_DECLINE_RCA",
        args={"asset_id": "FS-17", "start": "2026-09-14T00:00:00Z", "end": "2026-09-21T00:00:00Z"},
        confidence=0.9,
    )
    plan = build_plan("test-run-02", "session-02", decision, op02)
    assert plan.requires_approval is False
    tools_called = [c.tool for c in plan.calls]
    assert "get_asset_context" in tools_called
    assert "get_historian_aggregates" in tools_called
    assert "get_events" in tools_called

    policy_res = validate_plan(plan)
    assert policy_res.approved is True, f"Policy violations: {policy_res.violations}"


def test_op06_manifest_and_plan():
    op06 = get_objective("OP06_KNOWLEDGE_LOOKUP")
    assert op06 is not None
    assert op06.safety_class == "READ"
    assert op06.scope == "GLOBAL"
    assert "evidence-cards" in op06.allowed_visuals

    decision = RouteDecision(
        route="SIMPLE",
        intent="procedure",
        objective_id="OP06_KNOWLEDGE_LOOKUP",
        args={"query": "What is underload protection?"},
        confidence=0.95,
    )
    plan = build_plan("test-run-06", "session-06", decision, op06)
    assert plan.requires_approval is False
    tools_called = [c.tool for c in plan.calls]
    assert tools_called == ["search_knowledge"]

    policy_res = validate_plan(plan)
    assert policy_res.approved is True, f"Policy violations: {policy_res.violations}"


def test_op02_formatter_and_cards():
    # 1. Declining well data
    rows_declining = [
        ["2026-09-14T00:00:00Z", 500.0, 490.0, 2.0, 1200.0],
        ["2026-09-17T00:00:00Z", 420.0, 410.0, 2.0, 1150.0],
        ["2026-09-21T00:00:00Z", 300.0, 290.0, 2.0, 1050.0],
    ]
    item_agg = EvidenceItem(
        evidence_id="EV-agg-02",
        tool="get_historian_aggregates",
        source_domain="historian",
        fetched_at=datetime.now(timezone.utc),
        status="OK",
        payload={
            "well_id": "FS-17",
            "columns": ["bucket", "liquid_rate_bpd", "oil_rate_bopd", "water_cut_pct", "int_prs_psi"],
            "rows": rows_declining,
        },
        unit_map={"liquid_rate_bpd": "BPD", "oil_rate_bopd": "BOPD", "int_prs_psi": "PSI"},
    )
    pack = EvidencePack(run_id="run-dec", version=1, sealed=True, items=[item_agg])
    fmt = format_pack(pack)

    trend = fmt.by_signal("production_trend")
    assert trend is not None
    assert trend.raw == "DECLINING"

    rate = fmt.by_signal("decline_rate_bpd_per_day")
    assert rate is not None
    assert rate.raw > 0.0
    assert "BPD/day" in rate.value_str

    viz = plan_visualization("OP02_PRODUCTION_DECLINE_RCA", pack, fmt)
    assert "production-decline" in viz.card_ids
    assert "pressure-corridor" in viz.card_ids


def test_op02_formatter_stable_well():
    # 2. Stable well data
    rows_stable = [
        ["2026-09-14T00:00:00Z", 400.0, 395.0, 1.0, 1200.0],
        ["2026-09-17T00:00:00Z", 402.0, 397.0, 1.0, 1205.0],
        ["2026-09-21T00:00:00Z", 399.0, 394.0, 1.0, 1198.0],
    ]
    item_agg = EvidenceItem(
        evidence_id="EV-agg-stable",
        tool="get_historian_aggregates",
        source_domain="historian",
        fetched_at=datetime.now(timezone.utc),
        status="OK",
        payload={
            "well_id": "FNW-01",
            "columns": ["bucket", "liquid_rate_bpd", "oil_rate_bopd", "water_cut_pct", "int_prs_psi"],
            "rows": rows_stable,
        },
        unit_map={"liquid_rate_bpd": "BPD", "oil_rate_bopd": "BOPD", "int_prs_psi": "PSI"},
    )
    pack = EvidencePack(run_id="run-stab", version=1, sealed=True, items=[item_agg])
    fmt = format_pack(pack)

    trend = fmt.by_signal("production_trend")
    assert trend is not None
    assert trend.raw == "STABLE"


def test_op06_formatter_and_cards():
    hits = [
        {
            "doc_id": "API-RP-11S",
            "section": "5.3.2",
            "authority": "LEVEL_A",
            "page": 87,
            "snippet": "Underload protection trips the ESP when motor load drops.",
            "score": 0.91,
        },
        {
            "doc_id": "FIELD-SOP-ESP-01",
            "section": "2.1",
            "authority": "LEVEL_B",
            "page": 12,
            "snippet": "Secondary procedures for reset.",
            "score": 0.82,
        },
    ]
    item_kb = EvidenceItem(
        evidence_id="EV-kb-06",
        tool="search_knowledge",
        source_domain="kb",
        fetched_at=datetime.now(timezone.utc),
        status="OK",
        payload={"query": "underload protection", "hits": hits},
    )
    pack = EvidencePack(run_id="run-kb", version=1, sealed=True, items=[item_kb])
    fmt = format_pack(pack)

    assert len(fmt.kb_hits) == 2
    # Ensure LEVEL_A ranked above LEVEL_B
    assert fmt.kb_hits[0].authority == "LEVEL_A"
    assert fmt.kb_hits[0].doc_id == "API-RP-11S"

    viz = plan_visualization("OP06_KNOWLEDGE_LOOKUP", pack, fmt)
    assert "evidence-cards" in viz.card_ids
