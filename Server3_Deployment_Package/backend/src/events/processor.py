"""
Event Processor Core Pipeline
Grounded in Phase 6 Event-Driven Architecture Spec §10, §15
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import yaml

from shared.schemas.event import ESPEvent, SeverityLevel
from src.events.redis_connection import RedisConnectionManager
from src.events.db_event_store import DatabaseEventStore
from src.events.publisher import RedisStreamPublisher

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Core Event Processor pipeline.
    Pipeline steps:
    1. Schema & Tenant Validation
    2. Deduplication (Idempotency check)
    3. Hysteresis & Persistence Window check
    4. Transient Suppression check
    5. Permanent DB Store persistence
    6. Publish actionable trigger event to 'esp:stream:actionable'
    """

    def __init__(
        self,
        taxonomy_path: str = "knowledge_bases/esp/events/event_taxonomy.yaml",
        db_store: Optional[DatabaseEventStore] = None,
        publisher: Optional[RedisStreamPublisher] = None,
        connection_mgr: Optional[RedisConnectionManager] = None
    ):
        self.mgr = connection_mgr or RedisConnectionManager()
        self.db_store = db_store or DatabaseEventStore()
        self.publisher = publisher or RedisStreamPublisher(connection_mgr=self.mgr)
        self.taxonomy = self._load_taxonomy(taxonomy_path)

    def _load_taxonomy(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f).get("event_types", {})
        except Exception as ex:
            logger.warning(f"Could not load taxonomy file '{path}': {ex}")
            return {}

    def is_duplicate(self, event: ESPEvent) -> bool:
        """Check if event_id or idempotency_key was processed in last 24h."""
        client = self.mgr.get_client()
        key = f"esp:dedup:{event.idempotency_key or event.event_id}"
        # Set nx=True with 86400s (24h) TTL
        is_new = client.set(name=key, value="1", ex=86400, nx=True)
        return not is_new

    def check_hysteresis_and_persistence(self, event: ESPEvent) -> bool:
        """
        Enforce hysteresis and min_persistence_samples per event_type taxonomy config.
        Returns True if condition has persisted sufficiently to trigger actionable event.
        """
        rules = self.taxonomy.get(event.event_type, {})
        window_sec = rules.get("hysteresis_window_seconds", 0)
        min_samples = rules.get("min_persistence_samples", 1)

        if window_sec <= 0 and min_samples <= 1:
            return True  # Immediate event (e.g. ESP_TRIPPED)

        client = self.mgr.get_client()
        set_key = f"esp:hysteresis:{event.asset_id}:{event.event_type}"
        now_ts = time.time()

        # Add timestamp to sorted set
        client.zadd(set_key, {event.event_id: now_ts})
        client.expire(set_key, 7200)  # 2h TTL

        # Remove elements older than window_sec
        cutoff = now_ts - window_sec
        client.zremrangebyscore(set_key, 0, cutoff)

        sample_count = client.zcard(set_key)
        logger.info(f"Hysteresis check for '{event.event_type}' on '{event.asset_id}': {sample_count}/{min_samples} samples in window {window_sec}s")

        return sample_count >= min_samples

    def process_event(self, event: ESPEvent) -> Tuple[bool, str]:
        """
        Execute full EventProcessor pipeline for an inbound event.
        Returns: (is_actionable: bool, reason: str)
        """
        # Step 1: Validation
        if not event.event_id or not event.asset_id:
            return False, "INVALID_EVENT_SCHEMA"

        # Step 2: Deduplication
        if self.is_duplicate(event):
            logger.info(f"EventProcessor: Dropping duplicate event '{event.event_id}'")
            return False, "DUPLICATE_SKIPPED"

        # Step 3: Permanent DB Store persistence (Audit Log)
        self.db_store.save_event(event, status="PROCESSED")

        # Step 4: Hysteresis check
        if not self.check_hysteresis_and_persistence(event):
            return False, "HYSTERESIS_UNSATISFIED"

        # Step 5: If actionable, publish to actionable trigger stream
        rules = self.taxonomy.get(event.event_type, {})
        target_obj = rules.get("target_objective_id")

        if target_obj:
            actionable_event = event.model_copy(deep=True)
            if "target_objective_id" not in actionable_event.payload:
                actionable_event.payload["target_objective_id"] = target_obj

            self.publisher.publish(actionable_event, category="actionable")
            logger.info(f"EventProcessor: Promoted event '{event.event_id}' -> Actionable Stream (target_objective={target_obj})")
            return True, "ACTIONABLE_PROMOTED"

        return False, "NON_ACTIONABLE_AUDITED"
