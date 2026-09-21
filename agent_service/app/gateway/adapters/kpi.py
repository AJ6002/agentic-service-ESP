"""
KPI Domain Adapter.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 Domain 5.
"""

from typing import Any, Optional
import httpx

from .common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response


async def fetch_kpi(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/kpi/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kpi", f"/kpi/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kpi", f"/kpi/{well_id}")


async def fetch_fleet_kpi(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/kpi/fleet"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kpi", "/kpi/fleet")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kpi", "/kpi/fleet")
