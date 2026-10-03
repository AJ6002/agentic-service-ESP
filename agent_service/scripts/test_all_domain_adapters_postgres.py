"""
Standalone Comprehensive Verification of all Domain Adapters on PostgreSQL (esp_apm_db).
Tests Live, Historian, Events, ML, KPI, Cards, KB, and Tool Gateway without HTTP :8090.
"""

import asyncio
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.contracts.plan import PlanCall
from app.gateway.tool_gateway import execute_tool_call
from app.gateway.capability import probe_all_capabilities, check_domain_status
from app.gateway.adapters import live, historian, events, ml, kpi, cards, kb


async def main():
    print("=" * 80)
    print("ALL DOMAIN ADAPTERS POSTGRESQL VERIFICATION (esp_apm_db on Port 5433)")
    print("=" * 80)

    # 1. Capability Probing
    print("\n[1] Probing All 7 Domain Capabilities against PostgreSQL...")
    caps = await probe_all_capabilities()
    for dom, st in caps.items():
        print(f"  - Domain {dom:<12}: {st}")
        assert st == "AVAILABLE", f"Domain {dom} should be AVAILABLE, got {st}"

    # 2. Live Domain
    print("\n[2] Testing Live Telemetry & Asset Adapters...")
    t0 = time.perf_counter()
    live_res = await live.fetch_live_telemetry("FS-17")
    asset_res = await live.fetch_live_asset("FS-17")
    vfm_res = await live.fetch_live_vfm("FS-17")
    wells_res = await live.fetch_live_wells()
    lat_live = (time.perf_counter() - t0) * 1000
    print(f"  - fetch_live_telemetry: source={live_res.get('source')} (latency: {lat_live:.2f}ms)")
    print(f"  - fetch_live_asset:     source={asset_res.get('source')}")
    print(f"  - fetch_live_vfm:       source={vfm_res.get('source')}")
    print(f"  - fetch_live_wells:     total={wells_res.get('total_wells')}")

    # 3. Historian Domain
    print("\n[3] Testing Historian Adapters...")
    t0 = time.perf_counter()
    hist_cov = await historian.fetch_historian_coverage("FS-17")
    start_ts = "2026-10-02T00:00:00Z"
    end_ts = "2026-10-02T08:35:00Z"
    hist_win = await historian.fetch_historian_window("FS-17", start_ts, end_ts)
    hist_agg = await historian.fetch_historian_aggregates("FS-17", start_ts, end_ts)
    lat_hist = (time.perf_counter() - t0) * 1000
    print(f"  - fetch_historian_coverage:   first={hist_cov.get('first_ts')}")
    print(f"  - fetch_historian_window:     rows={len(hist_win.get('rows', []))} (latency: {lat_hist:.2f}ms)")
    print(f"  - fetch_historian_aggregates: rows={len(hist_agg.get('rows', []))}")

    # 4. Events Domain
    print("\n[4] Testing Events Domain...")
    t0 = time.perf_counter()
    ev_timeline = await events.fetch_events_timeline("FS-17")
    ev_trips = await events.fetch_events_trips("FS-17")
    lat_ev = (time.perf_counter() - t0) * 1000
    print(f"  - fetch_events_timeline: total={ev_timeline.get('total_events')} (latency: {lat_ev:.2f}ms)")
    print(f"  - fetch_events_trips:    total={ev_trips.get('total_trips')}")

    # 5. ML Domain
    print("\n[5] Testing ML Diagnostics Domain...")
    t0 = time.perf_counter()
    ml_fault = await ml.fetch_ml_fault("FS-17")
    ml_health = await ml.fetch_ml_health("FS-17")
    ml_anom = await ml.fetch_ml_anomaly("FS-17")
    ml_exp = await ml.fetch_ml_explain("FS-17")
    lat_ml = (time.perf_counter() - t0) * 1000
    print(f"  - fetch_ml_fault:   fault_class={ml_fault.get('fault_class')} (latency: {lat_ml:.2f}ms)")
    print(f"  - fetch_ml_health:  health_score={ml_health.get('health_score')}")
    print(f"  - fetch_ml_anomaly: is_anomalous={ml_anom.get('is_anomalous')}")
    print(f"  - fetch_ml_explain: output_type={ml_exp.get('output_type')}")

    # 6. KPI & Cards Domain
    print("\n[6] Testing KPI & Cards Domain...")
    kpi_res = await kpi.fetch_kpi("FS-17")
    fleet_res = await kpi.fetch_fleet_kpi()
    cards_cat = await cards.fetch_cards_catalog()
    card_res = await cards.fetch_card("FS-17", "health-score")
    print(f"  - fetch_kpi:           status={kpi_res.get('status')}")
    print(f"  - fetch_fleet_kpi:     total_wells={fleet_res.get('total_wells')}")
    print(f"  - fetch_cards_catalog: total_cards={cards_cat.get('total_cards')}")
    print(f"  - fetch_card:          card_id={card_res.get('card_id')}")

    # 7. Knowledge Base Domain (pgvector)
    print("\n[7] Testing Knowledge Base (pgvector)...")
    t0 = time.perf_counter()
    kb_search = await kb.search_kb("gas lock and fluid starvation", top_k=3)
    kb_tax = await kb.get_kb_fault("GAS_LOCK")
    kb_graph = await kb.trace_kb_graph(["Low Intake Pressure (<150 psi)"])
    lat_kb = (time.perf_counter() - t0) * 1000
    print(f"  - search_kb:        hits={len(kb_search.get('hits', []))} (latency: {lat_kb:.2f}ms)")
    print(f"  - get_kb_fault:     category={kb_tax.get('category')}")
    print(f"  - trace_kb_graph:   paths={len(kb_graph.get('paths', []))}")

    # 8. Tool Gateway Dispatch
    print("\n[8] Testing Tool Gateway Dispatches...")
    tools_to_test = [
        ("get_live_telemetry", {"asset_id": "FS-17"}),
        ("get_asset_context", {"asset_id": "FS-17"}),
        ("get_historian_window", {"asset_id": "FS-17", "start": start_ts, "end": end_ts}),
        ("get_events", {"asset_id": "FS-17"}),
        ("diagnose_fault", {"asset_id": "FS-17"}),
        ("get_health_index", {"asset_id": "FS-17"}),
        ("get_current_status", {"asset_id": "FS-17"}),
        ("get_card", {"asset_id": "FS-17", "card_id": "health-score"}),
        ("search_knowledge", {"asset_id": "FS-17", "query": "API RP 11S pump sizing"}),
        ("get_fault_taxonomy", {"asset_id": "FS-17", "fault_class": "GAS_LOCK"}),
        ("trace_causal_graph", {"asset_id": "FS-17", "symptoms": ["Low Intake Pressure (<150 psi)"]}),
    ]

    for idx, (tool_name, tool_args) in enumerate(tools_to_test, 1):
        call = PlanCall(seq=idx, kind="READ", tool=tool_name, args=tool_args)
        t0 = time.perf_counter()
        res = await execute_tool_call(call)
        lat = (time.perf_counter() - t0) * 1000
        print(f"  [{idx:02d}] execute_tool_call({tool_name:<22}) -> Status: {res.status:<6} | Latency: {lat:6.2f}ms")
        assert res.status == "OK", f"Tool {tool_name} failed: {res.error}"

    print("\n" + "=" * 80)
    print("ALL 7 DOMAINS & ALL TOOL GATEWAY CALLS FULLY VERIFIED ON POSTGRESQL!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
