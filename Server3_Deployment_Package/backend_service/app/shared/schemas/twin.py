"""
Digital Twin & Simulation Contracts
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.7
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FrequencyWhatIfRequest(BaseModel):
    asset_id: str = Field(description="Target ESP asset ID")
    current_frequency_hz: float = Field(default=50.0)
    target_frequency_hz: float = Field(description="Proposed target VSD frequency in Hz")


class FrequencyWhatIfResponse(BaseModel):
    asset_id: str
    current_frequency_hz: float
    target_frequency_hz: float
    predicted_flow_bpd: float = Field(description="Estimated flow rate at target frequency")
    predicted_motor_temp_c: float = Field(description="Estimated motor temperature at target frequency")
    predicted_power_kw: float = Field(description="Estimated motor power draw in kW")
    operating_envelope_status: str = Field(default="WITHIN_LIMITS", description="WITHIN_LIMITS or EXCEEDS_LIMITS")
    warnings: List[str] = Field(default_factory=list)


class WaterCutWhatIfRequest(BaseModel):
    asset_id: str
    current_water_cut_pct: float = Field(default=20.0)
    target_water_cut_pct: float = Field(description="Target water cut percentage")


class WaterCutWhatIfResponse(BaseModel):
    asset_id: str
    predicted_fluid_sg: float
    predicted_tdh_ft: float
    impact_summary: str


class WHPWhatIfRequest(BaseModel):
    asset_id: str
    current_whp_psi: float
    target_whp_psi: float


class WHPWhatIfResponse(BaseModel):
    asset_id: str
    required_discharge_pressure_psi: float
    motor_load_impact_pct: float


class OptimizationRequest(BaseModel):
    asset_id: str
    max_motor_temp_c: float = Field(default=130.0)
    max_current_amps: float = Field(default=65.0)
    min_pip_psi: float = Field(default=300.0)


class OptimizationResponse(BaseModel):
    asset_id: str
    optimal_frequency_hz: float
    max_production_bpd: float
    constraints_satisfied: bool
    limiting_constraint: str
