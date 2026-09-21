"""
V2 Execution Plan Approval Routes
Provides endpoints for Human-in-the-Loop (HITL) approval or rejection of execution plans.
Hardened with atomic Redis idempotency locks, permanent audit logging, and session authentication.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Header

from src.agent.v2.plan_schema import PlanApprovalRequest, PlanStepStatus
from src.agent.v2.plan_repository import PlanRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ui/agent/plan", tags=["v2-plan"])
v2_approval_router = router
approval_router = router


@router.post("/resume", response_model=Dict[str, Any])
async def resume_plan_execution(
    req: PlanApprovalRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """
    POST /api/ui/agent/plan/resume
    Resumes or aborts an execution plan awaiting human operator approval.
    Enforces concurrency lock (409 Conflict), audit trail logging, and optional session authentication.
    """
    # Sanitize header arguments if called directly in Python
    clean_session_id = x_session_id if isinstance(x_session_id, str) else None
    clean_auth = authorization if isinstance(authorization, str) else None

    # 1. Session Authentication Check
    enforce_auth = os.getenv("V2_ENFORCE_HITL_AUTH", "false").lower() in ("true", "1", "yes") or os.getenv("V2_HITL_REQUIRE_AUTH") == "1"
    if enforce_auth and not clean_session_id and not clean_auth:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing X-Session-ID or Authorization header for safety-critical HITL decision",
        )


    action = req.action.strip().upper()
    if action not in ("APPROVE", "REJECT"):
        raise HTTPException(
            status_code=400,
            detail="action must be 'APPROVE' or 'REJECT'",
        )

    repo = PlanRepository()
    plan = repo.get_plan(req.run_id)
    if plan is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution plan '{req.run_id}' not found.",
        )

    # 2. Dual-Operator Concurrency & Idempotency Lock
    lock_key = f"esp:lock:resume:{req.run_id}"
    if repo._redis_client is not None:
        acquired = repo._redis_client.set(lock_key, "locked", nx=True, ex=10)
        if not acquired:
            raise HTTPException(
                status_code=409,
                detail="Conflict: Plan execution state has already been decided or is locked by another operator.",
            )
    else:
        with repo._lock:
            if not hasattr(repo, "_resume_locks"):
                repo._resume_locks = set()
            if req.run_id in repo._resume_locks:
                raise HTTPException(
                    status_code=409,
                    detail="Conflict: Plan execution state has already been decided or is locked by another operator.",
                )
            repo._resume_locks.add(req.run_id)

    # 3. Permanent Audit Trail Logging
    operator_id = clean_session_id or clean_auth or "operator_console"
    repo.save_audit_event(

        req.run_id,
        {
            "action": action,
            "operator_session_id": operator_id,
            "comment": req.comment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    if action == "APPROVE":
        plan = repo.set_approval_status(req.run_id, is_approved=True) or repo.get_plan(req.run_id)
        logger.info("Plan '%s' approved by operator '%s'. Resuming workflow.", req.run_id, operator_id)
        return {
            "status": "APPROVED",
            "run_id": req.run_id,
            "plan": plan.dict() if plan else None,
            "message": "Execution plan approved by operator. Workflow resuming.",
        }
    else:  # REJECT
        repo.update_step_status(
            run_id=req.run_id,
            step_id=1,
            status=PlanStepStatus.SKIPPED,
            observation="Operation aborted by operator.",
        )
        repo.set_approval_status(req.run_id, is_approved=False)
        logger.info("Plan '%s' rejected by operator '%s'. Workflow aborted.", req.run_id, operator_id)
        return {
            "status": "REJECTED",
            "run_id": req.run_id,
            "message": "Execution plan rejected by operator. Workflow aborted.",
        }


__all__ = [
    "router",
    "approval_router",
    "v2_approval_router",
    "resume_plan_execution",
]

