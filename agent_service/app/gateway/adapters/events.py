"""
Events Domain Adapter.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 Domain 3.
"""

from typing import Any, Optional
import httpx

from .common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response, build_temporal_meta


async def fetch_events_timeline(
    well_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    base = get_gateway_base_url()
    if not start or not end:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        if not end:
            end = now.isoformat().replace("+00:00", "Z")
        if not start:
            start = (now - timedelta(hours=24)).isoformat().replace("+00:00", "Z")

    params = {"well_id": well_id, "start": start, "end": end}
    url = f"{base}/events/timeline"
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        res = handle_adapter_response(resp, "events", "/events/timeline")
    else:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
            res = handle_adapter_response(resp, "events", "/events/timeline")
    if isinstance(res, dict):
        res["temporal_meta"] = build_temporal_meta(
            query_start=start,
            query_end=end,
            records=res.get("events", []),
            ts_field="timestamp"
        )
    return res


async def fetch_events_trips(
    well_id: str,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/events/trips"
    params = {"well_id": well_id}
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "events", "/events/trips")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "events", "/events/trips")


async def check_events_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/events/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "events", "/events/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "events", "/events/health")
