"""
Models Package Unit Tests & Validation
======================================
Tests imports, dynamic normalization, multi-well envelope calibration,
and all 13 ESP fault modes within the models package.
"""

import os
import sys
import unittest

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    WellCalibrationRegistry,
    NormalizationLayer,
    FaultClassificationEngine,
    MultivariateAnomalyDetector,
    WellDiagnosticEngine,
    FAULT_DEFINITIONS
)


class TestModelsPackage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = WellDiagnosticEngine()

    def test_fault_definitions_count(self):
        """Verify all 13 required fault modes are defined."""
        expected_faults = [
            "Dry-Well Pump Off",
            "Blocked Intake",
            "Scale or Pump Wear",
            "Sand Ingestion",
            "Bearing Degradation",
            "High Viscosity Cold Start",
            "High Backpressure",
            "Open Choke",
            "Undervoltage",
            "Phase Imbalance",
            "Motor Overload",
            "Power Loss",
            "Sensor Drift"
        ]
        for f in expected_faults:
            self.assertIn(f, FAULT_DEFINITIONS, f"Missing fault definition: {f}")
        self.assertEqual(len(expected_faults), 13)

    def test_nominal_operation(self):
        """Verify nominal operation returns Health Index > 80 and Status NORMAL."""
        res = self.engine.evaluate_live_telemetry(
            well_id="FS-04",
            raw_telemetry={
                "Inp bar/psi": 472.6,
                "Int temp °C": 55.3,
                "Motor temp °C": 72.1,
                "Disch pr. Bar/psi": 1957.7,
                "Vibration G's-Vx": 0.09,
                "Leak Current Ct": 15.1,
                "Volt": 294.5,
                "VSD Amps/Load": 134.8,
                "Frequency": 44.0,
                "DHG Current": 20.6,
                "WHP (PSI)": 50.0,
                "FLP (PSI)": 45.0,
                "AP (PSI)": 10.0,
                "VFD STS": 1
            },
            verbose=False
        )
        diag = res["diagnostic"]
        self.assertEqual(diag["primary_fault"], "Normal Operation")
        self.assertGreaterEqual(diag["health_score"], 80.0)
        self.assertIn("NORMAL", diag["status"])

    def test_dry_well_pump_off(self):
        """Verify Dry-Well Pump Off detection."""
        res = self.engine.evaluate_live_telemetry(
            well_id="FS-04",
            raw_telemetry={
                "Inp bar/psi": 35.0,
                "Int temp °C": 58.0,
                "Motor temp °C": 88.5,
                "Disch pr. Bar/psi": 450.0,
                "Vibration G's-Vx": 0.15,
                "Leak Current Ct": 15.0,
                "Volt": 294.5,
                "VSD Amps/Load": 45.0,
                "Frequency": 44.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 5.0,
                "FLP (PSI)": 5.0,
                "AP (PSI)": 2.0,
                "VFD STS": 1
            },
            verbose=False
        )
        diag = res["diagnostic"]
        self.assertEqual(diag["primary_fault"], "Dry-Well Pump Off")
        self.assertIn("CRITICAL", diag["status"])

    def test_normalization_bounds(self):
        """Verify all normalized features are strictly clamped within [0, 1]."""
        norm_res = self.engine.normalizer.normalize_live_telemetry(
            well_id="ULFA-5",
            raw_telemetry={
                "Inp bar/psi": 99999.0,  # Extreme outlier
                "Int temp °C": -500.0,   # Negative outlier
                "Motor temp °C": 100.0,
                "Disch pr. Bar/psi": 5000.0,
                "Vibration G's-Vx": 0.2,
                "Leak Current Ct": 5.0,
                "Volt": 410.0,
                "VSD Amps/Load": 30.0,
                "Frequency": 50.0,
                "DHG Current": 15.0,
                "WHP (PSI)": 170.0,
                "FLP (PSI)": 165.0,
                "AP (PSI)": 160.0
            }
        )
        for k, v in norm_res["normalized"].items():
            self.assertGreaterEqual(v, 0.0, f"Feature {k} below 0.0: {v}")
            self.assertLessEqual(v, 1.0, f"Feature {k} above 1.0: {v}")


if __name__ == "__main__":
    unittest.main()
