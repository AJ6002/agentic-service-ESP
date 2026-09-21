from typing import Any
from pydantic import BaseModel, Field
from .enums import CallKind, CallStatus

class PlanCall(BaseModel):
    seq: int
    kind: CallKind
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: CallStatus = "PENDING"
    evidence_id: str | None = None

class PlanArtifact(BaseModel):
    run_id: str
    session_id: str
    objective_id: str
    args: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    calls: list[PlanCall] = Field(default_factory=list)
    requires_approval: bool = False
