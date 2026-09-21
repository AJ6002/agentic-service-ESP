from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from .enums import CallStatus

class CallResult(BaseModel):
    seq: int
    status: CallStatus
    raw_response: dict[str, Any] | None = None
    error: str | None = None
    latency_ms: float = 0.0
    # Structured error provenance (spec §6 error envelope). Without these,
    # every failure collapsed to status="FAILED" and downstream code could
    # only ever produce Gap(reason="DEGRADED") — Gap(reason="ABSENT") was
    # unreachable, including for genuinely absent sources like the KB.
    error_code: str | None = None    # e.g. "MQTT_DISCONNECTED", "WELL_NOT_FOUND", "ABSENT"
    status_code: int | None = None   # HTTP status, e.g. 404, 503

class EvidenceItem(BaseModel):
    evidence_id: str
    tool: str
    source_domain: str
    fetched_at: datetime
    freshness_sec: float | None = None
    status: Literal["OK", "STALE", "PARTIAL"] = "OK"
    payload: dict[str, Any] = Field(default_factory=dict)
    unit_map: dict[str, str] = Field(default_factory=dict)

class QoDResult(BaseModel):
    accepted: bool
    evidence_item: Optional[EvidenceItem] = None
    rejection_reason: str | None = None

class Gap(BaseModel):
    source_domain: str
    reason: Literal["ABSENT", "DEGRADED", "TIMEOUT"]
    required: bool

class Conflict(BaseModel):
    description: str
    evidence_ids: list[str] = Field(default_factory=list)

class EvidencePack(BaseModel):
    run_id: str
    version: int = 1
    sealed: bool = False
    sealed_at: datetime | None = None
    items: list[EvidenceItem] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)

class SealResult(BaseModel):
    pack: EvidencePack
    status: Literal["COMPLETE", "INSUFFICIENT"]
    missing_required: list[str] = Field(default_factory=list)
