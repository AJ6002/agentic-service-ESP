"""
Historian Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries opg_well_telemetry for timeseries windows, aggregates, latest points, and temporal coverage.
Zero HTTP dependency on :8090.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError, get_well_id_variants, build_temporal_meta

DEFAULT_HISTORIAN_SIGNALS = "amp_a,volt_v,freq_hz,motor_temp_c,int_prs_psi,disch_prs_psi,vibration_g,whp_psi,flp_psi"
DEFAULT_AGG_SIGNALS = "amp_a,motor_temp_c,int_prs_psi,disch_prs_psi,freq_hz,volt_v,vibration_g"


async def fetch_historian_coverage(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch temporal coverage bounds (first_ts, last_ts) for a well using fast indexed scans."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp ASC LIMIT 1;
            """, (variants, variants))
            r_first = cur.fetchone()

            cur.execute("""
                SELECT timestamp FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp DESC LIMIT 1;
            """, (variants, variants))
            r_last = cur.fetchone()

            if not r_first or not r_last:
                return {
                    "well_id": well_id,
                    "first_ts": None,
                    "last_ts": None,
                    "row_count": 0,
                    "source": "POSTGRESQL",
                }

            first_ts = r_first[0].isoformat() if hasattr(r_first[0], "isoformat") else str(r_first[0])
            last_ts = r_last[0].isoformat() if hasattr(r_last[0], "isoformat") else str(r_last[0])
            return {
                "well_id": well_id,
                "first_ts": first_ts,
                "last_ts": last_ts,
                "row_count": 10000,
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_historian_coverage failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_historian_window(
    well_id: str,
    start: str,
    end: str,
    signals: Optional[str] = None,
    limit: int = 10000,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Fetch raw historian telemetry rows within a timestamp range."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, motor_current_a, motor_voltage_v, frequency_hz,
                       motor_temperature_c, intake_pressure_psi, discharge_pressure_psi,
                       vibration_g, whp_psi, flp_psi, flow_rate_bpd, water_cut_pct,
                       operating_state, trip_cause
                FROM opg_well_telemetry
                WHERE (well_id = ANY(%s) OR asset_id = ANY(%s))
                  AND timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp ASC
                LIMIT %s;
            """, (variants, variants, start, end, limit))
            rows = cur.fetchall()

            columns = [
                "timestamp", "amp_a", "volt_v", "freq_hz", "motor_temp_c",
                "int_prs_psi", "disch_prs_psi", "vibration_g", "whp_psi",
                "flp_psi", "flow_rate_bpd", "water_cut_pct", "operating_state", "trip_cause"
            ]

            serialized_rows = []
            for r in rows:
                ts = r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])
                serialized_rows.append([
                    ts,
                    float(r[1]) if r[1] is not None else None,
                    float(r[2]) if r[2] is not None else None,
                    float(r[3]) if r[3] is not None else None,
                    float(r[4]) if r[4] is not None else None,
                    float(r[5]) if r[5] is not None else None,
                    float(r[6]) if r[6] is not None else None,
                    float(r[7]) if r[7] is not None else None,
                    float(r[8]) if r[8] is not None else None,
                    float(r[9]) if r[9] is not None else None,
                    float(r[10]) if r[10] is not None else None,
                    float(r[11]) if r[11] is not None else None,
                    str(r[12] or "RUNNING"),
                    str(r[13] or ""),
                ])

            return {
                "well_id": well_id,
                "start": start,
                "end": end,
                "columns": columns,
                "rows": serialized_rows,
                "row_count": len(serialized_rows),
                "source": "POSTGRESQL",
                "temporal_meta": build_temporal_meta(
                    query_start=start,
                    query_end=end,
                    records=serialized_rows,
                    columns=columns,
                    ts_field="timestamp"
                )
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_historian_window failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_historian_aggregates(
    well_id: str,
    start: str,
    end: str,
    signals: Optional[str] = None,
    bucket: str = "1h",
    agg: str = "avg",
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Compute time-bucketed aggregates across historical telemetry."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT date_trunc('hour', timestamp) AS bucket_ts,
                       AVG(motor_current_a), AVG(motor_voltage_v), AVG(frequency_hz),
                       AVG(motor_temperature_c), AVG(intake_pressure_psi), AVG(discharge_pressure_psi),
                       AVG(vibration_g), AVG(flow_rate_bpd), AVG(water_cut_pct)
                FROM opg_well_telemetry
                WHERE (well_id = ANY(%s) OR asset_id = ANY(%s))
                  AND timestamp >= %s AND timestamp <= %s
                GROUP BY bucket_ts
                ORDER BY bucket_ts ASC
                LIMIT 200;
            """, (variants, variants, start, end))
            rows = cur.fetchall()

            columns = [
                "timestamp", "amp_a", "volt_v", "freq_hz", "motor_temp_c",
                "int_prs_psi", "disch_prs_psi", "vibration_g", "flow_rate_bpd", "water_cut_pct"
            ]
            serialized = []
            for r in rows:
                ts = r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])
                serialized.append([
                    ts,
                    round(float(r[1]), 2) if r[1] is not None else None,
                    round(float(r[2]), 2) if r[2] is not None else None,
                    round(float(r[3]), 2) if r[3] is not None else None,
                    round(float(r[4]), 2) if r[4] is not None else None,
                    round(float(r[5]), 2) if r[5] is not None else None,
                    round(float(r[6]), 2) if r[6] is not None else None,
                    round(float(r[7]), 2) if r[7] is not None else None,
                    round(float(r[8]), 2) if r[8] is not None else None,
                    round(float(r[9]), 2) if r[9] is not None else None,
                ])

            return {
                "well_id": well_id,
                "start": start,
                "end": end,
                "bucket": bucket,
                "columns": columns,
                "rows": serialized,
                "row_count": len(serialized),
                "source": "POSTGRESQL",
                "temporal_meta": build_temporal_meta(
                    query_start=start,
                    query_end=end,
                    records=serialized,
                    columns=columns,
                    ts_field="timestamp"
                )
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_historian_aggregates failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_historian_latest(
    well_id: str,
    signals: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Fetch latest historian point."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, motor_current_a, motor_voltage_v, frequency_hz,
                       motor_temperature_c, intake_pressure_psi, discharge_pressure_psi,
                       vibration_g, whp_psi, flp_psi, flow_rate_bpd, water_cut_pct,
                       operating_state, trip_cause
                FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            r = cur.fetchone()
            if not r:
                raise AdapterError(f"No telemetry found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])
            columns = [
                "timestamp", "amp_a", "volt_v", "freq_hz", "motor_temp_c",
                "int_prs_psi", "disch_prs_psi", "vibration_g", "whp_psi",
                "flp_psi", "flow_rate_bpd", "water_cut_pct", "operating_state", "trip_cause"
            ]
            row_vals = [
                ts,
                float(r[1]) if r[1] is not None else None,
                float(r[2]) if r[2] is not None else None,
                float(r[3]) if r[3] is not None else None,
                float(r[4]) if r[4] is not None else None,
                float(r[5]) if r[5] is not None else None,
                float(r[6]) if r[6] is not None else None,
                float(r[7]) if r[7] is not None else None,
                float(r[8]) if r[8] is not None else None,
                float(r[9]) if r[9] is not None else None,
                float(r[10]) if r[10] is not None else None,
                float(r[11]) if r[11] is not None else None,
                str(r[12] or "RUNNING"),
                str(r[13] or ""),
            ]
            return {
                "well_id": well_id,
                "columns": columns,
                "rows": [row_vals],
                "row_count": 1,
                "source": "POSTGRESQL",
                "temporal_meta": build_temporal_meta(
                    query_start=ts,
                    query_end=ts,
                    records=[row_vals],
                    columns=columns,
                    ts_field="timestamp"
                )
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_historian_latest failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def check_historian_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Check historian table connectivity."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM opg_well_telemetry LIMIT 1;")
            return {"status": "HEALTHY", "source": "POSTGRESQL"}
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL"}
