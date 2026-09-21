"""
Deterministic Engineering Physics Application Service
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.3
"""

import logging
from shared.schemas.engineering import (
    TDHRequest, TDHResponse, BEPRequest, BEPResponse, DrawdownRequest, DrawdownResponse
)

logger = logging.getLogger(__name__)


class EngineeringService:
    """
    Application Service for deterministic ESP physics calculations.
    """

    def calculate_tdh(self, req: TDHRequest) -> TDHResponse:
        """
        Calculate Total Dynamic Head: TDH = (PDP - PIP) * 2.31 / SG
        """
        if req.fluid_sg <= 0.0:
            raise ValueError("Fluid specific gravity must be positive.")

        delta_p = req.pdp_psi - req.pip_psi
        tdh = (delta_p * 2.31) / req.fluid_sg

        return TDHResponse(
            tdh_ft=round(tdh, 2),
            delta_p_psi=round(delta_p, 2),
            fluid_sg=req.fluid_sg,
            formula_used="(PDP - PIP) * 2.31 / SG",
            unit="ft"
        )

    def calculate_bep(self, req: BEPRequest) -> BEPResponse:
        """
        Calculate Best Efficiency Point (BEP) deviation.
        """
        if req.bep_target_bpd <= 0.0:
            raise ValueError("BEP target flow rate must be positive.")

        dev_bpd = req.current_flow_bpd - req.bep_target_bpd
        dev_pct = (dev_bpd / req.bep_target_bpd) * 100.0

        if dev_pct > 15.0:
            region = "UPTHRUST"
        elif dev_pct < -15.0:
            region = "DOWNTHRUST"
        else:
            region = "OPTIMAL"

        return BEPResponse(
            current_flow_bpd=req.current_flow_bpd,
            bep_target_bpd=req.bep_target_bpd,
            deviation_bpd=round(dev_bpd, 2),
            deviation_pct=round(dev_pct, 2),
            operating_region=region
        )

    def calculate_drawdown(self, req: DrawdownRequest) -> DrawdownResponse:
        """
        Calculate reservoir drawdown differential.
        """
        drawdown = req.static_reservoir_pressure_psi - req.flowing_bottomhole_pressure_psi
        return DrawdownResponse(
            drawdown_psi=round(drawdown, 2),
            productivity_index=None
        )
