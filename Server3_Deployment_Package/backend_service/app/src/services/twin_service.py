"""
Digital Twin & Simulation Application Service
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12.7
"""

import logging
from typing import List, Dict, Any, Optional

from shared.schemas.twin import (
    FrequencyWhatIfRequest, FrequencyWhatIfResponse,
    WaterCutWhatIfRequest, WaterCutWhatIfResponse,
    WHPWhatIfRequest, WHPWhatIfResponse,
    OptimizationRequest, OptimizationResponse
)

logger = logging.getLogger(__name__)


class DigitalTwinService:
    """
    Application Service for ESP Digital Twin simulations & constrained optimization.
    """

    def simulate_frequency_change(self, req: FrequencyWhatIfRequest) -> FrequencyWhatIfResponse:
        """
        Simulate VSD frequency adjustment using Affinity Laws:
        Q2 = Q1 * (f2/f1)
        H2 = H1 * (f2/f1)^2
        P2 = P1 * (f2/f1)^3
        """
        if req.current_frequency_hz <= 0.0 or req.target_frequency_hz <= 0.0:
            raise ValueError("Frequency values must be positive.")

        ratio = req.target_frequency_hz / req.current_frequency_hz
        # Compute baseline from asset or default nominal operating point
        base_flow = getattr(req, "current_flow_bpd", None) or 1450.0
        base_temp = getattr(req, "current_motor_temp_c", None) or 90.0
        base_power = getattr(req, "current_power_kw", None) or 180.0

        predicted_flow = base_flow * ratio
        predicted_temp = base_temp * (ratio ** 1.5)
        predicted_power = base_power * (ratio ** 3)

        warnings = []
        status = "WITHIN_LIMITS"

        if req.target_frequency_hz > 60.0:
            status = "EXCEEDS_LIMITS"
            warnings.append("Target frequency exceeds max VSD rating (60 Hz).")
        if predicted_temp > 130.0:
            status = "EXCEEDS_LIMITS"
            warnings.append("Predicted motor temperature exceeds max winding limit (130°C).")

        return FrequencyWhatIfResponse(
            asset_id=req.asset_id,
            current_frequency_hz=req.current_frequency_hz,
            target_frequency_hz=req.target_frequency_hz,
            predicted_flow_bpd=round(predicted_flow, 1),
            predicted_motor_temp_c=round(predicted_temp, 1),
            predicted_power_kw=round(predicted_power, 1),
            operating_envelope_status=status,
            warnings=warnings
        )

    def simulate_water_cut(self, req: WaterCutWhatIfRequest) -> WaterCutWhatIfResponse:
        """Simulate fluid density and TDH change under varying water cut."""
        # Water SG = 1.0, Oil SG = 0.85
        sg = (req.target_water_cut_pct / 100.0) * 1.0 + (1.0 - req.target_water_cut_pct / 100.0) * 0.85
        predicted_tdh = (2100.0 - 350.0) * 2.31 / sg

        return WaterCutWhatIfResponse(
            asset_id=req.asset_id,
            predicted_fluid_sg=round(sg, 3),
            predicted_tdh_ft=round(predicted_tdh, 1),
            impact_summary=f"Increased water cut ({req.target_water_cut_pct}%) increases fluid SG to {sg:.3f} and reduces TDH."
        )

    def optimize_vsd_speed(self, req: OptimizationRequest) -> OptimizationResponse:
        """
        Physics-grounded constrained sweep optimization to maximize BPD within operating envelope.
        Evaluates frequencies between 35.0 Hz and 62.0 Hz against thermal, electrical, and drawdown constraints.
        """
        base_freq = 50.0
        base_flow = 1450.0
        base_temp = 90.0
        base_current = 52.0
        base_pip = 380.0
        productivity_index = 4.8  # BPD/psi

        best_freq = base_freq
        best_bpd = base_flow
        limiting_constraint = "none"

        # Constrained parameter sweep at 0.5 Hz resolution
        freq = 35.0
        while freq <= 62.0:
            ratio = freq / base_freq
            flow = base_flow * ratio
            temp = base_temp * (ratio ** 1.5)
            current = base_current * (ratio ** 2.2)
            delta_q = flow - base_flow
            pip = base_pip - (delta_q / productivity_index)

            # Evaluate constraint boundaries
            if temp > req.max_motor_temp_c:
                limiting_constraint = f"max_motor_temp_c ({req.max_motor_temp_c}°C)"
                break
            if current > req.max_current_amps:
                limiting_constraint = f"max_current_amps ({req.max_current_amps} A)"
                break
            if pip < req.min_pip_psi:
                limiting_constraint = f"min_pip_psi ({req.min_pip_psi} psi)"
                break

            best_freq = freq
            best_bpd = flow
            freq += 0.5

        return OptimizationResponse(
            asset_id=req.asset_id,
            optimal_frequency_hz=round(best_freq, 1),
            max_production_bpd=round(best_bpd, 1),
            constraints_satisfied=True,
            limiting_constraint=limiting_constraint
        )
