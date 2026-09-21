from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from .enums import AssetSource, InterruptType, Route

class CandidateTool(BaseModel):
    tool: str
    score: float

class RouterInput(BaseModel):
    raw_message: str
    asset_id: str | None = None
    asset_source: AssetSource = "UNRESOLVED"
    time_label: str | None = None
    time_instant: datetime | None = None
    has_prior: bool = False
    prior_objective: str | None = None
    turn_count: int = 0
    candidate_objectives: list[str] = Field(default_factory=list)
    candidate_tools: list[str] = Field(default_factory=list)

class RouteDecision(BaseModel):
    route: Route
    intent: str | None = None
    objective_id: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    deferred_intents: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarify_reason: InterruptType | None = None
    clarify_slot: str | None = None
    clarify_options: list[str] = Field(default_factory=list)

    # The LLM sometimes emits an explicit JSON `null` for "no items" instead
    # of omitting the key or emitting `[]`/`{}` — both are reasonable model
    # behavior, but strict Pydantic validation was rejecting `null` outright
    # and silently demoting the whole decision to the degraded keyword
    # fallback (fallback_used=True) even though the LLM was live and
    # otherwise correct. Normalize null -> the field's empty default here,
    # instead of discarding a perfectly good LLM decision over one field.
    @field_validator("deferred_intents", "clarify_options", mode="before")
    @classmethod
    def _null_list_to_empty(cls, v):
        return [] if v is None else v

    @field_validator("args", mode="before")
    @classmethod
    def _null_dict_to_empty(cls, v):
        return {} if v is None else v
