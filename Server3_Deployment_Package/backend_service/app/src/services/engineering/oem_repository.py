"""
OEM Master Data Repository
Grounded in ESP_APM_Engineering_Service_Architecture_Granular_Design.docx §14
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class OEMPumpCurvePoint(BaseModel):
    flow_bpd: float
    head_ft_per_stage: float
    efficiency_pct: float
    bhp_per_stage: float


class OEMPumpDataset(BaseModel):
    pump_model_id: str
    manufacturer: str
    base_frequency_hz: float = 60.0
    min_ror_bpd: float
    max_ror_bpd: float
    bep_bpd: float
    curve_points: List[OEMPumpCurvePoint]


class OEMMotorDataset(BaseModel):
    motor_model_id: str
    manufacturer: str
    rated_hp: float
    nameplate_current_a: float
    rated_voltage_v: float
    full_load_efficiency_pct: float
    power_factor: float


# Master OEM Repository Fixtures (§14 of Granular Design)
_PUMP_DATASETS: Dict[str, OEMPumpDataset] = {
    "D1450": OEMPumpDataset(
        pump_model_id="D1450",
        manufacturer="Baker Hughes / Centrilift",
        base_frequency_hz=60.0,
        min_ror_bpd=900.0,
        max_ror_bpd=1950.0,
        bep_bpd=1450.0,
        curve_points=[
            OEMPumpCurvePoint(flow_bpd=0.0, head_ft_per_stage=42.5, efficiency_pct=0.0, bhp_per_stage=0.85),
            OEMPumpCurvePoint(flow_bpd=500.0, head_ft_per_stage=40.0, efficiency_pct=42.0, bhp_per_stage=0.92),
            OEMPumpCurvePoint(flow_bpd=1000.0, head_ft_per_stage=36.2, efficiency_pct=65.5, bhp_per_stage=0.98),
            OEMPumpCurvePoint(flow_bpd=1450.0, head_ft_per_stage=33.7, efficiency_pct=74.2, bhp_per_stage=1.02),
            OEMPumpCurvePoint(flow_bpd=1800.0, head_ft_per_stage=28.5, efficiency_pct=68.0, bhp_per_stage=1.05),
            OEMPumpCurvePoint(flow_bpd=2200.0, head_ft_per_stage=18.0, efficiency_pct=45.0, bhp_per_stage=1.10),
        ]
    ),
    "DN1750": OEMPumpDataset(
        pump_model_id="DN1750",
        manufacturer="Schlumberger / REDA",
        base_frequency_hz=60.0,
        min_ror_bpd=1100.0,
        max_ror_bpd=2400.0,
        bep_bpd=1750.0,
        curve_points=[
            OEMPumpCurvePoint(flow_bpd=0.0, head_ft_per_stage=48.0, efficiency_pct=0.0, bhp_per_stage=1.10),
            OEMPumpCurvePoint(flow_bpd=1000.0, head_ft_per_stage=43.5, efficiency_pct=58.0, bhp_per_stage=1.22),
            OEMPumpCurvePoint(flow_bpd=1750.0, head_ft_per_stage=37.0, efficiency_pct=76.5, bhp_per_stage=1.35),
            OEMPumpCurvePoint(flow_bpd=2400.0, head_ft_per_stage=26.0, efficiency_pct=62.0, bhp_per_stage=1.42),
        ]
    )
}

_MOTOR_DATASETS: Dict[str, OEMMotorDataset] = {
    "M500": OEMMotorDataset(
        motor_model_id="M500",
        manufacturer="Baker Hughes",
        rated_hp=150.0,
        nameplate_current_a=65.0,
        rated_voltage_v=2150.0,
        full_load_efficiency_pct=88.5,
        power_factor=0.86
    )
}


class OEMMasterRepository:

    @staticmethod
    def get_pump_dataset(model_id: str) -> Optional[OEMPumpDataset]:
        return _PUMP_DATASETS.get(model_id.upper())

    @staticmethod
    def get_motor_dataset(model_id: str) -> Optional[OEMMotorDataset]:
        return _MOTOR_DATASETS.get(model_id.upper())

    @staticmethod
    def interpolate_pump_head(model_id: str, stage_count: int, flow_bpd: float, frequency_hz: float = 60.0) -> Optional[Dict[str, float]]:
        ds = OEMMasterRepository.get_pump_dataset(model_id)
        if not ds:
            return None

        # Convert operating flow rate to equivalent base 60Hz flow rate using affinity law Q60 = Q_op * (60 / f)
        ratio = 60.0 / max(frequency_hz, 1.0)
        q_base = flow_bpd * ratio

        # Piecewise linear interpolation
        pts = sorted(ds.curve_points, key=lambda p: p.flow_bpd)
        if q_base <= pts[0].flow_bpd:
            head_stage_60 = pts[0].head_ft_per_stage
            eff = pts[0].efficiency_pct
        elif q_base >= pts[-1].flow_bpd:
            head_stage_60 = pts[-1].head_ft_per_stage
            eff = pts[-1].efficiency_pct
        else:
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i+1]
                if p1.flow_bpd <= q_base <= p2.flow_bpd:
                    t = (q_base - p1.flow_bpd) / (p2.flow_bpd - p1.flow_bpd)
                    head_stage_60 = p1.head_ft_per_stage + t * (p2.head_ft_per_stage - p1.head_ft_per_stage)
                    eff = p1.efficiency_pct + t * (p2.efficiency_pct - p1.efficiency_pct)
                    break

        # Adjust total head for frequency and stage count: H_op = H_stage_60 * stages * (f / 60)^2
        f_ratio = frequency_hz / 60.0
        total_head_ft = head_stage_60 * stage_count * (f_ratio ** 2)

        return {
            "total_head_ft": total_head_ft,
            "head_ft_per_stage": head_stage_60 * (f_ratio ** 2),
            "efficiency_pct": eff,
            "min_ror_bpd": ds.min_ror_bpd * (frequency_hz / 60.0),
            "max_ror_bpd": ds.max_ror_bpd * (frequency_hz / 60.0),
            "bep_bpd": ds.bep_bpd * (frequency_hz / 60.0)
        }
