"""
Dedicated SQLite Manager for ESP Intelligence & ML Tables.
Maintains absolute separation between raw telemetry (opg_well_telemetry)
and ML assessments, fault predictions, risk forecasts, RUL, and anomalies.
"""

import json
import logging
import aiosqlite
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

logger = logging.getLogger("esp.database_ml")


class MLDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def _get_connection(self):
        conn = await aiosqlite.connect(self.db_path, timeout=30.0)
        await conn.execute("PRAGMA busy_timeout = 30000;")
        conn.row_factory = aiosqlite.Row
        return conn

    async def init_ml_tables(self):
        """Create dedicated ML tables with compound indexes."""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute("PRAGMA busy_timeout = 30000;")
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            
            # 1. Unified Health Assessments Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_unified_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    rule_status TEXT NOT NULL,
                    fault_status TEXT NOT NULL,
                    fault_name TEXT NOT NULL,
                    fault_probability REAL DEFAULT 0.0,
                    confidence_level TEXT DEFAULT 'HIGH',
                    future_risk TEXT DEFAULT 'LOW',
                    primary_risk_fault TEXT DEFAULT '',
                    max_risk_probability REAL DEFAULT 0.0,
                    rul_status TEXT DEFAULT 'UNAVAILABLE',
                    rul_hours REAL,
                    rul_lower_hours REAL,
                    rul_upper_hours REAL,
                    anomaly_score REAL DEFAULT 0.0,
                    anomaly_status TEXT DEFAULT 'NORMAL',
                    data_quality TEXT DEFAULT 'GOOD',
                    top_reasons TEXT DEFAULT '[]',
                    operator_action TEXT DEFAULT '',
                    technical_explanation TEXT DEFAULT '',
                    shap_contributions TEXT DEFAULT '{}',
                    parameter_evaluations TEXT DEFAULT '[]',
                    model_versions TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 2. Fault Predictions Detail Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_fault_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    predicted_fault TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_unknown INTEGER DEFAULT 0,
                    class_probabilities TEXT DEFAULT '{}',
                    evidence TEXT DEFAULT '[]',
                    model_version TEXT NOT NULL,
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 3. Future Risk Forecasts Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_risk_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    target_fault TEXT NOT NULL,
                    horizon_hours REAL NOT NULL,
                    horizon_label TEXT NOT NULL,
                    probability REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    evidence TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 4. RUL Estimates Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_rul_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    estimated_rul_hours REAL,
                    uncertainty_lower_hours REAL,
                    uncertainty_upper_hours REAL,
                    confidence_interval_pct REAL DEFAULT 95.0,
                    data_coverage TEXT DEFAULT 'CALIBRATED',
                    model_version TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 5. Anomaly Events Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_anomaly_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    anomaly_score REAL NOT NULL,
                    threshold REAL NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    affected_parameters TEXT DEFAULT '[]',
                    reconstruction_errors TEXT DEFAULT '{}',
                    reason TEXT,
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 6. Prediction Validation & Audit Log Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_prediction_validation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_timestamp TEXT NOT NULL,
                    esp_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    predicted_fault TEXT NOT NULL,
                    predicted_confidence REAL NOT NULL,
                    future_risk_forecast TEXT,
                    actual_outcome TEXT DEFAULT 'PENDING',
                    actual_trip_cause TEXT DEFAULT '',
                    actual_fault_timestamp TEXT,
                    lead_time_hours REAL,
                    validation_status TEXT DEFAULT 'UNVERIFIED', -- 'CORRECT', 'FALSE_ALARM', 'MISSED', 'EARLY_DETECTION'
                    audited_by TEXT DEFAULT 'SYSTEM',
                    notes TEXT DEFAULT '',
                    updated_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 7. Model Registry & Metadata Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_model_registry (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    training_dataset TEXT NOT NULL,
                    feature_schema_hash TEXT NOT NULL,
                    training_period TEXT,
                    validation_metrics TEXT DEFAULT '{}',
                    thresholds TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'ACTIVE'
                );
            """)

            # 8. Verified Field Ground Truth Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_ground_truth (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ground_truth_id TEXT UNIQUE NOT NULL,
                    asset_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    fault_type TEXT NOT NULL,
                    is_healthy INTEGER DEFAULT 0,
                    event_start TEXT NOT NULL,
                    event_end TEXT,
                    confirmation_status TEXT DEFAULT 'UNVERIFIED', -- 'UNVERIFIED', 'CONFIRMED', 'FALSE_ALARM', 'REJECTED', 'UNKNOWN'
                    source TEXT DEFAULT 'OPERATOR_FIELD',
                    operator_note TEXT DEFAULT '',
                    maintenance_action TEXT DEFAULT '',
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                    verified_at TEXT
                );
            """)

            # 9. Prediction to Ground Truth Linkage Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_prediction_ground_truth_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    ground_truth_id TEXT NOT NULL,
                    match_type TEXT NOT NULL, -- 'TRUE_POSITIVE', 'FALSE_POSITIVE', 'FALSE_NEGATIVE', 'TRUE_NEGATIVE', 'EARLY_DETECTION'
                    lead_time_hours REAL,
                    detection_delay_sec REAL,
                    notes TEXT DEFAULT '',
                    linked_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 10. Training Candidate Quarantine Queue
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_training_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT UNIQUE NOT NULL,
                    telemetry_id INTEGER NOT NULL,
                    asset_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ground_truth_id TEXT NOT NULL,
                    verified_label TEXT NOT NULL,
                    lifecycle_state TEXT DEFAULT 'QUARANTINED', -- 'QUARANTINED', 'VALIDATED', 'TRAINING_READY', 'USED_IN_TRAINING'
                    quality_check_passed INTEGER DEFAULT 0,
                    leakage_check_passed INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                    updated_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 11. Learning Datasets Registry
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_learning_datasets (
                    dataset_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    samples_count INTEGER NOT NULL,
                    fault_distribution TEXT NOT NULL,
                    healthy_count INTEGER NOT NULL,
                    wells_list TEXT NOT NULL,
                    feature_version TEXT NOT NULL,
                    parquet_path TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                );
            """)

            # 12. Training Runs & Model Governance Log
            await db.execute("""
                CREATE TABLE IF NOT EXISTS esp_training_runs (
                    training_run_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    previous_version TEXT NOT NULL,
                    candidate_version TEXT NOT NULL,
                    dataset_version TEXT NOT NULL,
                    training_timestamp TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                    training_samples INTEGER NOT NULL,
                    training_events INTEGER NOT NULL,
                    training_wells INTEGER NOT NULL,
                    metrics_before TEXT NOT NULL,
                    metrics_after TEXT NOT NULL,
                    state TEXT DEFAULT 'TRAINED', -- 'TRAINED', 'EVALUATED', 'APPROVED', 'REJECTED', 'DEPLOYED', 'ROLLED_BACK'
                    decision_reason TEXT DEFAULT '',
                    artifact_hash TEXT NOT NULL
                );
            """)

            # Indexes for fast historical query and dashboard charts
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_assess_esp_time ON esp_unified_assessments(esp_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_assess_well_time ON esp_unified_assessments(well_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_assess_status ON esp_unified_assessments(overall_status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_fault_time ON esp_fault_predictions(esp_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_anomaly_time ON esp_anomaly_events(esp_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ml_validation_status ON esp_prediction_validation(validation_status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_gt_asset_time ON esp_ground_truth(asset_id, event_start DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_gt_status ON esp_ground_truth(confirmation_status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_candidates_state ON esp_training_candidates(lifecycle_state);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_training_runs_state ON esp_training_runs(state);")

            await db.commit()
            logger.info("Dedicated ESP ML SQLite tables initialized successfully.")


    async def save_unified_assessment(self, assessment: Dict[str, Any]) -> int:
        """Store a unified assessment record."""
        async with aiosqlite.connect(self.db_path) as db:
            rul_data = assessment.get("rul", {})
            anomaly_data = assessment.get("anomaly", {})
            
            top_reasons_str = json.dumps(assessment.get("top_reasons", []))
            shap_str = json.dumps(assessment.get("shap_contributions", {}))
            param_evals_str = json.dumps(assessment.get("parameter_evaluations", []))
            versions_str = json.dumps(assessment.get("model_versions", {}))

            cursor = await db.execute("""
                INSERT INTO esp_unified_assessments (
                    timestamp, esp_id, well_id, overall_status, rule_status,
                    fault_status, fault_name, fault_probability, confidence_level,
                    future_risk, primary_risk_fault, max_risk_probability,
                    rul_status, rul_hours, rul_lower_hours, rul_upper_hours,
                    anomaly_score, anomaly_status, data_quality,
                    top_reasons, operator_action, technical_explanation,
                    shap_contributions, parameter_evaluations, model_versions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment.get("timestamp", datetime.now(timezone.utc).isoformat()),
                assessment.get("esp_id", "UNKNOWN"),
                assessment.get("well_id", "UNKNOWN"),
                assessment.get("overall_status", "HEALTHY"),
                assessment.get("rule_status", "NORMAL"),
                assessment.get("fault_status", "HEALTHY"),
                assessment.get("fault_name", "Healthy Operation"),
                float(assessment.get("fault_probability", 1.0)),
                assessment.get("confidence_level", "HIGH"),
                assessment.get("future_risk", "LOW"),
                assessment.get("primary_risk_fault", "") or "",
                float(assessment.get("max_risk_probability", 0.0)),
                rul_data.get("status", "UNAVAILABLE"),
                rul_data.get("estimated_rul_hours"),
                rul_data.get("uncertainty_lower_hours"),
                rul_data.get("uncertainty_upper_hours"),
                float(anomaly_data.get("anomaly_score", 0.0)),
                anomaly_data.get("status", "NORMAL"),
                assessment.get("data_quality", "GOOD"),
                top_reasons_str,
                assessment.get("operator_action", ""),
                assessment.get("technical_explanation", ""),
                shap_str,
                param_evals_str,
                versions_str
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_latest_assessment(self, esp_id: Optional[str] = None, well_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve the latest unified assessment."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM esp_unified_assessments"
            params = []
            conditions = []
            if esp_id:
                conditions.append("esp_id = ?")
                params.append(esp_id)
            if well_id:
                conditions.append("well_id = ?")
                params.append(well_id)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC LIMIT 1;"

            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                d = dict(row)
                d["top_reasons"] = json.loads(d.get("top_reasons") or "[]")
                d["shap_contributions"] = json.loads(d.get("shap_contributions") or "{}")
                d["parameter_evaluations"] = json.loads(d.get("parameter_evaluations") or "[]")
                d["model_versions"] = json.loads(d.get("model_versions") or "{}")
                return d

    async def get_assessment_history(
        self,
        esp_id: Optional[str] = None,
        well_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve historical assessment records for timelines."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM esp_unified_assessments"
            params = []
            conditions = []
            if esp_id:
                conditions.append("esp_id = ?")
                params.append(esp_id)
            if well_id:
                conditions.append("well_id = ?")
                params.append(well_id)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC LIMIT ?;"
            params.append(limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    d["top_reasons"] = json.loads(d.get("top_reasons") or "[]")
                    d["shap_contributions"] = json.loads(d.get("shap_contributions") or "{}")
                    d["parameter_evaluations"] = json.loads(d.get("parameter_evaluations") or "[]")
                    d["model_versions"] = json.loads(d.get("model_versions") or "{}")
                    results.append(d)
                return results

    async def record_prediction_for_validation(self, record: Dict[str, Any]) -> int:
        """Record a prediction to be audited against field outcomes."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO esp_prediction_validation (
                    prediction_timestamp, esp_id, well_id, predicted_fault,
                    predicted_confidence, future_risk_forecast, validation_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("timestamp", datetime.now(timezone.utc).isoformat()),
                record.get("esp_id", "UNKNOWN"),
                record.get("well_id", "UNKNOWN"),
                record.get("predicted_fault", "HEALTHY"),
                float(record.get("confidence", 1.0)),
                record.get("future_risk_forecast", "LOW"),
                "UNVERIFIED",
                record.get("notes", "")
            ))
            await db.commit()
            return cursor.lastrowid

    # --- Phase 43 Continuous Learning Database Methods ---

    async def save_ground_truth(self, gt: Dict[str, Any]) -> str:
        """Insert or update a field ground truth outcome."""
        import uuid
        gt_id = gt.get("ground_truth_id") or f"GT-{uuid.uuid4().hex[:8].upper()}"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO esp_ground_truth (
                    ground_truth_id, asset_id, well_id, fault_type, is_healthy,
                    event_start, event_end, confirmation_status, source,
                    operator_note, maintenance_action, verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gt_id,
                gt.get("asset_id", "UNKNOWN"),
                gt.get("well_id", "UNKNOWN"),
                gt.get("fault_type", "HEALTHY"),
                1 if gt.get("fault_type") == "HEALTHY" or gt.get("is_healthy") else 0,
                gt.get("event_start", datetime.now(timezone.utc).isoformat()),
                gt.get("event_end"),
                gt.get("confirmation_status", "UNVERIFIED"),
                gt.get("source", "OPERATOR_FIELD"),
                gt.get("operator_note", ""),
                gt.get("maintenance_action", ""),
                gt.get("verified_at") or (datetime.now(timezone.utc).isoformat() if gt.get("confirmation_status") == "CONFIRMED" else None)
            ))
            await db.commit()
            return gt_id

    async def get_ground_truth(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve ground truth records."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM esp_ground_truth"
            params = []
            if status:
                query += " WHERE confirmation_status = ?"
                params.append(status)
            query += " ORDER BY id DESC LIMIT ?;"
            params.append(limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def save_prediction_links(self, links: List[Dict[str, Any]]):
        """Save prediction to ground truth event links."""
        async with aiosqlite.connect(self.db_path) as db:
            for l in links:
                await db.execute("""
                    INSERT INTO esp_prediction_ground_truth_links (
                        prediction_id, ground_truth_id, match_type,
                        lead_time_hours, detection_delay_sec, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    l.get("prediction_id", 0),
                    l.get("ground_truth_id", ""),
                    l.get("match_type", "TRUE_POSITIVE"),
                    l.get("lead_time_hours"),
                    l.get("detection_delay_sec"),
                    l.get("notes", "")
                ))
            await db.commit()

    async def get_prediction_links(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve prediction to ground truth links."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM esp_prediction_ground_truth_links ORDER BY id DESC LIMIT ?;", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_training_candidates(self, candidates: List[Dict[str, Any]]):
        """Add verified observations into training candidate quarantine queue."""
        import uuid
        async with aiosqlite.connect(self.db_path) as db:
            for c in candidates:
                cand_id = c.get("candidate_id") or f"CAND-{uuid.uuid4().hex[:8].upper()}"
                await db.execute("""
                    INSERT OR REPLACE INTO esp_training_candidates (
                        candidate_id, telemetry_id, asset_id, well_id,
                        timestamp, ground_truth_id, verified_label,
                        lifecycle_state, quality_check_passed, leakage_check_passed, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (

                    cand_id,
                    c.get("telemetry_id", 0),
                    c.get("asset_id", "UNKNOWN"),
                    c.get("well_id", "UNKNOWN"),
                    c.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    c.get("ground_truth_id", ""),
                    c.get("verified_label", "HEALTHY"),
                    c.get("lifecycle_state", "QUARANTINED"),
                    1 if c.get("quality_check_passed", True) else 0,
                    1 if c.get("leakage_check_passed", True) else 0,
                    c.get("notes", "")
                ))
            await db.commit()

    async def get_training_candidates(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve candidate records by lifecycle state."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM esp_training_candidates"
            params = []
            if state:
                query += " WHERE lifecycle_state = ?"
                params.append(state)
            query += " ORDER BY id DESC;"

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_candidate_state(self, candidate_id: str, new_state: str):
        """Promote candidate through quarantine lifecycle."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE esp_training_candidates
                SET lifecycle_state = ?, updated_at = (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
                WHERE candidate_id = ?
            """, (new_state, candidate_id))
            await db.commit()

    async def save_dataset_metadata(self, meta: Dict[str, Any]):
        """Register a versioned continuous learning dataset."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO esp_learning_datasets (
                    dataset_id, version, samples_count, fault_distribution,
                    healthy_count, wells_list, feature_version, parquet_path, sha256_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.get("dataset_id", "dataset_v1"),
                meta.get("version", "v1.0"),
                meta.get("samples_count", 0),
                json.dumps(meta.get("fault_distribution", {})),
                meta.get("healthy_count", 0),
                json.dumps(meta.get("wells_list", [])),
                meta.get("feature_version", "v1.0"),
                meta.get("parquet_path", ""),
                meta.get("sha256_hash", "")
            ))
            await db.commit()

    async def get_dataset_versions(self) -> List[Dict[str, Any]]:
        """List all versioned learning datasets."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM esp_learning_datasets ORDER BY created_at DESC;") as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    d["fault_distribution"] = json.loads(d.get("fault_distribution") or "{}")
                    d["wells_list"] = json.loads(d.get("wells_list") or "[]")
                    results.append(d)
                return results

    async def save_training_run(self, run: Dict[str, Any]):
        """Record model training run and candidate metrics."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO esp_training_runs (
                    training_run_id, model_type, previous_version, candidate_version,
                    dataset_version, training_samples, training_events, training_wells,
                    metrics_before, metrics_after, state, decision_reason, artifact_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.get("training_run_id", ""),
                run.get("model_type", "CLASSIFIER"),
                run.get("previous_version", "v1.0"),
                run.get("candidate_version", "v1.1_candidate"),
                run.get("dataset_version", "v1.0"),
                run.get("training_samples", 0),
                run.get("training_events", 0),
                run.get("training_wells", 0),
                json.dumps(run.get("metrics_before", {})),
                json.dumps(run.get("metrics_after", {})),
                run.get("state", "TRAINED"),
                run.get("decision_reason", ""),
                run.get("artifact_hash", "")
            ))
            await db.commit()

    async def get_training_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve training runs and candidate evaluation history."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM esp_training_runs ORDER BY training_timestamp DESC LIMIT ?;", (limit,)) as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    d["metrics_before"] = json.loads(d.get("metrics_before") or "{}")
                    d["metrics_after"] = json.loads(d.get("metrics_after") or "{}")
                    results.append(d)
                return results

    async def update_training_run_state(self, training_run_id: str, state: str, reason: str = ""):
        """Update candidate model state (APPROVED, REJECTED, DEPLOYED, ROLLED_BACK)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE esp_training_runs
                SET state = ?, decision_reason = ?
                WHERE training_run_id = ?
            """, (state, reason, training_run_id))
            await db.commit()


# Global instance
ml_db = MLDatabase()

