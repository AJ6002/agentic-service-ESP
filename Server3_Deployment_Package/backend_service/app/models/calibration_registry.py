"""
Well Calibration Registry Component
===================================
Manages parametric baseline envelopes (min, max, mean, std, median, p10, p90)
for all 73 individual wells across CCED field clusters (FS, FNW, FWS, ULFA),
with hierarchical family and global fallbacks.
"""

import os
import sys
import json
import glob
import re
import datetime
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STANDARD_SENSORS = [
    "Inp bar/psi",
    "Int temp °C",
    "Motor temp °C",
    "Disch pr. Bar/psi",
    "Vibration G's-Vx",
    "Leak Current Ct",
    "Volt",
    "VSD Amps/Load",
    "Frequency",
    "DHG Current",
    "WHP (PSI)",
    "FLP (PSI)",
    "AP (PSI)"
]

def clean_col_key(col_name: str) -> str:
    """Standardizes incoming column strings to canonical sensor names."""
    if col_name is None:
        return ""
    s = str(col_name).strip()
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    s = s.replace("\xb0", "°").replace("\ufffdC", "°C").replace("C", "°C").replace("", "")
    s = re.sub(r'\s+', ' ', s).strip()

    c_low = s.lower()
    if c_low in ["timestamp", "time", "datetime", "ts"] or ("report" in c_low and "date" in c_low):
        return "Report_DateTime"
    if "file" in c_low and "date" in c_low:
        return "File_DateTime"
    if "well" in c_low:
        return "Wells"
    if "inp" in c_low or "intake" in c_low or "suction" in c_low:
        return "Inp bar/psi"
    if "int" in c_low and "temp" in c_low:
        return "Int temp °C"
    if "motor" in c_low and "temp" in c_low:
        return "Motor temp °C"
    if "disch" in c_low or "discharge" in c_low:
        return "Disch pr. Bar/psi"
    if "vib" in c_low:
        return "Vibration G's-Vx"
    if "leak" in c_low:
        return "Leak Current Ct"
    if "volt" in c_low:
        return "Volt"
    if ("amp" in c_low and "timestamp" not in c_low) or "load" in c_low:
        return "VSD Amps/Load"
    if "freq" in c_low or "hz" in c_low:
        return "Frequency"
    if "dhg" in c_low:
        return "DHG Current"
    if "whp" in c_low:
        return "WHP (PSI)"
    if "flp" in c_low:
        return "FLP (PSI)"
    if "ap" in c_low:
        return "AP (PSI)"
    if "vfd" in c_low or "sts" in c_low or "status" in c_low:
        return "VFD STS"
    if "cluster" in c_low:
        return "Cluster"
    return s


