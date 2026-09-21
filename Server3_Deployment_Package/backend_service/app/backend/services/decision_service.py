"""
Unified ESP Decision Service.
Synthesizes signals from all 5 model systems into a final UnifiedESPAssessment.
Enforces hierarchical safety and diagnostic decision rules.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    UnifiedESPAssessment,
    ESPOverallStatus,
    ParameterStatus,
    DataQualityStatus,
    FaultClass,
    ParameterEvaluation,
    RuleEvaluationResult,
    FaultClassificationResult,
    FaultRiskPrediction,
    RULPredictionResult,
    AnomalyDetectionResult
)


class ESPDecisionService:
    def __init__(self):
        pass

    def synthesize(
        self,
        telemetry: CanonicalESPTelemetry,
        data_quality_status: DataQualityStatus,
        quality_warnings: List[str],
        parameter_evaluations: List[ParameterEvaluation],
        rules_fired: List[RuleEvaluationResult],
        classification_result: FaultClassificationResult,
        risk_predictions: List[FaultRiskPrediction],
        rul_result: RULPredictionResult,
        anomaly_result: AnomalyDetectionResult,
        explanation_bundle: Dict[str, Any],
        inference_latency_ms: float = 0.0
    ) -> UnifiedESPAssessment:
        """
        Hierarchical decision fusion:
        1. Critical rule violations OR high-confidence severe faults -> CRITICAL / FAULT
        2. Warning rules OR high future risk OR anomaly detected -> WARNING
        3. Nominal envelope + Healthy classification + low anomaly -> HEALTHY
        4. Degraded / Insufficient data quality -> UNKNOWN / INSUFFICIENT
        """
        # Determine Rule Status
        has_crit_rule = any(r.severity == "CRITICAL" for r in rules_fired)
        has_warn_rule = any(r.severity == "WARNING" for r in rules_fired)
        has_crit_param = any(p.status == ParameterStatus.CRITICAL for p in parameter_evaluations)
        has_warn_param = any(p.status == ParameterStatus.WARNING for p in parameter_evaluations)

        if has_crit_rule or has_crit_param:
            rule_status = ParameterStatus.CRITICAL
        elif has_warn_rule or has_warn_param:
            rule_status = ParameterStatus.WARNING
        else:
            rule_status = ParameterStatus.NORMAL

        # Hybrid Fault Determination: Check if a deterministic rule fired
        has_power_loss = any(r.fault == FaultClass.POWER_LOSS for r in rules_fired)
        rule_fault = next((r.fault for r in rules_fired if r.fault != FaultClass.HEALTHY), None)

        if has_power_loss:
            # Power loss is an instantaneous complete power failure taking absolute priority
            active_fault = FaultClass.POWER_LOSS
            volt_ratio = (telemetry.motor_voltage_v or 0.0) / 480.0
            fault_prob = round(min(0.985, max(0.910, 0.985 - volt_ratio * 0.075)), 3)
            conf_level = "CRITICAL (RULE)"
            fault_name = "Power Loss"
            detection_source = "RULE_ENGINE"
        elif rule_fault and (classification_result.predicted_fault == FaultClass.HEALTHY or classification_result.is_unknown):
            # Rule detected a deterministic fault that ML was not trained on (Rule-Only Fault)
            active_fault = rule_fault
            fault_prob = round(min(0.965, max(0.820, 0.880 + len(rules_fired) * 0.025)), 3)
            conf_level = "HIGH (RULE)"
            fault_name = rule_fault.value.replace("_", " ").title()
            detection_source = "RULE_ENGINE"
        elif classification_result.predicted_fault != FaultClass.HEALTHY and not classification_result.is_unknown:
            active_fault = classification_result.predicted_fault
            fault_prob = classification_result.confidence
            conf_level = classification_result.confidence_level
            fault_name = classification_result.predicted_fault.value.replace("_", " ").title()
            detection_source = "ML + RULE" if rule_fault == classification_result.predicted_fault else "ML_CLASSIFIER"
        elif classification_result.is_unknown:
            active_fault = FaultClass.UNKNOWN_UNSEEN
            fault_prob = classification_result.confidence
            conf_level = "LOW"
            fault_name = "Unknown / Low Confidence"
            detection_source = "UNKNOWN_FALLBACK"
        else:
            active_fault = FaultClass.HEALTHY
            fault_prob = classification_result.confidence
            conf_level = classification_result.confidence_level
            fault_name = "Healthy Operation"
            detection_source = "NOMINAL_MONITORING"

        # Overall Status Determination
        # Note: Future risk predictor is strictly RESEARCH_REPLAY_ONLY and does not falsely alarm live healthy status
        if data_quality_status == DataQualityStatus.INSUFFICIENT:
            overall_status = ESPOverallStatus.UNKNOWN
        elif has_crit_rule or active_fault in [
            FaultClass.DRY_WELL_PUMP_OFF, FaultClass.BLOCKED_INTAKE, FaultClass.MOTOR_OVERLOAD,
            FaultClass.UNDERVOLTAGE, FaultClass.POWER_LOSS, FaultClass.BEARING_DEGRADATION
        ] and fault_prob >= 0.70:
            overall_status = ESPOverallStatus.CRITICAL
        elif (
            active_fault != FaultClass.HEALTHY or
            rule_status in [ParameterStatus.WARNING, ParameterStatus.CRITICAL] or
            anomaly_result.is_anomaly
        ):
            overall_status = ESPOverallStatus.WARNING if active_fault == FaultClass.HEALTHY else ESPOverallStatus.FAULT
        else:
            overall_status = ESPOverallStatus.HEALTHY



        # Future Risk Synthesis
        max_risk_prob = max([r.probability for r in risk_predictions], default=0.0)
        primary_risk = "LOW"
        if max_risk_prob >= 0.70:
            primary_risk = "HIGH"
        elif max_risk_prob >= 0.40:
            primary_risk = "MEDIUM"

        primary_risk_fault = (
            risk_predictions[0].target_fault.value if risk_predictions else "None"
        )

        # Use rule operator action if rule-detected fault
        op_action = explanation_bundle.get("operator_action", "")
        if detection_source == "RULE_ENGINE" and rule_fault:
            from ml.data.fault_registry import fault_registry
            f_meta = fault_registry.get_fault(rule_fault.value)
            if f_meta:
                op_action = f_meta.operator_action

        return UnifiedESPAssessment(
            timestamp=telemetry.timestamp,
            esp_id=telemetry.esp_id,
            well_id=telemetry.well_id,
            overall_status=overall_status,
            rule_status=rule_status,
            fault_status=active_fault.value,
            fault_name=fault_name,
            fault_class=active_fault,
            fault_probability=fault_prob,
            confidence_level=conf_level,
            future_risk=primary_risk,
            primary_risk_fault=primary_risk_fault,
            max_risk_probability=round(max_risk_prob, 3),
            risk_predictions=risk_predictions,
            rul=rul_result,
            anomaly=anomaly_result,
            parameter_evaluations=parameter_evaluations,
            top_reasons=explanation_bundle.get("top_reasons", []),
            operator_action=op_action,
            technical_explanation=explanation_bundle.get("technical_details", ""),
            shap_contributions=explanation_bundle.get("shap_contributions", {}),

            trajectory_summary=explanation_bundle.get("trajectory_summary", ""),
            data_quality=data_quality_status,
            warnings=quality_warnings,
            model_versions={
                "rule_engine": "v1.0",
                "fault_classifier": classification_result.model_version,
                "risk_predictor": "v1.0",
                "rul_engine": rul_result.model_version,
                "anomaly_detector": "v1.0"
            },
            inference_latency_ms=round(inference_latency_ms, 2)
        )
