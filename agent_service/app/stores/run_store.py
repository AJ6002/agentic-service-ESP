import json
from typing import Optional, Any
from app.contracts.hitl import RunState
from .redis_client import get_redis_client

RUN_PREFIX = "esp:run"

def _run_key(run_id: str) -> str:
    return f"{RUN_PREFIX}:{run_id}"

def _pack_key(run_id: str, version: Any) -> str:
    return f"{RUN_PREFIX}:{run_id}:pack:v{version}"

def _pack_latest_key(run_id: str) -> str:
    return f"{RUN_PREFIX}:{run_id}:pack:latest_version"

def save_run(run: RunState, ttl_sec: int = 86400) -> None:
    r = get_redis_client()
    key = _run_key(run.run_id)
    r.set(key, run.model_dump_json(), ex=ttl_sec)

def get_run(run_id: str) -> Optional[RunState]:
    r = get_redis_client()
    data = r.get(_run_key(run_id))
    if not data:
        return None
    return RunState.model_validate_json(data)

def get_run_ttl(run_id: str) -> int:
    r = get_redis_client()
    return r.ttl(_run_key(run_id))

def save_pack(run_id: str, version: int, pack_data: dict, ttl_sec: int = 86400) -> None:
    r = get_redis_client()
    key = _pack_key(run_id, version)
    r.set(key, json.dumps(pack_data), ex=ttl_sec)
    r.set(_pack_latest_key(run_id), str(version), ex=ttl_sec)

def get_pack(run_id: str, version: str = "latest") -> Optional[dict]:
    r = get_redis_client()
    if version == "latest":
        v_str = r.get(_pack_latest_key(run_id))
        if not v_str:
            return None
        key = _pack_key(run_id, v_str)
    else:
        key = _pack_key(run_id, version)
    data = r.get(key)
    if not data:
        return None
    return json.loads(data)
