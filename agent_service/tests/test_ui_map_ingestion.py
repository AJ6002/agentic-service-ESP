import os
import pytest
from pathlib import Path

from app.contracts.ui_map import UiMapEntry
from app.stores.postgres_client import get_db_cursor
from scripts.ingest_ui_map_to_postgres import ingest_ui_map
from scripts.verify_ui_map_retrieval import search_chunks

YAML_PATH = Path(__file__).resolve().parent.parent / "config" / "ui_map" / "ui_map.yaml"

def test_ui_map_working_copy_exists_and_valid():
    assert YAML_PATH.is_file(), f"Expected UI map YAML at {YAML_PATH}"
    import yaml
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list)
    assert len(data) == 3
    entries = [UiMapEntry.model_validate(item) for item in data]
    assert len(entries) == 3
    assert {e.id for e in entries} == {"route.working-status", "component.subsystem-equalizer", "concept.tdh"}

def test_ingest_ui_map_idempotent_execution():
    # Run ingestion
    count1 = ingest_ui_map(str(YAML_PATH))
    assert count1 == 3

    # Re-run ingestion to prove idempotency
    count2 = ingest_ui_map(str(YAML_PATH))
    assert count2 == 3

def test_postgres_ui_map_chunks_tagged_distinctly():
    with get_db_cursor() as cur:
        cur.execute("SELECT chunk_id, source_domain, metadata FROM kb_chunks WHERE source_domain = 'ui_map' ORDER BY chunk_id;")
        rows = cur.fetchall()

    assert len(rows) == 3
    chunk_ids = [r[0] for r in rows]
    assert "ui_map:route.working-status" in chunk_ids
    assert "ui_map:component.subsystem-equalizer" in chunk_ids
    assert "ui_map:concept.tdh" in chunk_ids

    for r in rows:
        assert r[1] == "ui_map"
        meta = r[2]
        assert "type" in meta
        assert "workspace" in meta

def test_semantic_retrieval_subsystem_equalizer():
    hits = search_chunks("subsystem equalizer", top_k=3)
    assert len(hits) > 0
    top_hit = hits[0]
    assert top_hit["chunk_id"] == "ui_map:component.subsystem-equalizer"
    assert top_hit["source_domain"] == "ui_map"

def test_semantic_retrieval_gas_lock_domain_isolation():
    hits = search_chunks("gas lock", top_k=5)
    assert len(hits) > 0
    # Technical fault query must not match ui_map entries in top results
    for h in hits:
        assert h["source_domain"] != "ui_map"
