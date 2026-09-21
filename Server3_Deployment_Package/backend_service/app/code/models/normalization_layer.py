"""
Live Normalization Layer Component
==================================
Scales raw, un-normalized telemetry vectors (PSI, °C, A, V, Hz, G, mA)
into normalized [0, 1] features and computes dynamic physical engineering parameters.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from .calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS, clean_col_key


class NormalizationLayer:
    """
    Live Telemetry Normalization Layer:
    Takes raw, un-normalized measurements from site, performs dynamic physics feature engineering,
    and scales each sensor feature strictly to [0, 1] relative to the target well's historical envelope.
    """

    def __init__(self, registry: WellCalibrationRegistry):
        self.registry = registry

    def normalize_live_telemetry(
        self,
        well_id: str,
        raw_telemetry: Dict[str, Any],
        prev_telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a raw live telemetry packet:
        1. Cleans and maps column keys.
        2. Computes dynamic physical features (ΔP Head, Torque proxy, Power proxy, Thermal elevation, dT/dt).
        3. Scales all 13 sensors to [0, 1] relative to target well calibration envelope.
        """
        profile = self.registry.get_well_profile(well_id)
        sensors_profile = profile.get("sensors", {})

        # 1. Clean and standardize raw inputs
        raw_cleaned = {}
        for k, v in raw_telemetry.items():
            ck = clean_col_key(k)
            try:
                raw_cleaned[ck] = float(v) if v is not None and str(v).strip() != "" else 0.0
            except (ValueError, TypeError):
                raw_cleaned[ck] = 0.0

        # Fill any missing sensors with calibrated median
        for s in STANDARD_SENSORS:
            if s not in raw_cleaned:
                raw_cleaned[s] = sensors_profile.get(s, {}).get("median", 1.0)

        # 2. Physics Feature Engineering
        inp = raw_cleaned.get("Inp bar/psi", 0.0)
        disch = raw_cleaned.get("Disch pr. Bar/psi", 0.0)
        amps = raw_cleaned.get("VSD Amps/Load", 0.0)
        freq = raw_cleaned.get("Frequency", 50.0)
        volt = raw_cleaned.get("Volt", 400.0)
        m_temp = raw_cleaned.get("Motor temp °C", 70.0)
        i_temp = raw_cleaned.get("Int temp °C", 50.0)

        delta_p = disch - inp
        torque_proxy = amps / max(1.0, freq)
        power_proxy_kva = (volt * amps * 1.732) / 1000.0
        thermal_elevation = m_temp - i_temp
        pressure_ratio = disch / max(1.0, inp)

        # Thermal rate of change (dT/dt) if previous timestep available
        thermal_rate_hr = 0.0
        if prev_telemetry:
            prev_m_temp = float(prev_telemetry.get("Motor temp °C", m_temp))
            thermal_rate_hr = (m_temp - prev_m_temp) * 12.0  # Assumes 5-minute sampling interval

        dynamics = {
            "delta_p": round(delta_p, 2),
            "torque_proxy": round(torque_proxy, 3),
            "power_proxy_kva": round(power_proxy_kva, 2),
            "thermal_elevation": round(thermal_elevation, 2),
            "thermal_rate_hr": round(thermal_rate_hr, 2),
            "pressure_ratio": round(pressure_ratio, 2)
        }

        # 3. Min-Max Scaling strictly in [0, 1]
        normalized = {}
        for sensor in STANDARD_SENSORS:
            val = float(raw_cleaned.get(sensor, 1.0))
            if sensor in sensors_profile:
                p_min = sensors_profile[sensor]["min"]
                p_max = sensors_profile[sensor]["max"]
                if p_max > p_min:
                    norm_v = (val - p_min) / (p_max - p_min)
                else:
                    norm_v = 1.0
            else:
                norm_v = 0.5
            
            # Clip between [0, 1] for ML stability
            norm_col_name = f"norm_{re.sub(r'[^A-Za-z0-9]+', '_', sensor).strip('_')}"
            normalized[norm_col_name] = round(float(np.clip(norm_v, 0.0, 1.0)), 6)

        return {
            "well_id": well_id,
            "family": profile.get("family", "OTHER"),
            "raw": raw_cleaned,
            "normalized": normalized,
            "dynamics": dynamics
        }
