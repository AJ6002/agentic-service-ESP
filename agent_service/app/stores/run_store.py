import json
from typing import Optional, Any
from app.contracts.hitl import RunState
from .redis_client import get_redis_client

RUN_PREFIX = "esp:run"
_LOCAL_RUN_STORE: dict[str, str] = {}
_LOCAL_PACK_STORE: dict[str, str] = {}
_LOCAL_ARTIFACTS_STORE: dict[str, str] = {}

def _run_key(run_id: str) -> str:
    return f"{RUN_PREFIX}:{run_id}"

def _pack_key(run_id: str, version: Any) -> str:
    return f"{RUN_PREFIX}:{run_id}:pack:v{version}"

def _pack_latest_key(run_id: str) -> str:
    return f"{RUN_PREFIX}:{run_id}:pack:latest_version"

def save_run(run: RunState, ttl_sec: int = 86400) -> None:
    data_str = run.model_dump_json()
    _LOCAL_RUN_STORE[_run_key(run.run_id)] = data_str
    try:
        r = get_redis_client()
        key = _run_key(run.run_id)
        r.set(key, data_str, ex=ttl_sec)
    except Exception:
        pass

def get_run(run_id: str) -> Optional[RunState]:
    key = _run_key(run_id)
    try:
        r = get_redis_client()
        data = r.get(key)
        if data:
            return RunState.model_validate_json(data)
    except Exception:
        pass
    local_data = _LOCAL_RUN_STORE.get(key)
    if local_data:
        return RunState.model_validate_json(local_data)
    return None

def get_run_ttl(run_id: str) -> int:
    try:
        r = get_redis_client()
        return r.ttl(_run_key(run_id))
    except Exception:
        return 86400 if _run_key(run_id) in _LOCAL_RUN_STORE else -2

def save_pack(run_id: str, version: int, pack_data: dict, ttl_sec: int = 86400) -> None:
    data_str = json.dumps(pack_data)
    _LOCAL_PACK_STORE[_pack_key(run_id, version)] = data_str
    _LOCAL_PACK_STORE[_pack_latest_key(run_id)] = str(version)
    try:
        r = get_redis_client()
        key = _pack_key(run_id, version)
        r.set(key, data_str, ex=ttl_sec)
        r.set(_pack_latest_key(run_id), str(version), ex=ttl_sec)
    except Exception:
        pass

def get_pack(run_id: str, version: str = "latest") -> Optional[dict]:
    try:
        r = get_redis_client()
        if version == "latest":
            v_str = r.get(_pack_latest_key(run_id))
            if not v_str:
                v_str = _LOCAL_PACK_STORE.get(_pack_latest_key(run_id))
            if not v_str:
                return None
            key = _pack_key(run_id, v_str)
        else:
            key = _pack_key(run_id, version)
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass

    if version == "latest":
        v_str = _LOCAL_PACK_STORE.get(_pack_latest_key(run_id))
        if not v_str:
            return None
        key = _pack_key(run_id, v_str)
    else:
        key = _pack_key(run_id, version)

    local_data = _LOCAL_PACK_STORE.get(key)
    if local_data:
        return json.loads(local_data)
    return None

def _artifacts_key(run_id: str) -> str:
    return f"{RUN_PREFIX}:{run_id}:artifacts"

def save_run_artifacts(run_id: str, advisory: Optional[dict] = None, visualization: Optional[dict] = None, ttl_sec: int = 86400) -> None:
    data = {
        "advisory": advisory or {},
        "visualization": visualization or {},
    }
    data_str = json.dumps(data)
    _LOCAL_ARTIFACTS_STORE[_artifacts_key(run_id)] = data_str
    try:
        r = get_redis_client()
        r.set(_artifacts_key(run_id), data_str, ex=ttl_sec)
    except Exception:
        pass

def get_run_artifacts(run_id: str) -> tuple[Optional[dict], Optional[dict]]:
    key = _artifacts_key(run_id)
    try:
        r = get_redis_client()
        data = r.get(key)
        if data:
            parsed = json.loads(data)
            return parsed.get("advisory"), parsed.get("visualization")
    except Exception:
        pass
    local_data = _LOCAL_ARTIFACTS_STORE.get(key)
    if local_data:
        parsed = json.loads(local_data)
        return parsed.get("advisory"), parsed.get("visualization")
    return None, None
