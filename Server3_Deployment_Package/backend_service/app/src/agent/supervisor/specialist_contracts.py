"""
Typed Contracts for Domain-Specialist Inputs, Outputs, and Conflicts
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §10
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class SpecialistInput(BaseModel):
    """
    Standardized input payload passed from Supervisor to a Specialist Subgraph.
    """
    run_id: str = Field(description="Unique run identifier")
    objective_id: str = Field(description="Active Level-2 operational objective ID")
    asset_id: str = Field(description="Target ESP asset identifier")
    task: str = Field(description="Specific domain task assigned by Supervisor")
    required_evidence: List[str] = Field(default_factory=list, description="Required evidence types")
    allowed_tools: List[str] = Field(default_factory=list, description="Tool ACL list for this specialist task")
    policy_context: Dict[str, Any] = Field(default_factory=dict, description="Tenant and authorization context")
    prior_context_refs: List[str] = Field(default_factory=list, description="References to prior specialist findings")


class SpecialistOutput(BaseModel):
    """
    Standardized output payload returned from a Specialist Subgraph to the Supervisor.
    """
    specialist_id: str = Field(description="Identifier of domain specialist (e.g. well_performance, reliability)")
    status: Literal["complete", "partial", "failed"] = Field(description="Execution completion status")
    findings: List[str] = Field(default_factory=list, description="Domain reasoning findings and conclusions")
    evidence_refs: List[str] = Field(default_factory=list, description="Source evidence URIs/IDs")
    uncertainties: List[str] = Field(default_factory=list, description="Explicit uncertainties or missing inputs")
    contradictions: List[str] = Field(default_factory=list, description="Detected contradictions with other facts")
    next_verification: List[str] = Field(default_factory=list, description="Recommended operator verification steps")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Audit of tool calls executed")
    completion_reason: str = Field(default="", description="Summary of why execution completed or stopped")


class ConflictRecord(BaseModel):
    """
    Record of contradiction detected between specialists or data sources.
    """
    conflict_type: str = Field(description="Category of conflict: e.g. engineering_vs_ml, OEM_vs_procedure, dual_specialist")
    specialist_a: str = Field(description="First reporting specialist or source")
    specialist_b: str = Field(description="Second reporting specialist or source")
    description: str = Field(description="Detailed explanation of the contradiction")
    resolution: Optional[str] = Field(default=None, description="Applied Supervisor resolution strategy")
