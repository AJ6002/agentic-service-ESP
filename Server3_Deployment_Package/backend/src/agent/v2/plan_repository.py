"""
Plan Repository for V2 Architecture
Provides thread-safe persistence and retrieval of execution plans via Redis with in-memory fallback.
Hardened for distributed multi-worker concurrency and TTL management.
"""

import os
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

import redis

from .plan_schema import PlanArtifact, PlanStepStatus

logger = logging.getLogger(__name__)


class PlanRepository:
    """
    Repository for persisting and managing PlanArtifact lifecycle.
    Uses Redis as the primary distributed store with 24-hour TTL,
    and seamlessly falls back to a thread-safe in-memory cache when Redis is unavailable.
    """

    REDIS_KEY_TEMPLATE: str = "esp:plan:{run_id}"
    REDIS_AUDIT_KEY_TEMPLATE: str = "esp:audit:{run_id}"
    DEFAULT_TTL: int = 86400  # 24 hours

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = DEFAULT_TTL,
    ):
        self.default_ttl = default_ttl
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._memory_cache: Dict[str, str] = {}
        self._audit_cache: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()
        self._redis_client: Optional[redis.Redis] = None
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection; on failure, log distributed degradation warning."""
        try:
            client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
            client.ping()
            self._redis_client = client
            logger.info("PlanRepository connected to Redis at %s", self.redis_url)
        except Exception as exc:
            logger.warning(
                "[CRITICAL_DISTRIBUTED_STATE_DEGRADED] Redis unavailable at %s (%s); "
                "falling back to process-local in-memory cache. State will not be shared across workers.",
                self.redis_url,
                exc,
            )
            self._redis_client = None

    def _format_key(self, run_id: str) -> str:
        """Generate canonical Redis key for a given run ID."""
        return self.REDIS_KEY_TEMPLATE.format(run_id=run_id)

    def _format_audit_key(self, run_id: str) -> str:
        """Generate canonical Redis audit trail key for a given run ID."""
        return self.REDIS_AUDIT_KEY_TEMPLATE.format(run_id=run_id)

    def save_plan(self, plan: PlanArtifact) -> None:
        """
        Serializes PlanArtifact to JSON, stores in Redis with TTL (default 86400s),
        and synchronizes with the in-memory cache.
        """
        raw_json = plan.model_dump_json()
        key = self._format_key(plan.run_id)

        # Thread-safe in-memory cache update
        with self._lock:
            self._memory_cache[plan.run_id] = raw_json

        # Write to Redis if connected
        if self._redis_client is not None:
            try:
                self._redis_client.set(key, raw_json, ex=self.default_ttl)
            except Exception as exc:
                logger.warning(
                    "[CRITICAL_DISTRIBUTED_STATE_DEGRADED] Failed to persist plan '%s' to Redis (%s); "
                    "in-memory cache remains valid locally.",
                    plan.run_id,
                    exc,
                )

    def get_plan(self, run_id: str) -> Optional[PlanArtifact]:
        """
        Retrieve a PlanArtifact by run_id.
        Tries Redis first; falls back to in-memory cache.
        Validates schema_version.
        """
        key = self._format_key(run_id)
        raw_json: Optional[str] = None

        # 1. Try Redis
        if self._redis_client is not None:
            try:
                raw_json = self._redis_client.get(key)
            except Exception as exc:
                logger.warning(
                    "[CRITICAL_DISTRIBUTED_STATE_DEGRADED] Error querying Redis for plan '%s' (%s); "
                    "falling back to process memory.",
                    run_id,
                    exc,
                )

        # 2. Check in-memory fallback
        if raw_json is None:
            with self._lock:
                raw_json = self._memory_cache.get(run_id)

        if raw_json:
            plan = PlanArtifact.model_validate_json(raw_json)
            if plan.schema_version and plan.schema_version < "2.0.0":
                logger.warning(
                    "Plan '%s' has outdated schema_version '%s' (expected >= 2.0.0).",
                    run_id,
                    plan.schema_version,
                )
            return plan

        return None

    def get_ttl(self, run_id: str) -> int:
        """
        Return the remaining TTL in seconds for a given run ID from Redis,
        or default_ttl if operating in in-memory fallback.
        """
        if self._redis_client is not None:
            try:
                key = self._format_key(run_id)
                ttl = self._redis_client.ttl(key)
                return ttl
            except Exception as exc:
                logger.warning("Failed to fetch TTL for '%s': %s", run_id, exc)
        return self.default_ttl

    def update_step_status(
        self,
        run_id: str,
        step_id: int,
        status: PlanStepStatus,
        observation: Optional[str] = None,
        exec_ms: Optional[float] = None,
    ) -> Optional[PlanArtifact]:
        """
        Atomically update the status, observation summary, and execution duration of a plan step.
        Uses Redis WATCH transaction to prevent step clobbering under concurrency,
        preserving the existing key TTL.
        """
        # Coerce status to PlanStepStatus if passed as str
        if isinstance(status, str) and not isinstance(status, PlanStepStatus):
            status = PlanStepStatus(status)

        key = self._format_key(run_id)

        # Attempt atomic Redis update with WATCH transaction
        if self._redis_client is not None:
            for _ in range(5):  # retry loop for optimistic concurrency
                try:
                    with self._redis_client.pipeline() as pipe:
                        pipe.watch(key)
                        raw_json = pipe.get(key)
                        if not raw_json:
                            pipe.unwatch()
                            break
                        plan = PlanArtifact.model_validate_json(raw_json)
                        target_step = next((s for s in plan.steps if s.step_id == step_id), None)
                        if target_step is None:
                            pipe.unwatch()
                            logger.warning("update_step_status: Step %s not found in plan '%s'.", step_id, run_id)
                            return None

                        target_step.status = status
                        if observation is not None:
                            target_step.observation_summary = observation
                        if exec_ms is not None:
                            target_step.execution_time_ms = exec_ms

                        plan.updated_at = datetime.now(timezone.utc).isoformat()
                        new_json = plan.model_dump_json()

                        pipe.multi()
                        pipe.set(key, new_json, keepttl=True)
                        pipe.execute()

                        with self._lock:
                            self._memory_cache[run_id] = new_json
                        return plan
                except redis.WatchError:
                    continue
                except Exception as exc:
                    logger.warning(
                        "[CRITICAL_DISTRIBUTED_STATE_DEGRADED] Atomic Redis update failed (%s); "
                        "falling back to memory.",
                        exc,
                    )
                    break

        # In-memory fallback
        with self._lock:
            raw_json = self._memory_cache.get(run_id)
            if not raw_json:
                logger.warning("update_step_status: Plan '%s' not found.", run_id)
                return None

            plan = PlanArtifact.model_validate_json(raw_json)
            target_step = next((s for s in plan.steps if s.step_id == step_id), None)
            if target_step is None:
                logger.warning("update_step_status: Step %s not found in plan '%s'.", step_id, run_id)
                return None

            target_step.status = status
            if observation is not None:
                target_step.observation_summary = observation
            if exec_ms is not None:
                target_step.execution_time_ms = exec_ms

            plan.updated_at = datetime.now(timezone.utc).isoformat()
            self._memory_cache[run_id] = plan.model_dump_json()
            return plan

    def set_approval_status(self, run_id: str, is_approved: bool) -> Optional[PlanArtifact]:
        """
        Set human approval state (True/False) for a plan artifact.
        Updates updated_at and persists the modified plan.
        """
        plan = self.get_plan(run_id)
        if not plan:
            logger.warning("set_approval_status: Plan '%s' not found.", run_id)
            return None

        plan.is_approved = is_approved
        plan.updated_at = datetime.now(timezone.utc).isoformat()
        self.save_plan(plan)
        return plan

    def save_audit_event(self, run_id: str, event: dict) -> None:
        """
        Persist an audit trail event permanently in Redis (key: esp:audit:{run_id}, no TTL)
        and in the local audit cache.
        """
        event_with_ts = dict(event)
        if "timestamp" not in event_with_ts:
            event_with_ts["timestamp"] = datetime.now(timezone.utc).isoformat()

        serialized = json.dumps(event_with_ts)
        audit_key = self._format_audit_key(run_id)

        with self._lock:
            if run_id not in self._audit_cache:
                self._audit_cache[run_id] = []
            self._audit_cache[run_id].append(event_with_ts)

        if self._redis_client is not None:
            try:
                self._redis_client.rpush(audit_key, serialized)
            except Exception as exc:
                logger.warning(
                    "[CRITICAL_DISTRIBUTED_STATE_DEGRADED] Failed to persist audit event for '%s' to Redis: %s",
                    run_id,
                    exc,
                )

    def get_audit_trail(self, run_id: str) -> List[dict]:
        """
        Retrieve all audit trail events for a given run ID from Redis, or local cache on fallback.
        """
        audit_key = self._format_audit_key(run_id)
        if self._redis_client is not None:
            try:
                entries = self._redis_client.lrange(audit_key, 0, -1)
                if entries:
                    return [json.loads(e) for e in entries]
            except Exception as exc:
                logger.warning("Failed to retrieve audit trail from Redis for '%s': %s", run_id, exc)

        with self._lock:
            return list(self._audit_cache.get(run_id, []))
