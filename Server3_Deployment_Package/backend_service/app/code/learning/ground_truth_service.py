"""
Ground Truth & Field Outcome Verification Service.
Captures physical operator and technician feedback from site,
performs temporal/event matching with model predictions,
and generates event-level evaluation metrics (TP, FP, FN, Lead Time).
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from backend.database_ml import ml_db

logger = logging.getLogger("esp.learning.ground_truth")


class GroundTruthService:
    def __init__(self):
        pass

    async def record_field_outcome(
        self,
        asset_id: str,
        well_id: str,
        fault_type: str,
        confirmation_status: str,
        event_start: Optional[str] = None,
        event_end: Optional[str] = None,
        operator_note: str = "",
        maintenance_action: str = "",
        source: str = "OPERATOR_FIELD"
    ) -> Dict[str, Any]:
        """
        Record a verified or unverified field outcome from site operations.
        Statuses: 'UNVERIFIED', 'CONFIRMED', 'FALSE_ALARM', 'REJECTED', 'UNKNOWN'
        """
        gt_id = f"GT-{uuid.uuid4().hex[:8].upper()}"
        start_ts = event_start or datetime.now(timezone.utc).isoformat()
        
        gt_record = {
            "ground_truth_id": gt_id,
            "asset_id": asset_id,
            "well_id": well_id,
            "fault_type": fault_type,
            "is_healthy": 1 if fault_type.upper() == "HEALTHY" else 0,
            "event_start": start_ts,
            "event_end": event_end,
            "confirmation_status": confirmation_status.upper(),
            "source": source,
            "operator_note": operator_note,
            "maintenance_action": maintenance_action,
            "verified_at": datetime.now(timezone.utc).isoformat() if confirmation_status.upper() in ["CONFIRMED", "FALSE_ALARM"] else None
        }

        await ml_db.save_ground_truth(gt_record)
        logger.info(f"Recorded Ground Truth {gt_id} for well {well_id}: {fault_type} ({confirmation_status})")

        # Perform event-based temporal linking with recent predictions
        links = await self.link_predictions_to_outcome(gt_record)

        return {
            "status": "SUCCESS",
            "ground_truth_id": gt_id,
            "confirmation_status": confirmation_status.upper(),
            "matched_predictions_count": len(links),
            "links": links
        }

    async def link_predictions_to_outcome(self, gt_record: Dict[str, Any], window_hours: float = 24.0) -> List[Dict[str, Any]]:
        """
        Perform event-based temporal matching.
        Searches historical predictions in a window prior to event_start to compute:
        - True Positive: Predicted fault matches confirmed fault before trip.
        - Early Detection / Lead Time: Hours between first correct prediction and event_start.
        - False Positive: Predicted fault when field outcome was confirmed healthy or false alarm.
        - False Negative: Field experienced fault but model predicted healthy.
        """
        import aiosqlite
        from backend.config import DB_PATH

        asset_id = gt_record["asset_id"]
        event_start_str = gt_record["event_start"]
        try:
            event_dt = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
        except Exception:
            event_dt = datetime.now(timezone.utc)

        window_start_dt = event_dt - timedelta(hours=window_hours)
        window_start_str = window_start_dt.isoformat()

        links = []
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Fetch predictions around the event window
            async with db.execute("""
                SELECT id, timestamp, fault_status, fault_name, fault_probability, overall_status
                FROM esp_unified_assessments
                WHERE esp_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (asset_id, window_start_str, event_dt.isoformat())) as cursor:
                preds = await cursor.fetchall()

        if not preds:
            return []

        confirmed_fault = gt_record["fault_type"].upper()
        status = gt_record["confirmation_status"].upper()

        for p in preds:
            p_dict = dict(p)
            p_time_str = p_dict["timestamp"]
            try:
                p_dt = datetime.fromisoformat(p_time_str.replace("Z", "+00:00"))
                lead_time_hrs = max(0.0, (event_dt - p_dt).total_seconds() / 3600.0)
            except Exception:
                lead_time_hrs = 0.0

            pred_fault = (p_dict.get("fault_status") or "").upper()

            if status == "CONFIRMED":
                if pred_fault == confirmed_fault and confirmed_fault != "HEALTHY":
                    match_type = "TRUE_POSITIVE" if lead_time_hrs <= 2.0 else "EARLY_DETECTION"
                elif pred_fault == "HEALTHY" and confirmed_fault != "HEALTHY":
                    match_type = "FALSE_NEGATIVE"
                elif pred_fault != confirmed_fault and confirmed_fault != "HEALTHY":
                    match_type = "MISCLASSIFIED"
                else:
                    match_type = "TRUE_NEGATIVE"
            elif status == "FALSE_ALARM":
                match_type = "FALSE_POSITIVE" if pred_fault != "HEALTHY" else "TRUE_NEGATIVE"
            else:
                match_type = "UNVERIFIED"

            link = {
                "prediction_id": p_dict["id"],
                "ground_truth_id": gt_record["ground_truth_id"],
                "match_type": match_type,
                "lead_time_hours": round(lead_time_hrs, 2),
                "detection_delay_sec": 0.0,
                "notes": f"Predicted {pred_fault} vs Confirmed {confirmed_fault}"
            }
            links.append(link)

        if links:
            await ml_db.save_prediction_links(links)

        return links

    async def get_validation_summary(self) -> Dict[str, Any]:
        """Aggregate field validation scorecards from real linked outcomes."""
        import aiosqlite
        from backend.config import DB_PATH

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    COUNT(*) as total_links,
                    SUM(CASE WHEN match_type IN ('TRUE_POSITIVE', 'EARLY_DETECTION') THEN 1 ELSE 0 END) as true_positives,
                    SUM(CASE WHEN match_type = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) as false_positives,
                    SUM(CASE WHEN match_type = 'FALSE_NEGATIVE' THEN 1 ELSE 0 END) as false_negatives,
                    SUM(CASE WHEN match_type = 'TRUE_NEGATIVE' THEN 1 ELSE 0 END) as true_negatives,
                    AVG(CASE WHEN match_type IN ('TRUE_POSITIVE', 'EARLY_DETECTION') THEN lead_time_hours ELSE NULL END) as avg_lead_time
                FROM esp_prediction_ground_truth_links
            """) as cursor:
                row = await cursor.fetchone()

        tp = (row["true_positives"] or 0) if row else 0
        fp = (row["false_positives"] or 0) if row else 0
        fn = (row["false_negatives"] or 0) if row else 0
        tn = (row["true_negatives"] or 0) if row else 0
        avg_lt = (row["avg_lead_time"] or 0.0) if row else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "total_verified_links": (row["total_links"] or 0) if row else 0,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "field_precision": round(precision, 4),
            "field_recall": round(recall, 4),
            "field_f1": round(f1, 4),
            "average_lead_time_hours": round(avg_lt, 2),
            "source": "REAL_FIELD_GROUND_TRUTH"
        }


# Global instance
ground_truth_service = GroundTruthService()
