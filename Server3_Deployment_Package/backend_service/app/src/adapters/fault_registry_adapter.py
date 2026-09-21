"""
Fault Registry Adapter for ESP Agent
Loads authoritative 13-fault taxonomy from cced_esp/config/fault_registry.yaml
Provides single source of truth for candidate diagnostic hypotheses.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Search paths for the canonical fault_registry.yaml
CANDIDATE_PATHS = [
    Path(__file__).resolve().parent.parent / "knowledge_bases" / "esp" / "fault_registry.yaml",
    Path(__file__).resolve().parent.parent.parent.parent / "cced_esp" / "config" / "fault_registry.yaml",
    Path(__file__).resolve().parent.parent.parent / "cced_esp" / "config" / "fault_registry.yaml",
]


class FaultCandidate(BaseModel):
    fault_id: str
    display_name: str
    severity: str = "MEDIUM"
    detection_method: str = "ML + RULE"
    operator_action: str = ""
    explanation_template: str = ""


class FaultRegistryAdapter:
    """Adapter reading canonical 13-fault taxonomy for diagnostic hypothesis generation."""

    def __init__(self):
        self._faults: Dict[str, FaultCandidate] = {}
        self._non_fault_states: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        found_path = None
        for p in CANDIDATE_PATHS:
            if p.exists():
                found_path = p
                break

        if not found_path:
            logger.warning("[FaultRegistryAdapter] fault_registry.yaml not found on disk. Initializing fallback taxonomy.")
            self._init_fallback()
            return

        try:
            with open(found_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            for item in data.get("faults", []):
                fc = FaultCandidate(
                    fault_id=item.get("fault_id", "UNKNOWN"),
                    display_name=item.get("display_name", item.get("fault_id", "UNKNOWN")),
                    severity=item.get("severity", "MEDIUM"),
                    detection_method=item.get("detection_method", "ML + RULE"),
                    operator_action=item.get("operator_action", ""),
                    explanation_template=item.get("explanation_template", "")
                )
                self._faults[fc.fault_id] = fc

            self._non_fault_states = data.get("non_fault_states", [])
            logger.info(f"[FaultRegistryAdapter] Successfully loaded {len(self._faults)} canonical faults from {found_path}")
        except Exception as e:
            logger.error(f"[FaultRegistryAdapter] Error reading fault registry: {e}. Using fallback.")
            self._init_fallback()

    def _init_fallback(self):
        fallback_ids = [
            "DRY_WELL_PUMP_OFF", "BLOCKED_INTAKE", "SCALE_OR_PUMP_WEAR",
            "HIGH_VISCOSITY_COLD_START", "HIGH_BACKPRESSURE", "OPEN_CHOKE",
            "UNDERVOLTAGE", "PHASE_IMBALANCE", "MOTOR_OVERLOAD", "POWER_LOSS",
            "SENSOR_DRIFT", "SAND_INGESTION", "BEARING_DEGRADATION"
        ]
        self._faults = {
            fid: FaultCandidate(fault_id=fid, display_name=fid.replace("_", " ").title())
            for fid in fallback_ids
        }

    def list_candidates(self) -> List[FaultCandidate]:
        return list(self._faults.values())

    def get_candidate(self, fault_id: str) -> Optional[FaultCandidate]:
        return self._faults.get(fault_id)

    def get_candidate_ids(self) -> List[str]:
        return list(self._faults.keys())


# Singleton instance
fault_registry_adapter = FaultRegistryAdapter()
