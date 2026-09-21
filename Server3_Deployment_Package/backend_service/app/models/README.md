# CCED VFD Models Package

Comprehensive machine learning and physics-informed diagnostic models for Electric Submersible Pump (ESP) anomaly detection and failure classification across 73 CCED wells.

---

## Package Architecture

```
models/
├── __init__.py                   # Package exports & public API
├── calibration_registry.py       # WellCalibrationRegistry (73 well baseline envelopes & family fallbacks)
├── normalization_layer.py        # NormalizationLayer (Raw to [0, 1] scaling & physics dynamics)
├── fault_classifier.py           # FaultClassificationEngine (13 ESP failure modes)
├── anomaly_detector.py           # MultivariateAnomalyDetector (Isolation Forest model)
├── diagnostic_engine.py          # WellDiagnosticEngine (Main pipeline & Operator Intelligence Card)
├── well_calibration_registry.json# Active baseline statistical cache (73 wells)
├── test_models.py                # Unit test suite
└── README.md                     # Package documentation
```

---

## The 13 Supported Failure Modes

1. **Dry-Well Pump Off** (Fluid level collapse, underload current, cooling loss)
2. **Blocked Intake** (Suction starvation, $\Delta P \rightarrow 0$)
3. **Scale or Pump Wear** (Head loss at constant $50\,\text{Hz}$)
4. **Sand Ingestion** (Abrasive vibration surges $>0.30\,\text{G}$ + torque spikes)
5. **Bearing Degradation** (Severe vibration $>0.35\,\text{G}$ + friction motor heating)
6. **High Viscosity Cold Start** (Low Hz startup with heavy starting drag)
7. **High Backpressure** (Surface flowline restriction elevating discharge)
8. **Open Choke** (Zero wellhead pressure + runout flow overload)
9. **Undervoltage** (Grid voltage sag causing current surges)
10. **Phase Imbalance** (Ground insulation breakdown $>25\,\text{mA}$ + unbalanced heating)
11. **Motor Overload** (Continuous excessive amperage $>128\%$ rated)
12. **Power Loss** (Zero volts, zero amps, zero Hz)
13. **Sensor Drift** (Non-physical negative readings or flatlined transmitter)

---

## Quick Usage

```python
from models import WellDiagnosticEngine

# Initialize engine
engine = WellDiagnosticEngine()

# Live telemetry inference
result = engine.evaluate_live_telemetry(
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
    verbose=True
)
```
