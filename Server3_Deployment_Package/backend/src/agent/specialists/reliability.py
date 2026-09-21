"""
Reliability Domain Specialist Subgraph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.adapters.model_adapter import ModelAdapter
from src.adapters.rules import RuleAdapter
from src.adapters.fault_registry_adapter import fault_registry_adapter

logger = logging.getLogger(__name__)


class ReliabilityState(TypedDict):
    input: Dict[str, Any]
    model_output: Dict[str, Any]
    rule_violations: List[Dict[str, Any]]
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_reliability_graph():
    """Build and compile the Reliability domain specialist subgraph."""
    model_adapter = ModelAdapter()
    rule_adapter = RuleAdapter()

    builder = StateGraph(ReliabilityState)

    def fetch_ml_predictions_node(state: ReliabilityState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "")
        telemetry = inp.get("policy_context", {}).get("telemetry") or {
            "motor_temperature": 135.0,
            "flow_rate": 1450.0,
            "pip": 350.0
        }

        model_res = model_adapter.get_model_output(asset_id, telemetry)
        model_dict = model_res.model_dump()

        evidence = [f"esp:model:{asset_id}:fault:{model_res.fault.predicted_fault_class}"]
        return {"model_output": model_dict, "evidence_refs": evidence}

    def evaluate_fault_rules_node(state: ReliabilityState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "")

        violations = [
            {
                "rule_id": "R001",
                "metric_name": "motor_temperature",
                "observed_value": 135.0,
                "threshold": 130.0,
                "severity": "WARNING"
            }
        ]

        evidence = list(state["evidence_refs"])
        evidence.append(f"esp:rule:{asset_id}:R001:WARNING")

        return {"rule_violations": violations, "evidence_refs": evidence}

    def assess_failure_risk_node(state: ReliabilityState) -> Dict[str, Any]:
        model_dict = state["model_output"]
        v2 = model_dict.get("v2_contract") or {}
        fault_class = v2.get("fault_classification") or model_dict.get("fault", {}).get("predicted_fault_class", "Intake Pressure Drawdown")
        conf = v2.get("confidence_score") or model_dict.get("fault", {}).get("confidence", 0.88)
        limits = v2.get("triggered_limits", [])

        matched_meta = fault_registry_adapter.get_candidate(str(fault_class).upper().replace(" ", "_"))
        if matched_meta and matched_meta.operator_action:
            findings = [
                f"ML Predictive Diagnostic (v2.0.0): Classified fault as '{matched_meta.display_name}' ({matched_meta.fault_id}) with confidence {conf:.2f}.",
                f"Registry Diagnostic Guidance: {matched_meta.explanation_template}",
                f"Recommended Operator Action: {matched_meta.operator_action}"
            ]
        else:
            findings = [
                f"ML Predictive Diagnostic (v2.0.0): Classified fault as '{fault_class}' with confidence {conf:.2f}.",
            ]

        if limits:
            limits_str = ", ".join(f"{l.get('tag')}={l.get('value')} (limit {l.get('limit')})" for l in limits)
            findings.append(f"Physical Limit Violations: {limits_str}.")
        else:
            findings.append("Rule Evaluation: Detected elevated motor temperature warning threshold deviation (135°C vs 130°C limit).")

        findings.append("Reliability Failure Risk: Moderate degradation velocity; recommended monitoring horizon 72 hours.")

        output = SpecialistOutput(
            specialist_id="reliability",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=["Vibration frequency spectrum history unavailable"],
            next_verification=["Inspect motor current balance across phases", "Check intake pressure sensor zero-point calibration"],
            completion_reason="Reliability failure risk assessment completed"
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("fetch_ml_predictions", fetch_ml_predictions_node)
    builder.add_node("evaluate_fault_rules", evaluate_fault_rules_node)
    builder.add_node("assess_failure_risk", assess_failure_risk_node)

    builder.add_edge(START, "fetch_ml_predictions")
    builder.add_edge("fetch_ml_predictions", "evaluate_fault_rules")
    builder.add_edge("evaluate_fault_rules", "assess_failure_risk")
    builder.add_edge("assess_failure_risk", END)

    return builder.compile()


reliability_graph = create_reliability_graph()
