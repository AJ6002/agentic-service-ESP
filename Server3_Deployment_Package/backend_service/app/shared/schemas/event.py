"""
Canonical Event Schema & Severity Definitions
Grounded in Phase 6 Event-Driven Architecture Spec §5, §7
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SeverityLevel(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ESPEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(description="Unique event ID, e.g. EVT-92831")
    event_type: str = Field(description="Canonical event type name, e.g. FAILURE_RISK_INCREASED")
    event_version: str = Field(default="1.0", description="Schema version of event contract")
    asset_id: str = Field(description="Target ESP asset ID, e.g. FS-031")
    tenant_id: str = Field(default="CCED", description="Tenant isolation boundary ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO 8601 UTC timestamp")
    source_service: str = Field(description="Originating service name, e.g. failure-risk-model")
    source_version: str = Field(default="1.0.0", description="Service deployment version")
    severity: SeverityLevel = Field(default=SeverityLevel.INFO, description="Consequence-based severity level")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific payload dictionary")
    correlation_id: str = Field(default="", description="End-to-end transaction trace ID")
    causation_id: Optional[str] = Field(default=None, description="Predecessor event ID that caused this event")
    idempotency_key: str = Field(default="", description="Unique key for deduplication and exact-once processing")
