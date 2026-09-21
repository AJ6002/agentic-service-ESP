"""
Pydantic Schemas for Objective Definitions & Objective Registry
Grounded in PHASE_4_Objective_Layer_Implementation_Plan_ESP_APM.docx §20, §27
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class ObjectiveSafetyPolicy(BaseModel):
    advisory_only: bool = Field(default=True, description="Strict safety flag prohibiting autonomous control")
    max_frequency_change_hz: Optional[float] = Field(default=None, description="Max allowed frequency adjustment suggestion")
    forbidden_actions: List[str] = Field(default_factory=list, description="Explicitly prohibited operational recommendations")


class WorkflowVariant(BaseModel):
    variant_id: str = Field(description="Unique variant identifier, e.g. 'frequency_whatif'")
    title: str = Field(default="", description="Human-readable title of variant")
    description: str = Field(default="", description="Detailed description of variant scope and behavior")
    intent_classes: List[str] = Field(default_factory=list, description="Intent classification keywords triggering this variant")
    required_tools: List[str] = Field(default_factory=list, description="Tools specific to this variant")
    allowed_specialists: List[str] = Field(default_factory=list, description="Specialists participating in this variant")


class ObjectiveDefinition(BaseModel):
    objective_id: str = Field(description="Unique Level-2 operational objective identifier, e.g. OP02_PRODUCTION_DECLINE_RCA")
    version: str = Field(default="1.0", description="Schema version of objective definition")
    title: str = Field(default="", description="Human-readable title of objective")
    description: str = Field(default="", description="Detailed description of objective scope")

    scope: str = Field(
        default="single",
        description="Execution scope: 'single' (one asset, default — routes through resolve_asset/"
                    "data_quality_gate/specialists) or 'fleet' (cross-asset/aggregate — routes through "
                    "a dedicated fleet graph path, no single asset_id required). Defaults to 'single' "
                    "for backward compatibility with existing objective definitions."
    )

    # Sub-objective mechanics (Kind A vs Kind B)
    hypothesis_source: Optional[str] = Field(
        default=None,
        description="Pointer to canonical fault registry (e.g. 'fault_registry') for diagnostic ranking."
    )
    workflow_variants: List[WorkflowVariant] = Field(
        default_factory=list,
        description="Routable sub-paths with distinct tool chains."
    )

    strategic_objectives: List[str] = Field(default_factory=list, description="Level-1 Strategic Objective mappings (e.g. ['O1', 'O5'])")
    intent_classes: List[str] = Field(default_factory=list, description="Intent classification keywords / phrases")
    
    required_asset_context: List[str] = Field(default_factory=list, description="Required asset context attributes")
    required_signals: List[str] = Field(default_factory=list, description="Required telemetry sensor signal tags")
    required_evidence: List[str] = Field(default_factory=list, description="Required evidence types: telemetry, history, events, KB, models")
    required_tools: List[str] = Field(default_factory=list, description="Deterministic engineering calculation tools & services")
    allowed_specialists: List[str] = Field(default_factory=list, description="Specialist reasoning modules allowed")
    
    safety: ObjectiveSafetyPolicy = Field(default_factory=ObjectiveSafetyPolicy, description="Operational safety boundaries")
    output_format: str = Field(default="advisory_v1", description="Target advisory response format")
    
    success_criteria: List[str] = Field(default_factory=list, description="Machine-verifiable conditions for successful execution")
    verification_steps: List[str] = Field(default_factory=list, description="Human operator verification checks")

    @model_validator(mode="after")
    def validate_sub_objective_types(self):
        if self.hypothesis_source and self.workflow_variants:
            raise ValueError(
                f"Objective '{self.objective_id}' cannot declare both 'hypothesis_source' "
                f"and 'workflow_variants'. Kind A (Hypothesis) and Kind B (Workflow) are mutually exclusive."
            )
        return self
