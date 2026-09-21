"""
Pydantic Schema for Bounded Objective-Specific Working ContextView
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §16
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ContextView(BaseModel):
    """
    Bounded working context representation passed to LLM Advisory Generator.
    Grounded in Phase 8 Design §16.
    """
    run_id: str = Field(description="Unique agent run ID")
    objective_id: str = Field(description="Active operational objective ID")
    evidence_pack_id: str = Field(description="ID of associated frozen EvidencePack")
    asset_context: Dict[str, Any] = Field(default_factory=dict, description="Asset identity, equipment, and operating limits")
    current_state: Dict[str, Any] = Field(default_factory=dict, description="Latest validated sensor readings & QoD")
    trends: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant trend windows")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Triggering & supporting operational events")
    engineering: List[Dict[str, Any]] = Field(default_factory=list, description="Deterministic physics calculation outputs")
    model_outputs: List[Dict[str, Any]] = Field(default_factory=list, description="ML anomaly/fault predictions with confidence")
    knowledge: List[Dict[str, Any]] = Field(default_factory=list, description="Top authoritative KB chunks/SOPs")
    cases: List[Dict[str, Any]] = Field(default_factory=list, description="Top historical teardown RCA cases")
    specialist_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Structured specialist outputs")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Surfaced evidence conflicts")
    missing_data: List[str] = Field(default_factory=list, description="Explicit missing data tags/attributes")
    assumptions: List[str] = Field(default_factory=list, description="Engineering/operational assumptions")
    safety_constraints: List[str] = Field(default_factory=list, description="Mandatory advisory safety limits & forbidden actions")
