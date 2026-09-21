"""
Knowledge Base Domain Adapter (esp_kb_service).
Reference: ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md v2.1.0.

Separate microservice from Server 184's other domains — different host/port
(:8085, not :8090), and its two primary endpoints are POST with a JSON body,
not GET with query params. Everything else follows the same adapter
contract as historian/live/events/ml/kpi/cards: one call per function,
errors raised as AdapterError via handle_adapter_response, zero fabricated
data on failure.
"""

import os
from typing import Any, Optional

import httpx

from .common import DEFAULT_TIMEOUT_SEC, handle_adapter_response


def get_kb_base_url() -> str:
    return os.getenv("KB_SERVICE_BASE_URL", "http://192.168.1.184:8085").rstrip("/")


async def check_kb_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_kb_base_url()}/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/health")


async def search_kb(
    query: str,
    top_k: int = 5,
    min_authority: Optional[str] = None,
    category: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """
    POST /api/kb/search — primary semantic/hybrid search. Returns hits with
    the strict Evidence Pack contract (doc_id, section, revision, authority,
    applicability, page, snippet, score) per spec §3.
    """
    url = f"{get_kb_base_url()}/api/kb/search"
    body: dict[str, Any] = {"query": query, "top_k": top_k}
    if min_authority:
        body["min_authority"] = min_authority
    if category:
        body["category"] = category

    if client:
        resp = await client.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/search")
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/search")


async def trace_kb_graph(
    symptom_ids: list[str],
    observed_parameters: Optional[dict[str, float]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """
    POST /api/kb/graph/trace — symptom-to-root-cause causal chain + SOP.
    Not used by search_knowledge; kept for a later, dedicated diagnostic tool.
    """
    url = f"{get_kb_base_url()}/api/kb/graph/trace"
    body: dict[str, Any] = {"symptom_ids": symptom_ids}
    if observed_parameters:
        body["observed_parameters"] = observed_parameters

    if client:
        resp = await client.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/graph/trace")
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/graph/trace")


async def get_kb_fault(fault_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """GET /api/kb/faults/{fault_id} — single deterministic fault profile."""
    url = f"{get_kb_base_url()}/api/kb/faults/{fault_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/faults/{fault_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/faults/{fault_id}")


async def get_kb_standard(standard_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """GET /api/kb/standards/{standard_id} — certified standard clause lookup."""
    url = f"{get_kb_base_url()}/api/kb/standards/{standard_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/standards/{standard_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/standards/{standard_id}")
