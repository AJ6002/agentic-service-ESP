"""
Unified AgentState Schema for LangGraph Supervisor Orchestration
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §6
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class RunState(TypedDict):
    run_id: str
    objective_id: str
    trigger_type: Literal["user", "event"]
    correlation_id: str
    status: str
    schema_version: str


class RequestState(TypedDict):
    user_query: str
    event_id: Optional[str]
    asset_id: str


class ContextState(TypedDict):
    asset: Optional[Dict[str, Any]]
    telemetry: Dict[str, float]
    history: List[Dict[str, Any]]
    engineering: Dict[str, Any]
    models: Dict[str, Any]
    knowledge: List[Dict[str, Any]]


class PlanState(TypedDict):
    steps: List[str]
    active_step: int
    completion_criteria: List[str]


class SafetyState(TypedDict):
    is_safe: bool
    blocked_actions: List[str]
    escalation_required: bool


class AuditState(TypedDict):
    tool_calls: List[Dict[str, Any]]
    versions: Dict[str, str]
    trace_ids: List[str]
    node_timestamps: Dict[str, float]


class BudgetState(TypedDict):
    steps_used: int
    max_steps: int
    tool_calls_used: int
    max_tool_calls: int
    start_time: float
    timeout_seconds: float


class AgentState(TypedDict):
    """
    Top-level State object passed between nodes in the Supervisor Graph.
    """
    run: RunState
    request: RequestState
    context: ContextState
    plan: PlanState
    specialist_results: List[Dict[str, Any]]
    evidence_refs: List[str]
    conflicts: List[Dict[str, Any]]
    safety_state: SafetyState
    advisory_draft: Optional[Dict[str, Any]]
    audit: AuditState
    budget: BudgetState
    error: Optional[str]
    # B3: Clarification / HITL fields
    is_ambiguous: bool
    clarification_question: Optional[str]
    clarification_answer: Optional[str]


def create_initial_agent_state(
    run_id: str,
    asset_id: str,
    user_query: str = "",
    event_id: Optional[str] = None,
    objective_id: str = "OP02_PRODUCTION_DECLINE_RCA",
    trigger_type: Literal["user", "event"] = "user",
    correlation_id: str = ""
) -> AgentState:
    """Helper to construct a fully initialized AgentState object."""
    import time
    return {
        "run": {
            "run_id": run_id,
            "objective_id": objective_id,
            "trigger_type": trigger_type,
            "correlation_id": correlation_id or run_id,
            "status": "INITIALIZED",
            "schema_version": "1.0"
        },
        "request": {
            "user_query": user_query,
            "event_id": event_id,
            "asset_id": asset_id
        },
        "context": {
            "asset": None,
            "telemetry": {},
            "history": [],
            "engineering": {},
            "models": {},
            # ESP_APM_models live diagnosis (14-signal VFD engine, real MQTT-fed) — a
            # separate source from "models" above (the legacy health-index path). None
            # until load_minimum_context_node populates it; never fabricated.
            "vfd_diagnostic": None,
            "knowledge": []
        },
        "plan": {
            "steps": [],
            "active_step": 0,
            "completion_criteria": []
        },
        "specialist_results": [],
        "evidence_refs": [],
        "conflicts": [],
        "safety_state": {
            "is_safe": True,
            "blocked_actions": [],
            "escalation_required": False
        },
        "advisory_draft": None,
        "audit": {
            "tool_calls": [],
            "versions": {"phase": "7.0"},
            "trace_ids": [run_id],
            "node_timestamps": {}
        },
        "budget": {
            "steps_used": 0,
            "max_steps": 20,
            "tool_calls_used": 0,
            "max_tool_calls": 15,
            "start_time": time.time(),
            "timeout_seconds": 120.0
        },
        "error": None,
        "is_ambiguous": False,
        "clarification_question": None,
        "clarification_answer": None,
    }
