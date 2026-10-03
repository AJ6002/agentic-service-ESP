import json
from typing import Optional
from app.contracts.context import SessionSnapshot
from app.contracts.hitl import PendingInterrupt
from .redis_client import get_redis_client

SESSION_PREFIX = "esp:session"
_LOCAL_SESSION_STORE: dict[str, str] = {}
_LOCAL_PENDING_STORE: dict[str, str] = {}

def _session_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}"

def _pending_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}:pending"

def save_session(session_id: str, snapshot: SessionSnapshot, ttl_sec: int = 86400) -> None:
    data_str = snapshot.model_dump_json()
    _LOCAL_SESSION_STORE[_session_key(session_id)] = data_str
    try:
        r = get_redis_client()
        key = _session_key(session_id)
        r.set(key, data_str, ex=ttl_sec)
    except Exception:
        pass

def get_session(session_id: str) -> Optional[SessionSnapshot]:
    key = _session_key(session_id)
    try:
        r = get_redis_client()
        data = r.get(key)
        if data:
            return SessionSnapshot.model_validate_json(data)
    except Exception:
        pass
    local_data = _LOCAL_SESSION_STORE.get(key)
    if local_data:
        return SessionSnapshot.model_validate_json(local_data)
    return None

def delete_session(session_id: str) -> None:
    key = _session_key(session_id)
    _LOCAL_SESSION_STORE.pop(key, None)
    try:
        r = get_redis_client()
        r.delete(key)
    except Exception:
        pass

def save_pending(session_id: str, pending: PendingInterrupt, ttl_sec: int = 900) -> None:
    data_str = pending.model_dump_json()
    _LOCAL_PENDING_STORE[_pending_key(session_id)] = data_str
    try:
        r = get_redis_client()
        key = _pending_key(session_id)
        r.set(key, data_str, ex=ttl_sec)
    except Exception:
        pass

def get_pending(session_id: str) -> Optional[PendingInterrupt]:
    key = _pending_key(session_id)
    try:
        r = get_redis_client()
        data = r.get(key)
        if data:
            return PendingInterrupt.model_validate_json(data)
    except Exception:
        pass
    local_data = _LOCAL_PENDING_STORE.get(key)
    if local_data:
        return PendingInterrupt.model_validate_json(local_data)
    return None

def delete_pending(session_id: str) -> None:
    key = _pending_key(session_id)
    _LOCAL_PENDING_STORE.pop(key, None)
    try:
        r = get_redis_client()
        r.delete(key)
    except Exception:
        pass

def get_pending_ttl(session_id: str) -> int:
    try:
        r = get_redis_client()
        return r.ttl(_pending_key(session_id))
    except Exception:
        return 900 if _pending_key(session_id) in _LOCAL_PENDING_STORE else -2
