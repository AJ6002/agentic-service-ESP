from pydantic import BaseModel, Field
from typing import Any
from .enums import DecisionAction, TimeRangeLabel

class UIContext(BaseModel):
    selected_asset: str | None = None
    selected_time_range: TimeRangeLabel | None = None
    selected_visualization: str | None = None
    selected_finding: str | None = None

class QueryRequest(BaseModel):
    session_id: str
    message: str
    ui_context: UIContext | None = None
    clarify_on_insufficient: bool = False

class DecisionRequest(BaseModel):
    run_id: str
    action: DecisionAction
    token: str
    modified_args: dict[str, Any] | None = None
