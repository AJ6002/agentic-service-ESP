"""
Domain Capability & Liveness Probing.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0.
"""

from typing import Optional
import httpx

from app.contracts.enums import AdapterStatus
from .adapters.common import DEFAULT_TIMEOUT_SEC, get_gateway_base_url


async def check_domain_status(domain: str, client: Optional[httpx.AsyncClient] = None) -> AdapterStatus:
    """
    Checks liveness of a specific domain. Most domains live on Server 184
    (:8090); the Knowledge Base is a separate microservice on its own
    host/port (:8085, per kb.get_kb_base_url()) — it gets its own base URL,
    never the :8090 one.
    Returns AVAILABLE, DEGRADED, or ABSENT.
    """
    path_map = {
        "live": "/live/health",
        "historian": "/historian/health",
        "events": "/events/health",
        "ml": "/ml/health",
        "kpi": "/kpi/fleet",
        "cards": "/cards/catalog",
        "kb": "/health",
    }

    path = path_map.get(domain)
    if not path:
        return "ABSENT"

    if domain == "kb":
        from .adapters.kb import get_kb_base_url
        base = get_kb_base_url()
    else:
        base = get_gateway_base_url()

    url = f"{base}{path}"
    try:
        if client:
            resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        else:
            async with httpx.AsyncClient() as c:
                resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)

        if resp.status_code == 200:
            data = resp.json()
            # Spec specific degraded checks
            if domain == "live" and not data.get("mqtt_connected", True):
                return "DEGRADED"
            if domain == "historian" and data.get("row_count", 1) == 0:
                return "DEGRADED"
            if data.get("status") == "degraded":
                return "DEGRADED"
            return "AVAILABLE"
        elif resp.status_code in (503, 502, 504):
            return "DEGRADED"
        elif resp.status_code == 404:
            return "ABSENT"
        else:
            return "DEGRADED"
    except Exception:
        return "DEGRADED"


async def probe_all_capabilities(client: Optional[httpx.AsyncClient] = None) -> dict[str, AdapterStatus]:
    """
    Probes all 7 domains and returns status dictionary. Note: the `client`
    param, if supplied, is a client for Server 184 (:8090) — it is NOT
    reused for the "kb" domain, since check_domain_status() opens its own
    client against the KB service's own base URL for that one entry.
    """
    domains = ["live", "historian", "events", "ml", "kpi", "cards", "kb"]
    results = {}
    for d in domains:
        results[d] = await check_domain_status(d, client=client if d != "kb" else None)
    return results
