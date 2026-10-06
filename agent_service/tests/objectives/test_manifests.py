import yaml
import pytest
from pathlib import Path
from app.contracts.objective_manifest import ObjectiveManifest
from app.routing.objective_registry import get_objective

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
OBJECTIVES_DIR = CONFIG_DIR / "objectives"
CARDS_REGISTRY_PATH = CONFIG_DIR / "cards_registry.yaml"

PHASE2_OBJECTIVES = [
    "OP04.yaml",
    "OP05.yaml",
    "OP14.yaml",
    "OP02.yaml",
    "OP06.yaml",
]

FLEET_OBJECTIVES = [
    "OP08_FLEET_INVENTORY.yaml",
    "OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml",
    "OP13_FLEET_EXECUTIVE_REPORT.yaml",
]

ALL_OBJECTIVES = [
    "OP01_CURRENT_STATUS.yaml",
    "OP02.yaml",
    "OP03_FAULT_DIAGNOSIS.yaml",
    "OP04.yaml",
    "OP05.yaml",
    "OP06.yaml",
    "OP07_GENERAL_INQUIRY.yaml",
    "OP08_FLEET_INVENTORY.yaml",
    "OP09_FLEET_PRODUCTION_OPTIMIZATION.yaml",
    "OP13_FLEET_EXECUTIVE_REPORT.yaml",
    "OP14.yaml",
    "OP15_PLATFORM_GUIDE.yaml",
]

def _load_cards():
    with open(CARDS_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("cards", {})

@pytest.mark.parametrize("fname", ALL_OBJECTIVES)
def test_manifest_schema_validation(fname):
    """Check 1: YAML loads, validates against ObjectiveManifest schema."""
    yaml_file = OBJECTIVES_DIR / fname
    assert yaml_file.exists(), f"Missing objective file: {fname}"
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = ObjectiveManifest.model_validate(data)
    assert manifest.objective_id is not None
    assert manifest.safety_class in ("READ", "WRITE")
    assert manifest.scope in ("ASSET", "GLOBAL", "FLEET", "MULTI_ASSET")
    assert isinstance(manifest.required_evidence, list)

@pytest.mark.parametrize("fname", PHASE2_OBJECTIVES)
def test_phase2_allowed_visuals_registered(fname):
    """Check 2: All allowed_visuals in manifests must be registered in cards_registry.yaml."""
    yaml_file = OBJECTIVES_DIR / fname
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = ObjectiveManifest.model_validate(data)
    cards = _load_cards()
    for card_id in manifest.allowed_visuals:
        assert card_id in cards, f"Card {card_id} from {fname} not registered in cards_registry.yaml"

@pytest.mark.parametrize("fname", FLEET_OBJECTIVES)
def test_fleet_manifests_no_asset_id_requirement(fname):
    """Check 3: Fleet objectives must declare scope FLEET and require 0 asset_id arguments."""
    yaml_file = OBJECTIVES_DIR / fname
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = ObjectiveManifest.model_validate(data)
    
    assert manifest.scope == "FLEET", f"{fname} must have scope FLEET"
    required_args = manifest.arg_schema.get("required", [])
    assert "asset_id" not in required_args, f"{fname} must not require asset_id"
    assert len(required_args) == 0, f"{fname} must require 0 arguments"
    
    cards = _load_cards()
    for card_id in manifest.allowed_visuals:
        assert card_id in cards, f"Allowed visual {card_id} not in cards_registry.yaml"
    for card_id in (manifest.default_visuals or []):
        assert card_id in cards, f"Default visual {card_id} not in cards_registry.yaml"

def test_fleet_objectives_registry_resolution():
    """Check 4: Objective registry loads short and long IDs for fleet objectives."""
    for oid in ["OP08", "OP08_FLEET_INVENTORY", "OP09", "OP09_FLEET_PRODUCTION_OPTIMIZATION", "OP13", "OP13_FLEET_EXECUTIVE_REPORT"]:
        manifest = get_objective(oid)
        assert manifest is not None, f"Objective {oid} not found in objective registry"
        assert manifest.scope == "FLEET"
        assert "asset_id" not in manifest.arg_schema.get("required", [])
