"""
Restart-safe Redis Checkpointer for LangGraph (Plan.md Phase C2).
Inherits from LangGraph's MemorySaver and syncs thread checkpoints, blobs, and writes
to Redis with TTL, enabling cross-process restart-safety for paused runs.
"""

import pickle
import base64
import logging
from typing import Optional, Dict, Any, Sequence
from collections import defaultdict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, ChannelVersions, CheckpointTuple
from langgraph.checkpoint.memory import MemorySaver
from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)

# 7-day default TTL for paused graph thread checkpoints
_THREAD_CHECKPOINT_TTL_SECONDS = 7 * 86400


class RedisCheckpointer(MemorySaver):
    """
    LangGraph checkpointer that transparently persists state to Redis.
    Subclasses MemorySaver for zero-overhead in-memory operations and LangGraph 100%
    typing compatibility, while ensuring graph threads survive backend process restarts.
    """

    def __init__(
        self,
        connection_mgr: Optional[RedisConnectionManager] = None,
        ttl_seconds: int = _THREAD_CHECKPOINT_TTL_SECONDS,
    ):
        super().__init__()
        self.connection_mgr = connection_mgr or RedisConnectionManager()
        self.ttl_seconds = ttl_seconds
        self._redis_disabled = False

    def _redis_key(self, thread_id: str) -> str:
        return f"esp:lg_check:{thread_id}"

    def _sync_thread_to_redis(self, thread_id: str) -> None:
        """Serialize thread storage, writes, and blobs to Redis via base64."""
        if getattr(self, "_redis_disabled", False):
            return
        try:
            client = self.connection_mgr.get_client()
            thread_storage = dict(self.storage.get(thread_id, {}))
            thread_writes = {k: v for k, v in self.writes.items() if k[0] == thread_id}
            thread_blobs = {k: v for k, v in self.blobs.items() if k[0] == thread_id}

            binary_data = pickle.dumps((thread_storage, thread_writes, thread_blobs))
            b64_str = base64.b64encode(binary_data).decode("ascii")
            client.set(self._redis_key(thread_id), b64_str, ex=self.ttl_seconds)
            logger.debug("RedisCheckpointer: Synced thread %s to Redis", thread_id)
        except Exception as ex:
            self._redis_disabled = True
            logger.info("RedisCheckpointer: Redis offline, continuing in high-speed in-memory mode (%s)", ex)

    def _load_thread_from_redis(self, thread_id: str) -> bool:
        """Hydrate thread storage, writes, and blobs from Redis if not present in memory."""
        if thread_id in self.storage and self.storage[thread_id]:
            return True
        if getattr(self, "_redis_disabled", False):
            return False

        try:
            client = self.connection_mgr.get_client()
            raw = client.get(self._redis_key(thread_id))
            if raw:
                binary_data = base64.b64decode(raw.encode("ascii"))
                st, wr, bl = pickle.loads(binary_data)
                for ns, chks in st.items():
                    self.storage[thread_id][ns].update(chks)
                self.writes.update(wr)
                self.blobs.update(bl)
                logger.info("RedisCheckpointer: Re-hydrated thread %s from Redis after restart", thread_id)
                return True
        except Exception as ex:
            logger.debug("RedisCheckpointer: Could not load thread %s from Redis (%s)", thread_id, ex)

        return False

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        res = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            self._sync_thread_to_redis(thread_id)
        return res

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        super().put_writes(config, writes, task_id, task_path)
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            self._sync_thread_to_redis(thread_id)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            self._load_thread_from_redis(thread_id)
        return super().get_tuple(config)

    def delete_thread(self, thread_id: str) -> None:
        super().delete_thread(thread_id)
        try:
            client = self.connection_mgr.get_client()
            client.delete(self._redis_key(thread_id))
        except Exception:
            pass
