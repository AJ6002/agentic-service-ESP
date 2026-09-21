from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field
from .enums import AssetSource, InterruptType, MatchMethod, Resolution, TimeSource

class Mentions(BaseModel):
    assets: list[str] = Field(default_factory=list)
    times: list[str] = Field(default_factory=list)
    analysis: list[str] = Field(default_factory=list)
    pronouns: list[str] = Field(default_factory=list)

class AssetBinding(BaseModel):
    id: str | None = None
    source: AssetSource = "UNRESOLVED"
    confidence: float = 0.0
    match_method: MatchMethod = "NONE"

class TimeBinding(BaseModel):
    instant: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    source: TimeSource = "DEFAULT"
    label: str | None = None
    confidence: float = 1.0

class SessionSnapshot(BaseModel):
    last_objective: str | None = None
    last_analysis_id: str | None = None
    last_asset_id: str | None = None   # feeds SESSION/PRONOUN asset resolution
    turn_count: int = 0

class ContextFrame(BaseModel):
    session_id: str
    raw_message: str
    mentions: Mentions = Field(default_factory=Mentions)
    asset: AssetBinding = Field(default_factory=AssetBinding)
    time: TimeBinding = Field(default_factory=TimeBinding)
    resolution: Resolution = "NEW"
    pending_ref: str | None = None
    prior_analysis_ref: str | None = None
    needs_clarify: bool = False
    clarify_reason: InterruptType | None = None   # was a free string — must use the shared enum
    session_snapshot: SessionSnapshot = Field(default_factory=SessionSnapshot)
    query_params: dict[str, Any] = Field(default_factory=dict)
