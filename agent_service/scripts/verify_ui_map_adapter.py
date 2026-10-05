"""
Verification script for Sprint 5 UI Map Adapter & Tool Registration.
Executes live queries against PostgreSQL Server 184 and verifies:
1. Adapter operations (lookup_by_id, search_ui_map).
2. Tool Gateway dispatching (lookup_ui_map_entry, search_ui_map).
3. 9-field schema completeness.
4. Non-fabrication on nonexistent IDs.
5. Semantic ranking and domain isolation.
6. Evaluates all 7 Sprint 5 exit criteria and outputs SPRINT_5_UI_MAP_ADAPTER_VERIFICATION_REPORT.txt.
"""

import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath("agent_service"))

from app.gateway.adapters import ui_map
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall
from app.policy.policy_gate import ALLOWED_TOOLS
from app.gateway.capability import check_domain_status

REQUIRED_FIELDS = [
    "id",
    "type",
    "title",
    "path",
    "workspace",
    "summary",
    "description",
    "related",
    "aliases",
]

async def run_verification():
    lines = []
    def log(s=""):
        print(s)
        lines.append(s)

    log("=" * 80)
    log("SPRINT 5 — UI MAP ADAPTER & TOOL REGISTRATION VERIFICATION REPORT")
    log("=" * 80)
    log(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log()

    # TASK 5.1 — ADAPTER DIRECT OPERATIONS
    log("TASK 5.1 — ADAPTER DIRECT OPERATIONS (lookup_by_id & search_ui_map)")
    
    # 1. Lookup by valid ID
    log("\n[1] Testing lookup_by_id('component.subsystem-equalizer'):")
    entry_eq = await ui_map.lookup_by_id("component.subsystem-equalizer")
    if entry_eq:
        log(f"  ID: {entry_eq.get('id')}")
        log(f"  Type: {entry_eq.get('type')}")
        log(f"  Title: {entry_eq.get('title')}")
        log(f"  Workspace: {entry_eq.get('workspace')}")
        log(f"  Summary: {entry_eq.get('summary')[:80]}...")
        log(f"  Description: {entry_eq.get('description')[:80]}...")
        log(f"  Related: {entry_eq.get('related')}")
        log(f"  Aliases: {entry_eq.get('aliases')}")
        eq_fields_present = all(k in entry_eq for k in REQUIRED_FIELDS)
        log(f"  All 9 required fields present: {eq_fields_present}")
    else:
        eq_fields_present = False
        log("  Lookup returned None! (FAIL)")

    # 2. Lookup by missing ID
    log("\n[2] Testing lookup_by_id('nonexistent.fake-entity-99'):")
    entry_none = await ui_map.lookup_by_id("nonexistent.fake-entity-99")
    log(f"  Lookup returned: {entry_none} (Expected: None)")
    lookup_refuses_fake = (entry_none is None)

    # 3. Semantic search for UI element
    log("\n[3] Testing search_ui_map('subsystem equalizer', top_k=3):")
    hits_eq = await ui_map.search_ui_map("subsystem equalizer", top_k=3)
    for i, h in enumerate(hits_eq, 1):
        log(f"  Hit {i}: [{h.get('type')}] {h.get('id')} (score: {h.get('score')}) — {h.get('title')}")
    
    search_eq_top = (len(hits_eq) > 0 and hits_eq[0].get("id") == "component.subsystem-equalizer")
    log(f"  Top hit is component.subsystem-equalizer: {search_eq_top}")

    # 4. Search domain filtering (gas lock)
    log("\n[4] Testing search_ui_map('gas lock', top_k=3) for domain isolation:")
    hits_gl = await ui_map.search_ui_map("gas lock", top_k=3)
    log(f"  Returned {len(hits_gl)} hits from ui_map domain.")
    for i, h in enumerate(hits_gl, 1):
        log(f"  Hit {i}: [{h.get('type')}] {h.get('id')} (score: {h.get('score')}) — {h.get('title')}")
    # Must only contain ui_map items, never raw ESP documents
    domain_isolated = all(not str(h.get("id", "")).startswith("DOC-") for h in hits_gl)
    log(f"  Domain isolation verified (zero ESP doc chunks returned): {domain_isolated}")

    # TASK 5.2 — TOOL GATEWAY REGISTRATION & DISPATCH
    log("\n" + "-" * 80)
    log("TASK 5.2 — TOOL GATEWAY REGISTRATION & DISPATCH")
    
    # 5. Tool gateway lookup dispatch
    log("\n[5] Dispatching PlanCall tool='lookup_ui_map_entry' via execute_tool_call:")
    call_lookup = PlanCall(seq=1, kind="READ", tool="lookup_ui_map_entry", args={"entry_id": "route.working-status"})
    res_lookup = await execute_tool_call(call_lookup)
    log(f"  Status: {res_lookup.status} | Latency: {res_lookup.latency_ms}ms")
    log(f"  Raw response found: {res_lookup.raw_response.get('found')}")
    entry_ws = res_lookup.raw_response.get("entry")
    if entry_ws:
        log(f"  Entry: {entry_ws.get('id')} | Path: {entry_ws.get('path')} | Title: {entry_ws.get('title')}")
        lookup_gw_ok = (res_lookup.status == "OK" and entry_ws.get("id") == "route.working-status")
    else:
        lookup_gw_ok = False

    # 6. Tool gateway search dispatch
    log("\n[6] Dispatching PlanCall tool='search_ui_map' via execute_tool_call:")
    call_search = PlanCall(seq=2, kind="READ", tool="search_ui_map", args={"query": "total dynamic head concept", "top_k": 2})
    res_search = await execute_tool_call(call_search)
    log(f"  Status: {res_search.status} | Latency: {res_search.latency_ms}ms")
    gw_hits = res_search.raw_response.get("hits", [])
    log(f"  Returned {len(gw_hits)} hits:")
    for i, h in enumerate(gw_hits, 1):
        log(f"    Hit {i}: {h.get('id')} (score: {h.get('score')}) — {h.get('title')}")
    search_gw_ok = (res_search.status == "OK" and len(gw_hits) > 0 and gw_hits[0].get("id") == "concept.tdh")

    # 7. Policy Gate & Domain Probe
    log("\n[7] Policy Gate and Domain Capability Probing:")
    tools_registered = ("lookup_ui_map_entry" in ALLOWED_TOOLS and "search_ui_map" in ALLOWED_TOOLS)
    log(f"  Policy Gate ALLOWED_TOOLS registered: {tools_registered}")
    cap_status = await check_domain_status("ui_map")
    log(f"  Capability probe 'ui_map' status: {cap_status}")

    # Schema consistency across all results
    all_entries = [entry_eq, entry_ws] + hits_eq + hits_gl + gw_hits
    schema_all_ok = True
    for e in all_entries:
        if not e:
            continue
        for rf in REQUIRED_FIELDS:
            if rf not in e:
                schema_all_ok = False
                log(f"Schema violation: missing field '{rf}' in {e.get('id')}")

    log(f"  Schema consistency (9 fields across all responses): {schema_all_ok}")

    # SPRINT 5 EXIT CRITERIA EVALUATION
    log("\n" + "=" * 80)
    log("SPRINT 5 EXIT CRITERIA EVALUATION")
    log("=" * 80)
    
    crit = [
        (1, "Adapter has two operations", "lookup_by_id and search both present", hasattr(ui_map, "lookup_by_id") and hasattr(ui_map, "search_ui_map")),
        (2, "Both tools registered", "Tool gateway and policy gate list both", tools_registered and lookup_gw_ok and search_gw_ok),
        (3, "Lookup by ID works", "Returns full entry with all 9 fields", entry_eq is not None and eq_fields_present),
        (4, "Lookup by missing ID refuses", "Returns None, never fabricates", lookup_refuses_fake),
        (5, "Semantic search works", "'subsystem equalizer' returns equalizer as top hit", search_eq_top),
        (6, "Domain filter works", "Queries strictly search ui_map without cross-contamination", domain_isolated),
        (7, "Schema consistency", "Every response has all 9 fields", schema_all_ok),
    ]

    all_pass = True
    log(f"{'#':<3} | {'Check':<36} | {'Pass condition':<50} | {'Status'}")
    log("-" * 105)
    for c_id, name, cond, p in crit:
        if not p:
            all_pass = False
        log(f"{c_id:<3} | {name:<36} | {cond:<50} | {'PASSED [OK]' if p else 'FAILED [X]'}")
    log("-" * 105)
    
    log(f"\nOVERALL RESULT: {'SPRINT 5 SEALED & VERIFIED — READY FOR SPRINT 6' if all_pass else 'FAILURES DETECTED'}")

    os.makedirs("reports", exist_ok=True)
    report_file = "reports/SPRINT_5_UI_MAP_ADAPTER_VERIFICATION_REPORT.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote verification report to {report_file}")

if __name__ == "__main__":
    asyncio.run(run_verification())
