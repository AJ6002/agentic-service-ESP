"""
Field Validation & Ground Truth Tagging Engine.
Tracks real-world field verification audits, computes online field precision/recall,
and records human-in-the-loop operational feedback.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.database_ml import ml_db


class ESPFieldValidator:
    def __init__(self):
        pass

    async def log_field_verification(
        self,
        esp_id: str,
        well_id: str,
        predicted_fault: str,
        actual_fault: str,
        verification_status: str,  # "CONFIRMED_TRUE_POSITIVE", "FALSE_POSITIVE", "MISSED_FAULT"
        operator_notes: str = "",
        downtime_saved_hours: float = 0.0
    ) -> Dict[str, Any]:
        """Logs operator teardown/field findings against model prediction."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "esp_id": esp_id,
            "well_id": well_id,
            "predicted_fault": predicted_fault,
            "actual_fault": actual_fault,
            "verification_status": verification_status,
            "operator_notes": operator_notes,
            "downtime_saved_hours": downtime_saved_hours
        }

        # Store to SQLite
        try:
            conn = await ml_db._get_connection()
            await conn.execute("""
                INSERT INTO esp_prediction_validation (
                    prediction_timestamp, esp_id, well_id, predicted_fault, predicted_confidence,
                    actual_outcome, validation_status, notes, lead_time_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["timestamp"], record["esp_id"], record["well_id"],
                record["predicted_fault"], 1.0,
                record["actual_fault"],
                record["verification_status"], record["operator_notes"],
                record["downtime_saved_hours"]
            ))
            await conn.commit()
            await conn.close()
        except Exception as e:
            print(f"Error logging field verification: {e}")

        return {"status": "success", "record": record}

    async def get_field_scorecard(self) -> Dict[str, Any]:
        """Calculates field precision, false alarms, and uptime saved metrics."""
        try:
            conn = await ml_db._get_connection()
            cursor = await conn.execute("SELECT * FROM esp_prediction_validation ORDER BY id DESC")
            rows = await cursor.fetchall()
            await conn.close()
        except Exception as e:
            print(f"Error reading field validation: {e}")
            rows = []

        total_audits = len(rows)
        tp_count = sum(1 for r in rows if r["validation_status"] in ["CONFIRMED_TRUE_POSITIVE", "CORRECT"])
        fp_count = sum(1 for r in rows if r["validation_status"] in ["FALSE_POSITIVE", "FALSE_ALARM"])
        saved_hrs = sum(float(r["lead_time_hours"] or 0) for r in rows)

        field_precision = (tp_count / total_audits * 100.0) if total_audits > 0 else 0.0

        return {
            "total_field_audits": total_audits,
            "confirmed_faults": tp_count,
            "false_positives": fp_count,
            "field_precision_pct": round(field_precision, 1) if total_audits > 0 else None,
            "field_precision_status": "VALIDATED" if total_audits > 0 else "NO_FIELD_AUDITS_RECORDED",
            "total_downtime_saved_hours": round(saved_hrs, 1),
            "recent_audits": [dict(r) for r in rows[:10]]
        }



field_validator = ESPFieldValidator()
