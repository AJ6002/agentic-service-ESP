import json
import logging
from datetime import datetime
from typing import Any, Optional
from app.stores.redis_client import get_redis_client

logger = logging.getLogger("esp_audit")

AUDIT_LIST_KEY = "esp:audit:events"

def record_audit(
    event_type: str,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    """
    Append-only, write-only audit sink that never blocks execution.
    Logs to structured logger and pushes to Redis list 'esp:audit:events'.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "run_id": run_id,
        "session_id": session_id,
        "payload": payload or {},
    }
    
    # Non-blocking log
    logger.info(f"[AUDIT] {event_type} | run_id={run_id} | session_id={session_id}")
    
    try:
        r = get_redis_client()
        r.rpush(AUDIT_LIST_KEY, json.dumps(record))
    except Exception as ex:
        # Never crash the main execution path on audit failure
        logger.warning(f"[AUDIT_WARNING] Failed to push audit record to Redis: {ex}")

def get_audit_records(count: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent audit events for verification/testing."""
    try:
        r = get_redis_client()
        items = r.lrange(AUDIT_LIST_KEY, -count, -1)
        return [json.loads(item) for item in items]
    except Exception:
        return []

def clear_audit_records() -> None:
    """Clear audit records (used in test setup)."""
    try:
        r = get_redis_client()
        r.delete(AUDIT_LIST_KEY)
    except Exception:
        pass
