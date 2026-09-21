"""
Canonical ESP Telemetry, Label, and Assessment Schemas.
Defines the standard data contract across ingestion, feature engineering,
model inference, explainability, and frontend visualization.
"""

import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field



class ESPOverallStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    FAULT = "FAULT"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ParameterStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class DataQualityStatus(str, Enum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    INSUFFICIENT = "INSUFFICIENT"


class FaultClass(str, Enum):
    HEALTHY = "HEALTHY"
    DRY_WELL_PUMP_OFF = "DRY_WELL_PUMP_OFF"
    BLOCKED_INTAKE = "BLOCKED_INTAKE"
    SCALE_OR_PUMP_WEAR = "SCALE_OR_PUMP_WEAR"
    SAND_INGESTION = "SAND_INGESTION"
    BEARING_DEGRADATION = "BEARING_DEGRADATION"
    HIGH_VISCOSITY_COLD_START = "HIGH_VISCOSITY_COLD_START"
    HIGH_BACKPRESSURE = "HIGH_BACKPRESSURE"
    OPEN_CHOKE = "OPEN_CHOKE"
    UNDERVOLTAGE = "UNDERVOLTAGE"
    PHASE_IMBALANCE = "PHASE_IMBALANCE"
    MOTOR_OVERLOAD = "MOTOR_OVERLOAD"
    POWER_LOSS = "POWER_LOSS"
    SENSOR_DRIFT = "SENSOR_DRIFT"
    UNKNOWN_UNSEEN = "UNKNOWN_UNSEEN"


class SensorProvenance(str, Enum):
    LIVE_MQTT = "LIVE_MQTT"
    DATABASE = "DATABASE"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    UNAVAILABLE = "UNAVAILABLE"


class CanonicalESPTelemetry(BaseModel):
    """The 13 monitored physical parameters for ESP condition monitoring."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    esp_id: str = ""
    well_id: str = ""
    
    # 13 Monitored Physical Parameters
    liquid_rate_bpd: float = Field(0.0, description="Surface liquid rate in BPD")
    intake_pressure_psi: float = Field(0.0, description="Pump Intake Pressure (PIP) in PSI")
    motor_current_a: float = Field(0.0, description="Motor total/phase current in Amperes")
    motor_load_pct: float = Field(0.0, description="Motor loading in % of rated power (DERIVED: I / I_rated * 100)")
    motor_temperature_c: float = Field(0.0, description="Motor internal winding temperature in °C")
    vibration_rms: float = Field(0.0, description="Pump/motor multi-axis vibration in g RMS")
    discharge_pressure_psi: float = Field(0.0, description="Pump Discharge Pressure (PDP) in PSI")
    motor_voltage_v: float = Field(0.0, description="Motor terminal supply voltage in Volts")
    intake_temperature_c: Optional[float] = Field(None, description="Intake wellbore fluid temperature in °C (INFERRED if absent)")
    flowline_pressure_psi: Optional[float] = Field(None, description="Surface flowline header pressure in PSI (INFERRED if absent)")
    wellhead_pressure_psi: Optional[float] = Field(None, description="Surface wellhead tubing pressure in PSI (INFERRED if absent)")
    casing_pressure_psi: Optional[float] = Field(None, description="Surface casing annulus pressure in PSI (INFERRED if absent)")
    choke_size_64in: Optional[float] = Field(None, description="Surface production choke size in 64ths of an inch (INFERRED if absent)")
    
    # Additional Contextual & Electrical Telemetry
    frequency_hz: float = Field(0.0, description="VFD operating frequency in Hz")
    water_cut_pct: float = Field(0.0, description="Water cut percentage %")
    gas_flow_mscfd: float = Field(0.0, description="Surface gas production rate in MSCFD")
    
    # Asset Specifications & Downhole Diagnostics
    pump_model: Optional[str] = Field(None, description="Pump model code e.g. TE2700, TD650, B400")
    stages: Optional[int] = Field(None, description="Pump stage count")
    motor_hp: Optional[float] = Field(None, description="Motor nameplate horsepower")
    fluid_level_above_pump_ft: Optional[float] = Field(None, description="Fluid level above pump in ft")
    productivity_index_bpd_psi: Optional[float] = Field(None, description="Well productivity index")
    drawdown_psi: Optional[float] = Field(None, description="Drawdown pressure in PSI")
    gas_volume_fraction_pct: Optional[float] = Field(None, description="Pump intake gas volume fraction %")
    voltage_imbalance_pct: Optional[float] = Field(None, description="3-phase voltage imbalance %")
    current_imbalance_pct: Optional[float] = Field(None, description="3-phase current imbalance %")
    
    # Sensor Provenance Mapping per Field
    provenance_map: Dict[str, SensorProvenance] = Field(default_factory=dict)
    
    # Quality & Source Metadata
    data_quality: DataQualityStatus = DataQualityStatus.GOOD
    quality_notes: List[str] = Field(default_factory=list)
    source: str = "MQTT_LIVE"
    ingestion_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ParameterEvaluation(BaseModel):
    parameter: str
    canonical_name: str
    unit: str
    value: Optional[float]
    reference_min: float
    reference_max: float
    engineering_min: Optional[float] = None
    engineering_max: Optional[float] = None
    deviation: float = 0.0
    deviation_percent: float = 0.0
    status: ParameterStatus = ParameterStatus.NORMAL
    provenance: SensorProvenance = SensorProvenance.LIVE_MQTT
    provenance_note: str = "Live sensor measurement from MQTT"
    is_available: bool = True
    trend: str = "STABLE"  # "INCREASING", "DECREASING", "STABLE"
    rate_of_change: float = 0.0
    message: str = "Within normal operating envelope"


class RuleEvaluationResult(BaseModel):
    rule_id: str
    fault: FaultClass
    triggered: bool
    severity: str  # "INFO", "WARNING", "CRITICAL"
    condition_description: str
    persistence_seconds: float = 0.0
    explanation: str


class FaultClassificationResult(BaseModel):
    predicted_fault: FaultClass
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_level: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"
    class_probabilities: Dict[str, float] = Field(default_factory=dict)
    is_unknown: bool = False
    evidence: List[str] = Field(default_factory=list)
    model_version: str = "fault-classifier-v1.0"


class FaultRiskPrediction(BaseModel):
    target_fault: FaultClass
    horizon_hours: float
    horizon_label: str  # "1h", "6h", "12h", "24h", "3d", "7d"
    probability: float = Field(0.0, ge=0.0, le=1.0)
    risk_level: str = "LOW"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    trend: str = "STABLE"  # "INCREASING", "DECREASING", "STABLE"
    validation_status: str = "RESEARCH_REPLAY_ONLY"
    is_field_validated: bool = False
    evidence: List[str] = Field(default_factory=list)


class RULPredictionResult(BaseModel):
    status: str = "UNAVAILABLE"  # "AVAILABLE", "UNAVAILABLE"
    reason_code: str = "INSUFFICIENT_RUN_TO_FAILURE_HISTORY"
    required_data: str = "CONTINUOUS_MULTI_WEEK_LIFECYCLE"
    estimated_rul_hours: Optional[float] = None
    estimated_rul_days: Optional[float] = None

    uncertainty_lower_hours: Optional[float] = None
    uncertainty_upper_hours: Optional[float] = None
    confidence_interval_pct: float = 95.0
    data_coverage: str = "CALIBRATED"
    model_version: str = "rul-engine-v1.0"
    reason: Optional[str] = None


class AnomalyDetectionResult(BaseModel):
    anomaly_score: float = Field(0.0, ge=0.0, le=1.0)
    threshold: float = 0.70
    status: str = "NORMAL"  # "NORMAL", "UNUSUAL", "ANOMALOUS", "SEVERE_ANOMALY"
    severity: str = "NONE"  # "NONE", "LOW", "MEDIUM", "HIGH"
    is_anomaly: bool = False
    affected_parameters: List[str] = Field(default_factory=list)
    reconstruction_errors: Dict[str, float] = Field(default_factory=dict)
    reason: str = "Normal steady-state operating cluster"


class UnifiedESPAssessment(BaseModel):
    """The master health assessment synthesizing all model engines."""
    assessment_id: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    esp_id: str
    well_id: str
    
    # Master Unified Health Status
    overall_status: ESPOverallStatus = ESPOverallStatus.HEALTHY
    rule_status: ParameterStatus = ParameterStatus.NORMAL
    
    # Diagnosis & Confidence
    fault_status: str = "HEALTHY"
    fault_name: str = "Healthy Operation"
    fault_class: FaultClass = FaultClass.HEALTHY
    fault_probability: float = 1.0
    confidence_level: str = "HIGH"
    
    # Future Risk & RUL
    future_risk: str = "LOW"  # "LOW", "MEDIUM", "HIGH"
    primary_risk_fault: Optional[str] = None
    max_risk_probability: float = 0.0
    risk_predictions: List[FaultRiskPrediction] = Field(default_factory=list)
    
    rul: RULPredictionResult = Field(default_factory=RULPredictionResult)
    
    # Anomaly
    anomaly: AnomalyDetectionResult = Field(default_factory=AnomalyDetectionResult)
    
    # Parameter Evaluations (all 13 parameters)
    parameter_evaluations: List[ParameterEvaluation] = Field(default_factory=list)
    
    # Explainability & Narratives
    top_reasons: List[str] = Field(default_factory=list)
    operator_action: str = "Continue standard operational monitoring."
    technical_explanation: str = ""
    shap_contributions: Dict[str, float] = Field(default_factory=dict)
    trajectory_summary: str = "Stable multivariate trajectory within healthy envelope."
    
    # Operational & Model Metadata
    trace_id: str = Field(default_factory=lambda: f"TRC-{uuid.uuid4().hex[:10].upper()}")
    provenance: Dict[str, Any] = Field(default_factory=dict)
    data_quality: DataQualityStatus = DataQualityStatus.GOOD
    warnings: List[str] = Field(default_factory=list)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    inference_latency_ms: float = 0.0

