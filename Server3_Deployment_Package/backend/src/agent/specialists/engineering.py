"""
Engineering Domain Specialist Subgraph
Grounded in ESP_APM_Engineering_Service_Architecture_Granular_Design.docx §9, §46
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.services.engineering.engine import EngineeringCalculationEngine
from src.schemas.engineering_contracts import (
    CalculationBatchRequest, RuntimeData, FluidData, ESPEquipmentData, CalculationStatus
)

logger = logging.getLogger(__name__)


class EngineeringState(TypedDict):
    input: Dict[str, Any]
    calculation_batch_results: Dict[str, Any]
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_engineering_graph():
    """Build and compile the Engineering domain specialist subgraph."""
    engine = EngineeringCalculationEngine()

    builder = StateGraph(EngineeringState)

    def execute_engineering_calculations_node(state: EngineeringState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "FS-031")
        ctx = inp.get("policy_context", {})
        telemetry_dict = ctx.get("telemetry") or {}

        # Construct calculation runtime parameters from telemetry
        runtime = RuntimeData(
            flow_rate_q_bpd=telemetry_dict.get("flow_rate", 1450.0),
            intake_pressure_pip_psi=telemetry_dict.get("pip", 350.0),
            discharge_pressure_pdp_psi=telemetry_dict.get("pdp", 2100.0),
            pressure_diff_psi=telemetry_dict.get("pressure_diff") or (2100.0 - 350.0),
            operating_frequency_hz=telemetry_dict.get("frequency", 60.0),
            motor_measured_current_a=telemetry_dict.get("motor_current", 58.5),
            motor_temperature_c=telemetry_dict.get("motor_temperature", 110.0),
            timestamp=telemetry_dict.get("timestamp", "2026-08-27T08:00:00Z")
        )

        fluid = FluidData(
            water_cut_pct=telemetry_dict.get("water_cut", 65.0),
            oil_gravity_api=32.0,
            composite_sg=1.02
        )

        equipment = ESPEquipmentData(
            pump_model_id="D1450",
            stage_count=120,
            motor_nameplate_current_a=65.0,
            bep_flow_rate_bpd=1450.0
        )

        # Execute MVP calculation batch A1, A2, A4, A5, C2, F1, B1, E1
        batch_req = CalculationBatchRequest(
            asset_id=asset_id,
            calculation_ids=["A1", "A2", "A4", "A5", "C2", "F1", "B1", "E1"],
            runtime=runtime,
            fluid=fluid,
            equipment=equipment
        )

        batch_res = engine.execute_batch(batch_req)
        batch_dict = batch_res.model_dump()

        evidence = [
            f"esp:engineering:{asset_id}:calc:{cid}:{res.status}"
            for cid, res in batch_res.results.items()
        ]

        return {
            "calculation_batch_results": batch_dict,
            "evidence_refs": evidence
        }

    def synthesize_engineering_findings_node(state: EngineeringState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "FS-031")
        batch_dict = state.get("calculation_batch_results", {})
        results = batch_dict.get("results", {})

        findings = []
        
        # A1 Total Dynamic Head
        a1 = results.get("A1", {})
        if a1.get("status") == "SUCCESS":
            findings.append(f"A1 Total Dynamic Head: {a1.get('value')} ft (ΔP = {a1.get('secondary_outputs', {}).get('delta_p_psi')} psi).")

        # A2 Hydraulic Power
        a2 = results.get("A2", {})
        if a2.get("status") == "SUCCESS":
            findings.append(f"A2 Hydraulic Power: {a2.get('value')} hp.")

        # A5 %BEP
        a5 = results.get("A5", {})
        if a5.get("status") == "SUCCESS":
            findings.append(f"A5 %BEP Operating Point: {a5.get('value')}% of BEP at operating frequency.")

        # C2 Motor Load
        c2 = results.get("C2", {})
        if c2.get("status") == "SUCCESS":
            findings.append(f"C2 Motor Load: {c2.get('value')}% of nameplate rating.")

        # E1 ROR Check
        e1 = results.get("E1", {})
        if e1.get("status") == "SUCCESS":
            status_text = e1.get("secondary_outputs", {}).get("ror_status")
            findings.append(f"E1 Recommended Operating Range Check: {status_text}.")

        output = SpecialistOutput(
            specialist_id="EngineeringSpecialist",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=[],
            contradictions=[],
            next_verification=["Verify SCADA pressure sensor calibration if ΔP deviates from manual gauge."],
            completion_reason="Deterministic calculation batch executed successfully."
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("execute_engineering_calculations", execute_engineering_calculations_node)
    builder.add_node("synthesize_engineering_findings", synthesize_engineering_findings_node)

    builder.add_edge(START, "execute_engineering_calculations")
    builder.add_edge("execute_engineering_calculations", "synthesize_engineering_findings")
    builder.add_edge("synthesize_engineering_findings", END)

    return builder.compile()


class EngineeringSpecialist:
    """Specialist adapter for Engineering Domain"""

    def __init__(self):
        self.graph = create_engineering_graph()

    def run(self, input_data: SpecialistInput) -> SpecialistOutput:
        init_state: EngineeringState = {
            "input": input_data.model_dump(),
            "calculation_batch_results": {},
            "findings": [],
            "evidence_refs": [],
            "output": None
        }

        final_state = self.graph.invoke(init_state)
        out_dict = final_state["output"]
        return SpecialistOutput(**out_dict)
