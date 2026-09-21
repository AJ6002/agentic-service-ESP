"""
Event Payload Schemas
Grounded in Phase 6 Event-Driven Architecture Spec §5, §7
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class FailureRiskPayload(BaseModel):
    risk_7d: float = Field(description="Updated 7-day failure risk probability (0.0 to 1.0)")
    previous_risk_7d: float = Field(description="Previous 7-day failure risk probability")
    primary_failure_mode: Optional[str] = Field(default=None, description="Predicted primary failure mode")


class AnomalyDetectedPayload(BaseModel):
    anomaly_score: float = Field(description="Anomaly score metric")
    signal_tag: str = Field(description="Sensor signal tag exhibiting anomaly")
    observed_value: float = Field(description="Observed telemetry measurement")
    expected_range: Dict[str, float] = Field(default_factory=dict, description="Expected min/max range")


class TripEventPayload(BaseModel):
    trip_reason: str = Field(description="SCADA trip code or cause description")
    trip_timestamp: str = Field(description="Exact trip timestamp")
    last_frequency_hz: Optional[float] = Field(default=None)
    last_motor_temp_c: Optional[float] = Field(default=None)


class ConfigChangedPayload(BaseModel):
    changed_fields: List[str] = Field(default_factory=list)
    previous_version: Optional[str] = Field(default=None)
    new_version: str = Field(default="v2.1")


class AdvisoryCreatedPayload(BaseModel):
    advisory_id: str
    objective_id: str
    confidence: float
    recommendation: str


class OutcomeConfirmedPayload(BaseModel):
    advisory_id: str
    operator_id: str
    action_taken: str
    outcome_status: str
    production_gain_bpd: Optional[float] = Field(default=0.0)
