"""
Main Well Diagnostic Engine Component
=====================================
Orchestrates live telemetry ingestion, dynamic normalization, multi-well calibration,
physics feature extraction, ML anomaly detection, and 13-fault diagnostic card generation.
"""

import os
import sys
import datetime
from typing import Dict, List, Tuple, Optional, Any
from .calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS, clean_col_key
from .telemetry_adapter import SiteTelemetryAdapter
from .normalization_layer import NormalizationLayer
from .fault_classifier import FaultClassificationEngine, FAULT_DEFINITIONS
from .anomaly_detector import MultivariateAnomalyDetector

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class WellDiagnosticEngine:
    """
    Main Multi-Well Diagnostic Engine:
    Orchestrates real-time telemetry normalization, physics extraction, and 13-fault mode classification.
    """

    def __init__(
        self,
        categorized_dir: str = r"C:\Users\admin.DESKTOP-17T37DJ\Desktop\cced\categorized_wells",
        registry_file: Optional[str] = None
    ):
        self.registry = WellCalibrationRegistry(categorized_dir=categorized_dir, registry_file=registry_file)
        self.adapter = SiteTelemetryAdapter(self.registry)
        self.normalizer = NormalizationLayer(self.registry)
        self.classifier = FaultClassificationEngine()
        self.anomaly_detector = MultivariateAnomalyDetector()

    def evaluate_live_telemetry(
        self,
        well_id: str,
        raw_telemetry: Dict[str, Any],
        prev_telemetry: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Ingests a raw, un-normalized live site telemetry packet, standardizes it via SiteTelemetryAdapter,
        normalizes it, and returns the diagnostic card.
        """
        # 0. Pre-normalization Site Telemetry Adapter (Logical 14-parameter conversion & inference)
        std_telemetry = self.adapter.transform(well_id, raw_telemetry)
        std_prev = self.adapter.transform(well_id, prev_telemetry) if prev_telemetry is not None else None

        # 1. Real-time normalization and dynamics computation
        norm_result = self.normalizer.normalize_live_telemetry(well_id, std_telemetry, std_prev)
        norm_vector = list(norm_result["normalized"].values())

        # 2. ML Anomaly scoring (Per-Family Calibrated Isolation Forest)
        family = norm_result.get("family", "FIELD_SCADA")
        ml_anomaly = self.anomaly_detector.score_sample(norm_vector, family=family)

        # 3. Fault classification with dynamic Out-of-Spec setpoint checking
        profile = self.registry.get_well_profile(well_id)
        diagnostic = self.classifier.diagnose(
            well_id=well_id,
            norm_data=norm_result["normalized"],
            raw_data=norm_result["raw"],
            dynamics=norm_result["dynamics"],
            profile=profile
        )

        # Reconcile: If Isolation Forest flags a high-confidence anomaly corroborated by physical deviations:
        anom_prob = float(ml_anomaly.get("anomaly_probability", 0.0))
        has_deviations = len(diagnostic.get("out_of_spec_parameters", [])) > 0
        
        if ml_anomaly.get("is_anomaly") and anom_prob >= 0.70 and has_deviations and diagnostic.get("is_healthy", True):
            diagnostic["is_healthy"] = False
            diagnostic["status"] = "🟡 WATCHLIST"
            diagnostic["confidence"] = f"{anom_prob * 100:.1f}%"
            diagnostic["confidence_val"] = anom_prob
            diagnostic["health_score"] = min(float(diagnostic.get("health_score", 95.0)), 70.0)
            causes_text = " and ".join([item["text"] for item in diagnostic["out_of_spec_parameters"][:3]])
            verdict = f"Anomaly is Detected, According to the ML Suggestions it Can be 'Multivariate Telemetry Anomaly', Due to {causes_text}"
            diagnostic["canonical_verdict"] = verdict
            diagnostic["model_output"] = verdict
            diagnostic["primary_fault"] = "Multivariate Telemetry Anomaly"

        result = {
            "well_id": well_id,
            "family": norm_result["family"],
            "timestamp": raw_telemetry.get("Report_DateTime", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "diagnostic": diagnostic,
            "ml_anomaly": ml_anomaly,
            "dynamics": norm_result["dynamics"],
            "normalized_features": norm_result["normalized"],
            "raw_measurements": norm_result["raw"],
            "standardized_14_params": std_telemetry
        }

        if verbose:
            self.print_diagnostic_card(result)

        return result

    @staticmethod
    def print_diagnostic_card(result: Dict[str, Any]):
        """Prints a rich, formatted Operator Diagnostic Intelligence Card to console."""
        d = result["diagnostic"]
        dyn = result["dynamics"]
        well = result["well_id"]
        fam = result["family"]

        print("\n" + "=" * 80)
        print(f" CCED VFD DIAGNOSTIC INTELLIGENCE CARD | WELL: {well} ({fam})")
        print(f" Timestamp: {result['timestamp']} | Status: {d['status']}")
        print("=" * 80)
        print(f"  Health Index:            {d['health_score']:.1f} / 100")
        print(f"  Primary Fault Diagnosis: {d['primary_fault']} (Confidence: {d['confidence']})")
        print(f"  Est. Time-to-Trip:       {d['est_time_to_trip']}")
        print("-" * 80)
        print("  FAULT DESCRIPTION:")
        print(f"   {d['description']}")
        print("-" * 80)
        print("  PRIMARY ROOT-CAUSE DRIVERS:")
        for driver_name, driver_val in d["root_cause_drivers"]:
            print(f"   ■ {driver_name:20s}: {driver_val}")
        print("-" * 80)
        print("  KEY DYNAMICS:")
        print(f"   ΔP (Head): {dyn['delta_p']} PSI | Torque Proxy: {dyn['torque_proxy']} A/Hz | Power: {dyn['power_proxy_kva']} kVA")
        vib_val = result['raw_measurements'].get("Vibration G's-Vx", 0.0)
        mot_temp_val = result['raw_measurements'].get('Motor temp °C', 0.0)
        print(f"   Thermal Elevation: {dyn['thermal_elevation']} °C | Motor Temp: {mot_temp_val} °C | Vib: {vib_val} G")
        print("-" * 80)
        print("  RECOMMENDED OPERATOR ACTION:")
        print(f"   👉 {d['action_advisory']}")
        print("=" * 80 + "\n")
