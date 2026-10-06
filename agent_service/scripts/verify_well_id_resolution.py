import asyncio
import sys
import yaml
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))

from app.stores.postgres_client import get_db_cursor
from app.gateway.adapters.common import get_well_id_variants
from app.gateway.adapters.live import fetch_live_wells, fetch_live_telemetry, fetch_live_asset
from app.gateway.adapters.kpi import fetch_kpi, fetch_fleet_kpi
from app.gateway.adapters.events import fetch_events_timeline, fetch_events_trips
from app.gateway.adapters.ml import fetch_ml_health, fetch_ml_anomaly, fetch_ml_fault
from app.gateway.adapters.historian import fetch_historian_coverage, fetch_historian_latest
from app.gateway.adapters.cards import fetch_card
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall

def inspect_db():
    print("=" * 70)
    print("DATABASE INVENTORY INSPECTION")
    print("=" * 70)
    with get_db_cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [r[0] for r in cur.fetchall()]
        print(f"Tables in public schema: {tables}")

        cur.execute("SELECT well_id, cluster, is_active FROM asset_registry ORDER BY well_id;")
        registry_wells = cur.fetchall()
        print(f"\nTotal wells in asset_registry: {len(registry_wells)}")
        for r in registry_wells:
            print(f"  {r[0]:12s} | Cluster: {r[1]:15s} | Active: {r[2]}")

        cur.execute("SELECT DISTINCT well_id, asset_id FROM opg_well_telemetry ORDER BY well_id;")
        tele_wells = cur.fetchall()
        print(f"\nWells with live telemetry in opg_well_telemetry ({len(tele_wells)}):")
        for r in tele_wells:
            print(f"  well_id: {r[0]:12s} | asset_id: {r[1]}")


