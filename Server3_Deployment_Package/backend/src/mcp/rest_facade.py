"""
MCP REST Facade (Option B — HTTP transport).

Exposes the governed tool registry over plain HTTP so any client (including the agent
in `http` mode and external tools) can discover and invoke tools:

  GET  /api/mcp/tools                      -> list tool manifests (optionally scoped by objective)
  GET  /api/mcp/tools/{tool_name}          -> single tool manifest
  POST /api/mcp/tools/{tool_name}/invoke   -> execute a tool (RBAC-enforced)

The facade uses an in-process MCPToolClient so it does not recurse back over HTTP.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.mcp.client import MCPToolClient
from src.mcp.tool_registry import get_global_registry

router = APIRouter(prefix="/api/mcp", tags=["mcp"])

# Server-side client MUST be in-process to avoid HTTP self-recursion.
_server_client = MCPToolClient(mode="in_process")


class InvokeRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)
    objective_id: Optional[str] = Field(default=None, description="Active objective for RBAC scoping")


@router.get("/health")
def mcp_health():
    reg = get_global_registry()
    return {"status": "ok", "service": "mcp_tool_layer", "tool_count": len(reg.names())}


@router.get("/tools")
def list_tools(objective_id: Optional[str] = None):
    tools = _server_client.list_tools(objective_id)
    return {"count": len(tools), "objective_id": objective_id, "tools": tools}


@router.get("/tools/{tool_name}")
def get_tool(tool_name: str):
    spec = get_global_registry().get(tool_name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool '{tool_name}'.")
    return spec.to_manifest()


@router.post("/tools/{tool_name}/invoke")
def invoke_tool(tool_name: str, req: InvokeRequest):
    result = _server_client.invoke(tool_name, req.arguments, req.objective_id)
    if result.status == "denied":
        raise HTTPException(status_code=403, detail=result.error)
    if result.status == "error":
        # Unknown tool -> 404, execution failure -> 400.
        code = 404 if (result.error or "").startswith("Unknown tool") else 400
        raise HTTPException(status_code=code, detail=result.error)
    return result.to_dict()
