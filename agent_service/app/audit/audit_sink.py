import json
import logging
from datetime import datetime
from typing import Any, Optional
from app.stores.redis_client import get_redis_client

logger = logging.getLogger("esp_audit")

AUDIT_LIST_KEY = "esp:audit:events"
_LOCAL_AUDIT_LOG: list[dict[str, Any]] = []
_REDIS_AVAILABLE: bool = True

def record_audit(
    event_type: str,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    """
    Append-only, write-only audit sink that never blocks execution.
    Logs to structured logger, in-memory buffer, and Redis list 'esp:audit:events'.
    """
    global _REDIS_AVAILABLE
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "run_id": run_id,
        "session_id": session_id,
        "payload": payload or {},
    }
    
    # In-memory append
    _LOCAL_AUDIT_LOG.append(record)
    if len(_LOCAL_AUDIT_LOG) > 1000:
        _LOCAL_AUDIT_LOG.pop(0)

    # Non-blocking log
    logger.info(f"[AUDIT] {event_type} | run_id={run_id} | session_id={session_id}")
    
    if _REDIS_AVAILABLE:
        try:
            r = get_redis_client()
            r.rpush(AUDIT_LIST_KEY, json.dumps(record))
        except Exception as ex:
            _REDIS_AVAILABLE = False
            logger.warning(f"[AUDIT_WARNING] Redis audit sink unavailable, falling back to in-memory audit: {ex}")

def get_audit_records(count: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent audit events for verification/testing."""
    if _REDIS_AVAILABLE:
        try:
            r = get_redis_client()
            items = r.lrange(AUDIT_LIST_KEY, -count, -1)
            if items:
                return [json.loads(item) for item in items]
        except Exception:
            pass
    return _LOCAL_AUDIT_LOG[-count:]

def clear_audit_records() -> None:
    """Clear audit records (used in test setup)."""
    global _LOCAL_AUDIT_LOG
    _LOCAL_AUDIT_LOG = []
    if _REDIS_AVAILABLE:
        try:
            r = get_redis_client()
            r.delete(AUDIT_LIST_KEY)
        except Exception:
            pass
