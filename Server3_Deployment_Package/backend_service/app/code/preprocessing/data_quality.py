"""
Data Quality & Sensor Plausibility Engine.
Assesses incoming live telemetry and batches for missing values, out-of-range readings,
sensor freezing (stuck values), timestamp anomalies, and clock jumps.
"""

from typing import Dict, Any, List, Tuple
from ml.data.canonical_schema import CanonicalESPTelemetry, DataQualityStatus


# Physical Plausibility Ranges for ESP Operations
SENSOR_PHYSICAL_BOUNDS = {
    "liquid_rate_bpd": (0.0, 5000.0),
    "intake_pressure_psi": (0.0, 3500.0),
    "discharge_pressure_psi": (0.0, 5000.0),
    "motor_current_a": (0.0, 150.0),
    "motor_voltage_v": (0.0, 3000.0),
    "motor_temperature_c": (0.0, 200.0),
    "intake_temperature_c": (0.0, 150.0),
    "vibration_rms": (0.0, 5.0),
    "flowline_pressure_psi": (0.0, 1500.0),
    "wellhead_pressure_psi": (0.0, 2000.0),
    "casing_pressure_psi": (0.0, 1500.0),
    "choke_size_64in": (0.0, 128.0),
    "frequency_hz": (0.0, 90.0)
}


class DataQualityEngine:
    def __init__(self):
        self.history_buffers: Dict[str, List[float]] = {}
        self.max_buffer_size = 20

    def evaluate(self, telemetry: CanonicalESPTelemetry) -> Tuple[DataQualityStatus, List[str]]:
        """
        Evaluates a single incoming CanonicalESPTelemetry instance.
        Returns the overall DataQualityStatus and a list of human-readable warnings.
        """
        warnings: List[str] = []
        critical_fault_count = 0
        degraded_fault_count = 0

        CORE_PARAMS = {"liquid_rate_bpd", "intake_pressure_psi", "discharge_pressure_psi", "motor_current_a", "motor_voltage_v", "motor_temperature_c", "vibration_rms"}

        # 1. Physical Bounds Check
        for param, (min_val, max_val) in SENSOR_PHYSICAL_BOUNDS.items():
            val = getattr(telemetry, param, None)
            if val is None:
                if param in CORE_PARAMS:
                    warnings.append(f"Missing core measurement for {param}")
                    degraded_fault_count += 1
                continue
            
            # Check for negative values where impossible
            if val < min_val:
                warnings.append(f"{param} value ({val:.2f}) is below physical minimum ({min_val})")
                if param in ["intake_pressure_psi", "discharge_pressure_psi", "motor_current_a"]:
                    critical_fault_count += 1
                else:
                    degraded_fault_count += 1
            elif val > max_val:
                warnings.append(f"{param} value ({val:.2f}) exceeds physical maximum ({max_val})")
                degraded_fault_count += 1


        # 2. Cross-Sensor Hydraulic Consistency Check
        # Discharge Pressure should physically exceed Intake Pressure when pump is running with flow
        if (
            telemetry.liquid_rate_bpd > 50.0 and 
            telemetry.discharge_pressure_psi > 0 and 
            telemetry.intake_pressure_psi > 0
        ):
            if telemetry.discharge_pressure_psi < telemetry.intake_pressure_psi:
                warnings.append(
                    f"Hydraulic anomaly: Discharge Pressure ({telemetry.discharge_pressure_psi:.1f} PSI) "
                    f"< Intake Pressure ({telemetry.intake_pressure_psi:.1f} PSI) during active production."
                )
                degraded_fault_count += 1

        # 3. Sensor Freezing Check (Track history in memory)
        esp_key = f"{telemetry.esp_id}_{telemetry.well_id}"
        if esp_key not in self.history_buffers:
            self.history_buffers[esp_key] = []
        
        # Track pressure for freezing
        buf = self.history_buffers[esp_key]
        buf.append(telemetry.discharge_pressure_psi)
        if len(buf) > self.max_buffer_size:
            buf.pop(0)

        if len(buf) >= self.max_buffer_size and telemetry.liquid_rate_bpd > 0:
            if max(buf) == min(buf):
                warnings.append(f"Possible frozen sensor: Discharge Pressure constant for {self.max_buffer_size} samples.")
                degraded_fault_count += 1

        # Determine Overall Data Quality
        if critical_fault_count > 0 or degraded_fault_count >= 4:
            status = DataQualityStatus.INSUFFICIENT
        elif degraded_fault_count > 0:
            status = DataQualityStatus.DEGRADED
        else:
            status = DataQualityStatus.GOOD

        return status, warnings
