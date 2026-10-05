from datetime import datetime, timezone
import pytest
from app.routing.objective_registry import get_objective, load_objective_registry, clear_objective_registry
from app.planning.plan_builder import build_plan
from app.policy.policy_gate import validate_plan
from app.contracts.routing import RouteDecision
from app.contracts.evidence import EvidencePack, EvidenceItem
from app.evidence.formatter import format_pack, FormattedKbHit
from app.synthesis.citation_check import check_citation_provenance
from app.workflow.runner import run_workflow


@pytest.fixture(autouse=True)
def reload_registry():
    clear_objective_registry()
    load_objective_registry(force_reload=True)


def test_op15_manifest_loaded():
    manifest = get_objective("OP15_PLATFORM_GUIDE")
    assert manifest is not None, "OP15_PLATFORM_GUIDE manifest must be registered"
    assert manifest.objective_id == "OP15_PLATFORM_GUIDE"
    assert manifest.safety_class == "READ"
    assert manifest.scope == "GLOBAL"
    assert manifest.tool in ("lookup_ui_map_entry", "search_ui_map")
    
    # Also verify short ID lookup
    manifest_short = get_objective("OP15")
    assert manifest_short is not None
    assert manifest_short.objective_id == "OP15_PLATFORM_GUIDE"


def test_op15_plan_construction_and_policy():
    manifest = get_objective("OP15_PLATFORM_GUIDE")
    assert manifest is not None
    
    decision = RouteDecision(
        route="WORKFLOW",
        objective_id="OP15_PLATFORM_GUIDE",
        args={"entry_id": "route.working-status", "query": "Where is the live telemetry screen?"},
        confidence=0.95,
    )
    plan = build_plan(
        run_id="test_run_op15_01",
        session_id="test_session_op15",
        decision=decision,
        manifest=manifest,
    )
    
    assert plan.objective_id == "OP15_PLATFORM_GUIDE"
    assert len(plan.calls) >= 1
    tool_names = [c.tool for c in plan.calls]
    assert "lookup_ui_map_entry" in tool_names or "search_ui_map" in tool_names
    
    policy_res = validate_plan(plan)
    assert policy_res.approved is True
    assert len(policy_res.violations) == 0


def test_op15_evidence_pack_formatting():
    item = EvidenceItem(
        evidence_id="EV-TEST-UIMAP-01",
        tool="lookup_ui_map_entry",
        source_domain="ui_map",
        fetched_at=datetime.now(timezone.utc),
        payload={
            "found": True,
            "entry_id": "route.working-status",
            "entry": {
                "id": "route.working-status",
                "type": "route",
                "title": "Working Status",
                "path": "/working-status",
                "workspace": "operations",
                "summary": "Primary live monitoring dashboard for operational status and telemetry.",
                "description": "Displays intake/discharge pressures, motor temperature, and live alarms.",
                "related": ["component.subsystem-equalizer"],
                "aliases": ["live telemetry", "working status"],
            }
        },
    )
    pack = EvidencePack(
        run_id="test_run_op15_fmt",
        version=1,
        items=[item],
        sealed=True,
    )
    formatted = format_pack(pack)
    assert len(formatted.kb_hits) == 1
    hit: FormattedKbHit = formatted.kb_hits[0]
    assert hit.doc_id == "route.working-status"
    assert "Working Status" in hit.section
    assert hit.authority == "PLATFORM_UI_MAP"
    assert "/working-status" in hit.snippet
    assert "operations" in hit.snippet


def test_op15_citation_provenance_check():
    from app.contracts.advisory import Advisory
    
    item = EvidenceItem(
        evidence_id="EV-TEST-UIMAP-02",
        tool="lookup_ui_map_entry",
        source_domain="ui_map",
        fetched_at=datetime.now(timezone.utc),
        payload={
            "found": True,
            "entry_id": "component.subsystem-equalizer",
            "entry": {
                "id": "component.subsystem-equalizer",
                "type": "component",
                "title": "Subsystem Equalizer",
                "path": "/working-status#equalizer",
                "workspace": "operations",
                "summary": "Visual subsystem equalizer bar component.",
                "description": "Shows balance across hydraulic and electrical subsystems.",
                "related": ["route.working-status"],
                "aliases": ["equalizer"],
            }
        },
    )
    pack = EvidencePack(
        run_id="test_run_op15_cit",
        version=1,
        items=[item],
        sealed=True,
    )
    
    advisory = Advisory(
        objective_id="OP15_PLATFORM_GUIDE",
        assessment="The Subsystem Equalizer [component.subsystem-equalizer] provides hydraulic balance diagnostics.",
        recommendation="Navigate to [route.working-status] to inspect the equalizer.",
        troubleshooting_steps=["Check equalizer readings at [component.subsystem-equalizer] to assess telemetry."],
        confidence=1.0,
        cited_evidence_ids=["EV-TEST-UIMAP-02"],
    )
    
    cit_res = check_citation_provenance(advisory, pack)
    assert cit_res.passed is True


@pytest.mark.anyio
async def test_op15_workflow_direct_invocation_lookup():
    res = await run_workflow(
        run_id="run_live_op15_lookup",
        session_id="session_live_op15",
        objective_id="OP15_PLATFORM_GUIDE",
        args={"entry_id": "route.working-status", "query": "Where can I view the working status screen?"},
        user_query="Where can I view the working status screen?",
    )
    
    assert res.ok is True
    assert res.advisory is not None
    assert res.advisory.objective_id == "OP15_PLATFORM_GUIDE"
    assert "working-status" in res.advisory.assessment.lower() or "working status" in res.advisory.assessment.lower()
    assert "/working-status" in res.advisory.assessment or "/working-status" in res.advisory.recommendation or "working status" in res.text.lower()
    assert res.text.startswith("Platform guide:")


@pytest.mark.anyio
async def test_op15_workflow_direct_invocation_semantic_search():
    res = await run_workflow(
        run_id="run_live_op15_search",
        session_id="session_live_op15",
        objective_id="OP15_PLATFORM_GUIDE",
        args={"query": "What is the subsystem equalizer component?"},
        user_query="What is the subsystem equalizer component?",
    )
    
    assert res.ok is True
    assert res.advisory is not None
    assert res.advisory.objective_id == "OP15_PLATFORM_GUIDE"
    assert "equalizer" in res.advisory.assessment.lower() or "subsystem" in res.advisory.assessment.lower()


@pytest.mark.anyio
async def test_op15_workflow_direct_invocation_concept():
    res = await run_workflow(
        run_id="run_live_op15_concept",
        session_id="session_live_op15",
        objective_id="OP15_PLATFORM_GUIDE",
        args={"entry_id": "concept.tdh", "query": "What does Total Dynamic Head (TDH) mean in the platform?"},
        user_query="What does Total Dynamic Head (TDH) mean in the platform?",
    )
    
    assert res.ok is True
    assert res.advisory is not None
    assert res.advisory.objective_id == "OP15_PLATFORM_GUIDE"
    assert "tdh" in res.advisory.assessment.lower() or "head" in res.advisory.assessment.lower() or "total dynamic head" in res.advisory.assessment.lower()
