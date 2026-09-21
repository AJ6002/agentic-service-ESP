"""
Case & Outcome Learning Contracts
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.6
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CaseSearchRequest(BaseModel):
    query: str = Field(description="Search text or failure symptom description")
    pump_model: Optional[str] = Field(default=None)
    top_k: int = Field(default=3)


class RCACaseItem(BaseModel):
    case_id: str
    title: str
    pump_model: str
    observed_symptoms: List[str]
    confirmed_root_cause: str
    corrective_action_taken: str
    production_impact: str
    similarity_score: float = Field(default=1.0)


class CaseSearchResponse(BaseModel):
    cases: List[RCACaseItem] = Field(default_factory=list)


class OperatorVerificationCheck(BaseModel):
    check_id: str
    step_number: int
    description: str
    required_tool_equipment: str
    safety_precaution: str


class OutcomeCapturePayload(BaseModel):
    advisory_id: str = Field(description="Associated advisory ID")
    asset_id: str = Field(description="Target asset ID")
    operator_id: str = Field(description="Operator user ID")
    action_taken: str = Field(description="Action executed by field operator")
    outcome_status: str = Field(description="CONFIRMED_SUCCESS, UNRESOLVED, REJECTED")
    confirmed_root_cause: str = Field(description="Verified root cause code/text")
    production_gain_bpd: Optional[float] = Field(default=0.0)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
