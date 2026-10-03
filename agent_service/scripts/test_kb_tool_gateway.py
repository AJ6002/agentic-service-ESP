"""
Standalone Tool Gateway & Direct KB API Verification Script.
Validates all KB tools (search_knowledge, get_fault_taxonomy, trace_causal_graph, check_domain_status)
running on PostgreSQL + pgvector without HTTP port 8085.
"""

import asyncio
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.contracts.plan import PlanCall
from app.gateway.tool_gateway import execute_tool_call
from app.gateway.capability import check_domain_status
from app.gateway.adapters import kb

async def main():
    print("=" * 80)
    print("STANDALONE KB TOOL GATEWAY & PGVECTOR VERIFICATION")
    print("=" * 80)

    # 1. Probe Capability Status
    status = await check_domain_status("kb")
    print(f"\n[1] KB Domain Capability Status: {status}")
    assert status == "AVAILABLE", f"Expected AVAILABLE, got {status}"

    # 2. Tool Gateway: search_knowledge
    print("\n[2] Tool Gateway: execute_tool_call -> 'search_knowledge'")
    call1 = PlanCall(
        seq=1,
        kind="READ",
        tool="search_knowledge",
        args={"query": "API RP 11S pump sizing and total dynamic head", "asset_id": "FS-17"}
    )
    t0 = time.perf_counter()
    res1 = await execute_tool_call(call1)
    dur1 = (time.perf_counter() - t0) * 1000
    print(f"  Status: {res1.status} | Latency: {dur1:.2f}ms (Gateway reported: {res1.latency_ms}ms)")
    print(f"  Hits Found: {len(res1.raw_response.get('hits', []))}")
    for i, h in enumerate(res1.raw_response.get("hits", [])[:3], 1):
        print(f"    - Hit {i}: [{h['doc_title']}] § {h['section']} (Score: {h['score']})")
    assert res1.status == "OK"
    assert len(res1.raw_response.get("hits", [])) > 0

    # 3. Tool Gateway: get_fault_taxonomy
    print("\n[3] Tool Gateway: execute_tool_call -> 'get_fault_taxonomy'")
    call2 = PlanCall(
        seq=2,
        kind="READ",
        tool="get_fault_taxonomy",
        args={"fault_class": "GAS_LOCK", "asset_id": "FS-17"}
    )
    t0 = time.perf_counter()
    res2 = await execute_tool_call(call2)
    dur2 = (time.perf_counter() - t0) * 1000
    print(f"  Status: {res2.status} | Latency: {dur2:.2f}ms")
    print(f"  Fault: {res2.raw_response.get('preferred_name')} | Category: {res2.raw_response.get('category')}")
    print(f"  Contributing Factors: {res2.raw_response.get('contributing_factors')}")
    assert res2.status == "OK"
    assert res2.raw_response.get("fault_class") == "GAS_LOCK"

    # 4. Tool Gateway: trace_causal_graph
    print("\n[4] Tool Gateway: execute_tool_call -> 'trace_causal_graph'")
    call3 = PlanCall(
        seq=3,
        kind="READ",
        tool="trace_causal_graph",
        args={"symptom_ids": ["Low Intake Pressure (<150 psi)", "High Motor Temperature (>130°C)"], "asset_id": "FS-17"}
    )
    t0 = time.perf_counter()
    res3 = await execute_tool_call(call3)
    dur3 = (time.perf_counter() - t0) * 1000
    print(f"  Status: {res3.status} | Latency: {dur3:.2f}ms")
    print(f"  Paths Traced: {len(res3.raw_response.get('paths', []))}")
    print(f"  Root Causes: {res3.raw_response.get('root_causes', [])}")
    assert res3.status == "OK"
    assert len(res3.raw_response.get("paths", [])) > 0

    # 5. Direct Adapter Clauses Lookup (Standards)
    print("\n[5] Direct Adapter: kb.get_kb_standard -> '11S'")
    res4 = await kb.get_kb_standard("API_RP_11S")
    print(f"  Clauses Returned: {len(res4.get('clauses', []))}")
    for c in res4.get("clauses", [])[:2]:
        print(f"    - [{c['doc_title']}] § {c['section']}")

    print("\n" + "=" * 80)
    print("ALL STANDALONE KB TOOL GATEWAYS & PGVECTOR APIS PASSED 100%!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
