"""
CCED VFD Models Package
=======================
Exposes all diagnostic models, calibration registries, normalization layers,
and fault classifiers for real-time ESP telemetry anomaly detection.
"""

from .calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS, clean_col_key
from .telemetry_adapter import SiteTelemetryAdapter
from .normalization_layer import NormalizationLayer
from .fault_classifier import FaultClassificationEngine, FAULT_DEFINITIONS
from .anomaly_detector import MultivariateAnomalyDetector
from .diagnostic_engine import WellDiagnosticEngine

__all__ = [
    "WellCalibrationRegistry",
    "SiteTelemetryAdapter",
    "NormalizationLayer",
    "FaultClassificationEngine",
    "FAULT_DEFINITIONS",
    "MultivariateAnomalyDetector",
    "WellDiagnosticEngine",
    "STANDARD_SENSORS",
    "clean_col_key"
]
