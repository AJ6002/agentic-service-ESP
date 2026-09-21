from typing import Any, Literal, Union
from pydantic import BaseModel, Field
from .advisory import Advisory
from .enums import DecisionAction, FrameType, InterruptType
from .visualization import VisualizationSpec

class StatusFrame(BaseModel):
    type: Literal["status"] = "status"
    run_id: str
    stage: str
    progress: int
    message: str

class TextDeltaFrame(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    run_id: str
    delta: str

class ClarificationFrame(BaseModel):
    type: Literal["clarification"] = "clarification"
    run_id: str
    question: str
    options: list[str] = Field(default_factory=list)
    slot: str | None = None
    pending_ref: str | None = None

class InterruptFrame(BaseModel):
    type: Literal["interrupt"] = "interrupt"
    run_id: str
    reason: InterruptType = "APPROVE"
    pending_call: dict[str, Any] = Field(default_factory=dict)
    options: list[DecisionAction] = Field(default_factory=lambda: ["APPROVE", "MODIFY", "REJECT"])

class AdvisoryFrame(BaseModel):
    type: Literal["advisory"] = "advisory"
    run_id: str
    advisory: Union[Advisory, dict[str, Any]] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)

class VisualFrame(BaseModel):
    type: Literal["visual"] = "visual"
    run_id: str
    visualization: Union[VisualizationSpec, dict[str, Any]] = Field(default_factory=dict)

AdvisoryFrame.model_rebuild()
VisualFrame.model_rebuild()


class ErrorFrame(BaseModel):
    type: Literal["error"] = "error"
    run_id: str
    code: str
    message: str

class DoneFrame(BaseModel):
    type: Literal["done"] = "done"
    run_id: str
    status: str | None = None

Frame = Union[
    StatusFrame,
    TextDeltaFrame,
    ClarificationFrame,
    InterruptFrame,
    AdvisoryFrame,
    VisualFrame,
    ErrorFrame,
    DoneFrame,
]
