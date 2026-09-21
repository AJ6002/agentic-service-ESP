"""
Redis Stream & Consumer Group Bootstrapper
Grounded in Phase 6 Event-Driven Architecture Spec §6, §8
"""

import logging
from typing import Dict, List
from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)

STREAMS = [
    "esp:stream:telemetry",
    "esp:stream:model",
    "esp:stream:asset",
    "esp:stream:feedback",
    "esp:stream:actionable",
    "esp:stream:dlq"
]

CONSUMER_GROUPS: Dict[str, List[str]] = {
    "esp:stream:telemetry": ["esp:group:event-processor", "esp:group:audit-consumer"],
    "esp:stream:model": ["esp:group:event-processor", "esp:group:audit-consumer"],
    "esp:stream:asset": ["esp:group:event-processor", "esp:group:audit-consumer"],
    "esp:stream:feedback": ["esp:group:event-processor", "esp:group:audit-consumer"],
    "esp:stream:actionable": ["esp:group:agent-trigger", "esp:group:audit-consumer"],
}


def bootstrap_streams_and_groups() -> bool:
    """Ensure all required streams and consumer groups exist in Redis."""
    mgr = RedisConnectionManager()
    if not mgr.ping():
        logger.warning("Redis ping failed during stream bootstrap. Skipping.")
        return False

    client = mgr.get_client()

    for stream in STREAMS:
        # Create stream entry if missing
        try:
            client.xlen(stream)
        except Exception:
            pass

        # Create consumer groups
        groups = CONSUMER_GROUPS.get(stream, [])
        for group in groups:
            try:
                client.xgroup_create(name=stream, groupname=group, id="0", mkstream=True)
                logger.info(f"Created consumer group '{group}' on stream '{stream}'")
            except Exception as ex:
                if "BUSYGROUP" in str(ex):
                    logger.debug(f"Consumer group '{group}' already exists on '{stream}'")
                else:
                    logger.warning(f"Could not create consumer group '{group}' on '{stream}': {ex}")

    return True


if __name__ == "__main__":
    bootstrap_streams_and_groups()
