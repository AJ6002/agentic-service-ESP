"""
ESP APM MCP Service Layer
=========================

A governed tool layer for the agentic platform. Provides a single source of truth
(`ToolRegistry`) binding stable tool names + JSON schemas + governance metadata to
callables that invoke the real application services.

Consumed by:
  - MCPToolClient  (agent-side, Option A: the LangGraph Supervisor calls tools through
    this governed client with per-objective RBAC + audit)
  - REST facade + FastMCP server (Option B: external HTTP/MCP clients)
"""

from src.mcp.tool_registry import (
    ToolSpec,
    ToolRegistry,
    get_global_registry,
    ALL_OBJECTIVES,
)
from src.mcp.client import MCPToolClient, ToolResult

__all__ = [
    "ToolSpec",
    "ToolRegistry",
    "get_global_registry",
    "ALL_OBJECTIVES",
    "MCPToolClient",
    "ToolResult",
]
