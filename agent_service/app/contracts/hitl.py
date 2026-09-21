from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from .enums import InterruptType, ResumeAt, RunStatus
from .plan import PlanCall

class PendingInterrupt(BaseModel):
    run_id: str
    reason: InterruptType
    resume_at: ResumeAt
    slot: str | None = None
    options: list[str] = Field(default_factory=list)
    plan_ref: str | None = None
    pack_ref: str | None = None
    raised_at: datetime = Field(default_factory=datetime.utcnow)

class RunState(BaseModel):
    run_id: str
    session_id: str
    status: RunStatus = "RUNNING"
    resume_at: ResumeAt | None = None
    objective_id: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    plan: list[PlanCall] = Field(default_factory=list)
    evidence_pack_ref: str | None = None
    pending_ref: str | None = None
    decision: dict[str, Any] | None = None
    turn_count: int = 1
    replan_count: int = 0
