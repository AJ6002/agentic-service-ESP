from pydantic import BaseModel, Field
from typing import Any, Optional, Union
from .enums import DecisionAction, TimeRangeLabel

class UIContext(BaseModel, extra="allow"):
    selected_asset: Optional[str] = None
    selected_time_range: Optional[str] = None
    selected_visualization: Optional[str] = None
    selected_finding: Optional[str] = None
    active_tab: Optional[str] = None
    active_anomaly: Optional[str] = None
    fleet_filter: Optional[str] = None
    station_id: Optional[str] = None
    selected_route: Optional[str] = None

class QueryRequest(BaseModel, extra="allow"):
    session_id: str
    message: str
    well_id: Optional[str] = None
    asset_id: Optional[str] = None
    page_route: Optional[str] = None
    time_range: Optional[str] = None
    ui_context: Optional[Union[UIContext, dict[str, Any]]] = None
    clarify_on_insufficient: bool = False

class DecisionRequest(BaseModel):
    run_id: str
    action: DecisionAction
    token: str
    modified_args: Optional[dict[str, Any]] = None
