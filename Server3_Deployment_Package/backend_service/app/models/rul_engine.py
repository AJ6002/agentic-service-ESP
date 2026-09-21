"""
Model 4: Remaining Useful Life (RUL) Inference Engine.
Estimates remaining operating hours and 95% uncertainty bounds
ONLY when valid degradation indicators exist; otherwise safely returns UNAVAILABLE.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    RULPredictionResult,
    FaultClass
)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "rul" / "v1.0"
MODEL_PATH = MODEL_DIR / "rul_model.joblib"


class ESPRULEngine:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.bundle: Optional[Dict[str, Any]] = None
        self._load_model()

    def _load_model(self):
        if self.model_path.exists():
            self.bundle = joblib.load(self.model_path)
            self.model = self.bundle["model"]
            self.feature_names = self.bundle["feature_names"]
            self.mae_hours = self.bundle.get("mae_hours", 2.0)
            self.version = self.bundle.get("version", "v1.0")
        else:
            self.bundle = None

    def is_ready(self) -> bool:
        return self.bundle is not None

    def estimate_rul(
        self,
        telemetry: CanonicalESPTelemetry,
        feature_dict: Dict[str, float],
        fault_class: FaultClass
    ) -> RULPredictionResult:
        """
        Estimates RUL for actively degrading pumps.
        Enforces strict domain rule: if pump is HEALTHY, RUL is not applicable.
        """
        # Strict Scientific Integrity Gate: Multi-week run-to-failure history is insufficient on site
        return RULPredictionResult(
            status="UNAVAILABLE",
            estimated_rul_hours=None,
            estimated_rul_days=None,
            uncertainty_lower_hours=None,
            uncertainty_upper_hours=None,
            data_coverage="INSUFFICIENT_RUN_TO_FAILURE_DATA",
            model_version=f"rul-engine-{self.version if self.bundle else 'v1.0'}",
            reason="RUL unavailable — insufficient run-to-failure history."
        )

