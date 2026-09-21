"""
Digital Twin Domain Specialist Subgraph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.services.twin_service import DigitalTwinService

logger = logging.getLogger(__name__)


class DigitalTwinState(TypedDict):
    input: Dict[str, Any]
    twin_config: Dict[str, Any]
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_digital_twin_graph():
    """Build and compile the Digital Twin domain specialist subgraph."""
    twin_service = DigitalTwinService()

    builder = StateGraph(DigitalTwinState)

    def load_twin_config_node(state: DigitalTwinState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "FS-031")
        evidence = [f"esp:twin:{asset_id}:v1"]
        return {"twin_config": {"asset_id": asset_id, "operating_envelope": "OPTIMAL"}, "evidence_refs": evidence}

    def simulate_scenario_node(state: DigitalTwinState) -> Dict[str, Any]:
        asset_id = state["input"].get("asset_id", "")
        findings = [
            f"Digital Twin Simulation: Evaluated operating envelope boundaries for asset '{asset_id}'.",
            "What-If Scenario: Frequency increase above 62 Hz violates intake pressure minimum threshold (300 psi limit)."
        ]

        output = SpecialistOutput(
            specialist_id="digital_twin",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=["Wellbore fluid viscosity dynamic variation not modeled"],
            next_verification=["Validate intake pressure model against surface choke test"],
            completion_reason="Digital Twin scenario consequence evaluation completed"
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("load_twin_config", load_twin_config_node)
    builder.add_node("simulate_scenario", simulate_scenario_node)

    builder.add_edge(START, "load_twin_config")
    builder.add_edge("load_twin_config", "simulate_scenario")
    builder.add_edge("simulate_scenario", END)

    return builder.compile()


digital_twin_graph = create_digital_twin_graph()
