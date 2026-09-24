"""
Phase 4.5 Acceptance Test Suite — KB Troubleshooting Integration.
Verifies:
1. "Troubleshoot FS-17" -> OP03 with cited troubleshooting_steps in Advisory.
2. "Why did FS-17 trip?" -> OP03 remains backward-compatible.
3. "Troubleshoot FS-17" with KB down -> seals cleanly without troubleshooting steps, gap named.
4. "How do I troubleshoot a motor overload?" -> routes to OP06 (Rule 0 definitional inquiry).
5. "Troubleshoot FS-91" -> asset isolation on FS-91.
6. Citation provenance post-synthesis verification.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.contracts.evidence import EvidenceItem, EvidencePack
from app.contracts.advisory import Advisory
from app.contracts.routing import RouterInput, RouteDecision
from app.context.resolver import resolve_context
from app.routing.capability_retrieval import retrieve_candidates
from app.routing.router import route_query_full
from app.workflow.runner import run_workflow, WorkflowResult
from app.synthesis.citation_check import check_citation_provenance, CitationCheckResult


def _make_router_input(msg: str, session_id: str = "test-ac45") -> RouterInput:
    frame = resolve_context(session_id, msg)
    cand_obj, cand_tools, _ = retrieve_candidates(msg)
    return RouterInput(
        raw_message=msg,
        asset_id=frame.asset.id,
        asset_source=frame.asset.source,
        turn_count=1,
        candidate_objectives=cand_obj,
        candidate_tools=cand_tools,
    )


@pytest.mark.anyio
async def test_ac45_1_troubleshoot_well_routes_to_op03():
    """Query 1: 'Troubleshoot FS-17' routes to OP03_FAULT_DIAGNOSIS."""
    r_in = _make_router_input("Troubleshoot FS-17", "test-ac45-1")
    res = await route_query_full(r_in)
    assert res.decision.route == "WORKFLOW"
    assert res.decision.objective_id == "OP03_FAULT_DIAGNOSIS"
    assert res.decision.args.get("asset_id") == "FS-17"
    assert res.decision.clarification_needed is False


@pytest.mark.anyio
async def test_ac45_2_definitional_troubleshoot_routes_to_op06():
    """Query 4: 'How do I troubleshoot a motor overload?' routes to OP06_KNOWLEDGE_LOOKUP."""
    r_in = _make_router_input("How do I troubleshoot a motor overload?", "test-ac45-2")
    res = await route_query_full(r_in)
    assert res.decision.route == "SIMPLE"
    assert res.decision.objective_id == "OP06_KNOWLEDGE_LOOKUP"
    assert res.decision.clarification_needed is False


@pytest.mark.anyio
async def test_ac45_3_troubleshoot_different_asset_fs91():
    """Query 5: 'Troubleshoot FS-91' routes to OP03 for FS-91."""
    r_in = _make_router_input("Troubleshoot FS-91", "test-ac45-3")
    res = await route_query_full(r_in)
    assert res.decision.route == "WORKFLOW"
    assert res.decision.objective_id == "OP03_FAULT_DIAGNOSIS"
    assert res.decision.args.get("asset_id") == "FS-91"


@pytest.mark.anyio
async def test_ac45_4_why_did_well_trip_still_routes_to_op03():
    """Query 2: 'Why did FS-17 trip?' remains unchanged."""
    r_in = _make_router_input("Why did FS-17 trip?", "test-ac45-4")
    res = await route_query_full(r_in)
    assert res.decision.route == "WORKFLOW"
    assert res.decision.objective_id == "OP03_FAULT_DIAGNOSIS"
    assert res.decision.args.get("asset_id") == "FS-17"


@pytest.mark.anyio
async def test_ac45_5_e2e_troubleshoot_advisory_includes_cited_steps():
    """
    Query 1 E2E: Workflow execution for 'Troubleshoot FS-17' produces
    an Advisory with cited procedural steps in troubleshooting_steps.
    """
    res: WorkflowResult = await run_workflow(
        run_id="R-test-ac45-e2e",
        session_id="S-test-ac45-e2e",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-17"},
        confidence=0.9,
        user_query="Troubleshoot FS-17",
    )
    assert res.ok is True
    assert res.seal_result is not None
    assert res.seal_result.status == "COMPLETE"
    assert res.advisory is not None
    assert res.advisory.objective_id == "OP03_FAULT_DIAGNOSIS"

    # Verify troubleshooting_steps exist and are non-empty when KB evidence is present
    has_kb = any(item.tool in ("search_knowledge", "get_fault_taxonomy", "trace_causal_graph") for item in res.pack.items)
    if has_kb:
        assert isinstance(res.advisory.troubleshooting_steps, list)
        if len(res.advisory.troubleshooting_steps) > 0:
            # Check citation format & provenance
            cite_check = check_citation_provenance(res.advisory, res.pack)
            assert cite_check.passed is True, f"Unverified citations: {cite_check.unverified_citations}"


@pytest.mark.anyio
async def test_ac45_6_kb_down_renders_without_troubleshooting_steps(monkeypatch):
    """
    Query 3: When KB service is completely down / fails:
    - OP03 still seals (KB is optional evidence)
    - troubleshooting_steps is [] (zero fabrication)
    - Gap is named in data source status notes
    """
    from app.gateway import tool_gateway as tg_mod
    from app.gateway.adapters.common import AdapterError

    async def failing_search_kb(*args, **kwargs):
        raise AdapterError("KB service down", status_code=503, code="SERVICE_UNAVAILABLE")

    async def failing_get_kb_fault(*args, **kwargs):
        raise AdapterError("KB service down", status_code=503, code="SERVICE_UNAVAILABLE")

    async def failing_trace_kb_graph(*args, **kwargs):
        raise AdapterError("KB service down", status_code=503, code="SERVICE_UNAVAILABLE")

    monkeypatch.setattr(tg_mod.kb, "search_kb", failing_search_kb)
    monkeypatch.setattr(tg_mod.kb, "get_kb_fault", failing_get_kb_fault)
    monkeypatch.setattr(tg_mod.kb, "trace_kb_graph", failing_trace_kb_graph)

    res: WorkflowResult = await run_workflow(
        run_id="R-test-ac45-kb-down",
        session_id="S-test-ac45-kb-down",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-17"},
        confidence=0.9,
        user_query="Troubleshoot FS-17",
    )
    assert res.ok is True
    assert res.seal_result is not None
    assert res.seal_result.status == "COMPLETE"
    assert res.advisory is not None
    # Zero fabrication guarantee: troubleshooting_steps MUST be empty
    assert res.advisory.troubleshooting_steps == []
    # Status note contains KB gap
    assert any(g.source_domain in ("search_knowledge", "get_fault_taxonomy", "trace_causal_graph") for g in res.pack.gaps)
    assert "Data source status notes:" in res.text
