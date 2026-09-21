"""
LangGraph Run Checkpoint & State Persistence Manager
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §18
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.events.redis_connection import RedisConnectionManager
from src.events.db_event_store import DatabaseEventStore
from src.agent.supervisor.state import AgentState

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages short-lived graph state checkpoints in Redis and durable completion records in DB.
    """

    def __init__(
        self,
        connection_mgr: Optional[RedisConnectionManager] = None,
        db_store: Optional[DatabaseEventStore] = None
    ):
        self.connection_mgr = connection_mgr or RedisConnectionManager()
        self.db_store = db_store or DatabaseEventStore()
        self._memory_checkpoints: Dict[str, Dict[str, Any]] = {}

    def save_checkpoint(self, state: AgentState, ttl_seconds: int = 14400) -> bool:
        """
        Save active AgentState to Redis under key 'esp:checkpoint:{run_id}'.
        Fallback to in-memory store if Redis is unavailable.
        """
        run_id = state.get("run", {}).get("run_id")
        if not run_id:
            logger.error("CheckpointManager.save_checkpoint failed: missing run_id in state.")
            return False

        payload_str = json.dumps(state, default=str)
        self._memory_checkpoints[run_id] = json.loads(payload_str)

        try:
            client = self.connection_mgr.get_client()
            key = f"esp:checkpoint:{run_id}"
            client.set(name=key, value=payload_str, ex=ttl_seconds)
            logger.info(f"CheckpointManager: Saved state checkpoint for run '{run_id}' to Redis (TTL={ttl_seconds}s).")
            return True
        except Exception as ex:
            logger.warning(f"CheckpointManager: Redis save failed for run '{run_id}' ({ex}). Saved to memory fallback.")
            return False

    def load_checkpoint(self, run_id: str) -> Optional[AgentState]:
        """
        Retrieve active AgentState checkpoint by run_id from Redis or memory fallback.
        """
        try:
            client = self.connection_mgr.get_client()
            key = f"esp:checkpoint:{run_id}"
            data = client.get(key)
            if data:
                logger.info(f"CheckpointManager: Loaded checkpoint for run '{run_id}' from Redis.")
                return json.loads(data)
        except Exception as ex:
            logger.warning(f"CheckpointManager: Redis load failed for run '{run_id}' ({ex}). Checking memory fallback.")

        if run_id in self._memory_checkpoints:
            logger.info(f"CheckpointManager: Loaded checkpoint for run '{run_id}' from memory fallback.")
            return self._memory_checkpoints[run_id]

        logger.warning(f"CheckpointManager: No checkpoint found for run '{run_id}'.")
        return None

    def clear_checkpoint(self, run_id: str):
        """Remove short-lived checkpoint upon run completion."""
        self._memory_checkpoints.pop(run_id, None)
        try:
            client = self.connection_mgr.get_client()
            key = f"esp:checkpoint:{run_id}"
            client.delete(key)
            logger.info(f"CheckpointManager: Cleared Redis checkpoint for run '{run_id}'.")
        except Exception as ex:
            logger.warning(f"CheckpointManager: Failed to delete Redis checkpoint for '{run_id}': {ex}")
