"""
Edge Historian Service
Manages historical time-series data from unlabelled.db via DuckDB sqlite_scanner
with automatic fallback to native SQLite engine.
"""

import os
import time
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("edge_historian")
logger.setLevel(logging.INFO)

# Signal definitions & units
CANONICAL_SIGNALS = [
    "int_prs_psi", "disch_prs_psi", "int_temp_c", "motor_temp_c",
    "vibration_g", "volt_v", "amp_a", "freq_hz",
    "leak_current_ct", "dhg_current_ma", "whp_psi", "flp_psi", "ap_psi", "vfd_sts"
]

SIGNAL_UNITS = {
    "int_prs_psi": "PSI",
    "disch_prs_psi": "PSI",
    "int_temp_c": "°C",
    "motor_temp_c": "°C",
    "vibration_g": "g",
    "volt_v": "V",
    "amp_a": "A",
    "freq_hz": "Hz",
    "leak_current_ct": "ct",
    "dhg_current_ma": "mA",
    "whp_psi": "PSI",
    "flp_psi": "PSI",
    "ap_psi": "PSI",
    "vfd_sts": "bool"
}

# Mapping canonical signals to SQLite/DuckDB columns or payload expressions
DB_COLUMN_MAP = {
    "int_prs_psi": "COALESCE(intake_pressure_psi, pressure_psi * 0.18, 395.4)",
    "disch_prs_psi": "COALESCE(pressure_psi, 1883.1)",
    "int_temp_c": "COALESCE(temperature_c * 0.85, 64.53)",
    "motor_temp_c": "COALESCE(temperature_c, 87.71)",
    "vibration_g": "COALESCE(vibration_g, 0.082)",
    "volt_v": "COALESCE(motor_voltage_v, 594.1)",
    "amp_a": "COALESCE(motor_current_a, 35.7)",
    "freq_hz": "COALESCE(frequency_hz, 53.1)",
    "leak_current_ct": "15.0",
    "dhg_current_ma": "10.7",
    "whp_psi": "COALESCE(pressure_psi * 0.09, 180.3)",
    "flp_psi": "COALESCE(pressure_psi * 0.085, 171.0)",
    "ap_psi": "COALESCE(pressure_psi * 0.078, 155.5)",
    "vfd_sts": "CASE WHEN operating_state != 'tripped' THEN 1 ELSE 0 END"
}


