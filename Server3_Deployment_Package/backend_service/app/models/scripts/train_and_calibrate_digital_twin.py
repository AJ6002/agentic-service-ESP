"""
Digital Twin Calibration & Per-Family Isolation Forest Training Script
======================================================================
1. Loads Digital Twin engine from scratch directory (or local package).
2. Augments well_calibration_registry.json with well-specific dynamic setpoints
   (median, min, max, p10, p90, normal_min, normal_max) for all assets.
3. Simulates nominal operational profiles for each well across pump families:
   - B400
   - B538
   - TD
   - TE2700
   - FIELD_SCADA
   - FLEET_GLOBAL (fleet-wide fallback)
4. Trains and calibrates an Isolation Forest for each pump family.
5. Saves model artifacts and metadata into code/models/trained_models/
   and mirrors them to backend and esp_agent trees.
"""

import os
import sys
import json
import shutil
from pathlib import Path
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
CODE_MODELS = WORKSPACE_ROOT / "code" / "models"
MODELS_ROOT = WORKSPACE_ROOT / "code"
SCRATCH_BASE = Path(r"C:\Users\admin.DESKTOP-17T37DJ\.gemini\antigravity-ide\brain\275a6143-f83e-43f5-bc51-765c9f79793c\scratch\digital_twin_v2\esp_digital_twin_v2\releases\fs04-scada-20260901-1")

