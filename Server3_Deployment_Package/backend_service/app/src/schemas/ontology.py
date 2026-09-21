"""
Strict Pydantic Ontology for Graph Extraction & Knowledge Grounding
Cognee Pattern 3: Schema-enforced failure chain and entity extraction.
Prevents ungrounded/hallucinated node creation when ingesting vendor manuals or SPE papers.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ESPMetricEnum(str, Enum):
    MOTOR_TEMP = "motor_temperature"
    INTAKE_PRESSURE = "intake_pressure"
    DISCHARGE_PRESSURE = "discharge_pressure"
    DRIVE_CURRENT = "drive_current"
    VIBRATION = "vibration"
    AXIAL_VIBRATION = "axial_vibration"
    FLOW_RATE = "flow_rate"
    FREQUENCY = "frequency"
    VOLTAGE = "voltage"


class SubsystemEnum(str, Enum):
    MOTOR = "Motor Section"
    PUMP = "Pump Section"
    SEAL = "Seal Section"
    INTAKE = "Intake Section"
    SURFACE_VSD = "Surface VSD / Transformer"
    CABLE = "Power Cable Section"


class FaultTaxonomyEnum(str, Enum):
    BEARING_WEAR = "Bearing Wear"
    MOTOR_OVERHEATING = "Motor Overheating"
    GAS_LOCK = "Gas Lock"
    PUMP_WEAR = "Pump Wear"
    SCALE_DEPOSITION = "Scale Deposition"
    UNDERLOAD = "Underload Trip"
    ELECTRICAL_FAULT = "Electrical Insulation Degradation"
    SPLINE_SHEAR = "Spline Shaft Torsion Shear"
    DEADHEADING = "Deadheading Stator Burnout"
    VOLTAGE_IMBALANCE = "Voltage Imbalance"


class FailureChain(BaseModel):
    """Canonical 1-hop or 2-hop causal chain extracted from an engineering document."""
    symptom: str = Field(description="Observed anomaly or telemetry symptom, e.g. High Motor Temperature")
    primary_metric: ESPMetricEnum = Field(description="Primary sensor metric indicating this symptom")
    mechanism: str = Field(description="Physical or chemical mechanism causing anomaly")
    failure_mode: FaultTaxonomyEnum = Field(description="Classified failure mode name")
    affected_subsystem: SubsystemEnum = Field(description="Subsystem affected")
    affected_component: str = Field(description="Component damaged, e.g. Stator Winding, Impeller")
    recommended_action: str = Field(description="Approved standard operating procedure or mitigation")
    source_document_id: str = Field(description="Manifest document ID, e.g. DOC-STD-API-11S")
    page: int = Field(default=1, description="Page number in original document")
    chunk_ids: List[str] = Field(default_factory=list, description="Linked knowledge chunk IDs in pgvector/Qdrant")


class GraphExtractionBatch(BaseModel):
    """Container for batch extraction outputs validated before inserting into Neo4j."""
    source_document_id: str = Field(description="Document ID being ingested")
    extracted_by: str = Field(default="Qwen2.5-3B-Instruct", description="LLM extractor model identifier")
    chains: List[FailureChain] = Field(default_factory=list, description="Extracted validated failure chains")
