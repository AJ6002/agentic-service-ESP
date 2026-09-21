"""
Historical Event Replay Engine
Grounded in Phase 6 Event-Driven Architecture Spec §16, §29
"""

import logging
from typing import List, Dict, Any, Optional

from shared.schemas.event import ESPEvent
from src.events.db_event_store import DatabaseEventStore
from src.events.processor import EventProcessor

logger = logging.getLogger(__name__)


class EventReplayEngine:
    """
    Replay engine that re-processes events from DatabaseEventStore or stream offsets.
    """

    def __init__(
        self,
        db_store: Optional[DatabaseEventStore] = None,
        processor: Optional[EventProcessor] = None
    ):
        self.db_store = db_store or DatabaseEventStore()
        self.processor = processor or EventProcessor(db_store=self.db_store)

    def replay_asset_history(self, asset_id: str, limit: int = 50, dry_run: bool = True) -> Dict[str, Any]:
        """
        Replay event history for an asset.
        """
        events = self.db_store.list_events_by_asset(asset_id=asset_id, limit=limit)
        # Replay in chronological order (oldest to newest)
        events.reverse()

        replayed_count = 0
        actionable_count = 0

        for evt in events:
            replayed_count += 1
            if not dry_run:
                # Override idempotency key to allow re-processing in dry-run/replay test
                evt.idempotency_key = f"REPLAY-{evt.event_id}"
                is_act, reason = self.processor.process_event(evt)
                if is_act:
                    actionable_count += 1

        logger.info(f"EventReplayEngine: Replayed {replayed_count} events for asset '{asset_id}' (dry_run={dry_run})")
        return {
            "asset_id": asset_id,
            "replayed_count": replayed_count,
            "actionable_count": actionable_count,
            "dry_run": dry_run
        }