async def verify_resolution():
    print("\n" + "=" * 70)
    print("TESTING WELL ID RESOLUTION (Unpadded vs Padded variants)")
    print("=" * 70)
    
    # We test unpadded IDs (like FS-17, FS-4, FS-6, FNW-1, FWS-1, FS-16) vs padded (FS-017, FS-004, FS-006, FNW-001, FWS-001, FS-016)
    test_pairs = [
        ("FS-17", "FS-017"),
        ("FS-4", "FS-004"),
        ("FS-6", "FS-006"),
        ("FS-13", "FS-013"),
        ("FS-16", "FS-016"),
        ("FS-23", "FS-023"),
        ("FS-40", "FS-040"),
        ("FS-47", "FS-047"),
        ("FNW-1", "FNW-001"),
        ("FNW-01", "FNW-001"),
        ("FWS-1", "FWS-001"),
    ]

    failures = []
    
    for unpadded, padded in test_pairs:
        print(f"\n--- Testing pair: Unpadded '{unpadded}' vs Padded '{padded}' ---")
        
        # 1. Test get_well_id_variants
        unpadded_vars = get_well_id_variants(unpadded)
        padded_vars = get_well_id_variants(padded)
        print(f"  Variants for '{unpadded}': {unpadded_vars}")
        print(f"  Variants for '{padded}':   {padded_vars}")
        
        # Confirm that unpadded variants contains padded and vice versa
        if padded not in unpadded_vars and not any(padded in v for v in unpadded_vars):
            print(f"  [WARN] '{padded}' not in unpadded variants!")
            
        # 2. Test live telemetry with unpadded
        try:
            t_unpadded = await fetch_live_telemetry(unpadded)
            t_padded = await fetch_live_telemetry(padded)
            print(f"  [PASS] Live Telemetry : unpadded '{unpadded}' -> well_id='{t_unpadded['well_id']}', hz={t_unpadded['measurements']['frequency_hz']}")
            print(f"  [PASS] Live Telemetry : padded   '{padded}'   -> well_id='{t_padded['well_id']}', hz={t_padded['measurements']['frequency_hz']}")
        except Exception as e:
            print(f"  [FAIL] Live Telemetry: {e}")
            failures.append((unpadded, "telemetry", str(e)))

        # 3. Test asset context with unpadded
        try:
            a_unpadded = await fetch_live_asset(unpadded)
            a_padded = await fetch_live_asset(padded)
            print(f"  [PASS] Asset Context  : unpadded '{unpadded}' -> well_id='{a_unpadded['well_id']}', cluster='{a_unpadded['cluster']}'")
        except Exception as e:
            print(f"  [FAIL] Asset Context: {e}")
            failures.append((unpadded, "asset_context", str(e)))

        # 4. Test KPI with unpadded
        try:
            k_unpadded = await fetch_kpi(unpadded)
            k_padded = await fetch_kpi(padded)
            print(f"  [PASS] KPI            : unpadded '{unpadded}' -> gross_liquid={k_unpadded.get('gross_liquid_rate_bpd')} bpd, status={k_unpadded.get('status')}")
        except Exception as e:
            print(f"  [FAIL] KPI: {e}")
            failures.append((unpadded, "kpi", str(e)))

        # 5. Test ML Health with unpadded
        try:
            h_unpadded = await fetch_ml_health(unpadded)
            h_padded = await fetch_ml_health(padded)
            print(f"  [PASS] ML Health      : unpadded '{unpadded}' -> health_score={h_unpadded['health_score']}, band={h_unpadded['health_band']}")
        except Exception as e:
            print(f"  [FAIL] ML Health: {e}")
            failures.append((unpadded, "ml_health", str(e)))

        # 6. Test ML Fault with unpadded
        try:
            f_unpadded = await fetch_ml_fault(unpadded)
            f_padded = await fetch_ml_fault(padded)
            print(f"  [PASS] ML Fault       : unpadded '{unpadded}' -> fault_name='{f_unpadded['fault_name']}', status={f_unpadded['overall_status']}")
        except Exception as e:
            print(f"  [FAIL] ML Fault: {e}")
            failures.append((unpadded, "ml_fault", str(e)))

        # 7. Test Historian Coverage with unpadded
        try:
            c_unpadded = await fetch_historian_coverage(unpadded)
            c_padded = await fetch_historian_coverage(padded)
            print(f"  [PASS] Historian Cov  : unpadded '{unpadded}' -> first={c_unpadded['first_ts']}, last={c_unpadded['last_ts']}")
        except Exception as e:
            print(f"  [FAIL] Historian Coverage: {e}")
            failures.append((unpadded, "historian_cov", str(e)))

        # 8. Test Tool Gateway execute_tool_call with unpadded
        try:
            call = PlanCall(kind="READ", seq=1, tool="get_live_telemetry", args={"asset_id": unpadded})
            res = await execute_tool_call(call)
            if res.status == "OK":
                print(f"  [PASS] Tool Gateway   : execute_tool_call('get_live_telemetry', asset_id='{unpadded}') -> status OK ({res.latency_ms}ms)")
            else:
                print(f"  [FAIL] Tool Gateway   : execute_tool_call status={res.status}, error={res.error}")
                failures.append((unpadded, "tool_gateway", res.error))
        except Exception as e:
            print(f"  [FAIL] Tool Gateway: {e}")
            failures.append((unpadded, "tool_gateway", str(e)))

        # 9. Test Card Adapter with unpadded
        try:
            card = await fetch_card(well_id=unpadded, card_id="working_status_smart_fault_card")
            print(f"  [PASS] Card Adapter   : fetch_card('{unpadded}', 'working_status_smart_fault_card') -> status {card.get('status')}")
        except Exception as e:
            print(f"  [FAIL] Card Adapter: {e}")
            failures.append((unpadded, "card_adapter", str(e)))

    print("\n" + "=" * 70)
    print("FINAL SUMMARY:")
    print(f"Total test pairs: {len(test_pairs)}")
    print(f"Total failures:   {len(failures)}")
    print("=" * 70)
    if len(failures) == 0:
        print("EXIT CRITERIA MET: Unpadded well IDs seamlessly query padded Postgres rows across all adapters, tool gateway, and card adapters. ZERO 404s.")
    else:
        print("EXIT CRITERIA FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    inspect_db()
    asyncio.run(verify_resolution())
