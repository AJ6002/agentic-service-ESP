"""
Site Telemetry Ingestion & Pre-Normalization Adapter
====================================================
Transforms incoming compact site SCADA telemetry packets into the canonical 
14-parameter format required by the CCED ESP diagnostic models and normalization layer.

Handles:
- Key alias resolution (e.g. 'Intake P' -> 'Inp bar/psi', 'Temp' -> 'Motor temp °C')
- Thermodynamic estimation of intake temperature when only motor temperature is provided
- VFD operating status deduction (running vs stopped)
- Parametric baseline imputation for unmonitored auxiliary sensors
- Pass-through and validation of enriched site features (Flow BPD, Voltage/Current Imbalance)
"""

import sys
import re
from typing import Dict, Any, Optional
from .calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class SiteTelemetryAdapter:
    """
    Modular Pre-Normalization Ingestion Adapter:
    Standardizes compact site SCADA packets into 14 canonical sensor parameters.
    """

    def __init__(self, registry: Optional[WellCalibrationRegistry] = None):
        self.registry = registry or WellCalibrationRegistry()

    def transform(self, well_id: str, site_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a raw site telemetry dictionary and returns a standardized 14-parameter dictionary.
        
        Example Input:
        {
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
        """
        if not isinstance(site_payload, dict):
            raise ValueError(f"site_payload must be a dictionary, got {type(site_payload)}")

        # Normalize incoming keys (lowercase, stripped, special characters removed)
        clean_input = {}
        def _flatten(d: Dict[str, Any]):
            for k, v in d.items():
                if isinstance(v, dict):
                    _flatten(v)
                else:
                    norm_k = re.sub(r'[^a-zA-Z0-9]', '', str(k).lower())
                    clean_input[norm_k] = v

        _flatten(site_payload)

        # Fetch well baseline profile for fallback and thermodynamic estimation
        profile = self.registry.get_well_profile(well_id)
        sensors = profile.get("sensors", profile) if isinstance(profile, dict) else {}

        output = {}

        # -------------------------------------------------------------
        # 1. Direct Sensor Key Resolution & Numeric Parsing
        # -------------------------------------------------------------
        # Intake Pressure (PSI)
        output["Inp bar/psi"] = self._extract_numeric(
            clean_input,
            ["intakep", "intakepsi", "intakepressure", "inpbarpsi", "inp", "suction", "suctionp", "pin"],
            default=sensors.get("Inp bar/psi", {}).get("median", 250.0)
        )

        # Discharge Pressure (PSI)
        output["Disch pr. Bar/psi"] = self._extract_numeric(
            clean_input,
            ["dischargep", "dischargepsi", "dischargepressure", "dischprbarpsi", "disch", "delivery", "pout"],
            default=sensors.get("Disch pr. Bar/psi", {}).get("median", 1800.0)
        )

        # Operating Frequency (Hz)
        output["Frequency"] = self._extract_numeric(
            clean_input,
            ["freq", "frequency", "hz", "speed", "vfdfreq", "rpm"],
            default=sensors.get("Frequency", {}).get("median", 50.0)
        )

        # Motor Current (Amps)
        output["VSD Amps/Load"] = self._extract_numeric(
            clean_input,
            ["current", "amps", "load", "vsdampsload", "motorcurrent", "i", "amp"],
            default=sensors.get("VSD Amps/Load", {}).get("median", 75.0)
        )

        # Supply Voltage (Volts)
        output["Volt"] = self._extract_numeric(
            clean_input,
            ["voltage", "volt", "v", "supplyvoltage", "vsdvoltage"],
            default=sensors.get("Volt", {}).get("median", 400.0)
        )

        # Radial Vibration (G)
        output["Vibration G's-Vx"] = self._extract_numeric(
            clean_input,
            ["vibration", "vibrationgsvx", "vib", "vx", "vibrationg", "vibrations"],
            default=sensors.get("Vibration G's-Vx", {}).get("median", 0.05)
        )

        # -------------------------------------------------------------
        # 2. Thermal Resolution (Motor Temp & Thermodynamic Intake Temp)
        # -------------------------------------------------------------
        # Motor Temperature (°C)
        motor_temp = self._extract_numeric(
            clean_input,
            ["motortemp", "motortempc", "temp", "temperature", "tmotor", "mtemp"],
            default=sensors.get("Motor temp °C", {}).get("median", 75.0)
        )
        output["Motor temp °C"] = motor_temp

        # Intake Temperature (°C)
        int_temp_val = self._extract_numeric(
            clean_input,
            ["inttemp", "inttempc", "intaketemp", "intaketempc", "tintake", "itemp"],
            default=None
        )

        if int_temp_val is not None:
            output["Int temp °C"] = int_temp_val
        else:
            # Thermodynamic estimation:
            # If well profile has baseline ΔT = Motor_median - Int_median, use it;
            # otherwise assume standard ESP thermal elevation of 18-22 °C or profile intake median.
            int_median = sensors.get("Int temp °C", {}).get("median", 55.0)
            mot_median = sensors.get("Motor temp °C", {}).get("median", 75.0)
            baseline_delta_t = max(10.0, mot_median - int_median) if mot_median > int_median else 18.0

            estimated_intake = max(20.0, motor_temp - baseline_delta_t)
            output["Int temp °C"] = round(estimated_intake, 2)

        # -------------------------------------------------------------
        # 3. VFD Operational Status Deduction
        # -------------------------------------------------------------
        vfd_sts_explicit = self._extract_numeric(
            clean_input,
            ["vfdsts", "vfdstatus", "status", "running", "state"],
            default=None
        )
        if vfd_sts_explicit is not None:
            output["VFD STS"] = int(vfd_sts_explicit > 0)
        else:
            # Logically deduce: running if Current > 1.0 A and Frequency > 5.0 Hz
            is_running = (output["VSD Amps/Load"] > 1.0) and (output["Frequency"] > 5.0)
            output["VFD STS"] = 1 if is_running else 0

        # -------------------------------------------------------------
        # 4. Parametric Auxiliary & Surface Gauges Imputation
        # -------------------------------------------------------------
        output["Leak Current Ct"] = self._extract_numeric(
            clean_input,
            ["leakcurrent", "leakcurrentct", "leakage", "leakcurrentma"],
            default=sensors.get("Leak Current Ct", {}).get("median", 0.0)
        )

        output["DHG Current"] = self._extract_numeric(
            clean_input,
            ["dhgcurrent", "dhg", "downholegauge"],
            default=sensors.get("DHG Current", {}).get("median", 0.0)
        )

        output["WHP (PSI)"] = self._extract_numeric(
            clean_input,
            ["whp", "whppsi", "wellheadpressure", "wellheadp", "wellheadpressurepsi"],
            default=sensors.get("WHP (PSI)", {}).get("median", 50.0)
        )

        output["FLP (PSI)"] = self._extract_numeric(
            clean_input,
            ["flp", "flppsi", "flowlinepressure", "flowlinep", "flowlinepressurepsi"],
            default=sensors.get("FLP (PSI)", {}).get("median", 45.0)
        )

        output["AP (PSI)"] = self._extract_numeric(
            clean_input,
            ["ap", "appsi", "annuluspressure", "annulusp", "casingpressurepsi", "casingpressure"],
            default=sensors.get("AP (PSI)", {}).get("median", 10.0)
        )

        # -------------------------------------------------------------
        # 5. Enriched Site Parameters (Pass-Through)
        # -------------------------------------------------------------
        output["Flow_BPD"] = self._extract_numeric(clean_input, ["flow", "flowbpd", "q", "liquidrate", "bpd"], default=0.0)
        output["V_Imb_pct"] = self._extract_numeric(clean_input, ["vimb", "voltageimbalance", "vimbpct", "vbalance"], default=0.0)
        output["I_Imb_pct"] = self._extract_numeric(clean_input, ["iimb", "currentimbalance", "iimbpct", "ibalance"], default=0.0)

        # Preserve metadata if provided
        for meta_k in ["report_datetime", "file_datetime", "wells", "cluster", "report_id"]:
            if meta_k in clean_input:
                output[meta_k] = clean_input[meta_k]

        return output

    @staticmethod
    def _extract_numeric(clean_dict: Dict[str, Any], candidate_keys: list, default: Any = 0.0) -> Any:
        """Helper to extract and cast first matching candidate key to float."""
        for k in candidate_keys:
            if k in clean_dict:
                val = clean_dict[k]
                try:
                    if val is None or val == "" or str(val).lower() in ["nan", "null", "none"]:
                        return default
                    return float(val)
                except (ValueError, TypeError):
                    return default
        return default
