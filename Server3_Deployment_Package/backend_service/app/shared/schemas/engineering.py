"""
Engineering Physics Calculation Contracts
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.3
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TDHRequest(BaseModel):
    pdp_psi: float = Field(description="Discharge pressure in psi")
    pip_psi: float = Field(description="Intake pressure in psi")
    fluid_sg: float = Field(default=1.0, description="Fluid specific gravity (default 1.0 water equivalent)")


class TDHResponse(BaseModel):
    tdh_ft: float = Field(description="Calculated Total Dynamic Head in feet")
    delta_p_psi: float = Field(description="Pressure differential across pump")
    fluid_sg: float
    formula_used: str = Field(default="(PDP - PIP) * 2.31 / SG")
    unit: str = Field(default="ft")


class BEPRequest(BaseModel):
    current_flow_bpd: float = Field(description="Current liquid flow rate in BPD")
    bep_target_bpd: float = Field(default=1750.0, description="Pump design Best Efficiency Point in BPD")


class BEPResponse(BaseModel):
    current_flow_bpd: float
    bep_target_bpd: float
    deviation_bpd: float = Field(description="Numerical flow deviation from BEP")
    deviation_pct: float = Field(description="Percentage flow deviation from BEP")
    operating_region: str = Field(description="UPTHRUST, OPTIMAL, DOWNTHRUST")


class DrawdownRequest(BaseModel):
    static_reservoir_pressure_psi: float
    flowing_bottomhole_pressure_psi: float


class DrawdownResponse(BaseModel):
    drawdown_psi: float
    productivity_index: Optional[float] = Field(default=None)
