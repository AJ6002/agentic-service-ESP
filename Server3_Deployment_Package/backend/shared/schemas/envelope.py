"""
Canonical REST Response Envelope
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §8
"""

from typing import Generic, TypeVar, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from shared.schemas.errors import ServiceErrorPayload

T = TypeVar("T")


class ResponseMeta(BaseModel):
    api_version: str = Field(default="v1", description="REST API version")
    service: str = Field(description="Originating service name")
    service_version: str = Field(default="1.0.0", description="Service deployment version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    request_id: str = Field(default="", description="Unique request tracing ID")
    correlation_id: str = Field(default="", description="End-to-end trace correlation ID")
    source_system: str = Field(default="ESP-APM", description="Source data platform")
    source_version: Optional[str] = Field(default="1.0", description="Source data version")


class RESTEnvelope(BaseModel, Generic[T]):
    data: Optional[T] = Field(default=None, description="Primary payload data object")
    meta: ResponseMeta = Field(description="Response metadata and lineage headers")
    errors: List[ServiceErrorPayload] = Field(default_factory=list, description="Error list")

    @classmethod
    def success(cls, data: Any, service: str, request_id: str = "", correlation_id: str = "", source_system: str = "ADVAIT"):
        return cls(
            data=data,
            meta=ResponseMeta(
                service=service,
                request_id=request_id,
                correlation_id=correlation_id,
                source_system=source_system
            ),
            errors=[]
        )

    @classmethod
    def error(cls, error: ServiceErrorPayload, service: str, request_id: str = "", correlation_id: str = ""):
        return cls(
            data=None,
            meta=ResponseMeta(
                service=service,
                request_id=request_id,
                correlation_id=correlation_id
            ),
            errors=[error]
        )
