import yaml
import pytest
from pathlib import Path
from app.contracts.objective_manifest import ObjectiveManifest

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

ALL_OBJECTIVES = [
    "OP01_CURRENT_STATUS.yaml",
    "OP02.yaml",
    "OP03_FAULT_DIAGNOSIS.yaml",
    "OP04.yaml",
    "OP05.yaml",
    "OP06.yaml",
    "OP07_GENERAL_INQUIRY.yaml",
    "OP14.yaml",
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
    assert manifest.scope in ("ASSET", "GLOBAL")
    assert isinstance(manifest.required_evidence, list)

@pytest.mark.parametrize("fname", PHASE2_OBJECTIVES)
def test_phase2_allowed_visuals_registered(fname):
    """Check 3: All allowed_visuals in manifests must be registered in cards_registry.yaml."""
    yaml_file = OBJECTIVES_DIR / fname
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = ObjectiveManifest.model_validate(data)
    cards = _load_cards()
    for card_id in manifest.allowed_visuals:
        assert card_id in cards, f"Card {card_id} from {fname} not registered in cards_registry.yaml"
