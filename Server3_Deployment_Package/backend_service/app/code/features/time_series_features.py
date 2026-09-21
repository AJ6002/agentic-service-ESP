"""
Time-Series Feature Engineering Engine.
Computes multi-scale statistical window features (mean, std, min, max, slope, EMA)
and physics-based cross-sensor domain ratios for ESP condition monitoring models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import deque
from ml.data.canonical_schema import CanonicalESPTelemetry

CORE_SENSORS = [
    "liquid_rate_bpd",
    "intake_pressure_psi",
    "motor_current_a",
    "motor_load_pct",
    "motor_temperature_c",
    "vibration_rms",
    "discharge_pressure_psi",
    "motor_voltage_v",
    "intake_temperature_c",
    "flowline_pressure_psi",
    "wellhead_pressure_psi",
    "casing_pressure_psi",
    "choke_size_64in"
]


class RollingFeatureExtractor:
    def __init__(self, window_sizes: List[int] = [5, 15, 30]):
        self.window_sizes = window_sizes
        self.max_window = max(window_sizes)
        # In-memory history per well: esp_id -> deque of dicts
        self.buffers: Dict[str, deque] = {}

    def push_and_extract(self, telemetry: CanonicalESPTelemetry) -> Dict[str, float]:
        """Push latest telemetry and return calculated rolling feature dictionary."""
        esp_key = f"{telemetry.esp_id}_{telemetry.well_id}"
        if esp_key not in self.buffers:
            self.buffers[esp_key] = deque(maxlen=self.max_window)

        # Extract numeric vector
        raw_vals = {s: float(getattr(telemetry, s, 0.0) or 0.0) for s in CORE_SENSORS}
        self.buffers[esp_key].append(raw_vals)


        return self.compute_features(esp_key, telemetry)

    def compute_features(self, esp_key: str, latest_telemetry: CanonicalESPTelemetry) -> Dict[str, float]:
        """Compute instantaneous and multi-window features for the given well."""
        buf = list(self.buffers[esp_key])
        n_samples = len(buf)
        features: Dict[str, float] = {}

        # 1. Instantaneous Raw Values
        for s in CORE_SENSORS:
            val = getattr(latest_telemetry, s, 0.0)
            features[s] = float(val) if val is not None else 0.0

        # 2. Physics-Informed Cross-Sensor Domain Ratios
        dp = max(0.0, latest_telemetry.discharge_pressure_psi - latest_telemetry.intake_pressure_psi)
        features["differential_pressure_psi"] = dp
        
        # PDP to PIP Ratio
        pip_safe = max(1.0, latest_telemetry.intake_pressure_psi)
        features["pressure_ratio_pdp_pip"] = latest_telemetry.discharge_pressure_psi / pip_safe

        # Voltage to Current Ratio (Apparent Impedance Proxy)
        current_safe = max(0.1, latest_telemetry.motor_current_a)
        features["apparent_impedance_ohms"] = latest_telemetry.motor_voltage_v / current_safe

        # Thermal Gradient (Motor vs Intake Temp)
        intake_t = latest_telemetry.intake_temperature_c if latest_telemetry.intake_temperature_c is not None else (latest_telemetry.motor_temperature_c - 20.0 if latest_telemetry.motor_temperature_c > 20.0 else 55.0)
        features["thermal_gradient_c"] = latest_telemetry.motor_temperature_c - intake_t


        # Hydraulic Power Proxy (DP * Flow / 1000)
        features["hydraulic_power_proxy"] = (dp * latest_telemetry.liquid_rate_bpd) / 1000.0

        # Vibration to Flow Ratio
        flow_safe = max(1.0, latest_telemetry.liquid_rate_bpd)
        features["vibration_per_flow"] = (latest_telemetry.vibration_rms * 1000.0) / flow_safe

        # 3. Rolling Window Aggregations (5, 15, 30 samples)
        for w in self.window_sizes:
            sub_buf = buf[-w:] if n_samples >= w else buf
            w_len = len(sub_buf)

            for s in CORE_SENSORS:
                series = np.array([item[s] for item in sub_buf], dtype=float)
                mean_val = float(np.mean(series))
                std_val = float(np.std(series)) if w_len > 1 else 0.0
                min_val = float(np.min(series))
                max_val = float(np.max(series))

                features[f"{s}_mean_{w}"] = mean_val
                features[f"{s}_std_{w}"] = std_val
                features[f"{s}_min_{w}"] = min_val
                features[f"{s}_max_{w}"] = max_val

                # Rate of Change / Slope over window
                if w_len >= 2:
                    slope = float(series[-1] - series[0]) / float(w_len)
                else:
                    slope = 0.0
                features[f"{s}_slope_{w}"] = slope

        return features


def extract_batch_dataframe_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes time-series feature matrix for offline training datasets.
    Operates chronologically per well without future leakage.
    """
    feature_dfs = []
    
    for well_id, well_group in df.groupby("well_id", sort=False):
        well_group = well_group.copy()
        new_cols: Dict[str, Any] = {}
        
        # Cross-sensor features
        new_cols["differential_pressure_psi"] = (
            well_group["discharge_pressure_psi"] - well_group["intake_pressure_psi"]
        ).clip(lower=0.0)
        
        new_cols["pressure_ratio_pdp_pip"] = (
            well_group["discharge_pressure_psi"] / well_group["intake_pressure_psi"].clip(lower=1.0)
        )
        
        new_cols["apparent_impedance_ohms"] = (
            well_group["motor_voltage_v"] / well_group["motor_current_a"].clip(lower=0.1)
        )
        
        new_cols["thermal_gradient_c"] = (
            well_group["motor_temperature_c"] - well_group["intake_temperature_c"]
        )
        
        new_cols["hydraulic_power_proxy"] = (
            new_cols["differential_pressure_psi"] * well_group["liquid_rate_bpd"] / 1000.0
        )
        
        # Rolling features (5, 15, 30)
        for w in [5, 15, 30]:
            for s in CORE_SENSORS:
                new_cols[f"{s}_mean_{w}"] = well_group[s].rolling(window=w, min_periods=1).mean()
                new_cols[f"{s}_std_{w}"] = well_group[s].rolling(window=w, min_periods=1).std().fillna(0.0)
                new_cols[f"{s}_min_{w}"] = well_group[s].rolling(window=w, min_periods=1).min()
                new_cols[f"{s}_max_{w}"] = well_group[s].rolling(window=w, min_periods=1).max()
                new_cols[f"{s}_slope_{w}"] = (
                    (well_group[s] - well_group[s].shift(w - 1)).fillna(0.0) / float(w)
                )

        new_df = pd.DataFrame(new_cols, index=well_group.index)
        combined_well = pd.concat([well_group, new_df], axis=1)
        feature_dfs.append(combined_well)

    full_features_df = pd.concat(feature_dfs, ignore_index=True)
    return full_features_df

