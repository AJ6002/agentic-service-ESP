"""
Events Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries events table and opg_well_telemetry for operational transitions, trips, and alarms.
Zero HTTP dependency on :8090.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError, get_well_id_variants, build_temporal_meta


async def fetch_events_timeline(
    well_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Fetch chronological event timeline for well."""
    if not start or not end:
        now = datetime.now(timezone.utc)
        if not end:
            end = now.isoformat().replace("+00:00", "Z")
        if not start:
            start = (now - timedelta(hours=24)).isoformat().replace("+00:00", "Z")

    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            # 1. Check explicit events table
            cur.execute("""
                SELECT event_id, timestamp, operating_state, scenario, trip_cause, alarms, severity
                FROM events
                WHERE well_id = ANY(%s)
                  AND timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp DESC;
            """, (variants, start, end))
            rows = cur.fetchall()

            events_list = []
            for r in rows:
                ts = r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1])
                alarm_arr = [a.strip() for a in str(r[5] or "").split(",") if a.strip()]
                events_list.append({
                    "event_id": r[0],
                    "timestamp": ts,
                    "operating_state": r[2] or "NORMAL",
                    "scenario": r[3] or "NOMINAL",
                    "trip_cause": r[4] or "",
                    "alarms": alarm_arr,
                    "severity": r[6] or "INFO",
                })

            # 2. If events table has 0 records, query recent telemetry using index
            if not events_list:
                cur.execute("""
                    SELECT timestamp, operating_state, scenario, trip_cause, alarms, alerts
                    FROM opg_well_telemetry
                    WHERE well_id = ANY(%s)
                      AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp DESC
                    LIMIT 200;
                """, (variants, start, end))
                t_rows = cur.fetchall()
                for tr in t_rows:
                    is_trip_or_non_running = (tr[3] and str(tr[3]).strip()) or (tr[1] and str(tr[1]).lower() != "running")
                    if is_trip_or_non_running:
                        ts = tr[0].isoformat() if hasattr(tr[0], "isoformat") else str(tr[0])
                        alarm_arr = [a.strip() for a in str(tr[4] or "").split(",") if a.strip()]
                        events_list.append({
                            "event_id": f"EV-TELEM-{well_id}-{len(events_list)+1}",
                            "timestamp": ts,
                            "operating_state": tr[1] or "TRIP",
                            "scenario": tr[2] or "OPERATIONAL_TRIP",
                            "trip_cause": tr[3] or "TRIP_DETECTED",
                            "alarms": alarm_arr,
                            "severity": "CRITICAL",
                        })
                        if len(events_list) >= 20:
                            break

            return {
                "well_id": well_id,
                "start": start,
                "end": end,
                "events": events_list,
                "total_events": len(events_list),
                "source": "POSTGRESQL",
                "temporal_meta": build_temporal_meta(
                    query_start=start,
                    query_end=end,
                    records=events_list,
                    ts_field="timestamp"
                )
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_events_timeline failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_events_trips(
    well_id: str,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Fetch trip-specific historical records."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT event_id, timestamp, operating_state, scenario, trip_cause, alarms, severity
                FROM events
                WHERE well_id = ANY(%s)
                  AND (operating_state ILIKE '%%TRIP%%' OR (trip_cause IS NOT NULL AND trip_cause != ''))
                ORDER BY timestamp DESC
                LIMIT 50;
            """, (variants,))
            rows = cur.fetchall()

            trips = []
            for r in rows:
                ts = r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1])
                alarm_arr = [a.strip() for a in str(r[5] or "").split(",") if a.strip()]
                trips.append({
                    "event_id": r[0],
                    "timestamp": ts,
                    "operating_state": r[2],
                    "scenario": r[3],
                    "trip_cause": r[4],
                    "alarms": alarm_arr,
                    "severity": r[6],
                })

            if not trips:
                cur.execute("""
                    SELECT timestamp, operating_state, scenario, trip_cause, alarms
                    FROM opg_well_telemetry
                    WHERE well_id = ANY(%s)
                    ORDER BY timestamp DESC
                    LIMIT 200;
                """, (variants,))
                for tr in cur.fetchall():
                    is_trip = (tr[3] and str(tr[3]).strip()) or (tr[1] and str(tr[1]).lower() != "running")
                    if is_trip:
                        ts = tr[0].isoformat() if hasattr(tr[0], "isoformat") else str(tr[0])
                        trips.append({
                            "event_id": f"TRIP-TELEM-{well_id}-{len(trips)+1}",
                            "timestamp": ts,
                            "operating_state": tr[1] or "TRIP",
                            "scenario": tr[2] or "TRIP",
                            "trip_cause": tr[3] or "TRIP_DETECTED",
                            "alarms": [a.strip() for a in str(tr[4] or "").split(",") if a.strip()],
                            "severity": "CRITICAL",
                        })
                        if len(trips) >= 10:
                            break

            return {
                "well_id": well_id,
                "trips": trips,
                "total_trips": len(trips),
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_events_trips failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def check_events_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Check events table liveness."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT count(*) FROM events;")
            cnt = cur.fetchone()[0]
            return {"status": "HEALTHY", "source": "POSTGRESQL", "row_count": cnt}
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL"}
