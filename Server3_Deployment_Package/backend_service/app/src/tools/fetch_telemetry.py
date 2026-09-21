from typing import List, Optional, Dict, Any
from src.adapters.telemetry import TelemetryAdapter
from src.schemas.canonical import TelemetryMetric
from src.schemas.contracts import TimeSeriesPayload, TimeSeriesSignal, TimeSeriesPoint


def fetch_telemetry_tool(telemetry_adapter: TelemetryAdapter, asset_id: str) -> List[TelemetryMetric]:
    """Tool function to fetch and translate telemetry for a given asset."""
    return telemetry_adapter.load_latest_telemetry(asset_id=asset_id)


def get_history_window_tool(
    asset_id: str,
    start_time: Optional[str] = "6h",
    end_time: Optional[str] = None,
    signals: Optional[List[str]] = None,
    aggregation: str = "raw",
    limit: int = 1000
) -> TimeSeriesPayload:
    """
    Typed Agent Tool: historian.get_window(...)
    Grounded in Guidelines.pdf Appendix B & historian.txt §7, §10
    Fetches time-series window with aggregation, quality tagging, and coverage calculation.
    """
    from src.adapters.live_data_bridge import live_bridge
    raw_res = live_bridge.get_historian_window(
        asset_id=asset_id,
        start_time=start_time,
        end_time=end_time,
        signals=signals,
        aggregation=aggregation,
        limit=limit
    )

    if raw_res and "series" in raw_res:
        return TimeSeriesPayload(**raw_res)

    # Resilient local fallback if backend REST is starting up
    import sqlite3
    from pathlib import Path
    from datetime import datetime, timezone, timedelta
    
    _base_dir = Path(__file__).resolve().parents[3]  # root of workspace or esp_agent parent
    db_candidates = [
        _base_dir / "cced_esp" / "data" / "unlabelled.db",
        _base_dir / "data" / "unlabelled.db",
        Path("cced_esp/data/unlabelled.db"),
        Path("../cced_esp/data/unlabelled.db"),
    ]
    target_db = next((p for p in db_candidates if p.exists()), None)
    now_iso = datetime.now(timezone.utc).isoformat()
    
    if not target_db:
        return TimeSeriesPayload(
            asset_id=asset_id,
            start_time=now_iso,
            end_time=now_iso,
            aggregation=aggregation,
            coverage=0.0,
            quality_summary="NO_DATA",
            total_points=0,
            series=[]
        )

    try:
        conn = sqlite3.connect(str(target_db))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute(
            "SELECT timestamp, flow_rate_bpd, intake_pressure_psi, pressure_psi, temperature_c, frequency_hz, motor_current_a FROM opg_well_telemetry WHERE well_id = ? OR asset_id LIKE ? ORDER BY id DESC LIMIT ?",
            (asset_id, f"%{asset_id}%", limit)
        ).fetchall()
        conn.close()

        rev_rows = list(reversed(rows))
        sig_definitions = [
            ("flow_rate", "flow_rate_bpd", "bpd"),
            ("intake_pressure", "intake_pressure_psi", "psi"),
            ("discharge_pressure", "pressure_psi", "psi"),
            ("motor_temperature", "temperature_c", "°C"),
            ("frequency", "frequency_hz", "Hz"),
            ("motor_current", "motor_current_a", "A"),
        ]

        series_list = []
        for s_name, col_name, unit in sig_definitions:
            if signals and s_name not in signals:
                continue
            pts = [
                TimeSeriesPoint(timestamp=str(r["timestamp"]), value=round(float(r[col_name] or 0.0), 2))
                for r in rev_rows if r[col_name] is not None
            ]
            series_list.append(TimeSeriesSignal(
                signal=s_name,
                unit=unit,
                quality="GOOD" if pts else "NO_DATA",
                points=pts
            ))

        return TimeSeriesPayload(
            asset_id=asset_id,
            start_time=rev_rows[0]["timestamp"] if rev_rows else now_iso,
            end_time=rev_rows[-1]["timestamp"] if rev_rows else now_iso,
            aggregation=aggregation,
            coverage=1.0 if rev_rows else 0.0,
            quality_summary="GOOD" if rev_rows else "NO_DATA",
            total_points=sum(len(s.points) for s in series_list),
            series=series_list
        )
    except Exception:
        return TimeSeriesPayload(
            asset_id=asset_id,
            start_time=now_iso,
            end_time=now_iso,
            aggregation=aggregation,
            coverage=0.0,
            quality_summary="ERROR",
            total_points=0,
            series=[]
        )

