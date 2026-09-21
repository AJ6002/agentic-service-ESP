#!/usr/bin/env python3
"""
Test Well Diagnostic Engine on pre-computed normalized.db
==========================================================
Ingests telemetry from cced_esp/data/normalized.db, evaluates it
via WellDiagnosticEngine (Multi-Well Calibration Registry, Physics Extraction,
Multivariate Isolation Forest Anomaly Detection, and 13-Fault Classification Engine),
and outputs the Diagnostic Intelligence Card and structured model payload.
"""

import os
import sys
import argparse
import sqlite3
import json
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "models" else Path(__file__).resolve().parent
CODE_DIR = ROOT_DIR if ROOT_DIR.name == "code" else ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
if str(CODE_DIR / "models") not in sys.path:
    sys.path.insert(0, str(CODE_DIR / "models"))

from models.diagnostic_engine import WellDiagnosticEngine

DEFAULT_DB_PATH = ROOT_DIR / "cced_esp" / "data" / "normalized.db"


def run_model_test(well_id: str = "FS-04", db_path: Path = DEFAULT_DB_PATH, show_json: bool = False, limit: int = 1, target_ts: str = None):
    if not db_path.exists():
        print(f"[-] Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if well_id.upper() == "ALL":
        cursor.execute("SELECT DISTINCT Wells FROM opg_normalized_telemetry ORDER BY Wells")
        wells_to_test = [r[0] for r in cursor.fetchall()]
    else:
        wells_to_test = [well_id]

    engine = WellDiagnosticEngine()

    for w in wells_to_test:
        if target_ts:
            cursor.execute(
                """
                SELECT * FROM opg_normalized_telemetry
                WHERE Wells = ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (w, target_ts, limit)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM opg_normalized_telemetry
                WHERE Wells = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (w, limit)
            )
        rows = cursor.fetchall()
        if not rows:
            print(f"[!] Warning: No telemetry rows found for Well {w}")
            continue

        for row in rows:
            # Map columns back to canonical raw 14 sensor inputs
            raw_data = {
                "Report_DateTime": row["timestamp"],
                "Inp bar/psi": row["Inp bar/psi"],
                "Int temp °C": row["Int temp °C"],
                "Motor temp °C": row["Motor temp °C"],
                "Disch pr. Bar/psi": row["Disch pr. Bar/psi"],
                "Vibration G's-Vx": row["Vibration G's-Vx"],
                "Leak Current Ct": row["Leak Current Ct"],
                "Volt": row["Volt"],
                "VSD Amps/Load": row["VSD Amps/Load"],
                "Frequency": row["Frequency"],
                "DHG Current": row["DHG Current"],
                "WHP (PSI)": row["WHP (PSI)"],
                "FLP (PSI)": row["FLP (PSI)"],
                "AP (PSI)": row["AP (PSI)"],
                "VFD STS": row["VFD STS"],
            }

            # Execute full model pipeline
            result = engine.evaluate_live_telemetry(w, raw_data, verbose=True)

            diag = result["diagnostic"]
            ml_ano = result["ml_anomaly"]
            dyn = result["dynamics"]

            print(" [DETAILED ML MODEL TELEMETRY BREAKDOWN]")
            print(f"  • Isolation Forest Anomaly Probability : {ml_ano['anomaly_probability'] * 100:.1f}% (Outlier: {ml_ano['is_anomaly']})")
            print(f"  • Isolation Forest Decision Score      : {ml_ano['raw_decision_score']}")
            print(f"  • Physics Dynamics Delta-P Head        : {dyn['delta_p']} PSI")
            print(f"  • Physics Dynamics Torque Proxy        : {dyn['torque_proxy']} A/Hz")
            print(f"  • Physics Dynamics Power Load          : {dyn['power_proxy_kva']} kVA")
            print(f"  • Physics Dynamics Thermal Elevation   : {dyn['thermal_elevation']} °C")
            all_sc = diag.get("all_scores", {})
            if all_sc:
                print("\n  • Active Fault Probabilities (>20% threshold):")
                for fault_name, prob in all_sc.items():
                    print(f"    - {fault_name:30s}: {prob}")
            else:
                print("\n  • Active Fault Probabilities: None elevated (Normal Baseline Operation)")

            if show_json:
                print("\n" + "-"*80)
                print("RAW STRUCTURED JSON MODEL OUTPUT:")
                print(json.dumps(result, indent=2, default=str))
                print("-"*80 + "\n")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ML Models on normalized.db")
    parser.add_argument("--well", type=str, default="FS-04", help="Well ID to test (or ALL)")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to normalized.db")
    parser.add_argument("--json", action="store_true", help="Print raw structured JSON dictionary")
    parser.add_argument("--limit", type=int, default=1, help="Number of latest telemetry rows to evaluate")
    parser.add_argument("--timestamp", type=str, default=None, help="Target ISO timestamp to diagnose (e.g. 2026-09-03T10:02:00)")

    args = parser.parse_args()
    run_model_test(well_id=args.well, db_path=Path(args.db), show_json=args.json, limit=args.limit, target_ts=args.timestamp)