class WellCalibrationRegistry:
    """
    Scans categorized historical well datasets to construct baseline operating profiles.
    Caches baseline statistics in a local JSON registry for fast (<1ms) inference.
    """

    def __init__(
        self,
        categorized_dir: str = r"C:\Users\admin.DESKTOP-17T37DJ\Desktop\cced\categorized_wells",
        registry_file: Optional[str] = None
    ):
        self.categorized_dir = categorized_dir
        if registry_file is None:
            # Default to registry JSON in models folder or parent directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            registry_file = os.path.join(base_dir, "well_calibration_registry.json")
            if not os.path.exists(registry_file):
                parent_reg = os.path.join(os.path.dirname(base_dir), "well_calibration_registry.json")
                if os.path.exists(parent_reg):
                    registry_file = parent_reg

        self.registry_file = registry_file
        self.registry: Dict[str, Any] = {}
        self.family_profiles: Dict[str, Any] = {}
        self.global_profile: Dict[str, Any] = {}
        self._load_or_build()

    def _load_or_build(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.registry = data.get("wells", {})
                    self.family_profiles = data.get("families", {})
                    self.global_profile = data.get("global", {})
                if self.registry:
                    return
            except Exception as e:
                print(f"[!] Warning loading registry {self.registry_file}: {e}. Rebuilding...")

        self.build_registry_from_files()

    def build_registry_from_files(self):
        print("Building well calibration baseline registry from categorized files...")
        csv_files = glob.glob(os.path.join(self.categorized_dir, "**", "*.csv"), recursive=True)
        csv_files = [f for f in csv_files if "Wells_Summary_Index" not in f]

        if not csv_files:
            print(f"[!] Warning: No categorized well CSVs found in {self.categorized_dir}.")
            return

        all_well_stats = {}
        family_accumulators = {}
        all_dfs = []

        for csv_path in csv_files:
            try:
                df = pd.read_csv(csv_path, low_memory=False)
                df.columns = [clean_col_key(c) for c in df.columns]
                df = df.loc[:, ~df.columns.duplicated()].copy()
                
                well_name = os.path.splitext(os.path.basename(csv_path))[0].replace("_", "-")
                if "Wells" in df.columns and len(df["Wells"].dropna()) > 0:
                    well_name = str(df["Wells"].dropna().iloc[0]).strip()
                
                family = re.match(r'^([A-Za-z]+)', well_name).group(1).upper() if re.match(r'^([A-Za-z]+)', well_name) else "OTHER"
                
                well_stats = {"family": family, "sensors": {}}
                for sensor in STANDARD_SENSORS:
                    if sensor in df.columns:
                        s_vals = pd.to_numeric(df[sensor], errors="coerce").dropna()
                        pos_vals = s_vals[s_vals > 0]
                        act_vals = pos_vals if len(pos_vals) > 0 else s_vals
                        if len(s_vals) > 0:
                            well_stats["sensors"][sensor] = {
                                "min": float(s_vals.min()),
                                "max": float(s_vals.max()),
                                "mean": float(act_vals.mean()),
                                "std": float(act_vals.std()) if len(act_vals) > 1 else 1.0,
                                "median": float(act_vals.median()),
                                "p10": float(np.percentile(act_vals, 10)),
                                "p90": float(np.percentile(act_vals, 90))
                            }
                
                all_well_stats[well_name] = well_stats
                
                if family not in family_accumulators:
                    family_accumulators[family] = []
                family_accumulators[family].append(df)
                all_dfs.append(df)
            except Exception as e:
                print(f"  [!] Error profiling {csv_path}: {e}")

        self.registry = all_well_stats

        # Compute Family profiles
        for fam, dfs in family_accumulators.items():
            fam_df = pd.concat(dfs, ignore_index=True)
            self.family_profiles[fam] = self._compute_df_profile(fam_df)

        # Compute Global profile
        if all_dfs:
            master_df = pd.concat(all_dfs, ignore_index=True)
            self.global_profile = self._compute_df_profile(master_df)

        # Save to JSON
        cache_data = {
            "wells": self.registry,
            "families": self.family_profiles,
            "global": self.global_profile,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
        print(f"[OK] Calibration Registry built for {len(self.registry)} wells and saved to {self.registry_file}")

    def _compute_df_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        profile = {"sensors": {}}
        for sensor in STANDARD_SENSORS:
            if sensor in df.columns:
                s_vals = pd.to_numeric(df[sensor], errors="coerce").dropna()
                pos_vals = s_vals[s_vals > 0]
                act_vals = pos_vals if len(pos_vals) > 0 else s_vals
                if len(s_vals) > 0:
                    profile["sensors"][sensor] = {
                        "min": float(s_vals.min()),
                        "max": float(s_vals.max()),
                        "mean": float(act_vals.mean()),
                        "std": float(act_vals.std()) if len(act_vals) > 1 else 1.0,
                        "median": float(act_vals.median()),
                        "p10": float(np.percentile(act_vals, 10)),
                        "p90": float(np.percentile(act_vals, 90))
                    }
        return profile

    def get_well_profile(self, well_id: str) -> Dict[str, Any]:
        """Returns baseline profile for specific well, with alias resolution and fallback to family/global."""
        w_clean = str(well_id).strip()

        def _is_valid(p):
            if not p or not isinstance(p, dict):
                return False
            s = p.get("sensors", {})
            inp_m = float(s.get("Inp bar/psi", {}).get("median", 0.0))
            pdp_m = float(s.get("Disch pr. Bar/psi", {}).get("median", 0.0))
            return inp_m > 10.0 and pdp_m > 50.0
        
        # 1. Exact match in registry if sensors are valid (> 0)
        if w_clean in self.registry and _is_valid(self.registry[w_clean]):
            return self.registry[w_clean]
        
        # 2. Alias resolution (for wells that share identical low-voltage SCADA curves)
        aliases = {
            "FNW-01": "FS-31",
            "FNW-06": "FS-31",
            "FS-06": "FS-04",
            "FS-17": "FS-31",
            "FS-21": "FS-21",
            "FS-91": "FS-31",
            "FS-96": "FS-31",
            "FS-121": "FS-31",
            "FS-129": "FS-31",
            "ULFA-5": "FS-31"
        }
        target_alias = aliases.get(w_clean)
        if target_alias and target_alias in self.registry and _is_valid(self.registry[target_alias]):
            prof = dict(self.registry[target_alias])
            prof["aliased_from"] = target_alias
            return prof

        # 3. Fuzzy normalized well ID match (e.g. FS-04 <-> FS-4, FS-096 <-> FS-96)
        w_alt = w_clean.replace("-0", "-") if "-0" in w_clean else w_clean.replace("-", "-0")
        if w_alt in self.registry and _is_valid(self.registry[w_alt]):
            return self.registry[w_alt]

        # 4. Standard calibrated fallback profiles (prevents 0.0 limit crashes)
        m = re.match(r'^([A-Za-z]+)', w_clean)
        fam = m.group(1).upper() if m else "FIELD_SCADA"

        # Special calibration for FWS (B538-5000 medium voltage fleet)
        if "FWS" in w_clean.upper():
            return {
                "family": "B538",
                "sensors": {
                    "Inp bar/psi": {"median": 350.0, "normal_min": 180.0, "normal_max": 600.0, "p10": 250.0, "p90": 480.0, "min": 0.0, "max": 1200.0},
                    "Disch pr. Bar/psi": {"median": 2100.0, "normal_min": 1400.0, "normal_max": 2700.0, "p10": 1700.0, "p90": 2350.0, "min": 500.0, "max": 3500.0},
                    "VSD Amps/Load": {"median": 45.0, "normal_min": 15.0, "normal_max": 120.0, "p10": 20.0, "p90": 90.0, "min": 5.0, "max": 200.0},
                    "Volt": {"median": 1100.0, "normal_min": 750.0, "normal_max": 2500.0, "p10": 850.0, "p90": 2400.0, "min": 200.0, "max": 3000.0},
                    "Frequency": {"median": 50.0, "normal_min": 35.0, "normal_max": 65.0, "p10": 42.0, "p90": 58.0, "min": 20.0, "max": 75.0},
                    "Motor temp °C": {"median": 85.0, "normal_min": 40.0, "normal_max": 125.0, "p10": 65.0, "p90": 105.0, "min": 20.0, "max": 160.0},
                    "Int temp °C": {"median": 65.0, "normal_min": 35.0, "normal_max": 95.0, "p10": 50.0, "p90": 75.0, "min": 15.0, "max": 110.0},
                    "Vibration G's-Vx": {"median": 0.10, "normal_min": 0.0, "normal_max": 0.60, "p10": 0.02, "p90": 0.25, "min": 0.0, "max": 2.0},
                    "WHP (PSI)": {"median": 150.0, "normal_min": 10.0, "normal_max": 350.0, "p10": 30.0, "p90": 200.0, "min": 0.0, "max": 600.0},
                    "FLP (PSI)": {"median": 130.0, "normal_min": 5.0, "normal_max": 300.0, "p10": 20.0, "p90": 180.0, "min": 0.0, "max": 500.0},
                    "AP (PSI)": {"median": 10.0, "normal_min": 0.0, "normal_max": 100.0, "p10": 0.0, "p90": 30.0, "min": 0.0, "max": 250.0},
                    "Leak Current Ct": {"median": 15.0, "normal_min": 0.0, "normal_max": 35.0, "p10": 2.0, "p90": 25.0, "min": 0.0, "max": 80.0},
                    "DHG Current": {"median": 80.0, "normal_min": 5.0, "normal_max": 130.0, "p10": 10.0, "p90": 105.0, "min": 0.0, "max": 160.0}
                }
            }
        
        default_sensors = {
            "Inp bar/psi": {"median": 350.0, "normal_min": 180.0, "normal_max": 550.0, "p10": 280.0, "p90": 450.0, "min": 0.0, "max": 1200.0},
            "Disch pr. Bar/psi": {"median": 2000.0, "normal_min": 1400.0, "normal_max": 2500.0, "p10": 1700.0, "p90": 2250.0, "min": 500.0, "max": 3500.0},
            "VSD Amps/Load": {"median": 75.0, "normal_min": 20.0, "normal_max": 140.0, "p10": 45.0, "p90": 110.0, "min": 5.0, "max": 200.0},
            "Volt": {"median": 400.0, "normal_min": 250.0, "normal_max": 1200.0, "p10": 320.0, "p90": 1150.0, "min": 100.0, "max": 1500.0},
            "Frequency": {"median": 50.0, "normal_min": 35.0, "normal_max": 60.0, "p10": 42.0, "p90": 55.0, "min": 20.0, "max": 70.0},
            "Motor temp °C": {"median": 80.0, "normal_min": 40.0, "normal_max": 120.0, "p10": 60.0, "p90": 95.0, "min": 20.0, "max": 150.0},
            "Int temp °C": {"median": 60.0, "normal_min": 35.0, "normal_max": 95.0, "p10": 50.0, "p90": 70.0, "min": 15.0, "max": 110.0},
            "Vibration G's-Vx": {"median": 0.08, "normal_min": 0.0, "normal_max": 0.60, "p10": 0.02, "p90": 0.20, "min": 0.0, "max": 2.0},
            "WHP (PSI)": {"median": 80.0, "normal_min": 10.0, "normal_max": 250.0, "p10": 30.0, "p90": 150.0, "min": 0.0, "max": 500.0},
            "FLP (PSI)": {"median": 60.0, "normal_min": 5.0, "normal_max": 200.0, "p10": 20.0, "p90": 120.0, "min": 0.0, "max": 400.0},
            "AP (PSI)": {"median": 15.0, "normal_min": 0.0, "normal_max": 100.0, "p10": 5.0, "p90": 40.0, "min": 0.0, "max": 250.0},
            "Leak Current Ct": {"median": 10.0, "normal_min": 0.0, "normal_max": 35.0, "p10": 2.0, "p90": 20.0, "min": 0.0, "max": 80.0},
            "DHG Current": {"median": 20.0, "normal_min": 5.0, "normal_max": 50.0, "p10": 10.0, "p90": 30.0, "min": 0.0, "max": 100.0}
        }
        return {"family": fam, "sensors": default_sensors}

    def get_sensor_setpoints(self, well_id: str, sensor_name: str) -> Dict[str, Any]:
        """
        Retrieves dynamic setpoints for a specific well and sensor.
        Returns: {sensor, median, min, max, p10, p90, normal_min, normal_max, unit}
        """
        prof = self.get_well_profile(well_id)
        sensors = prof.get("sensors", {})
        canonical_key = clean_col_key(sensor_name)
        spec = sensors.get(canonical_key, {})

        median = float(spec.get("median", 100.0))
        p10 = float(spec.get("p10", max(0.0, median * 0.85)))
        p90 = float(spec.get("p90", median * 1.15))

        normal_min = float(spec.get("normal_min", p10 * 0.92))
        normal_max = float(spec.get("normal_max", p90 * 1.08))
        min_limit = float(spec.get("min", normal_min * 0.70))
        max_limit = float(spec.get("max", normal_max * 1.30))

        units = {
            "Inp bar/psi": "PSI",
            "Disch pr. Bar/psi": "PSI",
            "WHP (PSI)": "PSI",
            "FLP (PSI)": "PSI",
            "AP (PSI)": "PSI",
            "VSD Amps/Load": "A",
            "Volt": "V",
            "Frequency": "Hz",
            "Motor temp °C": "°C",
            "Int temp °C": "°C",
            "Vibration G's-Vx": "G",
            "Leak Current Ct": "mA",
            "DHG Current": "mA",
            "Liquid Rate (BPD)": "BPD"
        }

        short_names = {
            "Inp bar/psi": "PIP",
            "Disch pr. Bar/psi": "PDP",
            "WHP (PSI)": "WHP",
            "FLP (PSI)": "FLP",
            "AP (PSI)": "Annulus P",
            "VSD Amps/Load": "Motor Current",
            "Volt": "Bus Voltage",
            "Frequency": "Frequency",
            "Motor temp °C": "Motor Temp",
            "Int temp °C": "Intake Temp",
            "Vibration G's-Vx": "Vibration",
            "Leak Current Ct": "Leak Current",
            "DHG Current": "DHG Current"
        }

        return {
            "sensor": canonical_key,
            "short_name": short_names.get(canonical_key, canonical_key),
            "median": median,
            "p10": p10,
            "p90": p90,
            "normal_min": normal_min,
            "normal_max": normal_max,
            "min": min_limit,
            "max": max_limit,
            "unit": units.get(canonical_key, "")
        }

    def evaluate_out_of_spec(
        self,
        well_id: str,
        raw_telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates input parameters against the well-specific calibrated setpoint boundaries.
        Returns a structured list of Out-of-Spec violations.
        """
        violations = []
        if not isinstance(raw_telemetry, dict):
            return violations

        # Clean keys
        cleaned_telemetry = {}
        for k, v in raw_telemetry.items():
            if isinstance(v, (int, float)):
                ck = clean_col_key(str(k))
                cleaned_telemetry[ck] = float(v)

        for sensor_name in STANDARD_SENSORS:
            if sensor_name not in cleaned_telemetry:
                continue

            val = cleaned_telemetry[sensor_name]
            sp = self.get_sensor_setpoints(well_id, sensor_name)
            normal_min = sp["normal_min"]
            normal_max = sp["normal_max"]
            unit = sp["unit"]
            short_name = sp["short_name"]

            if val > normal_max:
                violations.append({
                    "param": sensor_name,
                    "tag": short_name,
                    "status": "OUT_OF_SPEC_HIGH",
                    "direction": "Higher than max limit",
                    "value": round(val, 2),
                    "limit": round(normal_max, 2),
                    "unit": unit,
                    "summary": f"Higher than max limit in {sensor_name} ({val:.1f} > {normal_max:.1f} {unit})"
                })
            elif val < normal_min:
                violations.append({
                    "param": sensor_name,
                    "tag": short_name,
                    "status": "OUT_OF_SPEC_LOW",
                    "direction": "Lower than min limit",
                    "value": round(val, 2),
                    "limit": round(normal_min, 2),
                    "unit": unit,
                    "summary": f"Lower than min limit in {sensor_name} ({val:.1f} < {normal_min:.1f} {unit})"
                })

        return violations

