"""
Objective Registry Service
Grounded in PHASE_4_Objective_Layer_Implementation_Plan_ESP_APM.docx §17, §27
"""

import os
import json
import logging
from typing import Dict, List, Optional

from src.schemas.objective import ObjectiveDefinition

from pathlib import Path

logger = logging.getLogger(__name__)

_ESP_AGENT_ROOT = Path(__file__).resolve().parent.parent.parent
_CANDIDATE_OBJECTIVES_DIR = _ESP_AGENT_ROOT / "knowledge_bases" / "esp" / "objectives"
DEFAULT_OBJECTIVES_DIR = str(_CANDIDATE_OBJECTIVES_DIR) if _CANDIDATE_OBJECTIVES_DIR.exists() else "knowledge_bases/esp/objectives"

_CANDIDATE_MAPPING_PATH = _ESP_AGENT_ROOT / "knowledge_bases" / "esp" / "events" / "event_objective_mapping.yaml"
DEFAULT_EVENT_MAPPINGS_PATH = str(_CANDIDATE_MAPPING_PATH) if _CANDIDATE_MAPPING_PATH.exists() else "knowledge_bases/esp/events/event_objective_mapping.yaml"

class ObjectiveRegistry:
    """
    Control-plane registry that loads and validates Level-2 Operational Objectives.
    """

    def __init__(self, objectives_dir: Optional[str] = None):
        self.objectives_dir = objectives_dir or DEFAULT_OBJECTIVES_DIR
        self._registry: Dict[str, ObjectiveDefinition] = {}
        self._event_mappings: Dict[str, str] = {}
        self.load_objectives()
        self.load_event_mappings(DEFAULT_EVENT_MAPPINGS_PATH)

    def load_objectives(self):
        """Load and validate all JSON objective definitions from objectives_dir."""
        self._registry.clear()
        
        if not os.path.exists(self.objectives_dir):
            logger.warning(f"Objectives directory '{self.objectives_dir}' not found. Loading fallback objectives.")
            self._load_fallback_objectives()
            return

        loaded_count = 0
        for fname in os.listdir(self.objectives_dir):
            if fname.endswith(".json") and fname != "strategic_objectives.json":
                fpath = os.path.join(self.objectives_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    obj_def = ObjectiveDefinition(**data)
                    self._registry[obj_def.objective_id] = obj_def
                    loaded_count += 1
                except Exception as ex:
                    logger.error(f"Failed to load objective file '{fname}': {ex}")

        if loaded_count == 0:
            logger.warning("No valid objective JSON files found. Loading fallback objectives.")
            self._load_fallback_objectives()
        else:
            logger.info(f"ObjectiveRegistry successfully loaded {len(self._registry)} Level-2 objectives.")

    def load_event_mappings(self, mapping_path: str = "knowledge_bases/esp/events/event_objective_mapping.yaml"):
        """Load event-to-objective mapping registry as single authority."""
        self._event_mappings.clear()
        if not os.path.exists(mapping_path):
            logger.warning(f"Event mapping file '{mapping_path}' not found.")
            return

        try:
            import yaml
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            for m in data.get("mappings", []):
                evt = m.get("event_type")
                obj_id = m.get("target_objective_id")
                if evt and obj_id:
                    self._event_mappings[evt] = obj_id
            logger.info(f"ObjectiveRegistry loaded {len(self._event_mappings)} event-to-objective mappings.")
        except Exception as ex:
            logger.error(f"Failed to load event mappings from '{mapping_path}': {ex}")

    def resolve_event_mapping(self, event_code: str) -> Optional[str]:
        """Resolve an event code or event_type string to a target Phase-4 Objective ID."""
        return self._event_mappings.get(event_code)

    def get(self, objective_id: str) -> Optional[ObjectiveDefinition]:
        """Retrieve objective definition by ID, fallback to default if unknown."""
        if objective_id in self._registry:
            return self._registry[objective_id]
        if objective_id in ("CLARIFICATION", "UNCLASSIFIED"):
            return None
        # Return fallback objective if ID is unrecognized
        logger.warning(f"Objective ID '{objective_id}' not found in registry. Returning default OP03_FAULT_DIAGNOSIS.")
        return self._registry.get("OP03_FAULT_DIAGNOSIS")

    def list_all(self) -> List[ObjectiveDefinition]:
        """Return list of all registered objective definitions."""
        return list(self._registry.values())

    def _load_fallback_objectives(self):
        """Hard-coded fallback definitions if JSON files are missing."""
        fallback_op02 = ObjectiveDefinition(
            objective_id="OP02_PRODUCTION_DECLINE_RCA",
            title="Production Decline Root Cause Analysis",
            description="Diagnose root causes for reduced liquid rate or production drop.",
            strategic_objectives=["O1", "O5"],
            intent_classes=["production_decline", "producing less", "low flow", "bpd drop"],
            required_asset_context=["asset_id", "tag_mapping", "be_point_bpd"],
            required_signals=["flowline_pressure", "intake_pressure", "discharge_pressure", "frequency", "drive_current_average", "motor_temperature"],
            required_evidence=["current_snapshot", "6h_history", "24h_history"],
            required_tools=["get_asset_context", "get_live_snapshot", "calculate_operating_point"],
            allowed_specialists=["well_performance", "reliability"],
            success_criteria=["ranked hypotheses", "evidence cited", "verification steps provided"]
        )
        fallback_op03 = ObjectiveDefinition(
            objective_id="OP03_FAULT_DIAGNOSIS",
            title="ESP Fault & Anomaly Diagnosis",
            description="Identify downhole equipment faults or anomalies.",
            strategic_objectives=["O2", "O5"],
            intent_classes=["diagnose", "fault", "issue", "problem", "overheating", "vibration"],
            required_asset_context=["asset_id", "pump_model"],
            required_signals=["motor_temperature", "vibration_x"],
            required_evidence=["current_snapshot", "model_predictions"],
            required_tools=["get_asset_context", "model_adapter.get_model_output"],
            allowed_specialists=["reliability"],
            success_criteria=["fault classified", "confidence score provided"]
        )
        self._registry[fallback_op02.objective_id] = fallback_op02
        self._registry[fallback_op03.objective_id] = fallback_op03
