"""
Service Contract Registry Loader & Validation Utility
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §6
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "service_registry.yaml")


class ServiceRegistry:
    """
    Registry class that parses and validates service_registry.yaml on startup.
    """

    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self._services: Dict[str, Any] = {}
        self.load_registry()

    def load_registry(self):
        """Load and parse service registry YAML file."""
        if not os.path.exists(self.registry_path):
            logger.warning(f"Service registry file '{self.registry_path}' not found. Initializing empty registry.")
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._services = data.get("services", {})
            logger.info(f"Loaded {len(self._services)} services into ServiceRegistry.")
        except Exception as ex:
            logger.error(f"Failed to parse service registry YAML: {ex}")
            raise

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve service contract by service_id."""
        return self._services.get(service_id)

    def list_services(self) -> List[str]:
        """Return list of registered service IDs."""
        return list(self._services.keys())
