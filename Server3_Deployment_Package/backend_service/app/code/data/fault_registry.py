"""
Central Python interface for the 13-Fault Hybrid Diagnostic Registry.
Provides programmatic access to fault definitions, detection methods,
and required inputs without duplicating configuration across codebase.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "fault_registry.yaml"


class FaultMetadata(BaseModel):
    fault_id: str
    display_name: str
    detection_method: str  # "ML + RULE" or "RULE_ONLY"
    ml_supported: bool
    rule_supported: bool
    training_examples: int
    event_count: int
    affected_wells: List[str]
    required_inputs: List[str]
    severity: str
    confidence_method: str
    validation_status: str
    readiness: str
    rule_definition: str
    operator_action: str
    explanation_template: str


class ESPFaultRegistry:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self._load_registry()

    def _load_registry(self):
        if not self.config_path.exists():
            self.faults: Dict[str, FaultMetadata] = {}
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        self.faults = {
            item["fault_id"]: FaultMetadata(**item)
            for item in data.get("faults", [])
        }
        self.non_fault_states = data.get("non_fault_states", [])

    def get_fault(self, fault_id: str) -> Optional[FaultMetadata]:
        return self.faults.get(fault_id)

    def list_all_faults(self) -> List[FaultMetadata]:
        return list(self.faults.values())

    def get_ml_supported_faults(self) -> List[FaultMetadata]:
        return [f for f in self.faults.values() if f.ml_supported]

    def get_rule_only_faults(self) -> List[FaultMetadata]:
        return [f for f in self.faults.values() if not f.ml_supported]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faults": [f.model_dump() for f in self.faults.values()],
            "non_fault_states": self.non_fault_states
        }


# Global Registry Instance
fault_registry = ESPFaultRegistry()
