"""
Advisory & Tool Audit Application Service
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.8
"""

import logging
from typing import List, Dict, Any, Optional

from shared.schemas.audit import (
    ToolCallAuditPayload, AdvisoryAuditPayload, ExecutionTraceReconstruction
)

logger = logging.getLogger(__name__)


class AuditService:
    """
    Application Service for advisory logging, tool call tracing, and execution path reconstruction.
    """

    def __init__(self):
        self._advisories_store: Dict[str, AdvisoryAuditPayload] = {}
        self._tool_calls_store: Dict[str, List[ToolCallAuditPayload]] = {}

    def log_advisory(self, payload: AdvisoryAuditPayload) -> Dict[str, Any]:
        """Persist generated StandardAdvisoryPayload trace."""
        self._advisories_store[payload.trace_id] = payload
        logger.info(f"AuditService logged advisory {payload.advisory_id} (trace_id={payload.trace_id})")
        return {"status": "LOGGED", "trace_id": payload.trace_id}

    def log_tool_call(self, payload: ToolCallAuditPayload) -> Dict[str, Any]:
        """Persist material tool call trace."""
        if payload.trace_id not in self._tool_calls_store:
            self._tool_calls_store[payload.trace_id] = []
        self._tool_calls_store[payload.trace_id].append(payload)
        logger.info(f"AuditService logged tool call '{payload.tool_name}' for trace {payload.trace_id}")
        return {"status": "LOGGED", "trace_id": payload.trace_id}

    def get_execution_trace(self, trace_id: str) -> ExecutionTraceReconstruction:
        """Reconstruct end-to-end execution path."""
        adv = self._advisories_store.get(trace_id)
        calls = self._tool_calls_store.get(trace_id, [])

        return ExecutionTraceReconstruction(
            trace_id=trace_id,
            request_id=adv.advisory_id if adv else "UNKNOWN",
            asset_id=adv.asset_id if adv else "UNKNOWN",
            objective_id=adv.objective_id if adv else "UNKNOWN",
            advisory=adv.model_dump() if adv else None,
            tool_calls=calls
        )
