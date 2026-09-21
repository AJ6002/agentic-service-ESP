"""
CCED VFD Fault Scenario Testing & Validation Harness
====================================================
Validates the WellDiagnosticEngine and Normalization Layer against:
1. Nominal baseline telemetry across multiple well types (FS-04, ULFA-5, FNW-01, FWS-012).
2. All 13 Specific Well Fault Modes:
   - Dry-Well Pump Off
   - Blocked Intake
   - Scale or Pump Wear
   - Sand Ingestion
   - Bearing Degradation
   - High Viscosity Cold Start
   - High Backpressure
   - Open Choke
   - Undervoltage
   - Phase Imbalance
   - Motor Overload
   - Power Loss
   - Sensor Drift
"""

import sys
import time
import os
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
    from models.diagnostic_engine import WellDiagnosticEngine
except ImportError:
    from diagnostic_engine import WellDiagnosticEngine



def run_all_tests():
    print("\n" + "#" * 80)
    print(" CCED VFD DIAGNOSTIC ENGINE: 13-FAULT VALIDATION SUITE")
    print("#" * 80 + "\n")

    engine = WellDiagnosticEngine()

    test_cases = [
        {
            "name": "Test 1: Normal Nominal Operation (Well FS-04)",
            "well_id": "FS-04",
            "telemetry": {
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
            "expected_fault": "Normal Operation"
        },
        {
            "name": "Test 2: Normal Operation on High-Pressure Well (ULFA-5)",
            "well_id": "ULFA-5",
            "telemetry": {
                "Inp bar/psi": 1939.8,
                "Int temp °C": 92.6,
                "Motor temp °C": 102.1,
                "Disch pr. Bar/psi": 5342.5,
                "Vibration G's-Vx": 0.20,
                "Leak Current Ct": 5.0,
                "Volt": 410.3,
                "VSD Amps/Load": 30.2,
                "Frequency": 49.0,
                "DHG Current": 15.0,
                "WHP (PSI)": 171.5,
                "FLP (PSI)": 168.5,
                "AP (PSI)": 168.4,
                "VFD STS": 1
            },
            "expected_fault": "Normal Operation"
        },
        {
            "name": "Fault 1: Dry-Well Pump Off (Intake Collapse + Underload Amps)",
            "well_id": "FS-04",
            "telemetry": {
                "Inp bar/psi": 35.0,        # Sump drained below pump
                "Int temp °C": 58.0,
                "Motor temp °C": 88.5,       # Overheating due to lack of cooling flow
                "Disch pr. Bar/psi": 450.0,
                "Vibration G's-Vx": 0.15,
                "Leak Current Ct": 15.0,
                "Volt": 294.5,
                "VSD Amps/Load": 45.0,       # Severe underload (running dry)
                "Frequency": 44.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 5.0,
                "FLP (PSI)": 5.0,
                "AP (PSI)": 2.0,
                "VFD STS": 1
            },
            "expected_fault": "Dry-Well Pump Off"
        },
        {
            "name": "Fault 2: Blocked Intake Screen (Suction Starved, Zero DeltaP)",
            "well_id": "FNW-01",
            "telemetry": {
                "Inp bar/psi": 15.0,         # Severe suction starvation
                "Int temp °C": 48.0,
                "Motor temp °C": 74.0,
                "Disch pr. Bar/psi": 120.0,  # Discharge pressure collapsed
                "Vibration G's-Vx": 0.12,
                "Leak Current Ct": 8.0,
                "Volt": 380.0,
                "VSD Amps/Load": 30.0,       # Motor underload (no work done)
                "Frequency": 50.0,
                "DHG Current": 18.0,
                "WHP (PSI)": 2.0,
                "FLP (PSI)": 2.0,
                "AP (PSI)": 5.0,
                "VFD STS": 1
            },
            "expected_fault": "Blocked Intake"
        },
        {
            "name": "Fault 3: Scale or Pump Wear (Loss of Head at Constant Speed)",
            "well_id": "FS-06",
            "telemetry": {
                "Inp bar/psi": 155.0,        # Normal intake (baseline ~154 PSI)
                "Int temp °C": 52.0,
                "Motor temp °C": 75.0,
                "Disch pr. Bar/psi": 650.0,  # DeltaP dropped significantly to 495 PSI (normal head ~1500 PSI)
                "Vibration G's-Vx": 0.18,
                "Leak Current Ct": 12.0,
                "Volt": 405.0,
                "VSD Amps/Load": 92.0,       # Normal running amps (baseline ~93 A)
                "Frequency": 50.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 20.0,
                "FLP (PSI)": 18.0,
                "AP (PSI)": 8.0,
                "VFD STS": 1
            },
            "expected_fault": "Scale or Pump Wear"
        },
        {
            "name": "Fault 4: Sand Ingestion (Abrasive Friction, High Vibration & Current Spikes)",
            "well_id": "FS-101",
            "telemetry": {
                "Inp bar/psi": 380.0,
                "Int temp °C": 54.0,
                "Motor temp °C": 78.0,
                "Disch pr. Bar/psi": 1850.0,
                "Vibration G's-Vx": 0.42,    # Abrasive mechanical turbulence
                "Leak Current Ct": 14.0,
                "Volt": 320.0,
                "VSD Amps/Load": 175.0,      # Solids friction torque spike (+50% load)
                "Frequency": 48.0,
                "DHG Current": 19.0,
                "WHP (PSI)": 55.0,
                "FLP (PSI)": 50.0,
                "AP (PSI)": 15.0,
                "VFD STS": 1
            },
            "expected_fault": "Sand Ingestion"
        },
        {
            "name": "Fault 5: Bearing Degradation (Severe Vibration & Heat)",
            "well_id": "FS-110",
            "telemetry": {
                "Inp bar/psi": 450.0,
                "Int temp °C": 55.0,
                "Motor temp °C": 91.0,       # Friction heat from bearing
                "Disch pr. Bar/psi": 1920.0,
                "Vibration G's-Vx": 0.48,    # Severe radial bearing wear (> 0.35 G)
                "Leak Current Ct": 15.0,
                "Volt": 300.0,
                "VSD Amps/Load": 58.0,       # Normal electrical load with bearing failure
                "Frequency": 45.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 48.0,
                "FLP (PSI)": 45.0,
                "AP (PSI)": 12.0,
                "VFD STS": 1
            },
            "expected_fault": "Bearing Degradation"
        },
        {
            "name": "Fault 6: High Viscosity Cold Start (Low Hz, Extreme Starting Amps)",
            "well_id": "FWS-012",
            "telemetry": {
                "Inp bar/psi": 580.0,
                "Int temp °C": 28.0,         # Cold crude
                "Motor temp °C": 45.0,
                "Disch pr. Bar/psi": 750.0,
                "Vibration G's-Vx": 0.08,
                "Leak Current Ct": 5.0,
                "Volt": 480.0,
                "VSD Amps/Load": 720.0,      # Extreme starting current (>150% rated)
                "Frequency": 32.0,           # Low startup frequency
                "DHG Current": 15.0,
                "WHP (PSI)": 20.0,
                "FLP (PSI)": 18.0,
                "AP (PSI)": 5.0,
                "VFD STS": 1
            },
            "expected_fault": "High Viscosity Cold Start"
        },
        {
            "name": "Fault 7: High Backpressure (Surface Flowline Restriction)",
            "well_id": "FS-04",
            "telemetry": {
                "Inp bar/psi": 460.0,
                "Int temp °C": 55.0,
                "Motor temp °C": 79.0,
                "Disch pr. Bar/psi": 2650.0, # Forced abnormally high
                "Vibration G's-Vx": 0.12,
                "Leak Current Ct": 15.0,
                "Volt": 294.5,
                "VSD Amps/Load": 142.0,
                "Frequency": 44.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 185.0,          # High wellhead pressure
                "FLP (PSI)": 178.0,          # Flowline restriction
                "AP (PSI)": 15.0,
                "VFD STS": 1
            },
            "expected_fault": "High Backpressure"
        },
        {
            "name": "Fault 8: Open Choke (Runout Flow Condition, High Amps)",
            "well_id": "FS-201",
            "telemetry": {
                "Inp bar/psi": 420.0,
                "Int temp °C": 52.0,
                "Motor temp °C": 76.0,
                "Disch pr. Bar/psi": 950.0,  # Discharge dropped significantly due to zero backpressure
                "Vibration G's-Vx": 0.15,
                "Leak Current Ct": 10.0,
                "Volt": 540.0,
                "VSD Amps/Load": 165.0,      # High runout amps (+70% load)
                "Frequency": 50.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 2.0,            # Choke wide open (nominal ~213 PSI)
                "FLP (PSI)": 2.0,
                "AP (PSI)": 5.0,
                "VFD STS": 1
            },
            "expected_fault": "Open Choke"
        },
        {
            "name": "Fault 9: Undervoltage (Surface Grid Sag Causing High Current)",
            "well_id": "FS-04",
            "telemetry": {
                "Inp bar/psi": 470.0,
                "Int temp °C": 55.0,
                "Motor temp °C": 82.0,
                "Disch pr. Bar/psi": 1950.0,
                "Vibration G's-Vx": 0.10,
                "Leak Current Ct": 15.0,
                "Volt": 215.0,               # Voltage sag (nominal ~295 V)
                "VSD Amps/Load": 162.0,      # Drawing extra current to maintain kW
                "Frequency": 44.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 50.0,
                "FLP (PSI)": 45.0,
                "AP (PSI)": 10.0,
                "VFD STS": 1
            },
            "expected_fault": "Undervoltage"
        },
        {
            "name": "Fault 10: Phase Imbalance (Insulation Breakdown & Heating)",
            "well_id": "FS-16",
            "telemetry": {
                "Inp bar/psi": 220.0,
                "Int temp °C": 51.0,
                "Motor temp °C": 96.5,       # Severe unbalanced heating
                "Disch pr. Bar/psi": 1800.0,
                "Vibration G's-Vx": 0.28,
                "Leak Current Ct": 38.5,     # High ground leakage current
                "Volt": 310.0,
                "VSD Amps/Load": 98.0,
                "Frequency": 45.0,
                "DHG Current": 19.0,
                "WHP (PSI)": 40.0,
                "FLP (PSI)": 35.0,
                "AP (PSI)": 12.0,
                "VFD STS": 1
            },
            "expected_fault": "Phase Imbalance"
        },
        {
            "name": "Fault 11: Motor Overload (Continuous Extreme Amperage)",
            "well_id": "FS-201",
            "telemetry": {
                "Inp bar/psi": 410.0,
                "Int temp °C": 56.0,
                "Motor temp °C": 94.0,       # Approaching thermal trip limit
                "Disch pr. Bar/psi": 1980.0,
                "Vibration G's-Vx": 0.18,
                "Leak Current Ct": 14.0,
                "Volt": 540.0,               # Normal rated voltage
                "VSD Amps/Load": 185.0,      # Continuous overload (+90% over rated)
                "Frequency": 50.0,
                "DHG Current": 20.0,
                "WHP (PSI)": 60.0,
                "FLP (PSI)": 55.0,
                "AP (PSI)": 15.0,
                "VFD STS": 1
            },
            "expected_fault": "Motor Overload"
        },
        {
            "name": "Fault 12: Power Loss (Grid / VFD Tripped to Zero)",
            "well_id": "FS-04",
            "telemetry": {
                "Inp bar/psi": 472.0,
                "Int temp °C": 55.0,
                "Motor temp °C": 68.0,
                "Disch pr. Bar/psi": 480.0,
                "Vibration G's-Vx": 0.0,
                "Leak Current Ct": 0.0,
                "Volt": 0.0,                 # Zero Volts
                "VSD Amps/Load": 0.0,        # Zero Amps
                "Frequency": 0.0,            # Zero Hz
                "DHG Current": 0.0,
                "WHP (PSI)": 10.0,
                "FLP (PSI)": 8.0,
                "AP (PSI)": 5.0,
                "VFD STS": 0                 # Pump stopped
            },
            "expected_fault": "Power Loss"
        },
        {
            "name": "Fault 13: Sensor Drift / Telemetry Integrity Fault",
            "well_id": "FS-200",
            "telemetry": {
                "Inp bar/psi": -150.0,       # Non-physical negative pressure
                "Int temp °C": 50.0,
                "Motor temp °C": 70.0,
                "Disch pr. Bar/psi": 1800.0,
                "Vibration G's-Vx": 0.10,
                "Leak Current Ct": 10.0,
                "Volt": 380.0,
                "VSD Amps/Load": 60.0,
                "Frequency": 50.0,
                "DHG Current": 15.0,
                "WHP (PSI)": 40.0,
                "FLP (PSI)": 35.0,
                "AP (PSI)": 10.0,
                "VFD STS": 1
            },
            "expected_fault": "Sensor Drift"
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, tc in enumerate(test_cases):
        # Print rich diagnostic card for the first nominal and first critical fault
        is_verbose = (i == 0 or i == 2)
        if is_verbose:
            print("\n" + "=" * 80)
            print(f" DEMONSTRATING FULL OPERATOR DIAGNOSTIC CARD: {tc['name']}")
            print("=" * 80)

        res = engine.evaluate_live_telemetry(
            well_id=tc["well_id"],
            raw_telemetry=tc["telemetry"],
            verbose=is_verbose
        )
        diag = res["diagnostic"]
        detected = diag["primary_fault"]
        expected = tc["expected_fault"]

        if detected == expected:
            print(f" [PASS] {tc['name']:68s} -> {detected} ({diag['confidence']})")
            passed += 1
        else:
            print(f" [FAIL] {tc['name']}")
            print(f"        Expected: {expected} | Diagnosed: {detected}")
            print(f"        All Scores: {diag['all_scores']}")



    print("\n" + "#" * 80)
    print(f" VALIDATION SUMMARY: {passed} / {total} Test Scenarios Passed ({passed/total*100:.1f}%)")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    run_all_tests()
