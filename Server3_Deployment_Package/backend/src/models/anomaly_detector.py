"""
Multivariate Machine Learning Anomaly Detector Component
========================================================
Unsupervised machine learning model using Per-Family Isolation Forests to detect
multivariate outliers and anomalous operating vectors across the 13 normalized sensor dimensions.

Trained and calibrated against Digital Twin nominal operating profiles:
- B400 family
- B538 family
- TD family
- TE2700 family
- FIELD_SCADA family
- FLEET_GLOBAL fallback
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

logger = logging.getLogger(__name__)

# Family alias mapping
FAMILY_ALIAS_MAP = {
    "B400": "b400",
    "B538": "b538",
    "TD": "td",
    "TE2700": "te2700",
    "FIELD_SCADA": "field_scada",
    "FLEET_GLOBAL": "fleet_global"
}


class StatisticalFallbackModel:
    """
    Deterministic statistical envelope fallback when pre-trained joblib model is unavailable.
    Evaluates multi-sensor boundary deviations without relying on random Gaussian noise.
    """
    def __init__(self, n_features: int = 13):
        self.n_features = n_features

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        # X is (N, 13) normalized in [0, 1].
        scores = []
        for row in X:
            # Extreme boundary breaches (stuck at exact min or max 0.0 or 1.0)
            breaches = np.sum((row <= 0.005) | (row >= 0.995))
            if breaches >= 3:
                scores.append(-0.15)
            elif breaches >= 2:
                scores.append(-0.08)
            elif breaches >= 1:
                scores.append(0.02)
            else:
                scores.append(0.12)
        return np.array(scores, dtype=float)


class MultivariateAnomalyDetector:
    """
    Per-Family Calibrated Isolation Forest Anomaly Detector:
    Loads pre-trained family models to flag multi-sensor correlation breakdowns
    against each well's specific pump curve and nominal envelope.
    """

    _loaded_models: Dict[str, Any] = {}
    _metadata: Optional[Dict[str, Any]] = None

    def __init__(self, contamination: float = 0.01, random_state: int = 42, models_dir: Optional[str] = None):
        self.contamination = contamination
        self.random_state = random_state
        
        # Locate trained models directory
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            candidates = [
                current_dir / "trained_models",
                current_dir.parent / "models" / "trained_models",
                current_dir.parent / "trained_models",
                Path(__file__).resolve().parents[2] / "code" / "models" / "trained_models"
            ]
            self.models_dir = None
            for c in candidates:
                if c.exists() and (c / "models_metadata.json").exists():
                    self.models_dir = c
                    break
            if not self.models_dir:
                self.models_dir = candidates[0]

        self._load_metadata()

    def _load_metadata(self):
        if MultivariateAnomalyDetector._metadata is not None:
            return
        if self.models_dir and (self.models_dir / "models_metadata.json").exists():
            try:
                with open(self.models_dir / "models_metadata.json", "r", encoding="utf-8") as f:
                    MultivariateAnomalyDetector._metadata = json.load(f)
            except Exception:
                MultivariateAnomalyDetector._metadata = {}
        else:
            MultivariateAnomalyDetector._metadata = {}

    def _get_family_model(self, family: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
        """Returns the pre-trained IsolationForest for the given family, or FLEET_GLOBAL."""
        fam_key = "FLEET_GLOBAL"
        if family:
            f_upper = str(family).strip().upper()
            for k in ["B400", "B538", "TD", "TE2700", "FIELD_SCADA"]:
                if k in f_upper or f_upper in k:
                    fam_key = k
                    break

        if fam_key in MultivariateAnomalyDetector._loaded_models:
            cached_model = MultivariateAnomalyDetector._loaded_models[fam_key]
            fam_meta = dict((MultivariateAnomalyDetector._metadata.get("families", {}).get(fam_key, {})
                        if MultivariateAnomalyDetector._metadata else {}))
            fam_meta["model_source"] = "STATISTICAL_FALLBACK" if isinstance(cached_model, StatisticalFallbackModel) else "PRETRAINED_JOB_LIB"
            return cached_model, fam_meta

        # Attempt to load model from disk
        if self.models_dir and self.models_dir.exists():
            fname = f"{fam_key.lower()}_isolation_forest.joblib"
            m_path = self.models_dir / fname
            if not m_path.exists():
                # Fallback to fleet_global
                m_path = self.models_dir / "fleet_global_isolation_forest.joblib"

            if m_path.exists():
                try:
                    loaded = joblib.load(m_path)
                    MultivariateAnomalyDetector._loaded_models[fam_key] = loaded
                    fam_meta = dict((MultivariateAnomalyDetector._metadata.get("families", {}).get(fam_key, {})
                                if MultivariateAnomalyDetector._metadata else {}))
                    fam_meta["model_source"] = "PRETRAINED_JOB_LIB"
                    return loaded, fam_meta
                except Exception as exc:
                    logger.error("[AnomalyDetector] Model load error for %s from %s: %s", fam_key, m_path, exc, exc_info=True)

        # Fallback inline statistical model (deterministic envelope, never random Gaussian noise)
        logger.warning("[AnomalyDetector] Using statistical envelope fallback for family %s", fam_key)
        fallback = StatisticalFallbackModel(n_features=13)
        fam_meta = {
            "model_source": "STATISTICAL_FALLBACK",
            "nominal_score_mean": 0.10,
            "nominal_score_p5": 0.02,
            "nominal_score_min": -0.05,
            "sigmoid_midpoint": -0.08
        }
        MultivariateAnomalyDetector._loaded_models[fam_key] = fallback
        return fallback, fam_meta

    def score_sample(self, norm_vector: List[float], family: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes anomaly score and outlier flag for a single normalized [0, 1] vector.
        Uses calibrated per-family thresholding grounded in Digital Twin baseline profiles.
        """
        X = np.array(norm_vector, dtype=float).reshape(1, -1)
        model, fam_meta = self._get_family_model(family)

        raw_score = float(model.decision_function(X)[0])
        
        # Calibrated decision boundary:
        nominal_p5 = float(fam_meta.get("nominal_score_p5", 0.02))
        nominal_mean = float(fam_meta.get("nominal_score_mean", 0.10))
        nominal_min = float(fam_meta.get("nominal_score_min", nominal_p5 - 0.05))

        # Midpoint safely below nominal minimum envelope so healthy wells don't trip false positives:
        sigmoid_midpoint = min(float(fam_meta.get("sigmoid_midpoint", nominal_min - 0.035)), nominal_min - 0.035)
        
        # Logistic sigmoid probability calibrated against nominal score distribution
        k = 30.0
        prob = float(1.0 / (1.0 + np.exp(k * (raw_score - sigmoid_midpoint))))
        prob = float(np.clip(prob, 0.01, 0.99))
        is_outlier = bool(raw_score < sigmoid_midpoint or prob >= 0.50)

        return {
            "is_anomaly": is_outlier,
            "raw_decision_score": round(raw_score, 4),
            "anomaly_probability": round(prob, 4),
            "family_used": family or "FLEET_GLOBAL",
            "nominal_baseline_mean": round(nominal_mean, 4),
            "model_source": fam_meta.get("model_source", "PRETRAINED_JOB_LIB")
        }
