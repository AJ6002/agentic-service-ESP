"""
Episodic per-well memory store for cross-session durability (Plan.md Phase C1).
Stores rolling operational summaries per asset in Redis with in-memory fallback.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)

# 30-day default TTL for episodic well memories
_WELL_MEMORY_TTL_SECONDS = 30 * 86400
_MAX_ROLLING_EVENTS = 5


class WellEpisodicMemoryStore:
    """
    Episodic memory store keyed by well/asset ID (e.g. FSWS-001-A), independent of sessions.
    Survives session close and browser tab changes.
    """

    def __init__(self, connection_mgr: Optional[RedisConnectionManager] = None):
        self.connection_mgr = connection_mgr or RedisConnectionManager()
        self._fallback_store: Dict[str, Dict[str, Any]] = {}

    def _get_key(self, asset_id: str) -> str:
        return f"esp:well_memory:{asset_id.strip().upper()}"

    def get_memory(self, asset_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Retrieve the episodic history dict for an asset."""
        if not asset_id or asset_id == "UNKNOWN":
            return None

        clean_id = asset_id.strip().upper()
        key = self._get_key(clean_id)

        try:
            client = self.connection_mgr.get_client()
            raw = client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as ex:
            logger.debug("WellEpisodicMemoryStore: Redis read failed for %s (%s)", clean_id, ex)

        return self._fallback_store.get(clean_id)

    def record_advisory(self, asset_id: Optional[str], advisory: Any) -> None:
        """
        Update the well's episodic memory with findings from a completed advisory.
        Only records real operational advisories (ignores pure clarifications).
        """
        if not asset_id or asset_id == "UNKNOWN" or not advisory:
            return

        obj_id = getattr(advisory, "objective_id", "")
        if obj_id == "CLARIFICATION":
            return

        clean_id = asset_id.strip().upper()
        key = self._get_key(clean_id)
        now_iso = datetime.utcnow().isoformat()

        diagnosis = str(getattr(advisory, "diagnosis", "") or getattr(advisory, "assessment", ""))[:300]
        recommendation = str(getattr(advisory, "recommendation", ""))[:300]

        existing = self.get_memory(clean_id) or {
            "well_id": clean_id,
            "total_assessments": 0,
            "recent_events": [],
        }

        existing["last_updated"] = now_iso
        existing["total_assessments"] = existing.get("total_assessments", 0) + 1
        existing["last_objective"] = obj_id
        existing["last_diagnosis"] = diagnosis
        existing["last_recommendation"] = recommendation

        recent = existing.get("recent_events", [])
        recent.append({
            "timestamp": now_iso,
            "objective_id": obj_id,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
        })
        existing["recent_events"] = recent[-_MAX_ROLLING_EVENTS:]

        # Save to in-memory fallback
        self._fallback_store[clean_id] = existing

        # Persist to Redis
        try:
            client = self.connection_mgr.get_client()
            client.set(key, json.dumps(existing), ex=_WELL_MEMORY_TTL_SECONDS)
            logger.info("WellEpisodicMemoryStore: Updated episodic memory for %s", clean_id)
        except Exception as ex:
            logger.warning("WellEpisodicMemoryStore: Redis write failed for %s (%s)", clean_id, ex)

    def format_prompt_context(self, asset_id: Optional[str]) -> Optional[Dict[str, str]]:
        """Format the well's episodic memory as a concise dict for CompactContextBuilder."""
        mem = self.get_memory(asset_id)
        if not mem:
            return None

        return {
            "last_assessed": mem.get("last_updated", "Unknown"),
            "total_assessments": str(mem.get("total_assessments", 1)),
            "prior_objective": mem.get("last_objective", "N/A"),
            "prior_diagnosis": mem.get("last_diagnosis", "Nominal"),
            "prior_recommendation": mem.get("last_recommendation", "Continue monitoring"),
        }

    def clear(self, asset_id: str) -> None:
        """Clear memory for a given well (primarily for testing)."""
        clean_id = asset_id.strip().upper()
        self._fallback_store.pop(clean_id, None)
        try:
            client = self.connection_mgr.get_client()
            client.delete(self._get_key(clean_id))
        except Exception:
            pass
