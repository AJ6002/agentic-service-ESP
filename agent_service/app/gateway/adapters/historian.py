"""
Historian Domain Adapter.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 Domain 1.
"""

from typing import Any, Optional
import httpx

from .common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response, build_temporal_meta


async def fetch_historian_window(
    well_id: str,
    start: str,
    end: str,
    signals: Optional[str] = None,
    limit: int = 10000,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    base = get_gateway_base_url()
    params = {"well_id": well_id, "start": start, "end": end, "limit": limit}
    if signals:
        params["signals"] = signals
    url = f"{base}/historian/window"
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        res = handle_adapter_response(resp, "historian", "/historian/window")
    else:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
            res = handle_adapter_response(resp, "historian", "/historian/window")
    if isinstance(res, dict):
        res["temporal_meta"] = build_temporal_meta(
            query_start=start,
            query_end=end,
            records=res.get("rows", []),
            columns=res.get("columns", []),
            ts_field="timestamp"
        )
    return res


async def fetch_historian_aggregates(
    well_id: str,
    start: str,
    end: str,
    signals: Optional[str] = None,
    bucket: str = "1h",
    agg: str = "avg",
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    base = get_gateway_base_url()
    params = {
        "well_id": well_id,
        "start": start,
        "end": end,
        "bucket": bucket,
        "agg": agg,
    }
    if signals:
        params["signals"] = signals
    url = f"{base}/historian/aggregates"
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        res = handle_adapter_response(resp, "historian", "/historian/aggregates")
    else:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
            res = handle_adapter_response(resp, "historian", "/historian/aggregates")
    if isinstance(res, dict):
        res["temporal_meta"] = build_temporal_meta(
            query_start=start,
            query_end=end,
            records=res.get("rows", []),
            columns=res.get("columns", []),
            ts_field="bucket"
        )
    return res


async def fetch_historian_latest(
    well_id: str,
    signals: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    base = get_gateway_base_url()
    params = {"well_id": well_id}
    if signals:
        params["signals"] = signals
    url = f"{base}/historian/latest"
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/latest")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/latest")


async def fetch_historian_coverage(
    well_id: str,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/historian/coverage"
    params = {"well_id": well_id}
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/coverage")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/coverage")


async def check_historian_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/historian/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "historian", "/historian/health")
