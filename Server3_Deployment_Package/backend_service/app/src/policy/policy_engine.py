"""
Policy & Access Control Engine (ACL & Multi-Tenant Security)
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §13, §14
"""

import logging
from typing import List, Dict, Any, Optional

from src.agent.objective_registry import ObjectiveRegistry
from shared.schemas.errors import ServiceErrorPayload

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy & Access Control Engine.
    Executes BEFORE Application Services are called.
    """

    def __init__(self, registry: Optional[ObjectiveRegistry] = None):
        self.registry = registry or ObjectiveRegistry()

    def enforce_tenant_isolation(self, tenant_id: Optional[str], asset_id: str):
        """Verify tenant authorization for asset query scope."""
        if not tenant_id:
            logger.info(f"No X-Tenant-ID header provided. Authorizing asset '{asset_id}' under default multi-tenant context.")
            return

        # Check tenant authorization rules
        allowed_tenants = ["default", "cced", "tenant-alpha", "tenant-beta", "cced_operator"]
        if tenant_id.lower() not in allowed_tenants and not tenant_id.lower().startswith("tenant"):
            logger.warning(f"Tenant isolation breach: '{tenant_id}' denied access to asset '{asset_id}'")
            raise PermissionError(f"Tenant '{tenant_id}' unauthorized to access asset '{asset_id}'")

        logger.info(f"PolicyEngine verified tenant '{tenant_id}' access to asset '{asset_id}'")

    def enforce_tool_acl(self, objective_id: str, tool_name: str):
        """
        Verify tool call authorization against active objective.
        Raises PermissionError if tool is unauthorized for active objective context.
        """
        obj_def = self.registry.get(objective_id)
        if not obj_def:
            logger.warning(f"Unknown objective '{objective_id}'. Allowing default tools.")
            return

        # Check explicit forbidden actions
        if obj_def.safety and tool_name in obj_def.safety.forbidden_actions:
            raise PermissionError(f"POLICY_VIOLATION: Tool '{tool_name}' is explicitly forbidden under objective '{objective_id}'.")

        logger.info(f"PolicyEngine authorized tool '{tool_name}' under objective '{objective_id}'")

    def enforce_specialist_rbac(self, objective_id: str, specialist_name: str):
        """Verify specialist execution path under active objective."""
        obj_def = self.registry.get(objective_id)
        if not obj_def:
            return

        if obj_def.allowed_specialists and specialist_name not in obj_def.allowed_specialists:
            raise PermissionError(f"POLICY_VIOLATION: Specialist '{specialist_name}' not allowed under objective '{objective_id}'. Allowed: {obj_def.allowed_specialists}")

        logger.info(f"PolicyEngine authorized specialist '{specialist_name}' under objective '{objective_id}'")
