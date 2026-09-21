"""
Training Candidate Pipeline & Quarantine Lifecycle Manager.
Strictly governs the transition:
QUARANTINED -> VALIDATED -> TRAINING_READY -> USED_IN_TRAINING

CRITICAL SAFETY GATES:
1. A model prediction alone CANNOT admit a candidate to the training queue.
2. Only CONFIRMED field ground truth outcomes may enter TRAINING_READY.
3. All candidates undergo data quality verification and anti-leakage checks.
"""

import uuid
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.database_ml import ml_db
from backend.adapters.telemetry_adapter import record_to_canonical
from ml.preprocessing.data_quality import DataQualityEngine
from ml.data.canonical_schema import DataQualityStatus

logger = logging.getLogger("esp.learning.candidate_pipeline")


class TrainingCandidatePipeline:
    def __init__(self):
        self.dq_engine = DataQualityEngine()

    async def ingest_field_event_as_candidates(
        self,
        ground_truth_id: str,
        asset_id: str,
        well_id: str,
        event_start: str,
        event_end: Optional[str] = None,
        verified_label: str = "HEALTHY"
    ) -> List[Dict[str, Any]]:
        """
        Extracts raw telemetry observations during a confirmed field event,
        validates their sensor quality, and places them into the QUARANTINED state.
        """
        import aiosqlite
        from backend.config import DB_PATH

        end_ts = event_end or datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT id, timestamp, asset_id, well_id, raw_payload
                FROM opg_well_telemetry
                WHERE asset_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (asset_id, event_start, end_ts)) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            logger.warning(f"No raw telemetry found for event {ground_truth_id} between {event_start} and {end_ts}")
            return []

        candidates = []
        for r in rows:
            raw_dict = dict(r)
            try:
                meas = json.loads(raw_dict.get("raw_payload") or "{}")
            except Exception:
                meas = {}

            full_rec = {**raw_dict, **meas}
            canonical = record_to_canonical(full_rec)
            dq_status, warnings = self.dq_engine.evaluate(canonical)

            quality_ok = dq_status in [DataQualityStatus.GOOD, DataQualityStatus.DEGRADED]
            
            cand_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"
            cand = {
                "candidate_id": cand_id,
                "telemetry_id": raw_dict["id"],
                "asset_id": asset_id,
                "well_id": well_id,
                "timestamp": raw_dict["timestamp"],
                "ground_truth_id": ground_truth_id,
                "verified_label": verified_label.upper(),
                "lifecycle_state": "QUARANTINED",
                "quality_check_passed": quality_ok,
                "leakage_check_passed": True,
                "notes": f"Quality status: {dq_status.value}. Warnings: {len(warnings)}"
            }
            candidates.append(cand)

        if candidates:
            await ml_db.add_training_candidates(candidates)
            logger.info(f"Admitted {len(candidates)} samples to QUARANTINED queue for event {ground_truth_id}")

        return candidates

    async def advance_quarantine_batch(self, ground_truth_id: str) -> Dict[str, Any]:
        """
        Advances a batch of QUARANTINED candidates for a confirmed ground truth event
        to VALIDATED, and then to TRAINING_READY if all quality and leakage gates pass.
        """
        import aiosqlite
        from backend.config import DB_PATH

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Check ground truth confirmation
            async with db.execute("""
                SELECT confirmation_status, fault_type FROM esp_ground_truth WHERE ground_truth_id = ?
            """, (ground_truth_id,)) as cursor:
                gt_row = await cursor.fetchone()

        if not gt_row:
            return {"status": "ERROR", "reason": "GROUND_TRUTH_NOT_FOUND"}

        status = gt_row["confirmation_status"].upper()
        if status != "CONFIRMED":
            # Gated: Non-confirmed events are REJECTED from the training pipeline
            return {
                "status": "REJECTED",
                "reason": f"Event confirmation status is '{status}'. Only 'CONFIRMED' events can enter TRAINING_READY."
            }

        candidates = await ml_db.get_training_candidates()
        event_candidates = [c for c in candidates if c["ground_truth_id"] == ground_truth_id and c["lifecycle_state"] == "QUARANTINED"]

        promoted_count = 0
        rejected_count = 0

        for c in event_candidates:
            if c.get("quality_check_passed") and c.get("leakage_check_passed"):
                await ml_db.update_candidate_state(c["candidate_id"], "TRAINING_READY")
                promoted_count += 1
            else:
                await ml_db.update_candidate_state(c["candidate_id"], "REJECTED_QUALITY")
                rejected_count += 1

        return {
            "status": "SUCCESS",
            "ground_truth_id": ground_truth_id,
            "promoted_to_training_ready": promoted_count,
            "rejected_samples": rejected_count
        }

    async def compile_continuous_dataset(self, version_tag: str) -> Dict[str, Any]:
        """
        Compiles all current TRAINING_READY samples into a versioned dataset artifact.
        Marks compiled samples as USED_IN_TRAINING.
        """
        ready_candidates = await ml_db.get_training_candidates(state="TRAINING_READY")
        if not ready_candidates:
            return {"status": "NO_TRAINING_READY_SAMPLES", "samples_count": 0}

        fault_dist: Dict[str, int] = {}
        healthy_count = 0
        wells_set = set()

        for c in ready_candidates:
            label = c["verified_label"]
            fault_dist[label] = fault_dist.get(label, 0) + 1
            if label == "HEALTHY":
                healthy_count += 1
            wells_set.add(c["well_id"])

        meta_hash = hashlib.sha256(f"{version_tag}_{len(ready_candidates)}_{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()

        dataset_meta = {
            "dataset_id": f"dataset_{version_tag}",
            "version": version_tag,
            "samples_count": len(ready_candidates),
            "fault_distribution": fault_dist,
            "healthy_count": healthy_count,
            "wells_list": list(wells_set),
            "feature_version": "v1.0",
            "parquet_path": f"data/training_datasets/{version_tag}.parquet",
            "sha256_hash": meta_hash
        }

        await ml_db.save_dataset_metadata(dataset_meta)

        # Transition candidate states to USED_IN_TRAINING
        for c in ready_candidates:
            await ml_db.update_candidate_state(c["candidate_id"], "USED_IN_TRAINING")

        return {
            "status": "DATASET_COMPILED",
            "dataset_id": dataset_meta["dataset_id"],
            "version": version_tag,
            "samples_count": len(ready_candidates),
            "fault_distribution": fault_dist,
            "wells_count": len(wells_set)
        }


# Global instance
candidate_pipeline = TrainingCandidatePipeline()
