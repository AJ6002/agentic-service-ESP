import os
from pathlib import Path
import pytest
import yaml
from pydantic import ValidationError

from app.contracts.ui_map import UiMapEntry, UiMapType, UiMapWorkspace


def test_ui_map_entry_model_valid():
    entry = UiMapEntry(
        id="route.test",
        type="route",
        title="Test Route",
        path="/test",
        workspace="operations",
        summary="A test route summary.",
        description="A full test description containing grounded facts.",
        related=["component.test"],
        aliases=["test"],
    )
    assert entry.id == "route.test"
    assert entry.type == "route"
    assert entry.path == "/test"
    assert entry.workspace == "operations"
    assert entry.related == ["component.test"]
    assert entry.aliases == ["test"]


def test_ui_map_entry_invalid_type_rejected():
    with pytest.raises(ValidationError):
        UiMapEntry(
            id="bad.type",
            type="invalid_type",  # not in enum
            title="Bad",
            workspace="operations",
            summary="Bad summary",
            description="Bad desc",
        )


def test_ui_map_entry_invalid_workspace_rejected():
    with pytest.raises(ValidationError):
        UiMapEntry(
            id="bad.workspace",
            type="concept",
            title="Bad",
            workspace="invalid_workspace",  # not in enum
            summary="Bad summary",
            description="Bad desc",
        )


def test_ui_map_entry_missing_required_fields_rejected():
    with pytest.raises(ValidationError):
        # Missing description and summary
        UiMapEntry(
            id="bad.missing",
            type="concept",
            title="Bad",
            workspace="platform",
        )


def test_ui_map_yaml_file_validation():
    # Resolve dashboard ui_map.yaml path
    env_path = os.environ.get("UI_MAP_PATH")
    if env_path and Path(env_path).is_file():
        yaml_path = Path(env_path)
    else:
        # Standard relative location from agent repo to esp-insight-suite
        yaml_path = Path("a:/TAS-AI/esp-insight-suite/docs/ui_map/ui_map.yaml")
        if not yaml_path.is_file():
            # Fallback to local machine path structure
            yaml_path = Path(r"A:\TAS-AI\esp-insight-suite\docs\ui_map\ui_map.yaml")

    assert yaml_path.is_file(), f"ui_map.yaml not found at {yaml_path}"

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    assert isinstance(raw_data, list), "ui_map.yaml root must be a list of entries"
    assert len(raw_data) >= 3, f"Expected at least 3 sample entries, found {len(raw_data)}"

    # Parse and validate each entry through Pydantic contract
    entries: list[UiMapEntry] = []
    seen_ids = set()
    types_found = set()

    for item in raw_data:
        entry = UiMapEntry.model_validate(item)
        entries.append(entry)

        # Ensure ID uniqueness
        assert entry.id not in seen_ids, f"Duplicate ui_map ID: {entry.id}"
        seen_ids.add(entry.id)
        types_found.add(entry.type)

        # Word count check: 100-300 words
        word_count = len(entry.description.split())
        assert 100 <= word_count <= 300, (
            f"Entry {entry.id} description must be 100-300 words, got {word_count}"
        )

    # Verify 3 distinct required sample types exist
    assert "route" in types_found, "Missing 'route' sample entry"
    assert "component" in types_found, "Missing 'component' sample entry"
    assert "concept" in types_found, "Missing 'concept' sample entry"

    # Verify cross-references (related) point to existing IDs in the map
    for entry in entries:
        for rel in entry.related:
            assert rel in seen_ids, f"Entry {entry.id} references non-existent related ID: {rel}"

    # Specific checks on sample entries
    route_entry = next(e for e in entries if e.id == "route.working-status")
    assert route_entry.path == "/working-status"
    assert route_entry.workspace == "operations"

    comp_entry = next(e for e in entries if e.id == "component.subsystem-equalizer")
    assert comp_entry.path is None
    assert comp_entry.workspace == "operations"

    concept_entry = next(e for e in entries if e.id == "concept.tdh")
    assert concept_entry.path is None
    assert concept_entry.workspace == "platform"
