"""
Engineering Explanation Templates & Operator Advisory Library.
Provides physical domain explanations and actionable operational recommendations
for all 13 ESP fault classes, healthy operations, and novel anomalies.
"""

from typing import Dict, Any, List, Optional
from ml.data.canonical_schema import CanonicalESPTelemetry, FaultClass, ParameterEvaluation


FAULT_NARRATIVES = {
    FaultClass.HEALTHY: {
        "summary": "Pump is operating normally within its design envelope.",
        "why": ["All 13 monitored physical parameters remain within reference safety limits.", "Multivariate operating trajectory is stable."],
        "action": "Continue standard operational monitoring."
    },
    FaultClass.DRY_WELL_PUMP_OFF: {
        "summary": "Pump-off / loss of prime detected due to low downhole fluid level.",
        "why": ["Pump intake pressure collapsed below safety margin.", "Motor current dropped into electrical underload."],
        "action": "Throttle production choke or pause pump to allow reservoir fluid level recovery."
    },
    FaultClass.BLOCKED_INTAKE: {
        "summary": "Physical obstruction or debris detected at pump intake screen.",
        "why": ["Pump intake pressure and liquid rate dropped significantly while VFD frequency remained constant."],
        "action": "Perform intake screen backwash or cycle pump; inspect for scale/paraffin deposition."
    },
    FaultClass.SCALE_OR_PUMP_WEAR: {
        "summary": "Hydraulic degradation from internal stage wear or scale buildup.",
        "why": ["Differential pressure generation has degraded relative to power draw.", "Liquid production rate declining over time."],
        "action": "Schedule chemical scale inhibitor treatment or plan pump replacement workover."
    },
    FaultClass.SAND_INGESTION: {
        "summary": "Abrasive solids / sand ingestion detected.",
        "why": ["Vibration amplitude spiked above threshold.", "Erratic motor current oscillations observed."],
        "action": "Choke well to reduce fluid inflow drawdown velocity; inspect surface sand separators."
    },
    FaultClass.BEARING_DEGRADATION: {
        "summary": "Mechanical bearing wear or misalignment detected.",
        "why": ["High-frequency mechanical vibration elevated.", "Motor internal winding temperature increasing steadily."],
        "action": "Monitor vibration spectrum closely; schedule preventative pump replacement before motor seizure."
    },
    FaultClass.HIGH_VISCOSITY_COLD_START: {
        "summary": "High viscosity fluid resistance during startup.",
        "why": ["Motor loading elevated with cold wellbore fluid temperature.", "Startup torque resistance observed."],
        "action": "Allow gradual thermal equilibration; maintain controlled frequency ramp rate."
    },
    FaultClass.HIGH_BACKPRESSURE: {
        "summary": "Excessive flowline or surface restriction backpressure.",
        "why": ["Discharge pressure elevated above operating envelope.", "Production rate restricted despite high motor load."],
        "action": "Inspect surface valves, flowlines, heater-treater, and separator pressure."
    },
    FaultClass.OPEN_CHOKE: {
        "summary": "Surface choke over-opened, operating off the pump curve.",
        "why": ["Liquid production exceeds design maximum with depressed discharge head."],
        "action": "Trim surface choke orifice to restore ESP to its recommended operating range."
    },
    FaultClass.UNDERVOLTAGE: {
        "summary": "Electrical supply undervoltage condition.",
        "why": ["Motor terminal voltage depressed significantly below electrical operating limits."],
        "action": "Check power grid feeder, transformer tap setting, and surface VFD DC bus."
    },
    FaultClass.PHASE_IMBALANCE: {
        "summary": "Electrical current / voltage phase unbalance.",
        "why": ["Current variance between phases detected.", "Motor thermal ramp observed without proportional hydraulic load."],
        "action": "Perform phase-level voltage and current balance check at surface switchboard."
    },
    FaultClass.MOTOR_OVERLOAD: {
        "summary": "Thermal overload condition on ESP motor.",
        "why": ["Motor current continuously above rated full-load amperes (FLA).", "Winding temperature elevated."],
        "action": "Reduce operating frequency or throttle choke immediately to prevent motor burnout."
    },
    FaultClass.POWER_LOSS: {
        "summary": "Sudden electrical power supply interruption.",
        "why": ["Motor voltage and current collapsed instantaneously."],
        "action": "Inspect surface electrical substation, breakers, and VFD fault logs."
    },
    FaultClass.SENSOR_DRIFT: {
        "summary": "Downhole sensor calibration drift or gauge anomaly.",
        "why": ["Sensor reading deviates persistently from redundant and hydraulic correlation models."],
        "action": "Calibrate sensor; switch condition monitoring to secondary casing/surface pressure models."
    },
    FaultClass.UNKNOWN_UNSEEN: {
        "summary": "Unusual multivariate operating pattern detected (not in known fault library).",
        "why": ["High anomaly score with reconstruction error exceeding normal manifold.", "Class confidence does not match known fault library signatures."],
        "action": "Continue monitoring and request engineering diagnostic review."
    }
}


def build_explanation(
    fault_class: FaultClass,
    confidence: float,
    telemetry: CanonicalESPTelemetry,
    evaluations: List[ParameterEvaluation],
    anomaly_score: float = 0.0
) -> Dict[str, Any]:
    """Builds operator and engineer explanations."""
    template = FAULT_NARRATIVES.get(fault_class, FAULT_NARRATIVES[FaultClass.UNKNOWN_UNSEEN])
    
    why_bullets = list(template["why"])
    
    # Add parameter-specific deviation bullets
    for p in evaluations:
        if p.status.value in ["WARNING", "CRITICAL"]:
            why_bullets.append(f"{p.parameter}: {p.value:.1f} {p.unit} ({p.message})")

    # Generate trajectory summary
    trajectory_elements = []
    if telemetry.motor_temperature_c > 102.0:
        trajectory_elements.append("Motor Temp: ↑ elevated")
    if telemetry.motor_current_a > 38.0:
        trajectory_elements.append("Motor Current: ↑ elevated")
    elif telemetry.motor_current_a < 20.0 and telemetry.motor_current_a > 0:
        trajectory_elements.append("Motor Current: ↓ underload")
    if telemetry.discharge_pressure_psi > 2200.0:
        trajectory_elements.append("Discharge P: ↑ high")
    if telemetry.intake_pressure_psi < 150.0:
        trajectory_elements.append("Intake P: ↓ low")

    traj_summary = ", ".join(trajectory_elements) if trajectory_elements else "All core parameters tracking stable trajectory."

    return {
        "summary": template["summary"],
        "top_reasons": why_bullets[:5],
        "operator_action": template["action"],
        "trajectory_summary": traj_summary,
        "technical_details": f"Diagnosed {fault_class.value} with {confidence*100:.1f}% calibrated confidence (Anomaly Score: {anomaly_score:.3f})."
    }
