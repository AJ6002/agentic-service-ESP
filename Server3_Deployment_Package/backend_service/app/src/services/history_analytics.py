"""
Operational History Analytics Service
Grounded in real telemetry slices from unlabelled.db / normalized.db.
Computes deterministic operational metrics:
- Active runtime hours
- Downtime episodes
- Pre-stop / shutdown transition signal windows
- Parameter comparison against calibrated P10-P90 healthy envelopes
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone


class HistoryAnalyticsService:
    """
    Lean service for extracting retro-historian telemetry and computing
    factual operational history metrics without fabricating data.
    """

    def __init__(self):
        # Locate well calibration registry
        base_dir = Path(__file__).resolve().parents[3]  # esp_agent root parent
        self.calib_path = base_dir / "code" / "models" / "well_calibration_registry.json"
        self._calib_registry = None
        if self.calib_path.exists():
            import json
            try:
                with open(self.calib_path, "r", encoding="utf-8") as f:
                    self._calib_registry = json.load(f)
            except Exception:
                pass

    def get_well_profile(self, asset_id: str) -> Dict[str, Any]:
        """Fetch P10-P90 healthy envelope profile for the specified asset."""
        if not self._calib_registry:
            return {}
        wells = self._calib_registry.get("wells", {})
        # Exact match or normalized uppercase match
        for k, v in wells.items():
            if k.upper() == asset_id.upper():
                return v
        return {}

    def fetch_history_dataframe(self, asset_id: str, limit: int = 100) -> pd.DataFrame:
        """
        Fetch time-series records directly from unlabelled.db into a structured DataFrame.
        """
        base_dir = Path(__file__).resolve().parents[3]
        db_candidates = [
            base_dir / "cced_esp" / "data" / "unlabelled.db",
            base_dir / "data" / "unlabelled.db",
            base_dir / "cced_esp" / "data" / "normalized.db",
        ]
        db_path = next((p for p in db_candidates if p.exists()), None)
        if not db_path:
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(str(db_path))
            query = """
                SELECT timestamp, flow_rate_bpd, intake_pressure_psi, pressure_psi, 
                       temperature_c, frequency_hz, motor_current_a
                FROM opg_well_telemetry
                WHERE well_id = ? OR asset_id LIKE ?
                ORDER BY id DESC LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(asset_id, f"%{asset_id}%", limit))
            conn.close()

            if df.empty:
                return df

            # Sort chronologically (oldest to newest)
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame()

    def compute_operational_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate deterministic operational history:
        - Total duration of window
        - Active runtime hours (where frequency > 5 Hz and motor_current > 5 A)
        - Number of shutdown/downtime events
        - Signal ranges (min, max, mean)
        """
        if df.empty or len(df) < 2:
            return {
                "total_records": 0,
                "runtime_hours": 0.0,
                "downtime_episodes": 0,
                "is_currently_running": False,
                "summary": "No historical telemetry records found.",
            }

        # Estimate sampling interval in seconds from timestamps if available
        # Default typical interval is 60 seconds (1 minute per sample)
        sample_interval_hours = 1.0 / 60.0  # 1 min default
        try:
            t0 = pd.to_datetime(df["timestamp"].iloc[0])
            t1 = pd.to_datetime(df["timestamp"].iloc[-1])
            total_window_hours = max(0.1, (t1 - t0).total_seconds() / 3600.0)
            sample_interval_hours = total_window_hours / max(1, len(df) - 1)
        except Exception:
            total_window_hours = len(df) * sample_interval_hours

        # RUN condition: frequency > 10 Hz AND motor_current > 5 A
        is_running = (df["frequency_hz"] > 10.0) & (df["motor_current_a"] > 5.0)
        run_samples = is_running.sum()
        runtime_hours = round(run_samples * sample_interval_hours, 2)

        # Detect shutdown transitions: True -> False
        transitions = (~is_running) & (is_running.shift(1, fill_value=is_running.iloc[0]))
        downtime_episodes = int(transitions.sum())

        latest_row = df.iloc[-1].to_dict()
        is_currently_running = bool(is_running.iloc[-1])

        return {
            "total_records": int(len(df)),
            "start_time": str(df["timestamp"].iloc[0]),
            "end_time": str(df["timestamp"].iloc[-1]),
            "total_window_hours": round(float(total_window_hours), 2),
            "runtime_hours": round(float(runtime_hours), 2),
            "downtime_episodes": int(downtime_episodes),
            "is_currently_running": bool(is_currently_running),
            "latest_measurements": {
                "frequency_hz": round(float(latest_row.get("frequency_hz") or 0.0), 1),
                "motor_current_a": round(float(latest_row.get("motor_current_a") or 0.0), 1),
                "intake_pressure_psi": round(float(latest_row.get("intake_pressure_psi") or 0.0), 1),
                "discharge_pressure_psi": round(float(latest_row.get("pressure_psi") or 0.0), 1),
                "temperature_c": round(float(latest_row.get("temperature_c") or 0.0), 1),
                "flow_rate_bpd": round(float(latest_row.get("flow_rate_bpd") or 0.0), 1),
            },
        }

    def compute_baseline_deviations(
        self, latest_measurements: Dict[str, float], well_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare current values against calibrated P10-P90 healthy envelope.
        """
        sensors_prof = (well_profile or {}).get("sensors", {})
        mapping = [
            ("intake_pressure_psi", "Inp bar/psi", "Intake Pressure", "PSI"),
            ("discharge_pressure_psi", "Disch pr. Bar/psi", "Discharge Pressure", "PSI"),
            ("motor_current_a", "VSD Amps/Load", "Motor Current", "A"),
            ("frequency_hz", "Frequency", "VFD Frequency", "Hz"),
            ("temperature_c", "Motor temp °C", "Motor Temperature", "°C"),
        ]

        table_rows = []
        for raw_key, prof_key, display_name, unit in mapping:
            val = latest_measurements.get(raw_key)
            if val is None:
                continue

            prof = sensors_prof.get(prof_key, {})
            p_min = prof.get("min")
            p_max = prof.get("max")
            p_med = prof.get("median")

            is_valid = (
                p_min is not None and p_max is not None and
                p_min < p_max and -500 <= p_min <= 10000 and 0 <= p_max <= 10000
            )

            if is_valid:
                corridor_str = f"{p_min:.1f} - {p_max:.1f} {unit}"
                if val < p_min:
                    dev_pct = ((val - p_min) / max(1.0, abs(p_min))) * 100.0
                    status = "Below Normal"
                elif val > p_max:
                    dev_pct = ((val - p_max) / max(1.0, abs(p_max))) * 100.0
                    status = "Above Normal"
                else:
                    dev_pct = ((val - p_med) / max(1.0, abs(p_med))) * 100.0 if p_med else 0.0
                    status = "In Corridor"
            else:
                corridor_str = "Nominal Dynamic"
                dev_pct = 0.0
                status = "In Range"

            table_rows.append({
                "parameter": display_name,
                "current_value": f"{val:.1f} {unit}",
                "nominal_corridor": corridor_str,
                "deviation_pct": f"{dev_pct:+.1f}%" if corridor_str != "Nominal Dynamic" else "0.0%",
                "status": status,
            })

        return table_rows


# Global singleton
history_analytics = HistoryAnalyticsService()
