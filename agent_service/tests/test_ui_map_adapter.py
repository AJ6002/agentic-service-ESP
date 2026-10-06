import pytest
from app.gateway.adapters import ui_map
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall, PlanArtifact
from app.policy.policy_gate import validate_plan, ALLOWED_TOOLS
from app.gateway.capability import check_domain_status

REQUIRED_FIELDS = {
    "id",
    "type",
    "title",
    "path",
    "workspace",
    "summary",
    "description",
    "related",
    "aliases",
}

@pytest.mark.anyio
async def test_lookup_by_id_success():
    entry = await ui_map.lookup_by_id("component.subsystem-equalizer")
    assert entry is not None, "Expected entry for 'component.subsystem-equalizer'"
    assert entry["id"] == "component.subsystem-equalizer"
    assert entry["type"] == "component"
    assert "Subsystem Equalizer" in entry["title"]
    assert entry["workspace"] == "operations"
    assert len(entry["summary"]) > 0
    assert len(entry["description"]) > 0
    assert isinstance(entry["related"], list)
    assert "route.working-status" in entry["related"]
    assert isinstance(entry["aliases"], list)
    assert "equalizer" in entry["aliases"]
    assert REQUIRED_FIELDS.issubset(entry.keys())

@pytest.mark.anyio
async def test_lookup_by_id_route():
    entry = await ui_map.lookup_by_id("route.working-status")
    assert entry is not None
    assert entry["id"] == "route.working-status"
    assert entry["type"] == "route"
    assert entry["path"] == "/working-status"
    assert entry["workspace"] == "operations"
    assert REQUIRED_FIELDS.issubset(entry.keys())

@pytest.mark.anyio
async def test_lookup_by_id_not_found():
    entry = await ui_map.lookup_by_id("nonexistent.fake-id-12345")
    assert entry is None, "Expected None for nonexistent entry ID"

@pytest.mark.anyio
async def test_lookup_by_id_empty_input():
    entry = await ui_map.lookup_by_id("")
    assert entry is None
    entry_none = await ui_map.lookup_by_id(None)
    assert entry_none is None

@pytest.mark.anyio
async def test_search_ui_map_semantic_top_hit():
    hits = await ui_map.search_ui_map("subsystem equalizer", top_k=3)
    assert len(hits) > 0
    top = hits[0]
    assert top["id"] == "component.subsystem-equalizer"
    assert top["type"] == "component"
    assert REQUIRED_FIELDS.issubset(top.keys())
    assert top.get("score", 0.0) > 0.65

@pytest.mark.anyio
async def test_search_ui_map_route_top_hit():
    hits = await ui_map.search_ui_map("working status dashboard", top_k=3)
    assert len(hits) > 0
    top = hits[0]
    assert top["id"] == "route.working-status"
    assert top["type"] == "route"
    assert REQUIRED_FIELDS.issubset(top.keys())

@pytest.mark.anyio
async def test_search_ui_map_domain_isolation():
    hits = await ui_map.search_ui_map("gas lock", top_k=3)
    # Even if cosine search is performed, all results must come only from ui_map domain
    valid_prefixes = ("route.", "component.", "concept.", "fault.", "glossary.", "preset.", "nav.", "channel.")
    for h in hits:
        assert any(h["id"].startswith(p) for p in valid_prefixes)
        assert REQUIRED_FIELDS.issubset(h.keys())

@pytest.mark.anyio
async def test_tool_gateway_dispatch_lookup():
    call = PlanCall(seq=1, kind="READ", tool="lookup_ui_map_entry", args={"entry_id": "component.subsystem-equalizer"})
    res = await execute_tool_call(call)
    assert res.status == "OK"
    assert res.raw_response.get("found") is True
    entry = res.raw_response.get("entry")
    assert entry["id"] == "component.subsystem-equalizer"
    assert REQUIRED_FIELDS.issubset(entry.keys())

@pytest.mark.anyio
async def test_tool_gateway_dispatch_lookup_not_found():
    call = PlanCall(seq=1, kind="READ", tool="lookup_ui_map_entry", args={"entry_id": "unknown.entity"})
    res = await execute_tool_call(call)
    assert res.status == "OK"
    assert res.raw_response.get("found") is False
    assert res.raw_response.get("entry") is None

@pytest.mark.anyio
async def test_tool_gateway_dispatch_search():
    call = PlanCall(seq=1, kind="READ", tool="search_ui_map", args={"query": "equalizer health index", "top_k": 2})
    res = await execute_tool_call(call)
    assert res.status == "OK"
    hits = res.raw_response.get("hits", [])
    assert len(hits) > 0
    assert hits[0]["id"] == "component.subsystem-equalizer"

def test_policy_gate_allowed_tools():
    assert "lookup_ui_map_entry" in ALLOWED_TOOLS
    assert "search_ui_map" in ALLOWED_TOOLS

@pytest.mark.anyio
async def test_capability_probe_ui_map():
    status = await check_domain_status("ui_map")
    assert status == "AVAILABLE"
