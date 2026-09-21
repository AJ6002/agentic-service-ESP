"""
Canonical Telemetry Service Contract
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.2
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TelemetryMeasurement(BaseModel):
    tag: str = Field(description="Canonical metric name or raw tag")
    value: float = Field(description="Numerical measurement value")
    unit: str = Field(description="Engineering unit (e.g. °C, psi, bpd, Hz, A, g)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    quality: str = Field(default="GOOD", description="GOOD, DEGRADED, STALE")
    raw_tag: Optional[str] = Field(default=None, description="Original SCADA sensor tag name")


class IngestTelemetryRequest(BaseModel):
    asset_id: str = Field(description="Target asset identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metrics: List[TelemetryMeasurement] = Field(default_factory=list)


class TelemetrySnapshot(BaseModel):
    asset_id: str
    timestamp: str
    qod_summary: str = Field(default="COMPLETE", description="COMPLETE, PARTIAL, STALE")
    freshness_seconds: float = Field(default=0.0)
    metrics: Dict[str, TelemetryMeasurement] = Field(default_factory=dict)
