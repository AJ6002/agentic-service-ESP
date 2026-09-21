"""
Pydantic Schemas for Multi-Source Evidence Packs and Context Lineage
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §7, §8, §9, §10, §13
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    ASSET = "ASSET"
    TELEMETRY = "TELEMETRY"
    TREND = "TREND"
    EVENT = "EVENT"
    ENGINEERING = "ENGINEERING"
    ML = "ML"
    KNOWLEDGE = "KNOWLEDGE"
    CASE = "CASE"
    SPECIALIST = "SPECIALIST"
    USER = "USER"
    VERIFICATION = "VERIFICATION"


class AuthorityLevel(str, Enum):
    LEVEL_A_INSTALLED_APPROVED = "LEVEL_A_INSTALLED_APPROVED"
    LEVEL_B_OEM = "LEVEL_B_OEM"
    LEVEL_C_CUSTOMER_ENG = "LEVEL_C_CUSTOMER_ENG"
    LEVEL_D_SITE_HISTORY = "LEVEL_D_SITE_HISTORY"
    LEVEL_E_INDUSTRY = "LEVEL_E_INDUSTRY"
    LEVEL_F_LLM_PRIOR = "LEVEL_F_LLM_PRIOR"


class QualityStatus(str, Enum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    CONFLICTING = "CONFLICTING"


class EvidenceItem(BaseModel):
    """
    Canonical 22-field EvidenceItem schema.
    Grounded in Phase 8 Design §7.
    """
    evidence_id: str = Field(description="Unique evidence identifier, e.g. EVID-TEL-001")
    evidence_type: EvidenceType = Field(description="Category of evidence item")
    asset_id: str = Field(description="Target asset identifier, e.g. FS-031")
    source_system: str = Field(description="Origin system, e.g. TelemetryAdapter, RetrievalService")
    source_id: str = Field(description="Source identifier (doc_id, sensor tag, model name)")
    source_version: str = Field(default="1.0.0", description="Version of source system/document")
    timestamp: str = Field(description="Creation/emission ISO timestamp")
    observed_at: str = Field(description="Observation ISO timestamp")
    authority_level: AuthorityLevel = Field(default=AuthorityLevel.LEVEL_D_SITE_HISTORY, description="§3.1 Authority level")
    quality_status: QualityStatus = Field(default=QualityStatus.GOOD, description="QoD quality status")
    confidence: float = Field(default=1.0, description="Confidence score 0.0 - 1.0")
    relevance_score: float = Field(default=1.0, description="Objective-specific relevance score 0.0 - 1.0")
    semantic_type: str = Field(default="measurement", description="Semantic metric or claim type")
    value: Any = Field(default=None, description="Raw or processed measurement/prediction value")
    unit: Optional[str] = Field(default=None, description="Engineering unit (°C, psi, bpd, ft, amps)")
    statement: str = Field(description="Human-readable claim or observation summary")
    supporting_signals: List[str] = Field(default_factory=list, description="Associated sensor tags or signal inputs")
    assumptions: List[str] = Field(default_factory=list, description="Engineering or contextual assumptions")
    limitations: List[str] = Field(default_factory=list, description="Known boundary limitations or missing context")
    citation: Optional[str] = Field(default=None, description="Document citation, section, or line reference")
    source_deep_link: Optional[str] = Field(
        default=None,
        description=(
            "Developer-mode deep-link URI to the exact source record. "
            "For file-based sources: file:// path with query params. "
            "For live servers (Neo4j, pgvector): real bolt/http URI populated only when server is reachable. "
            "Never mocked — absent when source is unavailable."
        )
    )

    derived_from: List[str] = Field(default_factory=list, description="IDs of upstream evidence items used in derivation")
    correlation_id: Optional[str] = Field(default=None, description="Run or transaction correlation ID")


class EvidenceConflict(BaseModel):
    """
    Structured representation of contradictory evidence sources.
    Grounded in Phase 8 Design §13.
    """
    conflict_id: str = Field(description="Unique conflict identifier")
    evidence_refs: List[str] = Field(description="IDs of conflicting evidence items")
    conflict_type: str = Field(description="Conflict category: TELEMETRY_DISCREPANCY, ML_VS_PHYSICS, SPECIALIST_DISAGREEMENT")
    values: Dict[str, Any] = Field(default_factory=dict, description="Conflicting values mapped by source")
    authority_comparison: str = Field(description="Analysis of source authority levels")
    impact: str = Field(default="MEDIUM", description="Severity impact of conflict")
    resolution_status: str = Field(default="UNRESOLVED", description="UNRESOLVED, RESOLVED, SURFACED")
    resolution_method: Optional[str] = Field(default=None, description="Applied resolution logic")
    next_verification: List[str] = Field(default_factory=list, description="Human operator verification steps")


class KnowledgeEvidence(BaseModel):
    claim: str = Field(description="Extracted text chunk claim from KB document")
    source: str = Field(description="Source document title")
    document_id: str = Field(description="Document ID manifest reference")
    page: Optional[int] = Field(default=1, description="Page number")
    section: Optional[str] = Field(default=None, description="Section heading")
    knowledge_id: str = Field(description="Unique knowledge item ID")
    knowledge_type: str = Field(default="ingested", description="Category of knowledge")
    score: float = Field(default=1.0, description="Similarity score or authority confidence")


class TelemetryEvidence(BaseModel):
    tag: str = Field(description="Canonical metric name or raw sensor tag")
    value: float = Field(description="Numerical measurement value")
    unit: str = Field(description="Canonical unit (e.g. °C, psi, bpd, g, amps)")
    timestamp: str = Field(description="Measurement timestamp ISO format")
    source: str = Field(default="live_simulator_api", description="Telemetry provider API")
    data_quality: str = Field(default="FRESH", description="Quality status: FRESH, STALE, MISSING")


class ModelEvidence(BaseModel):
    model_name: str = Field(description="External AI model name (e.g. fault_classifier)")
    prediction: str = Field(description="Model prediction string or output class")
    confidence: float = Field(description="Prediction confidence probability 0.0 to 1.0")
    timestamp: str = Field(description="Model execution timestamp")
    model_version: str = Field(default="1.0.0", description="Model version string")
    data_quality: str = Field(default="FRESH", description="Input data quality indicator")


class CalculationEvidence(BaseModel):
    calculation_name: str = Field(description="Engineering physics calculation name (e.g. TDH)")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters used in calculation")
    result: float = Field(description="Numerical calculation result")
    unit: str = Field(description="Calculation result unit")
    assumption: str = Field(default="Standard conditions", description="Engineering assumption string")
    calculation_version: str = Field(default="1.0", description="Formula implementation version")


class EvidencePack(BaseModel):
    """
    Immutable frozen snapshot envelope for an advisory run.
    Grounded in Phase 8 Design §6, §19, §30.
    """
    pack_id: str = Field(default="", description="Unique evidence pack identifier, e.g. PACK-001")
    request_id: str = Field(description="Unique request session ID")
    asset_id: str = Field(description="Target asset identifier (e.g. FS-031)")
    objective_id: str = Field(description="Agent objective ID (e.g. OP02_PRODUCTION_DECLINE_RCA)")
    created_at: str = Field(description="Creation ISO timestamp")
    frozen: bool = Field(default=True, description="Immutability flag")
    version: str = Field(default="1.0.0", description="Evidence pack schema version")
    checksum: Optional[str] = Field(default=None, description="SHA-256 cryptographic content hash")

    # Canonical Phase 8 Collections
    items: List[EvidenceItem] = Field(default_factory=list, description="Canonical 22-field evidence items")
    conflicts: List[EvidenceConflict] = Field(default_factory=list, description="Surfaced evidence conflicts")
    missing_data: List[str] = Field(default_factory=list, description="Explicit missing signals or attributes")

    # Backward-compatible fields
    asset_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Asset metadata context")
    knowledge_evidence: List[KnowledgeEvidence] = Field(default_factory=list, description="Retrieved KB evidence")
    telemetry_evidence: List[TelemetryEvidence] = Field(default_factory=list, description="Live telemetry evidence")
    model_evidence: List[ModelEvidence] = Field(default_factory=list, description="External model evidence")
    calculation_evidence: List[CalculationEvidence] = Field(default_factory=list, description="Physics calculation evidence")
    data_quality_summary: str = Field(default="COMPLETE", description="Summary status: COMPLETE, PARTIAL, STALE")
    
    telemetry_age_seconds: Optional[float] = Field(default=0.0, description="Age of telemetry data in seconds")
    model_prediction_age_seconds: Optional[float] = Field(default=0.0, description="Age of model predictions in seconds")
    knowledge_version: str = Field(default="1.0.0", description="Version of knowledge base used")
    calculation_timestamp: Optional[str] = Field(default=None, description="Timestamp of engineering calculations")
    
    constraints: List[str] = Field(default_factory=list, description="Mandatory safety and operational constraints")
    provenance: List[str] = Field(default_factory=list, description="List of authoritative sources used in pack")

