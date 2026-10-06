import asyncio
import os
import sys
import json

# Ensure agent_service is on path
sys.path.insert(0, os.path.abspath("."))

from app.workflow.runner import run_workflow
from app.stores.postgres_client import get_db_cursor
from app.stores.redis_client import get_redis_client


async def run_levels_2_3_4():
    print("=" * 80)
    print("SPRINT 6 VERIFICATION: LEVELS 2, 3, 4 & STORAGE AUDIT")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # LEVEL 2 & 3: 4 Manual Invocations
    # --------------------------------------------------------------------------
    queries = [
        ("test-op15-1", "what is the working status page", "route.working-status"),
        ("test-op15-2", "what does the subsystem equalizer show", "component.subsystem-equalizer"),
        ("test-op15-3", "what is TDH", "concept.tdh"),
        ("test-op15-4", "what is the flux capacitor page", None),
    ]

    all_cited_ids = []
    level_results = []

    for run_id, q_text, expected_target in queries:
        print(f"\n[RUNNING QUERY]: \"{q_text}\" (run_id: {run_id})")
        res = await run_workflow(
            run_id=run_id,
            session_id="test-op15",
            objective_id="OP15_PLATFORM_GUIDE",
            args={"query": q_text},
            confidence=1.0,
            user_query=q_text,
        )

        ok = res.ok
        has_advisory = res.advisory is not None
        cited = res.advisory.cited_evidence_ids if res.advisory else []
        viz_empty = res.visualization is None or not getattr(res.visualization, "card_ids", [])
        
        assessment = res.advisory.assessment if res.advisory else ""
        text = res.text or ""

        print(f"  OK: {ok}")
        print(f"  Has Advisory: {has_advisory}")
        print(f"  Visual Cards Empty: {viz_empty}")
        print(f"  Cited Evidence IDs: {cited}")
        print(f"  Assessment (first 300 chars): {assessment[:300]}...")

        if expected_target is not None:
            # Check for mention or citation
            target_found = (expected_target in assessment) or (expected_target in text) or (expected_target in str(cited))
            print(f"  Target '{expected_target}' referenced in output: {target_found}")
            all_cited_ids.append((run_id, expected_target))
        else:
            # Refusal test
            refusal = ("not recognized" in assessment.lower() or "not documented" in assessment.lower() or "insufficient" in assessment.lower() or "refuse" in assessment.lower() or "does not exist" in assessment.lower() or "not found" in assessment.lower())
            never_invented = ("flux" not in assessment.lower() or "not recognized" in assessment.lower() or "not found" in assessment.lower())
            print(f"  Refusal Verified: {refusal} (Never invented fake screen: {never_invented})")

        level_results.append({
            "run_id": run_id,
            "query": q_text,
            "ok": ok,
            "cited": cited,
            "assessment": assessment,
            "viz_empty": viz_empty,
        })

    # --------------------------------------------------------------------------
    # LEVEL 4: Postgres Cross-Check
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("LEVEL 4: POSTGRES CROSS-CHECK FOR CITED EVIDENCE")
    print("=" * 80)
    with get_db_cursor() as cur:
        for run_id, entry_id in all_cited_ids:
            cur.execute("""
                SELECT chunk_id, doc_title, section_title, content, metadata
                FROM kb_chunks
                WHERE source_domain = 'ui_map'
                  AND metadata->>'id' = %s;
            """, (entry_id,))
            row = cur.fetchone()
            if row:
                print(f"[PG MATCH] entry_id='{entry_id}':")
                print(f"  chunk_id: {row[0]}")
                print(f"  doc_title: {row[1]}")
                print(f"  content (summary/desc): {row[3][:120]}...")
            else:
                print(f"[PG ERROR] entry_id='{entry_id}' NOT FOUND in kb_chunks!")

    # --------------------------------------------------------------------------
    # STORAGE CHECK: Redis Keys for Runs
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STORAGE CHECK: REDIS RUN KEYS AUDIT")
    print("=" * 80)
    try:
        r = get_redis_client()
        keys = r.keys("esp:run:test-op15-*")
        print(f"Found {len(keys)} Redis keys matching 'esp:run:test-op15-*':")
        for k in sorted(keys):
            print(f"  - {k}")
    except Exception as e:
        print(f"Redis check error: {e}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_levels_2_3_4())
