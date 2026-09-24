from typing import Optional
from pydantic import BaseModel, Field
from app.contracts.plan import PlanArtifact
from app.routing.objective_registry import get_objective

class PolicyResult(BaseModel):
    approved: bool
    plan: PlanArtifact
    violations: list[str] = Field(default_factory=list)

ALLOWED_TOOLS = {
    "get_asset_context",
    "get_live_telemetry",
    "get_historian_window",
    "get_historian_aggregates",
    "get_historian_latest",
    "get_historian_coverage",
    "get_ml_results",
    "get_events",
    "get_events_timeline",
    "get_trips",
    "search_knowledge",
    "get_fault_taxonomy",
    "trace_causal_graph",
    "diagnose_fault",
    "get_anomaly",
    "get_health_index",
    "get_degradation",
    "get_explanation",
    "get_current_status",
    "get_card",
    "get_cards_catalog",
    "get_live_wells",
    "set_operating_frequency",
}

def validate_plan(plan: PlanArtifact) -> PolicyResult:
    """
    Deterministic Policy Gate validating entire plan before any call is dispatched.
    Ensures authorized tools, argument compliance with arg_schema, and safety class rules.
    """
    violations: list[str] = []
    manifest = get_objective(plan.objective_id)

    if not manifest:
        violations.append(f"Disallowed or unknown objective_id: {plan.objective_id}")
        return PolicyResult(approved=False, plan=plan, violations=violations)

    # 1. Validate tool authorization
    for call in plan.calls:
        if call.tool not in ALLOWED_TOOLS:
            violations.append(f"Disallowed tool '{call.tool}' at seq {call.seq}")

    # 2. Validate required arguments from manifest arg_schema
    schema = manifest.arg_schema or {}
    required_args = schema.get("required", [])
    for req in required_args:
        val = plan.args.get(req)
        if val is None or str(val).strip() == "":
            violations.append(f"Missing required argument '{req}' for {manifest.objective_id}")

    # 3. Validate safety-class consistency
    for call in plan.calls:
        if call.kind == "WRITE" and manifest.safety_class != "WRITE":
            violations.append(
                f"Safety violation: call {call.tool} is WRITE but objective {manifest.objective_id} is {manifest.safety_class}"
            )

    approved = len(violations) == 0
    return PolicyResult(approved=approved, plan=plan, violations=violations)
