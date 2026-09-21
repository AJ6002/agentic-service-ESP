"""
ML Diagnostics Domain Adapter.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 Domain 4.
"""

from typing import Any, Optional
import httpx

from .common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response, build_temporal_meta


async def fetch_ml_fault(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/ml/fault/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/fault/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/fault/{well_id}")


async def fetch_ml_health(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/ml/health/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/health/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/health/{well_id}")


async def fetch_ml_anomaly(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/ml/anomaly/{well_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/anomaly/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/anomaly/{well_id}")


async def fetch_ml_explain(well_id: str, output: str = "fault", client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/ml/explain/{well_id}"
    params = {"output": output}
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/explain/{well_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", f"/ml/explain/{well_id}")


async def check_ml_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/ml/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", "/ml/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "ml", "/ml/health")


async def query_mlresults(
    well_id: str,
    limit: Optional[int] = None,
    anomalous_only: Optional[bool] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    url = f"{get_gateway_base_url()}/api/mlresults/query"
    params: dict[str, Any] = {"asset_id": well_id}
    if limit is not None:
        params["limit"] = int(limit)
    if anomalous_only is not None:
        params["anomalous_only"] = str(bool(anomalous_only)).lower()
    if client:
        resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
        res = handle_adapter_response(resp, "ml", "/api/mlresults/query")
    else:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url, params=params, timeout=DEFAULT_TIMEOUT_SEC)
            res = handle_adapter_response(resp, "ml", "/api/mlresults/query")
    if isinstance(res, dict):
        if "well_id" not in res:
            res["well_id"] = res.get("asset_id") or well_id
        res["temporal_meta"] = build_temporal_meta(
            query_start=None,
            query_end=None,
            records=res.get("records") or res.get("results") or [],
            ts_field="timestamp"
        )
    return res
