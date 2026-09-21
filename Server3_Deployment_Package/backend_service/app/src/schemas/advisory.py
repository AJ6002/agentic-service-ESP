"""
Standard Advisory Response Schema for ESP Agentic Platform
Grounded in Guidelines.pdf Appendix C (pp. 30-31, lines 121-158)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AdvisoryEvidenceItem(BaseModel):
    source_type: str = Field(description="Telemetry, Model, KB, Calculation, Rule")
    source_id: str = Field(description="Document ID, Sensor Tag, or Model Name")
    observation: str = Field(description="Observed value or claim text")
    timestamp: str = Field(description="ISO timestamp")
    page: Optional[int] = Field(default=None, description="Page number if KB document")
    source_deep_link: Optional[str] = Field(default=None, description="Direct URL to database web viewer or GUI")

class StandardAdvisoryPayload(BaseModel):
    advisory_id: str = Field(description="Unique advisory generation ID")
    asset_id: str = Field(description="Target ESP asset identifier")
    objective_id: str = Field(description="Active agent objective ID")
    timestamp: str = Field(description="Advisory generation ISO timestamp")
    
    # Guidelines.pdf Appendix C Mandatory Response Fields
    assessment: str = Field(description="Clear summary statement of current asset state")
    evidence: List[AdvisoryEvidenceItem] = Field(default_factory=list, description="Source-cited observations")
    diagnosis: str = Field(description="Likely root cause diagnosis and ranked hypotheses")
    confidence: float = Field(description="Confidence score 0.0 - 1.0 (discloses missing inputs if < 1.0)")
    risk: str = Field(description="Failure risk horizon and operational consequences")
    recommendation: str = Field(description="Bounded operational action recommendation")
    expected_impact: str = Field(description="Expected production & reliability impact")
    constraints: List[str] = Field(default_factory=list, description="Mandatory safety limits & forbidden actions")
    verification: List[str] = Field(default_factory=list, description="Step-by-step human operator verification checks")
    
    provenance: List[str] = Field(default_factory=list, description="Authoritative sources & versions used")

    # UI Schema Compatibility Fields (Frontend AgentDialog & React UI)
    recommended_action: Optional[Dict[str, Any]] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None)

    # Phase 4: 5-Step Modal Diagnostic Response Fields
    trend: Optional[str] = Field(default=None, description="Established telemetry trend / slope")
    expected_vs_actual: List[Dict[str, Any]] = Field(default_factory=list, description="P10-P90 baseline comparison table")
    ranked_hypotheses: List[Dict[str, Any]] = Field(default_factory=list, description="Ranked diagnostic hypotheses")
    follow_up_prompts: List[str] = Field(default_factory=list, description="Interactive follow-up inquiries for operator")

    def model_post_init(self, __context: Any) -> None:
        if self.confidence_score is None:
            self.confidence_score = self.confidence
        if self.recommended_action is None:
            self.recommended_action = {
                "action_title": self.recommendation,
                "urgency": "HIGH" if self.confidence > 0.8 else "MEDIUM",
                "recommended_parameters": {}
            }
