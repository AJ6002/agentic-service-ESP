"""
Plan Node for V2 Architecture
Dynamically decomposes routed ToolCalls into sequential execution steps,
evaluates deterministic safety gates for human-in-the-loop approvals,
and persists execution plans to PlanRepository.
"""

import logging
import uuid
from typing import List, Optional, Tuple

from .plan_schema import PlanArtifact, PlanStep, PlanStepStatus
from .plan_repository import PlanRepository
from .orchestrator import ToolCall

logger = logging.getLogger(__name__)

# Map tool names to canonical operational objective IDs
TOOL_TO_OBJECTIVE = {
    "set_operating_frequency": "OP00_OPERATIONAL_CONTROL",
    "get_asset_status": "OP01_CURRENT_STATUS",
    "analyze_production_decline": "OP02_PRODUCTION_DECLINE_RCA",
    "diagnose_fault": "OP03_FAULT_DIAGNOSIS",
    "get_health_index": "OP04_HEALTH_ASSESSMENT",
    "check_early_warnings": "OP05_EARLY_WARNING",
    "lookup_sop_procedure": "OP06_PROCEDURE_LOOKUP",
    "general_inquiry": "OP07_GENERAL_INQUIRY",
    "get_fleet_inventory": "OP08_FLEET_INVENTORY",
    "get_fleet_production_optimization": "OP09_FLEET_PRODUCTION_OPTIMIZATION",
    "get_fleet_design_sizing": "OP10_FLEET_DESIGN_SIZING",
    "get_fleet_maintenance_priority": "OP11_FLEET_MAINTENANCE_PRIORITY",
    "get_fleet_case_analytics": "OP12_FLEET_CASE_ANALYTICS",
    "get_fleet_executive_report": "OP13_FLEET_EXECUTIVE_REPORT",
    "get_operational_history": "OP14_OPERATIONAL_HISTORY",
    "ask_clarification": "OP_CLARIFICATION",
    "get_agent_profile": "OP_AGENT_PROFILE",
    "explain_widget": "OP_EXPLAIN_WIDGET",
    "get_ml_results": "OP_ML_RESULTS",
    "render_visual": "OP_RENDER_VISUAL",
}


def _evaluate_safety_gate(query: str, tool_call: ToolCall) -> Tuple[bool, Optional[str]]:
    """
    Deterministic safety gate evaluation.
    Requires human approval for:
    - Actuation commands (e.g. set_operating_frequency or setpoint changes)
    - Active command interventions: shutdown, emergency stop, stop pump, trip pump
    Diagnostic and historical inquiries (e.g., 'why did it trip', 'what happened when it tripped')
    are read-only and do NOT require human approval.
    """
    q_lower = query.lower()

    if tool_call.name == "set_operating_frequency":
        return True, "VFD setpoint change requires human authorization"

    # Distinguish active control commands from investigative/diagnostic questions
    investigative_markers = ("why", "what happened", "how", "when", "show", "check", "explain", "investigat", "diagnos", "history", "log", "analy")
    is_inquiry = any(marker in q_lower for marker in investigative_markers)

    if not is_inquiry:
        critical_keywords = ("shutdown", "shut down", "trip the", "trip pump", "trip well", "kill", "stop pump", "emergency stop")
        for kw in critical_keywords:
            if kw in q_lower:
                return True, f"Operation involving critical action '{kw}' requires human authorization"
    else:
        # Even in inquiry, if explicit emergency shutdown command is invoked
        if "emergency shutdown" in q_lower or "emergency stop" in q_lower:
            return True, "Operation involving critical action 'emergency shutdown' requires human authorization"

    return False, None


