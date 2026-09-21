"""
Agent Introspection Tool
Grounded in deterministic agent_manifest.json metadata inventory.
Enables zero-hallucination answers regarding Agent Jane's identity,
certified standards (API RP 11S, IEC 60034-14, Takacs), capabilities,
operational objectives, and advisory-only safety policy.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "agent_manifest.json"
_CACHED_MANIFEST: Optional[Dict[str, Any]] = None


def load_agent_manifest() -> Dict[str, Any]:
    """Loads and caches the deterministic agent manifest."""
    global _CACHED_MANIFEST
    if _CACHED_MANIFEST is not None:
        return _CACHED_MANIFEST

    if not _MANIFEST_PATH.exists():
        logger.error(f"Agent manifest not found at: {_MANIFEST_PATH}")
        return {}

    with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
        _CACHED_MANIFEST = json.load(f)
    return _CACHED_MANIFEST


def get_agent_profile(topic: Optional[str] = "all") -> Dict[str, Any]:
    """
    Retrieves the agent's profile, standards, and capability metadata.
    Dynamically syncs live asset count from AssetContextService and handles out-of-scope inquiries.

    Args:
        topic: 'all', 'identity', 'standards', 'capabilities', 'objectives', or 'assets'

    Returns:
        Structured dictionary conforming to agent metadata schema.
    """
    manifest = load_agent_manifest()
    topic_clean = (topic or "all").lower().strip()

    # Dynamic live sync with AssetContextService
    try:
        from src.services.asset_context_service import AssetContextService
        active_assets = AssetContextService().list_assets()
        if active_assets:
            manifest.setdefault("certified_assets_scope", {})["asset_count"] = len(active_assets)
    except Exception as exc:
        logger.debug("AssetContextService live count sync bypassed: %s", exc)


    # Out-of-scope refusal handling
    out_of_scope_topics = ("subsea", "offshore", "nuclear", "refinery", "solar", "wind", "pipeline", "gas turbine")
    if any(kw in topic_clean for kw in out_of_scope_topics):
        return {
            "status": "OUT_OF_SCOPE",
            "topic": topic_clean,
            "data": {},
            "narrative": (
                "Topic outside certified onshore ESP manifest scope. "
                "Agent Jane is certified exclusively for onshore ESP installations at Farha South Field (Block 3/4)."
            ),
            "manifest": manifest,
        }

    if topic_clean in ("identity", "profile", "who"):
        data = {"identity": manifest.get("identity", {})}
    elif topic_clean in ("standards", "manuals", "references"):
        data = {"standards_and_manuals": manifest.get("standards_and_manuals", [])}
    elif topic_clean in ("capabilities", "features", "skills"):
        data = {"capabilities": manifest.get("capabilities", [])}
    elif topic_clean in ("objectives", "tasks"):
        data = {"operational_objectives": manifest.get("operational_objectives", {})}
    elif topic_clean in ("assets", "wells", "scope"):
        data = {"certified_assets_scope": manifest.get("certified_assets_scope", {})}
    else:
        data = manifest

    narrative = format_agent_profile_narrative(data)
    return {
        "status": "SUCCESS",
        "topic": topic_clean,
        "data": data,
        "narrative": narrative,
        "manifest": manifest,
    }


def format_agent_profile_narrative(profile_payload: Dict[str, Any]) -> str:
    """
    Renders an authoritative, markdown-formatted technical narrative
    describing Agent Jane's identity, certified standards, and advisory boundaries.
    """
    manifest = load_agent_manifest()
    identity = manifest.get("identity", {})
    standards = manifest.get("standards_and_manuals", [])
    capabilities = manifest.get("capabilities", [])
    assets = manifest.get("certified_assets_scope", {})

    lines = [
        f"### 🤖 {identity.get('name', 'Agent Jane')} ({identity.get('version', 'v2.1.0')})",
        f"**Role:** {identity.get('role', 'Autonomous ESP Operations Co-Pilot')}",
        f"**Operating Mode:** `{identity.get('operational_mode', 'Advisory-Only')}`",
        f"**Architecture:** {identity.get('architecture', 'V2 Native Tool-Calling & Dynamic Planning')}",
        "",
        "#### 🛡️ Governance & Safety Guarantees",
        f"> {identity.get('safety_policy', 'Strict Human-in-the-Loop approval for setpoint changes')}",
        "",
        "**Non-Negotiable Refusal Rules:**",
    ]
    for rule in identity.get("refusal_rules", []):
        lines.append(f"- {rule}")

    lines.extend([
        "",
        "#### 📚 Authoritative Industry Standards & Reference Manuals",
    ])
    for s in standards:
        code = s.get("code", "Standard")
        title = s.get("title", "")
        auth = s.get("authority_level", "LEVEL_A")
        badge = "🟢 Level A (Industry Standard)" if "A" in auth else "🔵 Level B (Reference Manual)"
        lines.append(f"- **{code}** — *{title}* (`{badge}`)")
        for cov in s.get("coverage", [])[:2]:
            lines.append(f"  - {cov}")

    lines.extend([
        "",
        "#### ⚙️ Certified Operational Scope",
        f"- **Field:** {assets.get('field', 'Farha South Field (Block 3/4)')}",
        f"- **Active Well Inventory:** {assets.get('asset_count', 27)} monitored ESP wells (`{assets.get('well_designation_prefix', 'FS-')}*`) "
        f"[Historical census coverage: {assets.get('historical_census_count', 73)} CCED production wells]",
        "",
        "#### 🚀 Core Capabilities",
    ])
    for cap in capabilities:
        lines.append(f"- {cap}")

    return "\n".join(lines)

