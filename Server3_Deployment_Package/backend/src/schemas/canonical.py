from typing import List, Optional
from pydantic import BaseModel, Field


class Asset(BaseModel):
    id: str = Field(..., description="Unique identification code for the asset")
    name: str = Field(..., description="Human readable name of the asset")
    subsystem_category: str = Field(..., description="Category or system group of the asset")
    operating_state: str = Field(..., description="Current operational state (e.g. running, stopped, fault)")


class TelemetryMetric(BaseModel):
    parameter_name: str = Field(..., description="Canonical parameter identifier")
    metric_type: str = Field(..., description="Type of measurement (e.g. thermal, electrical, pressure, vibration)")
    current_value: float = Field(..., description="Observed value")
    unit: str = Field(..., description="Unit of measurement")
    status: str = Field(..., description="Metric health status (normal, warning, critical)")
    timestamp: str = Field(..., description="Timestamp of reading")


class ComponentNode(BaseModel):
    component_name: str = Field(..., description="Name of the component")
    parent_component: Optional[str] = Field(None, description="Parent component or subsystem name")
    monitored_metrics: List[str] = Field(default_factory=list, description="Canonical metrics monitored by this component")


class DiagnosticResult(BaseModel):
    identified_fault: str = Field(..., description="Primary fault diagnosed by the agent")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    severity_level: str = Field(..., description="Overall severity (normal, warning, critical)")
    evidence_list: List[str] = Field(default_factory=list, description="Citations and evidence from telemetry, graph, rules, and RAG")
    recommended_action: str = Field(..., description="Recommended mitigation or troubleshooting action")