def _decompose_steps(tool_call: ToolCall, asset_id: str) -> List[PlanStep]:
    """
    Dynamically decomposes the ToolCall into 3–5 sequential PlanSteps
    assigned to specialized sub-agents.
    """
    name = tool_call.name

    if name == "set_operating_frequency":
        return [
            PlanStep(
                step_id=1,
                title="Audit Pre-Actuation Telemetry",
                specialist="telemetry",
                action="get_asset_status",
                expected_output="Current intake pressure, motor temperature, and baseline current",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Validate Operating Envelope & Thermal Limits",
                specialist="governance",
                action="validate_operating_limits",
                expected_output="Verification that requested frequency complies with safe operating envelope",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Request Operator HITL Authorization",
                specialist="hitl",
                action="request_human_approval",
                expected_output="Explicit operator confirmation and safety sign-off",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=4,
                title="Dispatch VFD Frequency Setpoint",
                specialist="control",
                action="set_operating_frequency",
                expected_output="Confirmed drive frequency change and telemetry acknowledgement",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=5,
                title="Verify Post-Actuation Telemetry Stabilization",
                specialist="telemetry",
                action="get_asset_status",
                expected_output="Stabilized operating metrics confirming successful transition",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "diagnose_fault":
        return [
            PlanStep(
                step_id=1,
                title="Ingest Asset Telemetry & Trip Signatures",
                specialist="telemetry",
                action="get_asset_status",
                expected_output="Real-time electrical current, vibration, and intake pressure signatures",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Run Diagnostic & Physics Fault Classifier",
                specialist="diagnostic",
                action="diagnose_fault",
                expected_output="Identified fault classification, confidence score, and root causes",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Attach Forensics Timeline Visual Evidence",
                specialist="visualizer",
                action="render_visual",
                expected_output="Synchronized dynamic tipping tracks and earliest departure marker",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=4,
                title="Retrieve SOP & Mitigation Protocols",
                specialist="knowledge",
                action="lookup_sop_procedure",
                expected_output="Authoritative standard operating procedures and mitigation recommendations",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "analyze_production_decline":
        return [
            PlanStep(
                step_id=1,
                title="Fetch Inflow & Historical Production Metrics",
                specialist="telemetry",
                action="get_operational_history",
                expected_output="Time-series drawdown, intake pressure, and liquid rate trends",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Execute Pump Curve & BEP Deviation Analysis",
                specialist="reservoir_production",
                action="analyze_production_decline",
                expected_output="Head degradation quantification and operating point shift relative to BEP",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Attach Pump Performance Visual Evidence",
                specialist="visualizer",
                action="render_visual",
                expected_output="H-Q curve operating point, BEP bounds, and head drift markers",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=4,
                title="Formulate Production Uplift Strategy",
                specialist="optimization",
                action="get_fleet_production_optimization",
                expected_output="Recommended frequency/choke adjustments and production uplift projection",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name in ("get_fleet_inventory", "get_fleet_production_optimization", "get_fleet_design_sizing",
                  "get_fleet_maintenance_priority", "get_fleet_case_analytics", "get_fleet_executive_report"):
        return [
            PlanStep(
                step_id=1,
                title="Query Fleet Inventory & Asset Registry",
                specialist="fleet_analytics",
                action="get_fleet_inventory",
                expected_output="Active well census and field-level operational distribution",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Analyze Fleet Degradation & Risk Rankings",
                specialist="reliability",
                action="get_fleet_maintenance_priority",
                expected_output="Prioritized list of degraded and high-risk assets",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Compile Executive Briefing & Action Items",
                specialist="reporting",
                action="get_fleet_executive_report",
                expected_output="Aggregated fleet health summary, production gaps, and maintenance recommendations",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "get_asset_status":
        return [
            PlanStep(
                step_id=1,
                title="Acquire Live SCADA Sensor Telemetry",
                specialist="telemetry",
                action="get_asset_status",
                expected_output="Current electrical drive parameters, pressures, and temperatures",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Correlate Statistical Operating Envelope",
                specialist="visualizer",
                action="render_visual",
                expected_output="P10-P90 baseline boundaries and out-of-spec channel indicators",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Evaluate Dynamic Operational Limits & Alerts",
                specialist="reliability",
                action="check_early_warnings",
                expected_output="Threshold violations, active alarms, and anomaly scores",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=4,
                title="Synthesize Operational Status Briefing",
                specialist="reporting",
                action="get_asset_status",
                expected_output="Grounded operational status report for operator review",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "get_operational_history":
        return [
            PlanStep(
                step_id=1,
                title="Query Historian Sensor Time-Series & Event Logs",
                specialist="telemetry",
                action="get_operational_history",
                expected_output="Continuous SCADA telemetry window and historical trip logs",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Evaluate Dynamic Stability & Baselines",
                specialist="diagnostic",
                action="diagnose_fault",
                expected_output="Multi-sensor stability evaluation and corridor departures",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Attach Forensics Timeline Visual Evidence",
                specialist="visualizer",
                action="render_visual",
                expected_output="Synchronized dynamic tipping tracks, trip lines, and sensor breakout markers",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name in ("lookup_sop_procedure", "general_inquiry", "get_agent_profile"):
        return [
            PlanStep(
                step_id=1,
                title="Retrieve Domain Standards & Operational Guidelines",
                specialist="knowledge",
                action="lookup_sop_procedure",
                expected_output="Verified API RP 11S / IEC standards and operational documentation",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Synthesize Technical Advisory & Engineering Guidance",
                specialist="advisor",
                action="general_inquiry",
                expected_output="Authoritative domain answer with technical explanations and citations",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Validate Against Site Operating Constraints",
                specialist="governance",
                action="validate_governance",
                expected_output="Verification of compliance with field safety standards",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "explain_widget":
        widget = tool_call.args.get("widget_id", "pump-curve")
        return [
            PlanStep(
                step_id=1,
                title=f"Resolve Visualization Specs for '{widget}'",
                specialist="knowledge",
                action="get_chart_spec",
                expected_output="Deterministic governing physics, axes, and visual styling",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Compute Live Operating Coordinates via Chart Factory",
                specialist="diagnostic",
                action="explain_widget",
                expected_output="Single-source operating point, BEP corridor, and dynamic thresholds",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Synthesize Contextual Narrative & Operational Guidance",
                specialist="advisor",
                action="synthesize_chart_explanation",
                expected_output="Authoritative visual explanation aligned with on-screen chart layout",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "render_visual":
        widget = tool_call.args.get("widget_id", "forensics-timeline")
        if widget == "forensics-timeline" or "timeline" in widget:
            step2_title = "Compute Single-Source Dynamic Tipping Timeline"
            step2_out = "Single-source forensic timeline points, baseline corridors, and breakout indicators"
        elif widget == "subsystem-equalizer" or "equalizer" in widget or "subsystem" in widget:
            step2_title = "Compute 4-Subsystem Baseline Deviations & Depth Pressure Profile"
            step2_out = "Subsystem equalizer deviations, 3-tier differential diagnosis, and wellbore hydrostatic curve"
        elif widget == "operating-envelope" or "envelope" in widget:
            step2_title = "Compute Statistical Operating Envelope Corridors"
            step2_out = "P10-P90 statistical boundaries and out-of-spec channel indicators"
        elif widget == "pump-curve" or "curve" in widget:
            step2_title = "Compute Factory OEM Pump Curve & BEP Drift"
            step2_out = "H-Q curve operating point, BEP bounds, and head drift markers"
        else:
            step2_title = "Compute Synchronized 4-Channel Telemetry Trends"
            step2_out = "Multi-channel synchronized telemetry streams"

        return [
            PlanStep(
                step_id=1,
                title=f"Resolve Visualization Specs for '{widget}'",
                specialist="knowledge",
                action="get_chart_spec",
                expected_output="Deterministic governing physics, axes, and visual styling",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title=step2_title,
                specialist="visualizer",
                action="render_visual",
                expected_output=step2_out,
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Synthesize Contextual Engineering Commentary",
                specialist="advisor",
                action="synthesize_chart_explanation",
                expected_output="Authoritative visual explanation aligned with on-screen chart layout",
                status=PlanStepStatus.PENDING,
            ),
        ]

    elif name == "get_ml_results":
        return [
            PlanStep(
                step_id=1,
                title="Query mlresults.db Model History",
                specialist="diagnostic",
                action="get_ml_results",
                expected_output="Recent ML model classifications, canonical verdicts, and health scores",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title="Evaluate Subsystem Reliability & Anomaly Severity",
                specialist="reliability",
                action="get_health_index",
                expected_output="Aggregated asset health index and trend direction",
                status=PlanStepStatus.PENDING,
            ),
        ]

    else:
        # Generic fallback 3-step sequence
        return [
            PlanStep(
                step_id=1,
                title="Ingest Operational Telemetry & Asset Baseline",
                specialist="telemetry",
                action="get_asset_status",
                expected_output="Current telemetry and baseline operating metrics",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=2,
                title=f"Execute {name.replace('_', ' ').title()}",
                specialist="specialist",
                action=name,
                expected_output=f"Execution outputs from {name}",
                status=PlanStepStatus.PENDING,
            ),
            PlanStep(
                step_id=3,
                title="Synthesize Findings & Operator Guidance",
                specialist="reporting",
                action="synthesize_advisory",
                expected_output="Integrated operational advisory and recommended next actions",
                status=PlanStepStatus.PENDING,
            ),
        ]


def create_execution_plan(
    query: str,
    tool_call: ToolCall,
    asset_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> PlanArtifact:
    """
    Creates and persists an execution PlanArtifact decomposed into 3-5 PlanSteps
    with deterministic safety gate evaluation.
    """
    resolved_run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
    resolved_thread_id = thread_id or f"thread-{uuid.uuid4().hex[:8]}"
    resolved_asset_id = asset_id or tool_call.args.get("asset_id") or ""

    requires_approval, approval_reason = _evaluate_safety_gate(query, tool_call)
    objective_id = TOOL_TO_OBJECTIVE.get(tool_call.name, "OP01_CURRENT_STATUS")
    steps = _decompose_steps(tool_call, resolved_asset_id)

    plan = PlanArtifact(
        run_id=resolved_run_id,
        thread_id=resolved_thread_id,
        asset_id=resolved_asset_id,
        objective_id=objective_id,
        query_intent=query,
        steps=steps,
        requires_human_approval=requires_approval,
        approval_reason=approval_reason,
        is_approved=False,
    )

    repo = PlanRepository()
    repo.save_plan(plan)
    logger.info("Persisted PlanArtifact %s (requires_approval=%s)", plan.run_id, plan.requires_human_approval)

    return plan
