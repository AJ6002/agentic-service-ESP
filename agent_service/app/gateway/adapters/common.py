"""
Common utilities for Server 184 domain adapters.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 §6.
"""

import os
from typing import Any, Optional
import httpx

# 30s default (env-overridable): Server 184 endpoints have been observed
# taking up to ~8-15s under load, and several READ calls run concurrently
# sharing one client. A tight ceiling caused working-but-slow calls to be
# wrongly reported DEGRADED/TIMEOUT. Generous ceiling, not "no timeout" —
# a genuinely hung upstream must still fail rather than block forever.
DEFAULT_TIMEOUT_SEC = float(os.getenv("GATEWAY_TIMEOUT_SEC", "2.0"))


def get_well_id_variants(well_id: str) -> list[str]:
    """
    Returns normalized variants of a well identifier to handle differences
    like FS-17 vs FS-017, ASSET-FS-017, FNW-1 vs FNW-001, etc.
    """
    if not well_id:
        return []
    clean = well_id.strip().upper()
    variants = {clean}
    bare = clean
    if bare.startswith("ASSET-"):
        bare = bare[6:]
        variants.add(bare)
    elif bare.startswith("WELL-"):
        bare = bare[5:]
        variants.add(bare)
    variants.add(f"ASSET-{bare}")

    if "-" in bare:
        parts = bare.split("-", 1)
        prefix, num_part = parts[0], parts[1]
        if num_part.isdigit():
            num = int(num_part)
            variants.add(f"{prefix}-{num}")
            variants.add(f"{prefix}-{num:02d}")
            variants.add(f"{prefix}-{num:03d}")
            variants.add(f"ASSET-{prefix}-{num}")
            variants.add(f"ASSET-{prefix}-{num:02d}")
            variants.add(f"ASSET-{prefix}-{num:03d}")

    return list(variants)


class AdapterError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


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
