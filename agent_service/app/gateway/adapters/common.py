"""
Common utilities for Server 184 domain adapters.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 §6.
"""

import os
from typing import Any, Optional
import httpx

# 20s default (env-overridable): Server 184 endpoints have been observed
# taking up to ~8s under load, and several READ calls run concurrently
# sharing one client. A tight ceiling caused working-but-slow calls to be
# wrongly reported DEGRADED/TIMEOUT. Generous ceiling, not "no timeout" —
# a genuinely hung upstream must still fail rather than block forever.
DEFAULT_TIMEOUT_SEC = float(os.getenv("GATEWAY_TIMEOUT_SEC", "20.0"))


def get_gateway_base_url() -> str:
    url = os.getenv("SERVER184_BASE_URL") or os.getenv("SERVER3_BASE_URL", "http://192.168.1.184:8090")
    return url.rstrip("/")


class AdapterError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def handle_adapter_response(resp: httpx.Response, domain: str, endpoint: str) -> dict[str, Any]:
    """
    Standard envelope handler per spec §6:
    - 200: returns parsed JSON
    - 404: WELL_NOT_FOUND or NO_DATA
    - 503: MQTT_DISCONNECTED or SERVICE_UNAVAILABLE
    - 400: WINDOW_TOO_LARGE / LIMIT_EXCEEDED
    """
    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    error_code = None
    detail = None
    try:
        err_json = resp.json()
        error_code = err_json.get("error", {}).get("code") if isinstance(err_json.get("error"), dict) else err_json.get("error")
        detail = err_json.get("error", {}).get("message") if isinstance(err_json.get("error"), dict) else err_json.get("detail", str(err_json))
    except Exception:
        detail = resp.text

    msg = f"{domain} {endpoint} returned HTTP {resp.status_code} [{error_code}]: {detail}"
    raise AdapterError(msg, status_code=resp.status_code, code=error_code)


def build_temporal_meta(
    query_start: Optional[str] = None,
    query_end: Optional[str] = None,
    records: Optional[list] = None,
    columns: Optional[list[str]] = None,
    ts_field: str = "timestamp",
) -> dict[str, Any]:
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    meta: dict[str, Any] = {"executed_at": now_utc}

    span_seconds = None
    if query_start and query_end:
        try:
            t0 = datetime.fromisoformat(query_start.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(query_end.replace("Z", "+00:00"))
            span_seconds = round(abs((t1 - t0).total_seconds()), 2)
        except Exception:
            pass

    meta["query_window"] = {
        "start": query_start,
        "end": query_end,
        "span_seconds": span_seconds,
    }

    earliest = None
    latest = None
    count = 0
    if records and isinstance(records, list):
        count = len(records)
        ts_vals = []
        ts_idx = -1
        if columns and isinstance(columns, list) and ts_field in columns:
            ts_idx = columns.index(ts_field)

        for r in records:
            if isinstance(r, dict) and ts_field in r and r[ts_field]:
                ts_vals.append(str(r[ts_field]))
            elif isinstance(r, list) and ts_idx >= 0 and len(r) > ts_idx and r[ts_idx]:
                ts_vals.append(str(r[ts_idx]))

        if ts_vals:
            earliest = min(ts_vals)
            latest = max(ts_vals)

    meta["data_bounds"] = {
        "earliest_ts": earliest,
        "latest_ts": latest,
        "point_count": count,
    }
    return meta