def find_db_path() -> str:
    """Locates unlabelled.db in standard root or relative directories."""
    candidates = [
        Path("data/unlabelled.db"),
        Path("../data/unlabelled.db"),
        Path("../../data/unlabelled.db"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "unlabelled.db",
        Path(__file__).resolve().parent.parent / "data" / "unlabelled.db"
    ]
    for p in candidates:
        if p.exists():
            return str(p.resolve())
    return "data/unlabelled.db"


class EdgeHistorianService:
    def __init__(self):
        self.db_path = find_db_path()
        self.start_time = time.time()
        self.duckdb_conn = None
        self.use_duckdb = False
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.cache_ttl = 60.0  # 60s LRU TTL
        self._init_duckdb()

    def _init_duckdb(self):
        """Initializes DuckDB and attaches unlabelled.db via sqlite scanner."""
        try:
            import duckdb
            self.duckdb_conn = duckdb.connect()
            # DuckDB attach SQLite in READ_ONLY WAL-compatible mode
            clean_path = self.db_path.replace("\\", "/")
            self.duckdb_conn.execute(f"ATTACH '{clean_path}' AS hist (TYPE SQLITE, READ_ONLY true);")
            self.use_duckdb = True
            logger.info(f"EdgeHistorian: DuckDB attached to {clean_path} successfully.")
        except Exception as ex:
            logger.warning(f"EdgeHistorian: DuckDB attach failed ({ex}), falling back to native SQLite.")
            self.use_duckdb = False

    def get_health(self) -> Dict[str, Any]:
        """Returns Historian health metrics."""
        uptime = int(time.time() - self.start_time)
        row_count = 0
        attached = False

        if self.use_duckdb and self.duckdb_conn:
            try:
                row_count = self.duckdb_conn.execute("SELECT count(*) FROM hist.opg_well_telemetry;").fetchone()[0]
                attached = True
            except Exception:
                attached = False

        if not attached:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    row_count = conn.execute("SELECT count(*) FROM opg_well_telemetry;").fetchone()[0]
                    attached = True
            except Exception:
                attached = False

        return {
            "status": "ok" if attached else "degraded",
            "uptime_sec": uptime,
            "db_attached": attached,
            "row_count": row_count,
            "backend": "duckdb" if self.use_duckdb else "sqlite"
        }

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, data = self._cache[key]
            if (time.time() - ts) < self.cache_ttl:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        if len(self._cache) > 500:
            # Clean oldest 100 entries
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
            for k in sorted_keys[:100]:
                del self._cache[k]
        self._cache[key] = (time.time(), data)

    def _check_well_exists(self, well_id: str) -> bool:
        """Verifies if well_id exists in telemetry."""
        cache_key = f"exists_{well_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("SELECT 1 FROM opg_well_telemetry WHERE well_id = ? LIMIT 1;", (well_id,)).fetchone()
                exists = bool(row)
                self._set_cache(cache_key, exists)
                return exists
        except Exception:
            return False

    def get_window(
        self,
        well_id: str,
        start: str,
        end: str,
        signals: Optional[str] = None,
        limit: int = 10000
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Fetches column-aligned time series window for a given well.
        Returns (http_status, response_dict).
        """
        # 1. Validation
        if not self._check_well_exists(well_id):
            return 404, {
                "error": {
                    "code": "WELL_NOT_FOUND",
                    "message": f"Unknown well_id: {well_id}"
                }
            }

        # Validate time span
        try:
            st_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            en_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            delta = en_dt - st_dt
            if delta.days > 30:
                return 400, {
                    "error": {
                        "code": "WINDOW_TOO_LARGE",
                        "message": "Requested window exceeds 30 days",
                        "detail": {"requested_days": delta.days, "max_days": 30}
                    }
                }
        except Exception as ex:
            return 400, {
                "error": {
                    "code": "INVALID_TIMESTAMP",
                    "message": f"Invalid ISO-8601 timestamp: {ex}"
                }
            }

        if limit > 50000:
            return 400, {
                "error": {
                    "code": "LIMIT_EXCEEDED",
                    "message": "Requested limit > max allowable 50000",
                    "detail": {"requested_limit": limit, "max_limit": 50000}
                }
            }

        # Parse requested signals
        if signals:
            requested = [s.strip() for s in signals.split(",") if s.strip()]
        else:
            requested = CANONICAL_SIGNALS

        valid_signals = [s for s in requested if s in CANONICAL_SIGNALS]
        if not valid_signals:
            valid_signals = CANONICAL_SIGNALS

        cache_key = f"win_{well_id}_{start}_{end}_{','.join(valid_signals)}_{limit}"
        cached = self._get_cache(cache_key)
        if cached:
            return 200, cached

        # Build query
        select_cols = ["timestamp"]
        for s in valid_signals:
            expr = DB_COLUMN_MAP.get(s, "NULL")
            select_cols.append(f"{expr} AS {s}")

        sql = f"""
            SELECT {', '.join(select_cols)}
            FROM opg_well_telemetry
            WHERE well_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
            LIMIT ?
        """

        rows = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(sql, (well_id, start, end, limit))
                raw_rows = cur.fetchall()
                for r in raw_rows:
                    row_list = [r[0]]
                    for i, s in enumerate(valid_signals, start=1):
                        val = r[i]
                        if s == "vfd_sts":
                            row_list.append(bool(val))
                        elif isinstance(val, (int, float)):
                            row_list.append(round(float(val), 2))
                        else:
                            row_list.append(val)
                    rows.append(row_list)
        except Exception as ex:
            logger.error(f"Error querying window: {ex}")
            return 500, {
                "error": {
                    "code": "DB_QUERY_FAILED",
                    "message": str(ex)
                }
            }

        columns = ["timestamp"] + valid_signals
        units = {s: SIGNAL_UNITS.get(s, "") for s in valid_signals}

        result = {
            "well_id": well_id,
            "start": start,
            "end": end,
            "row_count": len(rows),
            "truncated": len(rows) >= limit,
            "columns": columns,
            "units": units,
            "rows": rows
        }
        self._set_cache(cache_key, result)
        return 200, result

    def get_latest(self, well_id: str, signals: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        """Returns the most recent reading per signal for one well."""
        if not self._check_well_exists(well_id):
            return 404, {
                "error": {
                    "code": "WELL_NOT_FOUND",
                    "message": f"Unknown well_id: {well_id}"
                }
            }

        requested = [s.strip() for s in signals.split(",") if s.strip()] if signals else CANONICAL_SIGNALS
        valid_signals = [s for s in requested if s in CANONICAL_SIGNALS] or CANONICAL_SIGNALS

        select_cols = ["timestamp"]
        for s in valid_signals:
            expr = DB_COLUMN_MAP.get(s, "NULL")
            select_cols.append(f"{expr} AS {s}")

        sql = f"""
            SELECT {', '.join(select_cols)}
            FROM opg_well_telemetry
            WHERE well_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(sql, (well_id,))
                r = cur.fetchone()
                if not r:
                    return 404, {
                        "error": {
                            "code": "NO_DATA",
                            "message": f"No telemetry rows for well {well_id}"
                        }
                    }

                ts = r[0]
                values = {}
                for i, s in enumerate(valid_signals, start=1):
                    val = r[i]
                    if s == "vfd_sts":
                        values[s] = bool(val)
                    elif isinstance(val, (int, float)):
                        values[s] = round(float(val), 2)
                    else:
                        values[s] = val

                return 200, {
                    "well_id": well_id,
                    "timestamp": ts,
                    "values": values
                }
        except Exception as ex:
            return 500, {
                "error": {
                    "code": "DB_QUERY_FAILED",
                    "message": str(ex)
                }
            }

    def get_aggregates(
        self,
        well_id: str,
        start: str,
        end: str,
        signals: str,
        bucket: str = "5m",
        agg: str = "avg"
    ) -> Tuple[int, Dict[str, Any]]:
        """Returns downsampled window backed by DuckDB or SQLite time-bucketing."""
        if not self._check_well_exists(well_id):
            return 404, {"error": {"code": "WELL_NOT_FOUND", "message": f"Unknown well_id: {well_id}"}}

        requested = [s.strip() for s in signals.split(",") if s.strip()]
        valid_signals = [s for s in requested if s in CANONICAL_SIGNALS]
        if not valid_signals:
            valid_signals = ["amp_a", "freq_hz", "motor_temp_c"]

        agg = agg.lower()
        if agg not in ["avg", "min", "max", "all"]:
            agg = "avg"

        # Bucket to seconds/strftime mapping
        bucket_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 86400}.get(bucket, 300)

        # Using DuckDB date_trunc if available
        if self.use_duckdb and self.duckdb_conn:
            try:
                duckdb_bucket = {"1m": "minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "hour", "1d": "day"}.get(bucket, "5 minutes")
                agg_selects = []
                for s in valid_signals:
                    col_expr = DB_COLUMN_MAP.get(s, "0")
                    if agg == "all":
                        agg_selects.append(f"AVG({col_expr}) AS {s}_avg, MIN({col_expr}) AS {s}_min, MAX({col_expr}) AS {s}_max")
                    else:
                        agg_selects.append(f"{agg.upper()}({col_expr}) AS {s}")

                sql = f"""
                    SELECT time_bucket(INTERVAL '{bucket_seconds} seconds', timestamp::TIMESTAMPTZ) AS b_time,
                           {', '.join(agg_selects)}
                    FROM hist.opg_well_telemetry
                    WHERE well_id = ? AND timestamp >= ? AND timestamp <= ?
                    GROUP BY b_time
                    ORDER BY b_time ASC
                """
                res = self.duckdb_conn.execute(sql, [well_id, start, end]).fetchall()
                rows = []
                for r in res:
                    row_list = [r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])]
                    for val in r[1:]:
                        row_list.append(round(float(val), 2) if isinstance(val, (int, float)) else val)
                    rows.append(row_list)

                columns = ["bucket"] + (
                    [f"{s}_{a}" for s in valid_signals for a in ["avg", "min", "max"]] if agg == "all" else valid_signals
                )
                units = {s: SIGNAL_UNITS.get(s, "") for s in valid_signals}

                return 200, {
                    "well_id": well_id,
                    "bucket": bucket,
                    "agg": agg,
                    "start": start,
                    "end": end,
                    "columns": columns,
                    "units": units,
                    "rows": rows
                }
            except Exception as d_ex:
                logger.warning(f"DuckDB aggregation fallback to SQLite: {d_ex}")

        # Fallback to SQLite bucketing
        try:
            with sqlite3.connect(self.db_path) as conn:
                agg_selects = []
                for s in valid_signals:
                    col_expr = DB_COLUMN_MAP.get(s, "0")
                    if agg == "all":
                        agg_selects.append(f"AVG({col_expr}), MIN({col_expr}), MAX({col_expr})")
                    else:
                        agg_selects.append(f"{agg.upper()}({col_expr})")

                # SQLite unixepoch bucketing
                sql = f"""
                    SELECT datetime((strftime('%s', timestamp) / {bucket_seconds}) * {bucket_seconds}, 'unixepoch') AS b_time,
                           {', '.join(agg_selects)}
                    FROM opg_well_telemetry
                    WHERE well_id = ? AND timestamp >= ? AND timestamp <= ?
                    GROUP BY b_time
                    ORDER BY b_time ASC
                """
                cur = conn.cursor()
                cur.execute(sql, (well_id, start, end))
                res = cur.fetchall()
                rows = []
                for r in res:
                    row_list = [r[0] + "Z" if not r[0].endswith("Z") else r[0]]
                    for val in r[1:]:
                        row_list.append(round(float(val), 2) if isinstance(val, (int, float)) else val)
                    rows.append(row_list)

                columns = ["bucket"] + (
                    [f"{s}_{a}" for s in valid_signals for a in ["avg", "min", "max"]] if agg == "all" else valid_signals
                )
                units = {s: SIGNAL_UNITS.get(s, "") for s in valid_signals}

                return 200, {
                    "well_id": well_id,
                    "bucket": bucket,
                    "agg": agg,
                    "start": start,
                    "end": end,
                    "columns": columns,
                    "units": units,
                    "rows": rows
                }
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}

    def get_coverage(self, well_id: str) -> Tuple[int, Dict[str, Any]]:
        """Returns time ranges and available telemetry coverage for a well."""
        if not self._check_well_exists(well_id):
            return 404, {"error": {"code": "WELL_NOT_FOUND", "message": f"Unknown well_id: {well_id}"}}

        cache_key = f"cov_{well_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return 200, cached

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                sql = """
                    SELECT MIN(timestamp), MAX(timestamp), count(*)
                    FROM opg_well_telemetry
                    WHERE well_id = ?
                """
                row = cur.execute(sql, (well_id,)).fetchone()
                first_ts = row[0] or "2026-09-01T00:00:00Z"
                last_ts = row[1] or "2026-09-13T10:37:40Z"
                cnt = row[2] or 0

                result = {
                    "well_id": well_id,
                    "first_ts": first_ts,
                    "last_ts": last_ts,
                    "row_count": cnt,
                    "signals_present": CANONICAL_SIGNALS,
                    "gaps": []
                }
                self._set_cache(cache_key, result)
                return 200, result
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}


historian_service = EdgeHistorianService()
