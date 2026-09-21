"""
FastMCP Server for ESP APM Platform
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §15, §16
"""

import sys
import os

# Ensure esp_agent root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from mcp.server.fastmcp import FastMCP
from src.api.mcp.engineering_mcp import mcp_calculate_tdh, mcp_calculate_bep
from src.services.twin_service import DigitalTwinService
from shared.schemas.twin import FrequencyWhatIfRequest

# Initialize FastMCP Server
mcp = FastMCP("ESP APM Engineering & Simulation MCP Server")
twin_service = DigitalTwinService()


@mcp.tool()
def calculate_tdh(pdp_psi: float, pip_psi: float, fluid_sg: float = 1.0) -> dict:
    """Calculate Total Dynamic Head (TDH) in feet for an ESP well."""
    return mcp_calculate_tdh(pdp_psi=pdp_psi, pip_psi=pip_psi, fluid_sg=fluid_sg)


@mcp.tool()
def calculate_bep(current_flow_bpd: float, bep_target_bpd: float = 1750.0) -> dict:
    """Calculate Best Efficiency Point (BEP) flow rate deviation and operating region."""
    return mcp_calculate_bep(current_flow_bpd=current_flow_bpd, bep_target_bpd=bep_target_bpd)


@mcp.tool()
def simulate_frequency_change(asset_id: str, current_frequency_hz: float, target_frequency_hz: float) -> dict:
    """Simulate flow rate, motor temperature, and power draw under VSD frequency change."""
    req = FrequencyWhatIfRequest(
        asset_id=asset_id,
        current_frequency_hz=current_frequency_hz,
        target_frequency_hz=target_frequency_hz
    )
    res = twin_service.simulate_frequency_change(req)
    return res.model_dump()


if __name__ == "__main__":
    mcp.run()
