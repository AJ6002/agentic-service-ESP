import os
import glob
import yaml
from pathlib import Path
from typing import Dict, Optional
from app.contracts.objective_manifest import ObjectiveManifest

_OBJECTIVES: Dict[str, ObjectiveManifest] = {}


def clear_objective_registry() -> None:
    """Clears the in-process cache. Used in tests and hot-reload scenarios."""
    global _OBJECTIVES
    _OBJECTIVES.clear()


def load_objective_registry(
    config_dir: Optional[str] = None,
    force_reload: bool = False,
) -> Dict[str, ObjectiveManifest]:
    global _OBJECTIVES
    if _OBJECTIVES and not force_reload:
        return _OBJECTIVES

    if force_reload:
        _OBJECTIVES.clear()

    if config_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        config_dir = str(base_dir / "config" / "objectives")

    pattern = os.path.join(config_dir, "*.yaml")
    for file_path in glob.glob(pattern):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "objective_id" in data:
                manifest = ObjectiveManifest.model_validate(data)
                _OBJECTIVES[manifest.objective_id] = manifest
                short_id = manifest.objective_id.split("_")[0]
                if short_id not in _OBJECTIVES:
                    _OBJECTIVES[short_id] = manifest

    return _OBJECTIVES


def get_objective(objective_id: str) -> Optional[ObjectiveManifest]:
    registry = load_objective_registry()
    if objective_id in registry:
        return registry[objective_id]
    short_id = objective_id.split("_")[0]
    return registry.get(short_id)


def list_objectives() -> list[str]:
    registry = load_objective_registry()
    return [k for k in registry.keys() if "_" in k]
