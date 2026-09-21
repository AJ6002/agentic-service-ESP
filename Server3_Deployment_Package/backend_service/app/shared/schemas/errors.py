"""
Standardized Error Contract & Error Catalog
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §9
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: Optional[str] = Field(default=None, description="Target field name associated with error")
    message: str = Field(description="Detailed error explanation")


class ServiceErrorPayload(BaseModel):
    code: str = Field(description="Standardized error code, e.g. ASSET_NOT_FOUND")
    message: str = Field(description="Human-readable error description")
    target: Optional[str] = Field(default=None, description="Target entity or parameter")
    details: List[ErrorDetail] = Field(default_factory=list, description="Granular error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    @classmethod
    def create(cls, code: str, message: str, target: Optional[str] = None, details: Optional[List[ErrorDetail]] = None):
        return cls(
            code=code,
            message=message,
            target=target,
            details=details or []
        )
