"""
Execution Plan Schema for V2 Architecture
Defines typed contracts for agent plan steps, artifacts, and human-in-the-loop approvals.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlanStepStatus(str, Enum):
    """Lifecycle execution statuses for an individual plan step."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    """Discrete executable step inside a multi-step diagnostic or operational plan."""
    model_config = ConfigDict(populate_by_name=True)

    step_id: int = Field(description="1-based sequence index of the step")
    title: str = Field(description="Short human-readable title of the step")
    specialist: str = Field(description="Target specialist agent assigned to execute the step")
    action: str = Field(description="Specific tool call or operation to execute")
    expected_output: str = Field(description="Description of expected outcome or artifact")
    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING, description="Current execution state")
    observation_summary: Optional[str] = Field(default=None, description="Summarized output/finding after execution")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution duration in milliseconds")


class PlanArtifact(BaseModel):
    """
    Persistent Plan Artifact capturing the full execution lifecycle of a query or control objective.
    """
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(default="2.0.0", description="Semantic schema version of the PlanArtifact contract")
    run_id: str = Field(description="Unique identifier for this plan execution run")
    thread_id: str = Field(description="Conversation thread or session identifier")
    asset_id: str = Field(description="Target well/ESP asset identifier")
    objective_id: str = Field(description="Classified operational objective ID (e.g. OP01, OP03)")
    query_intent: str = Field(description="Original user intent or prompt summary")
    steps: List[PlanStep] = Field(default_factory=list, description="Ordered sequence of execution steps")
    requires_human_approval: bool = Field(default=False, description="Whether safety policy mandates HITL gate")
    approval_reason: Optional[str] = Field(default=None, description="Explanation why approval is required")
    is_approved: bool = Field(default=False, description="Whether human approval has been granted")
    audit_trail: List[dict] = Field(default_factory=list, description="Audit records for HITL decisions and execution milestones")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 creation timestamp"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 last update timestamp"
    )

    def dict(self, *args, **kwargs) -> dict:
        """Pydantic v1 backwards compatibility alias."""
        return self.model_dump(*args, **kwargs)


class PlanApprovalRequest(BaseModel):
    """Human-in-the-loop approval or rejection request payload."""
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(description="Run ID of the plan to approve or reject")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread identifier")
    action: str = Field(description="Decision action: 'APPROVE' or 'REJECT'")
    comment: Optional[str] = Field(default=None, description="Optional operator reviewer notes")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("APPROVE", "REJECT"):
            raise ValueError("action must be 'APPROVE' or 'REJECT'")
        return upper
