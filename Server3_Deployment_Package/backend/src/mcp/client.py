"""
MCPToolClient — the agent-side entry point into the governed MCP tool layer (Option A).

The LangGraph Supervisor calls tools exclusively through this client instead of touching
application services directly. The client:
  - enforces per-objective RBAC (via ToolSpec.allowed_objectives) BEFORE execution
  - audits every invocation (structured log line)
  - supports two transports:
      * in_process : call the shared ToolRegistry directly (fast, always available)
      * http       : call the gateway REST facade (/api/mcp/tools/{name}/invoke) over HTTP,
                     falling back to in_process if the HTTP call fails
  - never raises for control-flow: returns a structured ToolResult (status: success/denied/error)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.mcp.tool_registry import ToolRegistry, get_global_registry

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    tool: str
    status: str  # "success" | "denied" | "error"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transport: str = "in_process"
    latency_ms: float = 0.0
    objective_id: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "transport": self.transport,
            "latency_ms": round(self.latency_ms, 2),
            "objective_id": self.objective_id,
        }


class MCPToolClient:
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        mode: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.registry = registry or get_global_registry()
        self.mode = (mode or os.getenv("MCP_CLIENT_MODE", "in_process")).lower()
        self.base_url = (base_url or os.getenv("MCP_GATEWAY_URL", "http://127.0.0.1:8090")).rstrip("/")
        self._http_timeout = float(os.getenv("MCP_HTTP_TIMEOUT_SEC", "5.0"))

    # -- discovery -----------------------------------------------------------
    def list_tools(self, objective_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return [s.to_manifest() for s in self.registry.list(objective_id)]

    # -- invocation ----------------------------------------------------------
    def invoke(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        objective_id: Optional[str] = None,
    ) -> ToolResult:
        arguments = arguments or {}
        t0 = time.monotonic()

        spec = self.registry.get(tool_name)
        if spec is None:
            return ToolResult(tool=tool_name, status="error", objective_id=objective_id,
                              error=f"Unknown tool '{tool_name}'.",
                              latency_ms=(time.monotonic() - t0) * 1000)

        # RBAC is always enforced client-side, independent of transport.
        if not spec.is_allowed_for(objective_id):
            logger.warning("MCP RBAC: tool '%s' denied under objective '%s'", tool_name, objective_id)
            return ToolResult(tool=tool_name, status="denied", objective_id=objective_id,
                              error=f"Tool '{tool_name}' not permitted under objective '{objective_id}'.",
                              latency_ms=(time.monotonic() - t0) * 1000)

        if self.mode == "http":
            http_result = self._invoke_http(tool_name, arguments, objective_id, t0)
            if http_result is not None:
                return http_result
            logger.info("MCP client: HTTP transport unavailable for '%s' — falling back to in-process.", tool_name)

        return self._invoke_in_process(spec, tool_name, arguments, objective_id, t0)

    # -- transports ----------------------------------------------------------
    def _invoke_in_process(self, spec, tool_name, arguments, objective_id, t0) -> ToolResult:
        try:
            result = spec.handler(arguments)
            latency = (time.monotonic() - t0) * 1000
            logger.info("MCP tool OK  name=%s objective=%s transport=in_process latency=%.0fms",
                        tool_name, objective_id, latency)
            return ToolResult(tool=tool_name, status="success", result=result,
                              transport="in_process", latency_ms=latency, objective_id=objective_id)
        except Exception as exc:
            latency = (time.monotonic() - t0) * 1000
            logger.warning("MCP tool ERR name=%s objective=%s error=%s", tool_name, objective_id, exc)
            return ToolResult(tool=tool_name, status="error", error=str(exc),
                              transport="in_process", latency_ms=latency, objective_id=objective_id)

    def _invoke_http(self, tool_name, arguments, objective_id, t0) -> Optional[ToolResult]:
        try:
            import httpx
        except ImportError:
            return None
        url = f"{self.base_url}/api/mcp/tools/{tool_name}/invoke"
        try:
            resp = httpx.post(
                url,
                json={"arguments": arguments, "objective_id": objective_id},
                timeout=self._http_timeout,
            )
        except Exception as exc:
            logger.debug("MCP client HTTP error for '%s': %s", tool_name, exc)
            return None

        latency = (time.monotonic() - t0) * 1000
        if resp.status_code == 200:
            payload = resp.json()
            return ToolResult(tool=tool_name, status="success",
                              result=payload.get("result", payload),
                              transport="http", latency_ms=latency, objective_id=objective_id)
        if resp.status_code == 403:
            return ToolResult(tool=tool_name, status="denied", transport="http",
                              error=f"Tool '{tool_name}' denied under objective '{objective_id}'.",
                              latency_ms=latency, objective_id=objective_id)
        # Other status codes -> signal caller to fall back to in-process.
        logger.debug("MCP client HTTP non-200 (%s) for '%s'", resp.status_code, tool_name)
        return None
