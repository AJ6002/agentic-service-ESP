"""
Human-in-the-Loop (HITL) Approval Gate Node for V2 Architecture
Evaluates safety requirements on generated execution plans before specialist dispatch.
If human authorization is required and pending, halts workflow until operator approval.
"""

import logging
from typing import Any, Dict, Optional

from .plan_schema import PlanArtifact

logger = logging.getLogger(__name__)


def approval_gate(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates execution plan safety constraints.
    - If plan requires human approval and has not yet been approved:
      Sets state['approval_pending'] = True and records state['approval_reason'].
    - If plan is already approved or is low risk (no approval required):
      Sets state['approval_pending'] = False and allows workflow continuation.
    """
    plan = state.get("plan")
    if plan is None:
        state["approval_pending"] = False
        return state

    plan_obj: Optional[PlanArtifact] = None
    if isinstance(plan, PlanArtifact):
        plan_obj = plan
    elif isinstance(plan, dict):
        try:
            plan_obj = PlanArtifact.model_validate(plan)
        except Exception as exc:
            logger.warning("approval_gate: Failed to validate plan dict as PlanArtifact: %s", exc)
            # Fallback to direct dictionary access
            requires_approval = bool(plan.get("requires_human_approval", False))
            is_approved = bool(plan.get("is_approved", False))
            approval_reason = plan.get("approval_reason")
            if requires_approval and not is_approved:
                state["approval_pending"] = True
                state["approval_reason"] = approval_reason
            else:
                state["approval_pending"] = False
                state["approval_reason"] = None
            return state

    if plan_obj is not None:
        if plan_obj.requires_human_approval and not plan_obj.is_approved:
            state["approval_pending"] = True
            state["approval_reason"] = plan_obj.approval_reason
            logger.info(
                "approval_gate: Plan '%s' requires operator approval. Reason: %s",
                plan_obj.run_id,
                plan_obj.approval_reason,
            )
        else:
            state["approval_pending"] = False
            state["approval_reason"] = None
            logger.info("approval_gate: Plan '%s' cleared for execution.", plan_obj.run_id)

    return state


__all__ = ["approval_gate"]
