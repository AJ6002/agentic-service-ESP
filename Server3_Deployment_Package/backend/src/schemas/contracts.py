"""
External API Contracts & Data Payloads for ESP Agentic Platform
Grounded in Guidelines.pdf Appendix B (p. 30) & Architecture Design §4, §10
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AssetContextPayload(BaseModel):
    asset_id: str = Field(description="Unique asset identifier, e.g. ESP-Well-001")
    well_id: str = Field(description="Parent well identifier, e.g. WELL-045")
    asset_type: str = Field(default="ESP", description="Equipment type")
    status: str = Field(default="ACTIVE", description="Operational status: ACTIVE, SHUT_IN, TRIPPED")
    source_system: str = Field(default="ADVAIT", description="Originating platform")
    installation_depth_ft: Optional[float] = Field(default=8500.0, description="Pump setting depth in feet")
    pump_model: Optional[str] = Field(default="DN1750", description="OEM pump model name")
    motor_rating_hp: Optional[float] = Field(default=250.0, description="Motor nameplate horsepower")
    nameplate_current_amps: Optional[float] = Field(default=65.0, description="Motor rated current in amperes")
    be_point_bpd: Optional[float] = Field(default=1750.0, description="Best Efficiency Point flow rate in BPD")
    hierarchy: Optional[Dict[str, Any]] = Field(default=None, description="Customer, Block, Station, Cluster hierarchy")
    well_context: Optional[Dict[str, Any]] = Field(default=None, description="Detailed wellbore and location parameters")
    esp_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Complete ESP equipment component stack")
    tag_mapping: Optional[Dict[str, Any]] = Field(default=None, description="Physical SCADA tag to semantic name registry")
    operating_envelope: Optional[Dict[str, Any]] = Field(default=None, description="Approved operating limits and envelopes")
    source_provenance: Optional[Dict[str, Any]] = Field(default=None, description="Data origin and record versioning")

class TelemetryMetric(BaseModel):
    tag: str = Field(description="Sensor tag name, e.g. motor_temperature")
    value: float = Field(description="Numeric value")
    unit: str = Field(description="Engineering unit, e.g. °C, psi, bpd, Hz, amps")
    timestamp: str = Field(description="ISO timestamp")
    quality: str = Field(default="GOOD", description="Data quality indicator: GOOD, DEGRADED, STALE")

class TelemetryPayload(BaseModel):
    asset_id: str
    timestamp: str
    metrics: Dict[str, TelemetryMetric] = Field(default_factory=dict)
    data_quality_summary: str = Field(default="GOOD")

class TimeSeriesPoint(BaseModel):
    timestamp: str = Field(description="ISO observation timestamp")
    value: float = Field(description="Numeric measurement value")

class TimeSeriesSignal(BaseModel):
    signal: str = Field(description="Canonical signal name, e.g. flow_rate, intake_pressure")
    unit: str = Field(description="Engineering unit, e.g. bpd, psi, °C, Hz")
    quality: str = Field(default="GOOD", description="Signal quality flag: GOOD, DEGRADED, SPARSE, NO_DATA")
    points: List[TimeSeriesPoint] = Field(default_factory=list, description="Timestamped measurement points")

class TimeSeriesPayload(BaseModel):
    """
    Canonical Historian Window Contract.
    Grounded in Guidelines.pdf Appendix B (p. 30) & historian.txt §7
    """
    asset_id: str
    start_time: str
    end_time: str
    aggregation: str = Field(default="raw", description="raw, 1m, 5m, 15m, 1h, 1d")
    coverage: float = Field(default=1.0, description="Window data coverage score 0.0 - 1.0")
    quality_summary: str = Field(default="GOOD", description="GOOD, SPARSE, NO_DATA")
    total_points: int = Field(default=0)
    series: List[TimeSeriesSignal] = Field(default_factory=list)

class RuleDeviationCounts(BaseModel):
    h1: int = Field(default=0, alias="1h", description="Rule violations in last 1 hour")
    h24: int = Field(default=0, alias="24h", description="Rule violations in last 24 hours")
    d30: int = Field(default=0, alias="30d", description="Rule violations in last 30 days")

    class Config:
        populate_by_name = True

class RuleStatusPayload(BaseModel):
    asset_id: str
    timestamp: str
    violations: List[str] = Field(default_factory=list, description="Active rule violation codes")
    deviation_counts: RuleDeviationCounts = Field(default_factory=RuleDeviationCounts)

class AnomalyResultPayload(BaseModel):
    asset_id: str
    timestamp: str
    anomaly_score: float = Field(description="Multivariate anomaly probability 0.0 - 1.0")
    status: str = Field(description="Status: NORMAL, ELEVATED, ANOMALOUS")
    contributing_signals: List[str] = Field(default_factory=list, description="Top anomalous feature tags")

class FailurePredictionPayload(BaseModel):
    asset_id: str
    timestamp: str
    risk_24h: float = Field(description="Failure risk in next 24 hours (0.0 - 1.0)")
    risk_72h: float = Field(description="Failure risk in next 72 hours (0.0 - 1.0)")
    risk_7d: float = Field(description="Failure risk in next 7 days (0.0 - 1.0)")
    rul_hours: Optional[float] = Field(default=None, description="Remaining Useful Life in hours")
    primary_failure_mode: Optional[str] = Field(default=None, description="Dominant predicted failure mode")

class FaultDiagnosisPayload(BaseModel):
    asset_id: str
    timestamp: str
    predicted_fault_class: str = Field(description="Fault classification code, e.g. MOTOR_OVERHEATING")
    confidence: float = Field(description="Classification confidence score 0.0 - 1.0")
    supporting_evidence_features: List[str] = Field(default_factory=list)

class HealthIndexPayload(BaseModel):
    asset_id: str
    timestamp: str
    health_index: float = Field(description="Fused ESP health score 0 - 100")
    status: str = Field(description="HEALTHY, CAUTION, CRITICAL")
    contributors: List[str] = Field(default_factory=list)

class TriggeredLimitPayload(BaseModel):
    tag: str
    value: float
    limit: float
    type: str = Field(default="HIGH", description="HIGH or LOW limit violation")

class MLContractV2Payload(BaseModel):
    """
    ML Team v2.0.0 Dual-Tier Inference Engine Contract.
    Grounded in dependency_detail.md & ESP_Agentic_ML_Team_Dependencies_and_API_PreRequisites.md
    Extended with VFD Diagnostic Engine fields (ESP_APM_models WellDiagnosticEngine).
    """
    asset_id: str
    well_id: str
    timestamp: Any
    model_id: str = Field(default="esp-hybrid-dual-tier")
    model_version: str = Field(default="v2.0.0")
    feature_version: str = Field(default="phys-v2.1")
    status: str = Field(default="VALID", description="VALID, DEGRADED, UNAVAILABLE")
    state: str = Field(default="NORMAL", description="NORMAL, FAULT, ANOMALOUS")
    fault_classification: str = Field(default="Normal Operations")
    confidence_score: Optional[float] = Field(default=0.95, description="Probability score 0.0 - 1.0")
    is_anomaly: bool = Field(default=False)
    anomaly_score: float = Field(default=0.10, description="IsolationForest anomaly score 0.0 - 1.0")
    contributors: List[str] = Field(default_factory=list)
    triggered_limits: List[TriggeredLimitPayload] = Field(default_factory=list)
    telemetry_received: Dict[str, float] = Field(default_factory=dict)
    reason: Optional[str] = Field(default=None, description="Reason code when status is UNAVAILABLE, e.g. SENSOR_TELEMETRY_MISSING")
    last_valid_timestamp: Optional[Any] = Field(default=None, description="Last valid observation timestamp when state is DEGRADED")
    # ── VFD Diagnostic Engine extensions (from ESP_APM_models) ──────────────
    health_score: Optional[float] = Field(default=None, description="Composite Health Index 0-100 (from WellDiagnosticEngine)")
    est_time_to_trip: Optional[str] = Field(default=None, description="Estimated operational runway to trip, e.g. '18h' or 'N/A'")
    vfd_dynamics: Optional[Dict[str, float]] = Field(default=None, description="Physics dynamics: delta_p, torque_proxy, power_proxy_kva, thermal_elevation, thermal_rate_hr, pressure_ratio")
    normalized_features: Optional[Dict[str, float]] = Field(default=None, description="13-channel normalized [0,1] feature vector from NormalizationLayer")
    signals_filled: Optional[List[str]] = Field(default=None, description="VFD signal names filled from calibrated defaults (not from TEL API)")

class ModelOutputPayload(BaseModel):
    asset_id: str
    timestamp: str
    rules: Optional[RuleStatusPayload] = Field(default=None, description="Rule engine status; may be absent when sourced from LiveDataBridge health-index endpoint")
    anomaly: AnomalyResultPayload
    failure: FailurePredictionPayload
    fault: FaultDiagnosisPayload
    health: HealthIndexPayload
    model_versions: Dict[str, str] = Field(default_factory=dict)
    v2_contract: Optional[MLContractV2Payload] = Field(default=None, description="ML Team v2.0.0 output contract")

class DataQualityReport(BaseModel):
    status: str = Field(description="COMPLETE, PARTIAL, or STALE")
    missing_signals: List[str] = Field(default_factory=list, description="List of required signals missing from telemetry")
    stale_signals: List[str] = Field(default_factory=list, description="List of telemetry signals older than threshold")
    freshness_seconds: float = Field(default=0.0, description="Age of telemetry measurement in seconds")
    gate_passed: bool = Field(default=True, description="True if minimum evidence gate criteria passed")
    disclosure_message: str = Field(default="", description="User-facing explanation of telemetry data gaps")
    operating_range_note: str = Field(
        default="Operating ranges from seed data are NOT approved limits.",
        description="Mandatory disclaimer per Phase 4 §15"
    )

