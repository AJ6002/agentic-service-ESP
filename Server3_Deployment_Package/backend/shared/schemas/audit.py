"""
Audit Service Contracts
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.8
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ToolCallAuditPayload(BaseModel):
    trace_id: str = Field(description="Unique correlation trace ID")
    request_id: str = Field(description="Associated request ID")
    tool_name: str = Field(description="Invoked tool name")
    objective_id: str = Field(description="Active objective ID")
    asset_id: str = Field(description="Target asset ID")
    input_args: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(default=0.0)
    status: str = Field(default="SUCCESS", description="SUCCESS, ERROR, REFUSED")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AdvisoryAuditPayload(BaseModel):
    trace_id: str
    advisory_id: str
    asset_id: str
    objective_id: str
    user_query: str
    assessment: str
    confidence: float
    provenance: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ExecutionTraceReconstruction(BaseModel):
    trace_id: str
    request_id: str
    asset_id: str
    objective_id: str
    advisory: Optional[Dict[str, Any]] = Field(default=None)
    tool_calls: List[ToolCallAuditPayload] = Field(default_factory=list)
    outcome: Optional[Dict[str, Any]] = Field(default=None)
