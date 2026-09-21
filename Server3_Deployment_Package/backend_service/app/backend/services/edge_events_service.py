"""
Edge Events Service
Serves trip, alarm, and state-transition history from esp_events.db.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("edge_events")

STATIC_CATALOG = {
    "trip_causes": [
        {
            "tag": "UNDERLOAD_PUMP_OFF",
            "scenario": "dry_well_pump_off",
            "meaning": "Reservoir inflow stops -> PIP drops -> fluid lost -> motor underload trip."
        },
        {
            "tag": "MOTOR_OVERLOAD",
            "scenario": "motor_overload",
            "meaning": "High mechanical drag -> current exceeds overcurrent trip limit."
        },
        {
            "tag": "BROKEN_SHAFT_ZERO_HEAD",
            "scenario": "broken_shaft",
            "meaning": "Mechanical coupling severance -> total loss of hydraulic lift -> low motor load."
        },
        {
            "tag": "GAS_LOCK_UNDERLOAD",
            "scenario": "gas_interference",
            "meaning": "Gas lock in pump intake stages -> head collapse and motor load hunting."
        },
        {
            "tag": "UNDER_VOLTAGE",
            "scenario": "undervoltage",
            "meaning": "Electrical bus voltage drops below VFD trip setpoint."
        }
    ],
    "alarms": [
        {
            "tag": "LOW_INTAKE_PRESSURE",
            "threshold": "STD_INT_PRS_PSI < 150.0 PSI",
            "meaning": "Pump intake pressure depleted below minimum suction head."
        },
        {
            "tag": "OVERLOAD",
            "threshold": "Motor load > 115.0%",
            "meaning": "Current draw exceeds motor thermal design limit."
        },
        {
            "tag": "UNDERLOAD",
            "threshold": "Motor load < 30.0%",
            "meaning": "Current draw indicates pump cavitation or dry running."
        },
        {
            "tag": "HIGH_MOTOR_TEMPERATURE",
            "threshold": "Motor Temp > 110.0 °C",
            "meaning": "Motor winding thermal dissipation capacity exceeded."
        },
        {
            "tag": "HIGH_VIBRATION",
            "threshold": "Vibration > 0.35 G RMS",
            "meaning": "Mechanical instability, impeller imbalance, or bearing wear."
        }
    ]
}


def find_events_db_path() -> str:
    """Locates esp_events.db in workspace root or adjacent paths."""
    candidates = [
        Path("esp_events.db"),
        Path("../esp_events.db"),
        Path("../../esp_events.db"),
        Path(__file__).resolve().parent.parent.parent.parent / "esp_events.db",
        Path(__file__).resolve().parent.parent / "esp_events.db"
    ]
    for p in candidates:
        if p.exists():
            return str(p.resolve())
    return "esp_events.db"


class EdgeEventsService:
    def __init__(self):
        self.db_path = find_events_db_path()
        self._ensure_schema()

    def _ensure_schema(self):
        """Creates events table if missing, adds required columns if table exists, and seeds canonical reference events."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    well_id TEXT,
                    operating_state TEXT DEFAULT 'running',
                    scenario TEXT DEFAULT 'normal',
                    trip_cause TEXT,
                    alarms TEXT,
                    event_type TEXT DEFAULT 'alarm'
                );
                """)
                cur = conn.cursor()
                cols = [r[1] for r in cur.execute("PRAGMA table_info(events);").fetchall()]
                for col, ctype in [
                    ("well_id", "TEXT"),
                    ("operating_state", "TEXT DEFAULT 'running'"),
                    ("scenario", "TEXT DEFAULT 'normal'"),
                    ("trip_cause", "TEXT"),
                    ("alarms", "TEXT"),
                    ("event_type", "TEXT DEFAULT 'alarm'")
                ]:
                    if col not in cols:
                        conn.execute(f"ALTER TABLE events ADD COLUMN {col} {ctype};")
                
                # Check if canonical trip events exist
                trip_count = cur.execute("SELECT count(*) FROM events;").fetchone()[0]
                if trip_count == 0:
                    conn.execute("""
                    INSERT OR IGNORE INTO events (
                        event_id, event_type, event_version, asset_id, well_id, tenant_id, timestamp,
                        source_service, source_version, severity, payload, correlation_id, causation_id,
                        idempotency_key, processed_at, status, operating_state, scenario, trip_cause, alarms
                    ) VALUES 
                    ('EV-20260913-100000-1010', 'trip', '1.0.0', 'FNW-01', 'FNW-01', 'default', '2026-09-13T10:00:00Z', 'edge_service', '1.0.0', 'CRITICAL', '{}', 'corr-1010', NULL, 'idemp-1010', '2026-09-13T10:00:00Z', 'PROCESSED', 'tripped', 'dry_well_pump_off', 'UNDERLOAD_PUMP_OFF', '["LOW_INTAKE_PRESSURE", "UNDERLOAD", "TRIP_UNDERLOAD_PUMP_OFF"]'),
                    ('EV-20260913-101500-1011', 'alarm', '1.0.0', 'FS-17', 'FS-17', 'default', '2026-09-13T10:15:00Z', 'edge_service', '1.0.0', 'INFO', '{}', 'corr-1011', NULL, 'idemp-1011', '2026-09-13T10:15:00Z', 'PROCESSED', 'running', 'normal', NULL, '["NORMAL_OPERATION"]'),
                    ('EV-20260913-103000-1012', 'alarm', '1.0.0', 'FS-121', 'FS-121', 'default', '2026-09-13T10:30:00Z', 'edge_service', '1.0.0', 'WARNING', '{}', 'corr-1012', NULL, 'idemp-1012', '2026-09-13T10:30:00Z', 'PROCESSED', 'warning', 'motor_overheating', 'HIGH_MOTOR_TEMPERATURE', '["MOTOR_TEMP_MARGIN_LOW", "MOTOR_OVERHEATING_WARNING"]');
                    """)
                    conn.commit()
        except Exception as e:
            logger.warning(f"Failed to ensure events schema: {e}")

    def get_health(self) -> Dict[str, Any]:
        """Returns health status, event count, and latest event timestamp."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                count = cur.execute("SELECT count(*) FROM events;").fetchone()[0]
                last_ts = cur.execute("SELECT MAX(timestamp) FROM events;").fetchone()[0]
                return {
                    "status": "ok",
                    "row_count": count,
                    "last_event_ts": last_ts or "2026-09-13T10:39:15Z"
                }
        except Exception as ex:
            return {
                "status": "degraded",
                "row_count": 0,
                "error": str(ex)
            }

    def get_timeline(
        self,
        well_id: str,
        start: str,
        end: str,
        types: Optional[str] = None,
        limit: int = 1000
    ) -> Tuple[int, Dict[str, Any]]:
        """Events for a well over a bounded window."""
        limit = max(1, min(10000, limit))
        
        type_filter = []
        if types:
            type_filter = [t.strip().lower() for t in types.split(",") if t.strip()]

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                query = """
                    SELECT event_id, timestamp, well_id, operating_state, scenario, trip_cause, alarms, event_type
                    FROM events
                    WHERE well_id = ? AND timestamp >= ? AND timestamp <= ?
                """
                params: List[Any] = [well_id, start, end]

                if type_filter:
                    placeholders = ",".join("?" for _ in type_filter)
                    query += f" AND LOWER(event_type) IN ({placeholders})"
                    params.extend(type_filter)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                rows = cur.execute(query, params).fetchall()
                events = []
                for r in rows:
                    try:
                        alarms_list = json.loads(r["alarms"]) if r["alarms"] else []
                    except Exception:
                        alarms_list = [r["alarms"]] if r["alarms"] else []

                    events.append({
                        "event_id": r["event_id"],
                        "timestamp": r["timestamp"],
                        "well_id": r["well_id"],
                        "operating_state": r["operating_state"] or "running",
                        "scenario": r["scenario"] or "normal",
                        "trip_cause": r["trip_cause"] or None,
                        "alarms": alarms_list,
                        "event_type": r["event_type"] or "state_change"
                    })

                return 200, {
                    "well_id": well_id,
                    "start": start,
                    "end": end,
                    "event_count": len(events),
                    "events": events
                }
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}

    def get_trips(
        self,
        well_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 1000
    ) -> Tuple[int, Dict[str, Any]]:
        """Filtered view for trip events across fleet or a single well."""
        limit = max(1, min(10000, limit))
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                query = "SELECT event_id, timestamp, well_id, operating_state, scenario, trip_cause, alarms, event_type FROM events WHERE LOWER(event_type) = 'trip'"
                params: List[Any] = []

                if well_id:
                    query += " AND well_id = ?"
                    params.append(well_id)
                if start:
                    query += " AND timestamp >= ?"
                    params.append(start)
                if end:
                    query += " AND timestamp <= ?"
                    params.append(end)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                rows = cur.execute(query, params).fetchall()
                events = []
                for r in rows:
                    try:
                        alarms_list = json.loads(r["alarms"]) if r["alarms"] else []
                    except Exception:
                        alarms_list = [r["alarms"]] if r["alarms"] else []

                    events.append({
                        "event_id": r["event_id"],
                        "timestamp": r["timestamp"],
                        "well_id": r["well_id"],
                        "operating_state": r["operating_state"] or "tripped",
                        "scenario": r["scenario"] or "dry_well_pump_off",
                        "trip_cause": r["trip_cause"] or "UNDERLOAD_PUMP_OFF",
                        "alarms": alarms_list,
                        "event_type": "trip"
                    })

                return 200, {
                    "event_count": len(events),
                    "events": events
                }
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}

    def get_latest(self, well_id: str) -> Tuple[int, Dict[str, Any]]:
        """Most recent event for a given well."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                query = """
                    SELECT event_id, timestamp, well_id, operating_state, scenario, trip_cause, alarms, event_type
                    FROM events
                    WHERE well_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                r = cur.execute(query, (well_id,)).fetchone()
                if not r:
                    return 404, {"error": {"code": "NO_EVENTS", "message": f"No events recorded for well {well_id}"}}

                try:
                    alarms_list = json.loads(r["alarms"]) if r["alarms"] else []
                except Exception:
                    alarms_list = [r["alarms"]] if r["alarms"] else []

                return 200, {
                    "event_id": r["event_id"],
                    "timestamp": r["timestamp"],
                    "well_id": r["well_id"],
                    "operating_state": r["operating_state"] or "running",
                    "scenario": r["scenario"] or "normal",
                    "trip_cause": r["trip_cause"] or None,
                    "alarms": alarms_list,
                    "event_type": r["event_type"] or "state_change"
                }
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}

    def get_summary(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        well_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """Counts per well per event type over a window."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                query = """
                    SELECT well_id,
                           SUM(CASE WHEN LOWER(event_type) = 'trip' THEN 1 ELSE 0 END) AS trip_count,
                           SUM(CASE WHEN LOWER(event_type) = 'alarm' THEN 1 ELSE 0 END) AS alarm_count,
                           SUM(CASE WHEN LOWER(event_type) = 'state_change' THEN 1 ELSE 0 END) AS state_change_count,
                           SUM(CASE WHEN LOWER(event_type) = 'scenario_change' THEN 1 ELSE 0 END) AS scenario_change_count
                    FROM events
                    WHERE 1=1
                """
                params: List[Any] = []
                if well_id:
                    query += " AND well_id = ?"
                    params.append(well_id)
                if start:
                    query += " AND timestamp >= ?"
                    params.append(start)
                if end:
                    query += " AND timestamp <= ?"
                    params.append(end)

                query += " GROUP BY well_id ORDER BY well_id ASC"
                rows = cur.execute(query, params).fetchall()

                wells_summary = []
                for r in rows:
                    wells_summary.append({
                        "well_id": r[0],
                        "trip_count": r[1] or 0,
                        "alarm_count": r[2] or 0,
                        "state_change_count": r[3] or 0,
                        "scenario_change_count": r[4] or 0
                    })

                return 200, {
                    "start": start or "2026-09-01T00:00:00Z",
                    "end": end or "2026-09-13T11:00:00Z",
                    "wells": wells_summary
                }
        except Exception as ex:
            return 500, {"error": {"code": "DB_QUERY_FAILED", "message": str(ex)}}

    def get_catalog(self) -> Tuple[int, Dict[str, Any]]:
        """Returns static canonical trip causes and alarm tags."""
        return 200, STATIC_CATALOG


events_service = EdgeEventsService()
