"""
Engineering Physics MCP Tool Wrappers
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §15, §16
"""

from typing import Dict, Any
from src.services.engineering_service import EngineeringService
from shared.schemas.engineering import TDHRequest, BEPRequest

engineering_service = EngineeringService()


def mcp_calculate_tdh(pdp_psi: float, pip_psi: float, fluid_sg: float = 1.0) -> Dict[str, Any]:
    """
    MCP Tool wrapper for EngineeringService.calculate_tdh.
    """
    req = TDHRequest(pdp_psi=pdp_psi, pip_psi=pip_psi, fluid_sg=fluid_sg)
    res = engineering_service.calculate_tdh(req)
    return res.model_dump()


def mcp_calculate_bep(current_flow_bpd: float, bep_target_bpd: float = 1750.0) -> Dict[str, Any]:
    """
    MCP Tool wrapper for EngineeringService.calculate_bep.
    """
    req = BEPRequest(current_flow_bpd=current_flow_bpd, bep_target_bpd=bep_target_bpd)
    res = engineering_service.calculate_bep(req)
    return res.model_dump()
