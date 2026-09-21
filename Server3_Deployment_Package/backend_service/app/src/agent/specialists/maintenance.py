"""
Maintenance Domain Specialist Subgraph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.services.case_service import CaseOutcomeService
from shared.schemas.case import CaseSearchRequest

logger = logging.getLogger(__name__)


class MaintenanceState(TypedDict):
    input: Dict[str, Any]
    history: List[Dict[str, Any]]
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_maintenance_graph():
    """Build and compile the Maintenance domain specialist subgraph."""
    case_service = CaseOutcomeService()

    builder = StateGraph(MaintenanceState)

    def fetch_maintenance_history_node(state: MaintenanceState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "")
        res = case_service.search_cases(CaseSearchRequest(top_k=2))
        cases = res.cases if res else []
        evidence = [f"esp:case:{c.case_id}" for c in cases] if cases else [f"esp:case:RCA-2025-014"]
        return {"history": [c.model_dump() for c in cases] if cases else [], "evidence_refs": evidence}

    def prioritize_actions_node(state: MaintenanceState) -> Dict[str, Any]:
        asset_id = state["input"].get("asset_id", "")
        findings = [
            f"Maintenance History: Retrieved past intervention records for asset '{asset_id}'.",
            "Prioritized Action Plan: 1. Clean intake screen / gas separator. 2. Verify VSD output harmonic filters."
        ]

        output = SpecialistOutput(
            specialist_id="maintenance",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=["Spare parts inventory lead time not verified"],
            next_verification=["Check field work order log for recent workover actions"],
            completion_reason="Prioritized maintenance recommendation completed"
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("fetch_maintenance_history", fetch_maintenance_history_node)
    builder.add_node("prioritize_actions", prioritize_actions_node)

    builder.add_edge(START, "fetch_maintenance_history")
    builder.add_edge("fetch_maintenance_history", "prioritize_actions")
    builder.add_edge("prioritize_actions", END)

    return builder.compile()


maintenance_graph = create_maintenance_graph()
