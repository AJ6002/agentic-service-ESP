"""
Domain Capability & Liveness Probing backed by Centralized PostgreSQL (esp_apm_db).
Probes PostgreSQL database connectivity across all domain tables.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0.
"""

from typing import Optional
import httpx

from app.contracts.enums import AdapterStatus
from .adapters import cards, events, historian, kb, kpi, live, ml


async def check_domain_status(domain: str, client: Optional[httpx.AsyncClient] = None) -> AdapterStatus:
    """
    Checks liveness of a specific domain directly against PostgreSQL esp_apm_db.
    Returns AVAILABLE, DEGRADED, or ABSENT.
    """
    try:
        if domain == "kb":
            health = await kb.check_kb_health(client=client)
            if health.get("status") == "HEALTHY" and health.get("chunks", 0) > 0:
                return "AVAILABLE"
            return "DEGRADED"

        elif domain == "live":
            health = await live.check_live_health(client=client)
            return "AVAILABLE" if health.get("status") == "HEALTHY" else "DEGRADED"

        elif domain == "historian":
            health = await historian.check_historian_health(client=client)
            return "AVAILABLE" if health.get("status") == "HEALTHY" else "DEGRADED"

        elif domain == "events":
            health = await events.check_events_health(client=client)
            return "AVAILABLE" if health.get("status") == "HEALTHY" else "DEGRADED"

        elif domain == "ml":
            health = await ml.check_ml_health(client=client)
            return "AVAILABLE" if health.get("status") == "HEALTHY" else "DEGRADED"

        elif domain == "kpi":
            health = await kpi.fetch_fleet_kpi(client=client)
            return "AVAILABLE" if health.get("source") == "POSTGRESQL" else "DEGRADED"

        elif domain == "cards":
            health = await cards.fetch_cards_catalog(client=client)
            return "AVAILABLE" if health.get("source") == "POSTGRESQL" else "DEGRADED"

        else:
            return "ABSENT"

    except Exception:
        return "DEGRADED"


async def probe_all_capabilities(client: Optional[httpx.AsyncClient] = None) -> dict[str, AdapterStatus]:
    """Probes all 7 domains against PostgreSQL and returns status dictionary."""
    domains = ["live", "historian", "events", "ml", "kpi", "cards", "kb"]
    results = {}
    for d in domains:
        results[d] = await check_domain_status(d, client=client)
    return results
