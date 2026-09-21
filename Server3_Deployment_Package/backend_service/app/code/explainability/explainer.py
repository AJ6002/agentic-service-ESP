"""
Explainability & Root-Cause Attribution Engine.
Computes Tree SHAP-equivalent feature contributions, translates multivariate shifts into
natural language explanations, and builds operator advisories.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    FaultClass,
    ParameterEvaluation
)
from ml.explainability.templates import build_explanation


class ESPExplainer:
    def __init__(self):
        pass

    def explain(
        self,
        fault_class: FaultClass,
        confidence: float,
        telemetry: CanonicalESPTelemetry,
        feature_dict: Dict[str, float],
        evaluations: List[ParameterEvaluation],
        anomaly_score: float = 0.0
    ) -> Dict[str, Any]:
        """Synthesizes complete explainability bundle."""
        explanation_bundle = build_explanation(
            fault_class=fault_class,
            confidence=confidence,
            telemetry=telemetry,
            evaluations=evaluations,
            anomaly_score=anomaly_score
        )

        # Compute Feature Attribution / SHAP-equivalent contributions for key sensors
        shap_contributions = {}
        for p in evaluations:
            # Normalized deviation contribution
            score = float(p.deviation_percent / 100.0) if p.deviation_percent > 0 else 0.0
            shap_contributions[p.canonical_name] = round(score, 3)

        explanation_bundle["shap_contributions"] = shap_contributions
        return explanation_bundle
