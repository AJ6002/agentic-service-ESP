import json
from typing import Optional
from app.contracts.context import SessionSnapshot
from app.contracts.hitl import PendingInterrupt
from .redis_client import get_redis_client

SESSION_PREFIX = "esp:session"

def _session_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}"

def _pending_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}:pending"

def save_session(session_id: str, snapshot: SessionSnapshot, ttl_sec: int = 86400) -> None:
    r = get_redis_client()
    key = _session_key(session_id)
    r.set(key, snapshot.model_dump_json(), ex=ttl_sec)

def get_session(session_id: str) -> Optional[SessionSnapshot]:
    r = get_redis_client()
    data = r.get(_session_key(session_id))
    if not data:
        return None
    return SessionSnapshot.model_validate_json(data)

def delete_session(session_id: str) -> None:
    r = get_redis_client()
    r.delete(_session_key(session_id))

def save_pending(session_id: str, pending: PendingInterrupt, ttl_sec: int = 900) -> None:
    r = get_redis_client()
    key = _pending_key(session_id)
    r.set(key, pending.model_dump_json(), ex=ttl_sec)

def get_pending(session_id: str) -> Optional[PendingInterrupt]:
    r = get_redis_client()
    data = r.get(_pending_key(session_id))
    if not data:
        return None
    return PendingInterrupt.model_validate_json(data)

def delete_pending(session_id: str) -> None:
    r = get_redis_client()
    r.delete(_pending_key(session_id))

def get_pending_ttl(session_id: str) -> int:
    r = get_redis_client()
    return r.ttl(_pending_key(session_id))
