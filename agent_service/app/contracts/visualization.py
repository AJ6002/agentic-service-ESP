from typing import Any
from pydantic import BaseModel, Field

class VisualizationSpec(BaseModel):
    widget_id: str = "cards"
    card_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

