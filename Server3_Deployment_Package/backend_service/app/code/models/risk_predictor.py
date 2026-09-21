"""
Model 3: Future Fault Risk Predictor Inference Engine.
Forecasts future failure hazard across 1h, 6h, 24h horizons
with trajectory indicators and evidence synthesis.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    FaultRiskPrediction,
    FaultClass
)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "risk_predictor" / "v1.0"
MODEL_PATH = MODEL_DIR / "risk_predictor.joblib"


class ESPRiskPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.bundle: Optional[Dict[str, Any]] = None
        self._load_model()

    def _load_model(self):
        if self.model_path.exists():
            self.bundle = joblib.load(self.model_path)
            self.models = self.bundle["models"]
            self.feature_names = self.bundle["feature_names"]
            self.horizons = self.bundle["horizons"]
            self.version = self.bundle.get("version", "v1.0")
        else:
            self.bundle = None

    def is_ready(self) -> bool:
        return self.bundle is not None

    def predict_risk(
        self,
        telemetry: CanonicalESPTelemetry,
        feature_dict: Dict[str, float]
    ) -> List[FaultRiskPrediction]:
        """Evaluates multi-horizon failure risk."""
        if not self.is_ready():
            return [
                FaultRiskPrediction(
                    target_fault=FaultClass.UNKNOWN_UNSEEN,
                    horizon_hours=1.0,
                    horizon_label="1h",
                    probability=0.0,
                    risk_level="UNAVAILABLE",
                    trend="STABLE",
                    validation_status="RESEARCH_REPLAY_ONLY",
                    is_field_validated=False,
                    evidence=["Risk predictor model artifact not loaded or unavailable."]
                )
            ]

        feature_vec = np.array([feature_dict.get(fname, 0.0) for fname in self.feature_names]).reshape(1, -1)
        predictions: List[FaultRiskPrediction] = []

        horizon_hours_map = {"1h": 1.0, "6h": 6.0, "24h": 24.0}

        # Trajectory trend evidence
        trend_evidence = []
        dp_slope = feature_dict.get("discharge_pressure_psi_slope_15", 0.0)
        temp_slope = feature_dict.get("motor_temperature_c_slope_15", 0.0)
        current_slope = feature_dict.get("motor_current_a_slope_15", 0.0)
        
        if temp_slope > 0.05:
            trend_evidence.append(f"Motor temperature climbing (+{temp_slope*15:.1f}°C / 15m)")
        if current_slope > 0.10:
            trend_evidence.append(f"Motor current increasing (+{current_slope*15:.1f} A / 15m)")
        if dp_slope < -0.5:
            trend_evidence.append(f"Discharge pressure declining ({dp_slope*15:.1f} PSI / 15m)")

        trajectory_trend = "INCREASING" if (temp_slope > 0.05 or current_slope > 0.10) else "STABLE"

        for h_label in self.horizons:
            clf = self.models.get(h_label)
            if clf is None:
                continue

            probs = clf.predict_proba(feature_vec)[0]
            prob_val = float(probs[1]) if len(probs) > 1 else float(probs[0])

            # Determine Risk Level
            if prob_val >= 0.70:
                r_level = "CRITICAL" if h_label == "1h" else "HIGH"
            elif prob_val >= 0.40:
                r_level = "MEDIUM"
            else:
                r_level = "LOW"

            pred = FaultRiskPrediction(
                target_fault=FaultClass.MOTOR_OVERLOAD if "temperature" in str(trend_evidence) else FaultClass.DRY_WELL_PUMP_OFF,
                horizon_hours=horizon_hours_map.get(h_label, 1.0),
                horizon_label=h_label,
                probability=prob_val,
                risk_level=r_level,
                trend=trajectory_trend,
                evidence=trend_evidence if trend_evidence else ["Trajectory within nominal stability bands."]
            )
            predictions.append(pred)

        return predictions
