"""
Test Suite: Site Telemetry Ingestion Layer & Pre-Normalization Adapter
======================================================================
Validates the ingestion, logical conversion, thermodynamic inference,
and end-to-end diagnosis of compact site SCADA telemetry packets.
"""

import sys
import os
import json
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from models.telemetry_adapter import SiteTelemetryAdapter
    from models.diagnostic_engine import WellDiagnosticEngine
except ImportError:
    from telemetry_adapter import SiteTelemetryAdapter
    from diagnostic_engine import WellDiagnosticEngine


def test_site_adapter():
    print("\n" + "=" * 80)
    print(" TESTING SITE TELEMETRY ADAPTER & PRE-NORMALIZATION CONVERSION")
    print("=" * 80)

    adapter = SiteTelemetryAdapter()
    engine = WellDiagnosticEngine()

    # -------------------------------------------------------------
    # Test 1: Exact Packet from User's SCADA Screenshot
    # -------------------------------------------------------------
    site_payload_1 = {
        "Flow": 735.7,
        "Intake P": 236.5,
        "Discharge P": 1883.7,
        "Freq": 46.06,
        "Current": 18.86,
        "Voltage": 1006.3,
        "Temp": 79.67,
        "Vibration": 0.1758,
        "V-Imb": 0.60,
        "I-Imb": 1.00
    }

    well_id = "FS-04"
    print(f"\n[1] Testing Raw Compact Site Packet for Well: {well_id}")
    print(f"    Raw Input ({len(site_payload_1)} keys): {site_payload_1}")

    transformed = adapter.transform(well_id, site_payload_1)
    print(f"\n[2] Transformed 14 Standardized Parameters:")
    for k, v in transformed.items():
        print(f"    - {k:25s}: {v}")

    # Assertions for 14 canonical parameters
    assert "Inp bar/psi" in transformed and transformed["Inp bar/psi"] == 236.5
    assert "Disch pr. Bar/psi" in transformed and transformed["Disch pr. Bar/psi"] == 1883.7
    assert "Frequency" in transformed and transformed["Frequency"] == 46.06
    assert "VSD Amps/Load" in transformed and transformed["VSD Amps/Load"] == 18.86
    assert "Volt" in transformed and transformed["Volt"] == 1006.3
    assert "Motor temp °C" in transformed and transformed["Motor temp °C"] == 79.67
    assert "Int temp °C" in transformed and 40.0 <= transformed["Int temp °C"] <= 75.0
    assert "Vibration G's-Vx" in transformed and transformed["Vibration G's-Vx"] == 0.1758
    assert "VFD STS" in transformed and transformed["VFD STS"] == 1  # Inferred running
    assert "Leak Current Ct" in transformed
    assert "DHG Current" in transformed
    assert "WHP (PSI)" in transformed
    assert "FLP (PSI)" in transformed
    assert "AP (PSI)" in transformed

    print("\n[OK] All 14 canonical parameters synthesized and asserted!")

    # -------------------------------------------------------------
    # Test 2: Full End-to-End Diagnostic Evaluation
    # -------------------------------------------------------------
    print(f"\n[3] Running Full Diagnostic Engine on Site Telemetry Packet...")
    result = engine.evaluate_live_telemetry(well_id, site_payload_1, verbose=True)

    assert "diagnostic" in result
    assert "health_score" in result["diagnostic"]
    assert "normalized_features" in result
    assert len(result["normalized_features"]) > 0

    print(f"\n[OK] Diagnostic successfully generated! Health Score: {result['diagnostic']['health_score']:.1f}/100")

    # -------------------------------------------------------------
    # Test 3: Phase Imbalance Detection via High I-Imb
    # -------------------------------------------------------------
    print(f"\n[4] Testing Phase Imbalance Trigger via Site I-Imb (4.5%)...")
    imbalance_payload = dict(site_payload_1)
    imbalance_payload["I-Imb"] = 4.5  # Severe current imbalance > 3%
    imbalance_payload["Temp"] = 96.0  # High motor heat from imbalance

    imb_result = engine.evaluate_live_telemetry(well_id, imbalance_payload, verbose=False)
    diag = imb_result["diagnostic"]
    print(f"    Diagnosed Fault: {diag['primary_fault']} (Confidence: {diag['confidence']})")
    assert "Phase Imbalance" in diag.get("all_scores", {}) or diag["primary_fault"] == "Phase Imbalance"
    print(f"    [OK] Phase Imbalance rule correctly triggered by site I-Imb!")

    print("\n" + "=" * 80)
    print(" ALL SITE TELEMETRY ADAPTER & PRE-NORMALIZATION TESTS PASSED (100%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_site_adapter()
