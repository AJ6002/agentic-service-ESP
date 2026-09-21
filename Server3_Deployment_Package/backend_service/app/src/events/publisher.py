"""
Event Publisher Interface & Redis Stream Implementation
Grounded in Phase 6 Event-Driven Architecture Spec §6, §8, §21
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from shared.schemas.event import ESPEvent
from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)

STREAM_CATEGORY_MAP = {
    "operational": "esp:stream:telemetry",
    "model": "esp:stream:model",
    "asset_config": "esp:stream:asset",
    "agent_feedback": "esp:stream:feedback",
    "actionable": "esp:stream:actionable"
}


class EventPublisher(ABC):
    """
    Abstract Event Publisher Interface.
    Domain services depend on this interface, never on Redis directly.
    """

    @abstractmethod
    def publish(self, event: ESPEvent, category: str = "operational") -> str:
        """Publish an ESPEvent instance and return published message ID."""
        pass


class RedisStreamPublisher(EventPublisher):
    """
    Redis Streams implementation of EventPublisher.
    """

    def __init__(self, connection_mgr: Optional[RedisConnectionManager] = None):
        self.mgr = connection_mgr or RedisConnectionManager()

    def publish(self, event: ESPEvent, category: str = "operational") -> str:
        target_stream = STREAM_CATEGORY_MAP.get(category, "esp:stream:telemetry")
        client = self.mgr.get_client()

        payload_str = json.dumps(event.model_dump())
        msg_fields = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "asset_id": event.asset_id,
            "payload_json": payload_str
        }

        # XADD with MAXLEN ~ 10000 (48h transient buffer retention policy)
        msg_id = client.xadd(name=target_stream, fields=msg_fields, maxlen=10000, approximate=True)
        logger.info(f"Published event '{event.event_id}' (type={event.event_type}) to '{target_stream}' (msg_id={msg_id})")
        return str(msg_id)
