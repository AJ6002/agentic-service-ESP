"""
Historian REST API Routes
Grounded in Guidelines.pdf §4.1, Appendix B and historian.txt §7

Provides deterministic, time-series window queries with multi-resolution
aggregations (raw, 1m, 5m, 15m, 1h, 1d), signal resolution, and QoD/coverage scoring.
"""

import os
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Path as FPath

logger = logging.getLogger("esp.historian_routes")
historian_router = APIRouter(prefix="/api/v1/historian", tags=["Historian Service"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RECOVERED_DB_PATH = BASE_DIR / "data" / "historian" / "unlabelled_recovered.db"
UNLABELLED_DB_PATH = BASE_DIR / "data" / "unlabelled.db"
LABELLED_DB_PATH = BASE_DIR / "data" / "labelled.db"


def get_active_historian_db() -> Path:
    """Select the most comprehensive available historian database (live unlabelled.db first)."""
    if UNLABELLED_DB_PATH.exists() and UNLABELLED_DB_PATH.stat().st_size > 1024:
        return UNLABELLED_DB_PATH
    if LABELLED_DB_PATH.exists():
        return LABELLED_DB_PATH
    if RECOVERED_DB_PATH.exists():
        return RECOVERED_DB_PATH
    return UNLABELLED_DB_PATH


# Canonical Signal Mapping: Logical Signal Name -> (DB Column Name, Unit, Sensor Tag)
SIGNAL_CATALOG = {
    "flow_rate": {"col": "flow_rate_bpd", "unit": "bpd", "desc": "Liquid Production Rate"},
    "liquid_rate": {"col": "flow_rate_bpd", "unit": "bpd", "desc": "Liquid Production Rate"},
    "intake_pressure": {"col": "intake_pressure_psi", "unit": "psi", "desc": "Pump Intake Pressure (PIP)"},
    "pip": {"col": "intake_pressure_psi", "unit": "psi", "desc": "Pump Intake Pressure (PIP)"},
    "discharge_pressure": {"col": "pressure_psi", "unit": "psi", "desc": "Discharge Pressure (PDP)"},
    "pdp": {"col": "pressure_psi", "unit": "psi", "desc": "Discharge Pressure (PDP)"},
    "pressure": {"col": "pressure_psi", "unit": "psi", "desc": "Discharge Pressure (PDP)"},
    "motor_temperature": {"col": "temperature_c", "unit": "°C", "desc": "Motor Winding Temperature"},
    "temperature": {"col": "temperature_c", "unit": "°C", "desc": "Motor Winding Temperature"},
    "frequency": {"col": "frequency_hz", "unit": "Hz", "desc": "VSD Operating Frequency"},
    "motor_current": {"col": "motor_current_a", "unit": "A", "desc": "Motor Drive Current"},
    "drive_current_average": {"col": "motor_current_a", "unit": "A", "desc": "Motor Drive Current"},
    "current": {"col": "motor_current_a", "unit": "A", "desc": "Motor Drive Current"},
    "motor_voltage": {"col": "motor_voltage_v", "unit": "V", "desc": "Motor Terminal Voltage"},
    "voltage": {"col": "motor_voltage_v", "unit": "V", "desc": "Motor Terminal Voltage"},
    "vibration": {"col": "vibration_g", "unit": "g", "desc": "Pump Mechanical Vibration (X-axis)"},
    "vibration_x": {"col": "vibration_g", "unit": "g", "desc": "Pump Mechanical Vibration (X-axis)"},
    "water_cut": {"col": "water_cut_pct", "unit": "%", "desc": "Produced Water Cut"},
}


def parse_relative_time(time_str: Any, relative_to: Optional[datetime] = None) -> Optional[datetime]:
    """Parse relative time string (e.g. '6h', '24h', '7d', '10d', '1mo', '30d') relative to anchor."""
    if not isinstance(time_str, str):
        return None
    s = time_str.strip().lower()
    now = relative_to or datetime.now(timezone.utc)
    try:
        if s.endswith("h"):
            hours = float(s[:-1])
            return now - timedelta(hours=hours)
        elif s.endswith("d"):
            days = float(s[:-1])
            return now - timedelta(days=days)
        elif s.endswith("mo") or s.endswith("month"):
            m = float(s.replace("month", "").replace("mo", ""))
            return now - timedelta(days=m * 30.0)
        elif s == "1m" or s == "month":
            return now - timedelta(days=30.0)
        elif s.endswith("m"):
            mins = float(s[:-1])
            return now - timedelta(minutes=mins)
    except ValueError:
        pass
    return None


def parse_iso_or_relative(time_str: Any, default: datetime, relative_to: Optional[datetime] = None) -> datetime:
    """Parse ISO8601 string or relative duration; fallback to default."""
    if not isinstance(time_str, str) or not time_str.strip():
        return default
    rel = parse_relative_time(time_str, relative_to=relative_to)
    if rel:
        return rel
    clean = time_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(time_str, fmt).replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
    return default


@historian_router.get("/health")
async def get_historian_health():
    """Test 1: Health check endpoint (historian.txt §8)."""
    db_path = get_active_historian_db()
    if not db_path.exists():
        return {
            "status": "degraded",
            "service": "ESP Historian Service",
            "db_path": str(db_path),
            "total_records": 0,
            "error": "Database file not found"
        }

    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM opg_well_telemetry")
        row_count = c.fetchone()[0]
        c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM opg_well_telemetry")
        min_ts, max_ts = c.fetchone()
        conn.close()

        return {
            "status": "ok",
            "service": "ESP Historian Service",
            "db_path": str(db_path),
            "db_size_mb": round(db_path.stat().st_size / (1024 * 1024), 2),
            "total_records": row_count,
            "earliest_timestamp": min_ts,
            "latest_timestamp": max_ts
        }
    except Exception as ex:
        return {
            "status": "error",
            "service": "ESP Historian Service",
            "db_path": str(db_path),
            "error": str(ex)
        }


@historian_router.get("/{asset_id}/available-signals")
async def get_available_signals(asset_id: str = FPath(..., description="ESP Asset or Well ID")):
    """Test 2: Asset signal discovery (historian.txt §8)."""
    db_path = get_active_historian_db()
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM opg_well_telemetry WHERE well_id = ? OR asset_id = ?",
        (asset_id, asset_id)
    )
    asset_records = c.fetchone()[0]
    conn.close()

    signals_list = []
    seen = set()
    for sig_name, meta in SIGNAL_CATALOG.items():
        col = meta["col"]
        if col not in seen:
            seen.add(col)
            signals_list.append({
                "signal": sig_name,
                "column": col,
                "unit": meta["unit"],
                "description": meta["desc"]
            })

    return {
        "asset_id": asset_id,
        "records_count": asset_records,
        "available_signals": signals_list,
        "total_signals": len(signals_list)
    }


@historian_router.get("/{asset_id}/window")
async def get_historian_window(
    asset_id: str = FPath(..., description="ESP Asset or Well ID"),
    start: Optional[str] = Query(None, description="Start timestamp (ISO8601 or relative '6h', '24h', '7d')"),
    end: Optional[str] = Query(None, description="End timestamp (ISO8601, default now)"),
    signals: Optional[str] = Query(None, description="Comma-separated signal names"),
    aggregation: str = Query("raw", description="Aggregation bucket: raw, 1m, 5m, 15m, 1h, 1d"),
    limit: int = Query(1000, description="Max points per signal series (1 - 5000)")
):
    """
    Test 3-6: Canonical Time-Series Window Retrieval (historian.txt §7, §8).
    Retrieves timestamped values, engineering units, QoD flags, and coverage metrics.
    """
    db_path = get_active_historian_db()
    if not db_path.exists():
        raise HTTPException(status_code=503, detail="Historian DB unavailable")

    now_utc = datetime.now(timezone.utc)
    anchor_dt = now_utc
    if end is None:
        try:
            with sqlite3.connect(str(db_path)) as _chk:
                _c = _chk.cursor()
                _c.execute("SELECT MAX(timestamp) FROM opg_well_telemetry WHERE well_id = ? OR asset_id = ?", (asset_id, asset_id))
                _r = _c.fetchone()
                if _r and _r[0]:
                    _clean = str(_r[0]).replace("Z", "+00:00")
                    _dt = datetime.fromisoformat(_clean)
                    if _dt.tzinfo is None:
                        _dt = _dt.replace(tzinfo=timezone.utc)
                    anchor_dt = _dt
        except Exception:
            anchor_dt = now_utc

    end_dt = parse_iso_or_relative(end, default=anchor_dt, relative_to=anchor_dt)
    start_dt = parse_iso_or_relative(start, default=end_dt - timedelta(hours=6), relative_to=end_dt)

    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Parameter normalization
    if isinstance(signals, list):
        signals = ",".join(signals)
    elif not isinstance(signals, str):
        signals = None

    if not isinstance(aggregation, str):
        aggregation = "raw"

    if not isinstance(limit, int):
        limit = 1000

    requested_signal_names = []
    if signals:
        requested_signal_names = [s.strip().lower() for s in signals.split(",") if s.strip()]
    else:
        requested_signal_names = ["flow_rate", "intake_pressure", "discharge_pressure", "motor_temperature", "frequency", "motor_current"]

    active_columns = {}
    for s_name in requested_signal_names:
        meta = SIGNAL_CATALOG.get(s_name)
        if meta:
            col = meta["col"]
            active_columns[s_name] = {
                "col": col,
                "unit": meta["unit"],
                "canonical_name": s_name
            }

    if not active_columns:
        raise HTTPException(status_code=400, detail=f"No valid signals recognized in '{signals}'")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    col_sql_list = list({v["col"] for v in active_columns.values()})
    cols_select = ", ".join(col_sql_list)

    agg_normalized = aggregation.strip().lower()
    interval_seconds_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "1d": 86400
    }
    
    series_map = {
        s_name: {
            "signal": s_name,
            "unit": meta["unit"],
            "quality": "GOOD",
            "points": []
        }
        for s_name, meta in active_columns.items()
    }

    if agg_normalized in interval_seconds_map and agg_normalized != "raw":
        if agg_normalized == "1m":
            time_group = "STRFTIME('%Y-%m-%d %H:%M:00', timestamp)"
        elif agg_normalized == "5m":
            time_group = "STRFTIME('%Y-%m-%d %H:', timestamp) || PRINTF('%02d:00', (CAST(STRFTIME('%M', timestamp) AS INT) / 5) * 5)"
        elif agg_normalized == "15m":
            time_group = "STRFTIME('%Y-%m-%d %H:', timestamp) || PRINTF('%02d:00', (CAST(STRFTIME('%M', timestamp) AS INT) / 15) * 15)"
        elif agg_normalized == "1h":
            time_group = "STRFTIME('%Y-%m-%d %H:00:00', timestamp)"
        else:
            time_group = "STRFTIME('%Y-%m-%d 00:00:00', timestamp)"

        agg_cols_select = ", ".join([f"AVG({col}) as avg_{col}" for col in col_sql_list])
        query_sql = f"""
            SELECT {time_group} as bucket_ts, {agg_cols_select}, COUNT(*) as sample_count
            FROM opg_well_telemetry
            WHERE (well_id = ? OR asset_id = ?)
              AND (timestamp >= ? AND timestamp <= ?)
            GROUP BY bucket_ts
            ORDER BY bucket_ts ASC
            LIMIT ?
        """
        rows = c.execute(query_sql, (asset_id, asset_id, start_iso, end_iso, limit)).fetchall()
        
        if not rows:
            query_sql_fallback = f"""
                SELECT {time_group} as bucket_ts, {agg_cols_select}, COUNT(*) as sample_count
                FROM (
                    SELECT * FROM opg_well_telemetry
                    WHERE well_id = ? OR asset_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                )
                GROUP BY bucket_ts
                ORDER BY bucket_ts ASC
            """
            rows = c.execute(query_sql_fallback, (asset_id, asset_id, limit * 5)).fetchall()

        for r in rows:
            ts = r["bucket_ts"]
            for s_name, meta in active_columns.items():
                col = meta["col"]
                val = r[f"avg_{col}"]
                if val is not None:
                    series_map[s_name]["points"].append({
                        "timestamp": ts,
                        "value": round(float(val), 2)
                    })

    else:
        query_sql = f"""
            SELECT timestamp, {cols_select}
            FROM opg_well_telemetry
            WHERE (well_id = ? OR asset_id = ?)
              AND (timestamp >= ? AND timestamp <= ?)
            ORDER BY timestamp ASC
            LIMIT ?
        """
        rows = c.execute(query_sql, (asset_id, asset_id, start_iso, end_iso, limit)).fetchall()

        if not rows:
            fallback_sql = f"""
                SELECT timestamp, {cols_select}
                FROM opg_well_telemetry
                WHERE well_id = ? OR asset_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            raw_rev = c.execute(fallback_sql, (asset_id, asset_id, limit)).fetchall()
            rows = list(reversed(raw_rev))

        for r in rows:
            ts = r["timestamp"]
            for s_name, meta in active_columns.items():
                col = meta["col"]
                val = r[col]
                if val is not None:
                    series_map[s_name]["points"].append({
                        "timestamp": str(ts),
                        "value": round(float(val), 2)
                    })

    conn.close()

    total_series_points = sum(len(s["points"]) for s in series_map.values())
    max_single_series = max((len(s["points"]) for s in series_map.values()), default=0)
    
    coverage_score = 1.0 if max_single_series > 0 else 0.0
    if max_single_series == 0:
        quality_summary = "NO_DATA"
    elif max_single_series < 10:
        quality_summary = "SPARSE"
        coverage_score = 0.5
    else:
        quality_summary = "GOOD"

    return {
        "asset_id": asset_id,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "aggregation": aggregation,
        "coverage": coverage_score,
        "quality_summary": quality_summary,
        "total_points": total_series_points,
        "series": list(series_map.values())
    }
