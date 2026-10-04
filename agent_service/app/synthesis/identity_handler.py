from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import yaml

from app.gateway.capability import probe_all_capabilities
from app.routing.objective_registry import list_objectives
from app.llm.client import LLMUnavailableError
from app.llm.calls import identity_answer

_SELF_MODEL_CACHE: Optional[dict[str, Any]] = None
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "agent_identity.yaml"


@dataclass
class IdentityAnswer:
    text: str
    llm_available: bool


def load_self_model(force_reload: bool = False) -> dict[str, Any]:
    """Loads and caches agent_identity.yaml in memory."""
    global _SELF_MODEL_CACHE
    if _SELF_MODEL_CACHE is not None and not force_reload:
        return _SELF_MODEL_CACHE

    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _SELF_MODEL_CACHE = yaml.safe_load(f) or {}
    else:
        _SELF_MODEL_CACHE = {
            "identity": {
                "name": "ESP APM Operations Copilot",
                "role": "Advisory-only operations copilot and diagnostic assistant",
            },
            "boundaries": {
                "read_only": True,
                "safety_mandate": "Strictly advisory. Cannot actuate physical hardware or modify setpoints.",
            },
        }
    return _SELF_MODEL_CACHE


async def format_live_capabilities() -> str:
    """Introspects current runtime domain adapters and active objectives."""
    try:
        domain_status = await probe_all_capabilities()
    except Exception:
        domain_status = {"live": "UNKNOWN", "kb": "UNKNOWN"}

    try:
        objectives = list_objectives()
    except Exception:
        objectives = [
            "OP01_CURRENT_STATUS",
            "OP02_PRODUCTION_DECLINE_RCA",
            "OP03_FAULT_DIAGNOSIS",
            "OP04_HEALTH_ASSESSMENT",
            "OP05_EARLY_WARNING",
            "OP06_KNOWLEDGE_LOOKUP",
            "OP07_GENERAL_INQUIRY",
            "OP14_OPERATIONAL_HISTORY",
        ]

    lines = ["Active Objectives:"]
    for obj in sorted(objectives):
        lines.append(f"  - {obj}")

    lines.append("\nDomain Adapter Liveness:")
    for dom, status in sorted(domain_status.items()):
        lines.append(f"  - {dom}: {status}")

    return "\n".join(lines)


async def handle_identity_query(query: str) -> IdentityAnswer:
    """
    Synthesizes self-knowledge answers using the static self-model and live capabilities.
    Bypasses the workflow pipeline entirely.
    """
    model_data = load_self_model()
    static_model_str = yaml.dump(model_data, sort_keys=False)
    live_caps_str = await format_live_capabilities()

    try:
        content = await identity_answer(
            query=query,
            static_self_model=static_model_str,
            live_capabilities=live_caps_str,
        )
        if content and content.strip():
            return IdentityAnswer(text=content.strip(), llm_available=True)
    except LLMUnavailableError:
        pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("identity_answer failed: %s", e)

    # Offline / LLM unavailable fallback: deterministic answer from static self-model
    identity_info = model_data.get("identity", {})
    boundaries = model_data.get("boundaries", {})
    scope = model_data.get("scope", {})

    fallback_text = (
        f"I am the {identity_info.get('name', 'ESP APM Operations Copilot')}, "
        f"{identity_info.get('role', 'an advisory-only diagnostic assistant')}. "
        f"I monitor the {scope.get('operational_fleet', {}).get('field', 'Farha South')} ESP fleet, "
        f"diagnosing fault trips, assessing health indices, detecting early warning drift, and referencing approved engineering standards. "
        f"Boundary: {boundaries.get('safety_mandate', 'Strictly advisory and read-only; I do not execute equipment writes or setpoint adjustments.')}"
    )
    return IdentityAnswer(text=fallback_text, llm_available=False)
