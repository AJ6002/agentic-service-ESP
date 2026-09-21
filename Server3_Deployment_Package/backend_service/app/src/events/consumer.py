"""
Redis Stream Consumer Adapter
Grounded in Phase 6 Event-Driven Architecture Spec §6, §8, §20
"""

import json
import logging
from typing import Callable, List, Dict, Any, Optional
from shared.schemas.event import ESPEvent
from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)


class RedisStreamConsumer:
    """
    Consumer adapter consuming events from Redis Streams via Consumer Groups.
    """

    def __init__(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str = "worker-1",
        connection_mgr: Optional[RedisConnectionManager] = None
    ):
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.mgr = connection_mgr or RedisConnectionManager()

    def read_batch(self, count: int = 10, block_ms: int = 1000) -> List[Dict[str, Any]]:
        """Read a batch of messages from stream consumer group."""
        client = self.mgr.get_client()
        items = []

        try:
            res = client.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_name: ">"},
                count=count,
                block=block_ms
            )

            for stream, msgs in res:
                for msg_id, fields in msgs:
                    payload_json = fields.get("payload_json")
                    if payload_json:
                        evt_dict = json.loads(payload_json)
                        evt = ESPEvent(**evt_dict)
                        items.append({"msg_id": msg_id, "event": evt, "raw_fields": fields})

        except Exception as ex:
            if "NOGROUP" in str(ex):
                logger.warning(f"Consumer group '{self.group_name}' on '{self.stream_name}' missing.")
            else:
                logger.error(f"Error reading stream '{self.stream_name}': {ex}")

        return items

    def ack(self, msg_id: str):
        """Acknowledge message processing completion."""
        client = self.mgr.get_client()
        client.xack(self.stream_name, self.group_name, msg_id)
        logger.debug(f"Acked msg '{msg_id}' on '{self.stream_name}' ({self.group_name})")
