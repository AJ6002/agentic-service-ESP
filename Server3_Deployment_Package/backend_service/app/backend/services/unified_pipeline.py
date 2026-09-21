"""
Unified Real-Time Inference Pipeline.
Executes end-to-end inference across all 5 model systems:
Data Quality -> Feature Engineering -> Rules -> Classifier -> Risk -> RUL -> Anomaly -> Explainer -> Storage.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    UnifiedESPAssessment
)
from ml.preprocessing.data_quality import DataQualityEngine
from ml.features.time_series_features import RollingFeatureExtractor
from ml.models.rule_engine import ESPRuleEngine
from ml.models.fault_classifier import ESPFaultClassifier
from ml.models.risk_predictor import ESPRiskPredictor
from ml.models.rul_engine import ESPRULEngine
from ml.models.anomaly_detector import ESPAnomalyDetector
from ml.explainability.explainer import ESPExplainer
from backend.services.decision_service import ESPDecisionService
from backend.database_ml import ml_db

logger = logging.getLogger("esp.unified_pipeline")


class ESPUnifiedPipeline:
    def __init__(self):
        self.data_quality = DataQualityEngine()
        self.feature_extractor = RollingFeatureExtractor()
        self.rule_engine = ESPRuleEngine()
        self.classifier = ESPFaultClassifier()
        self.risk_predictor = ESPRiskPredictor()
        self.rul_engine = ESPRULEngine()
        self.anomaly_detector = ESPAnomalyDetector()
        self.explainer = ESPExplainer()
        self.decision_service = ESPDecisionService()

        # In-memory latest assessment cache for low-latency dashboard polling
        self.latest_assessments: Dict[str, UnifiedESPAssessment] = {}

    async def process_telemetry(
        self,
        telemetry: CanonicalESPTelemetry,
        persist_db: bool = True
    ) -> UnifiedESPAssessment:
        """Processes a single telemetry sample through the entire ML pipeline."""
        start_time = time.perf_counter()

        # 1. Data Quality & Plausibility Evaluation
        dq_status, dq_warnings = self.data_quality.evaluate(telemetry)

        # 2. Rolling Time-Series Feature Window Update
        features = self.feature_extractor.push_and_extract(telemetry)

        # 3. Rule & Operating Envelope Evaluation (Model 1)
        param_evals = self.rule_engine.evaluate_envelopes(telemetry)
        rules_fired = self.rule_engine.evaluate_rules(telemetry, features)

        # 4. Multiclass Fault Classifier (Model 2)
        classification = self.classifier.predict(telemetry, features)

        # 5. Future Fault Risk Predictor (Model 3)
        risk_predictions = self.risk_predictor.predict_risk(telemetry, features)

        # 6. RUL Estimation (Model 4)
        rul_result = self.rul_engine.estimate_rul(telemetry, features, classification.predicted_fault)

        # 7. Healthy-State Anomaly Detector (Model 5)
        anomaly_result = self.anomaly_detector.score(telemetry, features)

        # 8. Explainability Synthesis
        explanation_bundle = self.explainer.explain(
            fault_class=classification.predicted_fault,
            confidence=classification.confidence,
            telemetry=telemetry,
            feature_dict=features,
            evaluations=param_evals,
            anomaly_score=anomaly_result.anomaly_score
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 9. Unified Decision Synthesis
        assessment = self.decision_service.synthesize(
            telemetry=telemetry,
            data_quality_status=dq_status,
            quality_warnings=dq_warnings,
            parameter_evaluations=param_evals,
            rules_fired=rules_fired,
            classification_result=classification,
            risk_predictions=risk_predictions,
            rul_result=rul_result,
            anomaly_result=anomaly_result,
            explanation_bundle=explanation_bundle,
            inference_latency_ms=latency_ms
        )

        # 10. Cache & Persist
        well_key = f"{telemetry.esp_id}_{telemetry.well_id}"
        self.latest_assessments[well_key] = assessment
        self.latest_assessments["LATEST"] = assessment

        if persist_db:
            try:
                await ml_db.save_unified_assessment(assessment.model_dump())
            except Exception as e:
                logger.error(f"Error persisting assessment to SQLite: {e}")

        return assessment


# Global Pipeline Instance
esp_pipeline = ESPUnifiedPipeline()
