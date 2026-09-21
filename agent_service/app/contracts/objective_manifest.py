from typing import Any
from pydantic import BaseModel, Field
from .enums import SafetyClass, Scope

class ObjectiveManifest(BaseModel):
    objective_id: str
    tool: str
    safety_class: SafetyClass
    scope: Scope
    required_evidence: list[str] = Field(default_factory=list)
    optional_evidence: list[str] = Field(default_factory=list)
    allowed_visuals: list[str] = Field(default_factory=list)
    arg_schema: dict[str, Any] = Field(default_factory=dict)
    # Number of gap-fill retry rounds allowed (0 = disabled). Only OP03 opts in.
    max_gapfill_rounds: int = 0
