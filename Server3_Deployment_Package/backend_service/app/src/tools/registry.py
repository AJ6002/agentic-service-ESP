"""
Central Tool Registry & Least-Privilege ACL Gate
Grounded in Guidelines.pdf §13.2 (p. 24) & Architecture Design §6
"""

import logging
from typing import Callable, Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)

# Objective to Allowed Tool ACL Mapping (Phase 4 Reconciled + Legacy Aliases)
OBJECTIVE_TOOL_ACL: Dict[str, Set[str]] = {
    # Reconciled Phase 4 Level-2 Objective Catalog
    "OP00_OPERATIONAL_CONTROL": set(),  # Advisory-only safety lock: no execution tools allowed
    "OP01_CURRENT_STATUS": {"get_asset_context", "get_live_snapshot", "get_health_index", "get_history_window", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},
    "OP02_PRODUCTION_DECLINE_RCA": {"get_asset_context", "get_live_snapshot", "get_history_window", "calculate_operating_point", "calculate_tdh", "search_knowledge_base", "get_fault_diagnosis", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},
    "OP03_FAULT_DIAGNOSIS": {"get_live_snapshot", "get_history_window", "get_rule_status", "get_fault_diagnosis", "search_knowledge_base", "calculate_tdh", "query_topology", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},
    "OP04_HEALTH_ASSESSMENT": {"get_health_index", "get_rule_status", "get_anomaly_result", "get_history_window", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},
    "OP05_EARLY_WARNING": {"get_anomaly_result", "get_live_snapshot", "get_history_window", "search_knowledge_base", "get_failure_prediction", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},
    "OP06_PROCEDURE_LOOKUP": {"search_knowledge_base", "get_term_definition", "build_agent_context", "get_evidence_pack", "get_evidence_item", "get_conflicts"},

    # Legacy Objective Aliases
    "OBJ_CURRENT_STATUS": {"get_asset_context", "get_live_snapshot", "get_health_index", "get_history_window"},
    "OBJ_EXPLAIN_ALERT": {"get_rule_status", "get_live_snapshot", "search_knowledge_base", "get_anomaly_result", "get_fault_diagnosis", "get_history_window"},
    "OBJ_DIAGNOSE_FAULT": {"get_live_snapshot", "get_rule_status", "get_fault_diagnosis", "search_knowledge_base", "calculate_tdh", "query_topology", "get_history_window"},
    "OBJ_TELEMETRY_ANALYSIS": {"get_live_snapshot", "get_history_window", "calculate_operating_point"},
    "OBJ_HEALTH_ASSESSMENT": {"get_health_index", "get_rule_status", "get_anomaly_result", "get_history_window"},
    "OBJ_COMPARE_ASSETS": {"get_asset_list", "get_live_snapshot", "get_history_window"},
    "OBJ_TREND_ANALYSIS": {"get_history_window", "get_rule_status"},
    "OBJ_EARLY_WARNING": {"get_anomaly_result", "get_live_snapshot", "search_knowledge_base", "get_history_window"},
    "OBJ_FAILURE_RISK": {"get_failure_prediction", "get_rule_status", "get_fault_diagnosis", "get_history_window"},
    "OBJ_TROUBLESHOOTING": {"search_knowledge_base", "get_fault_diagnosis", "get_live_snapshot", "get_history_window"},
    "OBJ_PRODUCTION_PERF": {"calculate_operating_point", "calculate_tdh", "get_live_snapshot", "get_history_window"},
    "OBJ_SCENARIO_WHATIF": {"calculate_operating_point", "get_health_index", "get_history_window"},
    "OBJ_MAINTENANCE_HIST": {"get_maintenance_history", "search_knowledge_base"},
    "OBJ_DATA_QUALITY": {"get_live_snapshot", "get_history_window"},
    "OBJ_ASSET_CONTEXT": {"get_asset_context", "search_knowledge_base"},
    "OBJ_PROCEDURES": {"search_knowledge_base", "get_term_definition"},
    "OBJ_SHIFT_REPORT": {"get_asset_list", "get_health_index", "get_rule_status", "get_history_window"},
    "OBJ_OPERATIONAL_CONTROL": set()
}

class ToolRegistry:
    """
    Central Tool Registry with Objective ACL Enforcement
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        """Register a logical tool implementation."""
        self._tools[name] = func
        logger.info(f"Registered tool: {name}")

    def execute_tool(self, tool_name: str, objective_id: str, **kwargs) -> Any:
        """
        Execute tool if permitted under the active objective ACL.
        """
        allowed = OBJECTIVE_TOOL_ACL.get(objective_id, set())
        if tool_name not in allowed:
            raise PermissionError(f"Tool '{tool_name}' is forbidden under active objective '{objective_id}'.")

        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered in ToolRegistry.")

        return self._tools[tool_name](**kwargs)

    def is_tool_allowed(self, tool_name: str, objective_id: str) -> bool:
        """Check if a tool is permitted under an objective ACL."""
        allowed = OBJECTIVE_TOOL_ACL.get(objective_id, set())
        return tool_name in allowed


def get_default_tool_registry() -> ToolRegistry:
    """Factory helper creating a fully populated ToolRegistry with core tools."""
    registry = ToolRegistry()
    from src.tools.fetch_telemetry import get_history_window_tool
    registry.register_tool("get_history_window", get_history_window_tool)
    return registry
