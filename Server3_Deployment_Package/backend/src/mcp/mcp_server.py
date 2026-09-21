"""
FastMCP server builder (Option B — native MCP protocol over HTTP).

Exposes the governed tool registry as a real MCP server so MCP-native clients
(Claude Desktop, Kiro, etc.) can consume the ESP toolset. The MCP `mcp` package is
optional: if it is not installed, `build_fastmcp_app()` returns None and the gateway
simply skips mounting it (the REST facade still provides full HTTP access).

Because tool schemas are dynamic, the registry is exposed via two generic MCP tools:
  - list_esp_tools()                          -> discover available tools + schemas
  - invoke_esp_tool(tool_name, arguments, objective_id)  -> execute a governed tool

This keeps schema handling robust without fragile per-tool signature generation.

NOTE: Do NOT add `from __future__ import annotations` to this module — FastMCP inspects
real annotation objects (issubclass checks), which breaks if annotations are stringized.
"""

import logging
from typing import Any, Dict, Optional

from src.mcp.client import MCPToolClient
from src.mcp.tool_registry import get_global_registry

logger = logging.getLogger(__name__)


def build_fastmcp_server():
    """Return a configured FastMCP server, or None if the `mcp` package is unavailable."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        logger.info("MCP server: `mcp` package not installed — native MCP endpoint disabled "
                    "(REST facade at /api/mcp remains available).")
        return None

    mcp = FastMCP("ESP APM Agentic Tool Layer")
    client = MCPToolClient(mode="in_process")

    # NOTE: FastMCP infers tool schemas from parameter annotations and mishandles
    # typing.Optional/Union, so these signatures use plain classes with sentinel defaults.
    @mcp.tool()
    def list_esp_tools(objective_id: str = "") -> dict:
        """List available ESP tools and their JSON argument schemas, optionally scoped by objective."""
        tools = client.list_tools(objective_id or None)
        return {"count": len(tools), "tools": tools}

    @mcp.tool()
    def invoke_esp_tool(tool_name: str, arguments: dict = None, objective_id: str = "") -> dict:
        """Invoke a governed ESP tool by name with an argument dict (RBAC-enforced)."""
        return client.invoke(tool_name, arguments or {}, objective_id or None).to_dict()

    return mcp


def build_streamable_http_app():
    """Return an ASGI app for the MCP server over streamable-HTTP, or None if unavailable."""
    server = build_fastmcp_server()
    if server is None:
        return None
    try:
        return server.streamable_http_app()
    except Exception as exc:  # pragma: no cover - depends on mcp version
        logger.warning("MCP server: could not build streamable-http app: %s", exc)
        return None


if __name__ == "__main__":
    # Standalone stdio launch for local desktop MCP clients.
    srv = build_fastmcp_server()
    if srv is None:
        raise SystemExit("`mcp` package not installed. Run: pip install mcp")
    srv.run()
