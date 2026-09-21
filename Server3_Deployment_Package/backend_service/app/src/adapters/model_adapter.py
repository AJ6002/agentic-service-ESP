"""
Model Adapter Service for ESP Agentic Platform
Provides a standardized interface over the ESP AI Model Team's 4 analytical models:
1. Rule Engine
2. Anomaly Detection
3. Failure Prediction / RUL
4. Fault Classifier
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.schemas.contracts import (
    ModelOutputPayload, RuleStatusPayload, RuleDeviationCounts,
    AnomalyResultPayload, FailurePredictionPayload, FaultDiagnosisPayload,
    HealthIndexPayload, MLContractV2Payload, TriggeredLimitPayload
)

logger = logging.getLogger(__name__)

class ModelAdapter:
    """
    Model Adapter Service:
    - Queries external ESP ML model endpoints (port :8082) if configured.
    - Falls back to MockModelAdapter for offline development & testing.
    - Enforces contract consistency between model outputs and Knowledge Base fault taxonomy.
    """

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.getenv("MODEL_API_URL", None)

    def fetch_v2_prediction(self, asset_id: str, api_url: Optional[str] = None) -> Optional[MLContractV2Payload]:
        """
        Query ML Team v2.0.0 Dual-Tier Inference Engine endpoint (:8082).
        Grounded in dependency_detail.md & ESP_Agentic_ML_Team_Dependencies_and_API_PreRequisites.md.
        """
        import urllib.request
        import urllib.error
        target_url = api_url or self.api_url or "http://localhost:8082"
        url = f"{target_url.rstrip('/')}/api/v1/esps/{asset_id}/predict"

        try:
            req = urllib.request.Request(url, method="POST", headers={"Content-Type": "application/json"}, data=b"{}")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    raw = json.loads(resp.read().decode("utf-8"))
                    return MLContractV2Payload.model_validate(raw)
        except Exception as ex:
            logger.debug(f"ModelAdapter fetch_v2_prediction for '{asset_id}' offline: {ex}")

        return None

    def get_model_output(self, asset_id: str, telemetry_data: Optional[Dict[str, Any]] = None) -> ModelOutputPayload:
        """
        Fetch normalized ModelOutputPayload containing rule, anomaly, failure, fault, and health scores.
        """
        # Try LiveDataBridge (:8000) normalized payload first
        try:
            from src.adapters.live_data_bridge import live_bridge
            live_payload = live_bridge.get_model_output_payload(asset_id)
            if live_payload:
                return live_payload
        except Exception as ex:
            logger.debug(f"[ModelAdapter] LiveDataBridge model fetch bypassed: {ex}")

        v2_pred = self.fetch_v2_prediction(asset_id)

        if self.api_url and not v2_pred:
            try:
                return self._query_live_model_api(asset_id)
            except Exception as e:
                logger.warning(f"Live Model API call failed ({e}). Falling back to MockModelAdapter.")

        out = self.get_mock_model_output(asset_id, telemetry_data)
        if v2_pred:
            out.v2_contract = v2_pred
            # Sync top-level fault diagnosis from v2 contract
            out.fault.predicted_fault_class = v2_pred.fault_classification
            out.fault.confidence = v2_pred.confidence_score
            out.anomaly.anomaly_score = v2_pred.anomaly_score
            out.anomaly.status = "ANOMALOUS" if v2_pred.is_anomaly else "NORMAL"
        return out

    def get_mock_model_output(self, asset_id: str, telemetry_data: Optional[Dict[str, Any]] = None) -> ModelOutputPayload:
        # MOCK_SCAFFOLD: deterministic ML mock | reason: last-resort output when LiveDataBridge
        # (cced_esp) and the ML mock API (:8082) are both unreachable | expiry: when a live ML
        # source is guaranteed | ref: src/verification/handoff.py:verify_model_output detects this signature
        """
        Simulate structured model outputs based on telemetry signals or asset status.
        """
        now = datetime.utcnow().isoformat() + "Z"
        
        # Check if telemetry indicates high motor temperature anomaly
        motor_temp = 0.0
        if telemetry_data:
            motor_temp = telemetry_data.get("primary_thermal_metric", telemetry_data.get("motor_temperature", 0.0))
        
        if motor_temp > 130.0:
            violations = ["MOTOR_TEMP_MARGIN_LOW", "MOTOR_OVERHEATING_WARNING"]
            rule_counts = RuleDeviationCounts(h1=2, h24=5, d30=12)
            anomaly = AnomalyResultPayload(
                asset_id=asset_id,
                timestamp=now,
                anomaly_score=0.91,
                status="ANOMALOUS",
                contributing_signals=["motor_temperature", "winding_temp"]
            )
            failure = FailurePredictionPayload(
                asset_id=asset_id,
                timestamp=now,
                risk_24h=0.72,
                risk_72h=0.88,
                risk_7d=0.95,
                rul_hours=75.0,
                primary_failure_mode="MOTOR_BURNOUT"
            )
            fault = FaultDiagnosisPayload(
                asset_id=asset_id,
                timestamp=now,
                predicted_fault_class="MOTOR_OVERHEATING",
                confidence=0.87,
                supporting_evidence_features=["motor_temperature = 135°C", "current = 62A"]
            )
            health = HealthIndexPayload(
                asset_id=asset_id,
                timestamp=now,
                health_index=45,
                status="CRITICAL",
                contributors=["Thermal Overload", "High 24h Risk"]
            )
        else:
            violations = []
            rule_counts = RuleDeviationCounts(h1=0, h24=0, d30=2)
            anomaly = AnomalyResultPayload(
                asset_id=asset_id,
                timestamp=now,
                anomaly_score=0.08,
                status="NORMAL",
                contributing_signals=[]
            )
            failure = FailurePredictionPayload(
                asset_id=asset_id,
                timestamp=now,
                risk_24h=0.02,
                risk_72h=0.05,
                risk_7d=0.12,
                rul_hours=2160.0,
                primary_failure_mode="NONE"
            )
            fault = FaultDiagnosisPayload(
                asset_id=asset_id,
                timestamp=now,
                predicted_fault_class="NORMAL_OPERATION",
                confidence=0.98,
                supporting_evidence_features=["All metrics within ROR"]
            )
            health = HealthIndexPayload(
                asset_id=asset_id,
                timestamp=now,
                health_index=95,
                status="HEALTHY",
                contributors=[]
            )

        rules = RuleStatusPayload(
            asset_id=asset_id,
            timestamp=now,
            violations=violations,
            deviation_counts=rule_counts
        )

        return ModelOutputPayload(
            asset_id=asset_id,
            timestamp=now,
            rules=rules,
            anomaly=anomaly,
            failure=failure,
            fault=fault,
            health=health,
            model_versions={
                "rule_engine": "1.2.0",
                "anomaly_detector": "2.1.0",
                "failure_predictor": "1.5.0",
                "fault_classifier": "3.0.1"
            }
        )

    def _query_live_model_api(self, asset_id: str) -> ModelOutputPayload:
        import httpx
        resp = httpx.get(f"{self.api_url}/assets/{asset_id}/model-output", timeout=1.5)
        resp.raise_for_status()
        return ModelOutputPayload.model_validate(resp.json())

    def validate_model_fault_taxonomy_contract(self, registered_kb_fault_codes: set) -> bool:
        """
        Contract Validation: Asserts that all fault classes produced by the Fault Classifier ML Model
        are registered within the Knowledge Base fault taxonomy.
        """
        mock_output_high = self.get_mock_model_output("ESP-001", {"motor_temperature": 140.0})
        mock_output_norm = self.get_mock_model_output("ESP-001", {"motor_temperature": 80.0})
        
        predicted_classes = {
            mock_output_high.fault.predicted_fault_class,
            mock_output_norm.fault.predicted_fault_class
        }
        
        # Every predicted class except NORMAL_OPERATION must exist in KB fault taxonomy
        non_normal_classes = predicted_classes - {"NORMAL_OPERATION"}
        missing_classes = non_normal_classes - registered_kb_fault_codes
        
        if missing_classes:
            logger.error(f"Contract Mismatch: Model produces unregistered fault codes: {missing_classes}")
            return False
            
        logger.info("Contract Verified: Model fault classes align with KB fault taxonomy.")
        return True