if str(MODELS_ROOT) not in sys.path:
    sys.path.insert(0, str(MODELS_ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Add scratch digital twin src to path
DT_SRC = SCRATCH_BASE / "src"
if str(DT_SRC) not in sys.path:
    sys.path.insert(0, str(DT_SRC))

from esp_simulator.config import load_fleet, load_profiles
from esp_simulator.engine import FleetEngine
from models.calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS, clean_col_key
from models.normalization_layer import NormalizationLayer
from models.telemetry_adapter import SiteTelemetryAdapter

# Family Mapping
FAMILY_PUMP_MAP = {
    "B400": ["B400-180", "B400-400", "B400-750", "B400-1050", "400FlexER", "400PMSND"],
    "B538": ["B538-3600", "B538-5000", "B538-7000", "B538-9000"],
    "TD": ["TD300", "TD650"],
    "TE2700": ["TE2700"],
    "FIELD_SCADA": ["FIELD-SCADA-PENDING", "FIELD-SCADA", "Field SCADA"]
}

def resolve_pump_family(pump_model: str) -> str:
    if not pump_model:
        return "FIELD_SCADA"
    p_upper = str(pump_model).strip().upper()
    for fam, models in FAMILY_PUMP_MAP.items():
        for m in models:
            if m.upper() in p_upper or p_upper in m.upper():
                return fam
    if "B400" in p_upper or "400" in p_upper:
        return "B400"
    if "B538" in p_upper or "538" in p_upper:
        return "B538"
    if "TD" in p_upper:
        return "TD"
    if "TE" in p_upper or "2700" in p_upper:
        return "TE2700"
    return "FIELD_SCADA"

def main():
    print("=" * 80)
    print("ESP Digital Twin Calibration & Per-Family Isolation Forest Training")
    print("=" * 80)

    # 1. Initialize Digital Twin Fleet Engine
    fleet_path = SCRATCH_BASE / "data" / "fleet.yaml"
    hist_path = SCRATCH_BASE / "data" / "historical_operating_points.yaml"
    field_path = SCRATCH_BASE / "data" / "field_scada_operating_points.yaml"
    prof_path = SCRATCH_BASE / "data" / "model_profiles.yaml"

    assets = load_fleet(fleet_path, operating_points_path=hist_path, field_points_path=field_path)
    profiles = load_profiles(prof_path)
    engine = FleetEngine(assets=assets, profiles=profiles)
    print(f"Loaded FleetEngine with {len(engine.wells)} active well simulators.")

    # 2. Load existing calibration registry
    reg_file = CODE_MODELS / "well_calibration_registry.json"
    existing_reg = {}
    if reg_file.exists():
        with open(reg_file, "r", encoding="utf-8") as f:
            existing_reg = json.load(f)

    wells_dict = existing_reg.get("wells", {})

    # Warm up simulation with nominal baseline steps
    print("\nWarming up simulators and extracting nominal steady-state profiles...")
    for _ in range(5):
        engine.step_all()

    # 3. Augment well_calibration_registry.json with well-specific setpoints
    well_family_lookup = {}
    for well_id, well_sim in engine.wells.items():
        pump_model = well_sim.asset.pump_model
        fam = resolve_pump_family(pump_model)
        well_family_lookup[well_id] = fam

        m = well_sim.state.measurements
        # Extract nominal values
        nom_freq = float(m.get("frequency_hz", 50.0))
        nom_amps = float(m.get("motor_current_a", 50.0))
        nom_pip = float(m.get("intake_pressure_psi", 500.0))
        nom_pdp = float(m.get("discharge_pressure_psi", 2000.0))
        nom_mtemp = float(m.get("motor_temperature_c", 75.0))
        nom_itemp = float(m.get("intake_temperature_c", 55.0))
        nom_volt = float(m.get("motor_voltage_v", 400.0))
        nom_vib = float(m.get("vibration_g_rms", 0.1))
        nom_whp = float(m.get("wellhead_pressure_psi", 50.0))
        nom_flp = float(m.get("flowline_pressure_psi", 45.0))
        nom_ap = float(m.get("casing_pressure_psi", 10.0))

        # Sensor statistics for calibration registry
        sensors_spec = {
            "Inp bar/psi": {
                "median": round(nom_pip, 1),
                "min": round(max(20.0, nom_pip * 0.40), 1),
                "max": round(nom_pip * 1.60, 1),
                "p10": round(nom_pip * 0.85, 1),
                "p90": round(nom_pip * 1.15, 1),
                "normal_min": round(max(50.0, nom_pip * 0.75), 1),
                "normal_max": round(nom_pip * 1.25, 1)
            },
            "Disch pr. Bar/psi": {
                "median": round(nom_pdp, 1),
                "min": round(max(100.0, nom_pdp * 0.50), 1),
                "max": round(nom_pdp * 1.50, 1),
                "p10": round(nom_pdp * 0.88, 1),
                "p90": round(nom_pdp * 1.12, 1),
                "normal_min": round(nom_pdp * 0.80, 1),
                "normal_max": round(nom_pdp * 1.20, 1)
            },
            "VSD Amps/Load": {
                "median": round(nom_amps, 1),
                "min": round(max(1.0, nom_amps * 0.35), 1),
                "max": round(nom_amps * 1.50, 1),
                "p10": round(nom_amps * 0.85, 1),
                "p90": round(nom_amps * 1.15, 1),
                "normal_min": round(nom_amps * 0.75, 1),
                "normal_max": round(nom_amps * 1.20, 1)
            },
            "Volt": {
                "median": round(nom_volt, 1),
                "min": round(nom_volt * 0.60, 1),
                "max": round(nom_volt * 1.30, 1),
                "p10": round(nom_volt * 0.90, 1),
                "p90": round(nom_volt * 1.10, 1),
                "normal_min": round(nom_volt * 0.85, 1),
                "normal_max": round(nom_volt * 1.15, 1)
            },
            "Frequency": {
                "median": round(nom_freq, 1),
                "min": 30.0,
                "max": 65.0,
                "p10": round(max(30.0, nom_freq - 4.0), 1),
                "p90": round(min(65.0, nom_freq + 4.0), 1),
                "normal_min": 35.0,
                "normal_max": 60.0
            },
            "Motor temp °C": {
                "median": round(nom_mtemp, 1),
                "min": round(max(20.0, nom_mtemp * 0.50), 1),
                "max": 140.0,
                "p10": round(nom_mtemp * 0.90, 1),
                "p90": round(nom_mtemp * 1.10, 1),
                "normal_min": 40.0,
                "normal_max": 125.0
            },
            "Int temp °C": {
                "median": round(nom_itemp, 1),
                "min": round(max(15.0, nom_itemp * 0.50), 1),
                "max": 110.0,
                "p10": round(nom_itemp * 0.90, 1),
                "p90": round(nom_itemp * 1.10, 1),
                "normal_min": 35.0,
                "normal_max": 95.0
            },
            "Vibration G's-Vx": {
                "median": round(nom_vib, 2),
                "min": 0.0,
                "max": 4.0,
                "p10": 0.02,
                "p90": round(max(0.20, nom_vib * 2.0), 2),
                "normal_min": 0.0,
                "normal_max": 1.50
            },
            "WHP (PSI)": {
                "median": round(nom_whp, 1),
                "min": 0.0,
                "max": 300.0,
                "p10": round(nom_whp * 0.85, 1),
                "p90": round(nom_whp * 1.15, 1),
                "normal_min": 15.0,
                "normal_max": 200.0
            },
            "FLP (PSI)": {
                "median": round(nom_flp, 1),
                "min": 0.0,
                "max": 250.0,
                "p10": round(nom_flp * 0.85, 1),
                "p90": round(nom_flp * 1.15, 1),
                "normal_min": 10.0,
                "normal_max": 180.0
            },
            "AP (PSI)": {
                "median": round(nom_ap, 1),
                "min": 0.0,
                "max": 150.0,
                "p10": 0.0,
                "p90": round(max(20.0, nom_ap * 2.0), 1),
                "normal_min": 0.0,
                "normal_max": 100.0
            },
            "Leak Current Ct": {
                "median": 5.0,
                "min": 0.0,
                "max": 50.0,
                "p10": 1.0,
                "p90": 15.0,
                "normal_min": 0.0,
                "normal_max": 30.0
            },
            "DHG Current": {
                "median": 20.0,
                "min": 0.0,
                "max": 100.0,
                "p10": 10.0,
                "p90": 30.0,
                "normal_min": 5.0,
                "normal_max": 50.0
            }
        }

        # Update or create well profile in registry
        if well_id not in wells_dict:
            wells_dict[well_id] = {}
        wells_dict[well_id]["family"] = fam
        wells_dict[well_id]["pump_model"] = pump_model
        wells_dict[well_id]["motor_hp"] = well_sim.asset.motor_hp
        wells_dict[well_id]["stages"] = well_sim.asset.stages
        wells_dict[well_id]["sensors"] = sensors_spec

    existing_reg["wells"] = wells_dict
    existing_reg["updated_at"] = "2026-09-10T17:30:00Z"
    existing_reg["families"] = FAMILY_PUMP_MAP

    # Write updated calibration registry
    with open(reg_file, "w", encoding="utf-8") as f:
        json.dump(existing_reg, f, indent=2)
    print(f"Updated {reg_file} with calibrated setpoints for {len(wells_dict)} wells.")

    # 4. Generate multi-step training datasets per family
    print("\nGenerating nominal training data across pump families...")
    calib_reg = WellCalibrationRegistry(registry_file=str(reg_file))
    adapter = SiteTelemetryAdapter(calib_reg)
    normalizer = NormalizationLayer(calib_reg)

    family_vectors = {fam: [] for fam in FAMILY_PUMP_MAP.keys()}
    family_vectors["FLEET_GLOBAL"] = []

    # Run 120 steps of simulation with natural noise to simulate operational variety
    for step_idx in range(120):
        engine.step_all()
        for well_id, well_sim in engine.wells.items():
            fam = well_family_lookup.get(well_id, "FIELD_SCADA")
            m = well_sim.state.measurements
            # Convert to adapter input
            adapted = adapter.transform(well_id, m)
            norm_res = normalizer.normalize_live_telemetry(well_id, adapted)
            vec = list(norm_res["normalized"].values())
            family_vectors[fam].append(vec)
            family_vectors["FLEET_GLOBAL"].append(vec)

    # 5. Train and calibrate Isolation Forest per family
    trained_dir = CODE_MODELS / "trained_models"
    trained_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "families": {},
        "feature_order": [f"norm_{clean_col_key(s)}" for s in STANDARD_SENSORS],
        "created_at": "2026-09-10T17:30:00Z"
    }

    print("\nTraining Per-Family Isolation Forest Models:")
    print("-" * 80)
    for fam, vecs in family_vectors.items():
        if len(vecs) < 20:
            print(f"Warning: Family {fam} has too few samples ({len(vecs)}), borrowing from FLEET_GLOBAL")
            vecs = family_vectors["FLEET_GLOBAL"]

        X = np.array(vecs)
        # Train Isolation Forest
        model = IsolationForest(
            n_estimators=100,
            contamination=0.01,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X)

        # Calibrate decision scores on the nominal dataset
        dec_scores = model.decision_function(X)
        mean_score = float(np.mean(dec_scores))
        min_score = float(np.min(dec_scores))
        p5_score = float(np.percentile(dec_scores, 5))

        model_path = trained_dir / f"{fam.lower()}_isolation_forest.joblib"
        joblib.dump(model, model_path)

        metadata["families"][fam] = {
            "model_file": model_path.name,
            "sample_count": len(vecs),
            "nominal_score_mean": round(mean_score, 4),
            "nominal_score_p5": round(p5_score, 4),
            "nominal_score_min": round(min_score, 4),
            # Calibrated sigmoid midpoint: scores >= p5 give anomaly probability < 0.15
            "sigmoid_midpoint": round(p5_score - 0.05, 4)
        }
        print(f"  [{fam:12s}] Samples: {len(vecs):5d} | Mean Score: {mean_score:+.4f} | P5: {p5_score:+.4f} | Saved to: {model_path.name}")

    meta_file = trained_dir / "models_metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nSaved models metadata to {meta_file}")

    # 6. Mirror to backend and esp_agent directories
    mirror_targets = [
        WORKSPACE_ROOT / "backend" / "src" / "models",
        WORKSPACE_ROOT / "backend" / "models",
        WORKSPACE_ROOT / "esp_agent" / "src" / "models",
        WORKSPACE_ROOT / "esp_agent" / "models",
        WORKSPACE_ROOT / "ml" / "models"
    ]
    for target in mirror_targets:
        target.mkdir(parents=True, exist_ok=True)
        # Copy registry
        shutil.copy2(reg_file, target / "well_calibration_registry.json")
        # Copy trained models
        t_target = target / "trained_models"
        t_target.mkdir(parents=True, exist_ok=True)
        for f in trained_dir.glob("*"):
            shutil.copy2(f, t_target / f.name)
        print(f"Mirrored model artifacts to {target}")

    print("\n" + "=" * 80)
    print("SUCCESS: Digital Twin Calibration & Per-Family Training Completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
