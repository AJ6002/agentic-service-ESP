"""
Live Telemetry & MQTT Domain Adapter.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 Domain 2.
"""

from typing import Any, Optional
import httpx

from .common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response


async def fetch_live_telemetry(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/live/telemetry/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/telemetry/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/telemetry/{well_id}")


async def fetch_live_asset(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/live/asset/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/asset/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/asset/{well_id}")


async def fetch_live_vfm(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/live/vfm/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/vfm/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", f"/live/vfm/{well_id}")


async def fetch_live_wells(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/live/wells"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", "/live/wells")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", "/live/wells")


async def check_live_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/live/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", "/live/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "live", "/live/health")
