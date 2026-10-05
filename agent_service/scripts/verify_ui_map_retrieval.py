"""
Verification script for Sprint 4 UI Map Ingestion.
Validates:
1. Exact row count for source_domain = 'ui_map' in PostgreSQL.
2. Distinct count of non-ui_map ESP chunks.
3. Semantic vector search for UI elements (e.g. 'subsystem equalizer') returns ui_map chunk.
4. Domain isolation: technical ESP queries (e.g. 'gas lock') return ESP knowledge, not UI map.
5. Ingestion idempotency: re-running does not produce duplicate rows.
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath("agent_service"))

from app.stores.postgres_client import get_db_cursor
from app.gateway.adapters.kb import _get_embed_model

def search_chunks(query_text: str, top_k: int = 5, domain_filter: str = None) -> list[dict]:
    embedder = _get_embed_model()
    vec = list(embedder.embed([query_text]))[0].tolist()

    with get_db_cursor() as cur:
        if domain_filter:
            cur.execute("""
                SELECT chunk_id, doc_id, doc_title, section_title, content, source_domain, metadata,
                       (1 - (embedding <=> %s::vector)) AS score
                FROM kb_chunks
                WHERE source_domain = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (vec, domain_filter, vec, top_k))
        else:
            cur.execute("""
                SELECT chunk_id, doc_id, doc_title, section_title, content, source_domain, metadata,
                       (1 - (embedding <=> %s::vector)) AS score
                FROM kb_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (vec, vec, top_k))
        
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "chunk_id": r[0],
                "doc_id": r[1],
                "doc_title": r[2],
                "section_title": r[3],
                "content_snippet": r[4][:120] if r[4] else "",
                "source_domain": r[5],
                "metadata": r[6] if isinstance(r[6], dict) else (json.loads(r[6]) if r[6] else {}),
                "score": float(r[7] if r[7] is not None else 0.0),
            })
        return results

def main():
    lines = []
    def log(s=""):
        print(s)
        lines.append(s)

    log("=" * 80)
    log("SPRINT 4 — UI MAP INGESTION & RETRIEVAL VERIFICATION REPORT")
    log("=" * 80)
    log(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log()

    # 1. Row verification
    log("TASK 4.3 — VERIFY POSTGRESQL kb_chunks ROWS")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT chunk_id, source_domain, doc_title, section_title, LEFT(content, 60), metadata
            FROM kb_chunks
            WHERE source_domain = 'ui_map'
            ORDER BY chunk_id;
        """)
        ui_rows = cur.fetchall()

    log(f"Found {len(ui_rows)} rows with source_domain = 'ui_map':")
    for r in ui_rows:
        cid, sdom, dtitle, stitle, snippet, meta = r
        log(f"  - Chunk: {cid}")
        log(f"    Title: {dtitle} | Section: {stitle}")
        log(f"    Domain: {sdom} | Metadata Type: {meta.get('type') if isinstance(meta, dict) else meta}")
        log(f"    Snippet: {snippet}...")
    
    t4_3_pass = (len(ui_rows) == 3)
    log(f"Task 4.3 Result: {'PASS (3 rows found)' if t4_3_pass else 'FAIL'}")
    log("-" * 80)

    # 2. Semantic Retrievability & Domain Isolation
    log("\nTASK 4.4 — VERIFY RETRIEVABILITY & DOMAIN ISOLATION")
    
    log("\n[Test 1] Searching for: 'subsystem equalizer' across all kb_chunks (no domain filter)")
    hits_eq = search_chunks("subsystem equalizer", top_k=3)
    for i, h in enumerate(hits_eq, 1):
        log(f"  Hit {i}: [{h['source_domain']}] {h['chunk_id']} (score: {h['score']:.4f}) — {h['section_title']}")
    
    top_is_eq = (len(hits_eq) > 0 and hits_eq[0]["chunk_id"] == "ui_map:component.subsystem-equalizer")
    log(f"Result: Top hit is component.subsystem-equalizer -> {'PASS' if top_is_eq else 'FAIL'}")

    log("\n[Test 2] Searching for: 'working status dashboard' across all kb_chunks (no domain filter)")
    hits_ws = search_chunks("working status dashboard", top_k=3)
    for i, h in enumerate(hits_ws, 1):
        log(f"  Hit {i}: [{h['source_domain']}] {h['chunk_id']} (score: {h['score']:.4f}) — {h['section_title']}")
    
    top_is_ws = (len(hits_ws) > 0 and hits_ws[0]["chunk_id"] == "ui_map:route.working-status")
    log(f"Result: Top hit is route.working-status -> {'PASS' if top_is_ws else 'FAIL'}")

    log("\n[Test 3] Searching for: 'where can I find the equalizer?' across all kb_chunks")
    hits_find_eq = search_chunks("where can I find the equalizer?", top_k=3)
    for i, h in enumerate(hits_find_eq, 1):
        log(f"  Hit {i}: [{h['source_domain']}] {h['chunk_id']} (score: {h['score']:.4f}) — {h['section_title']}")
    
    find_eq_found = any(h["chunk_id"] == "ui_map:component.subsystem-equalizer" for h in hits_find_eq)
    log(f"Result: ui_map:component.subsystem-equalizer in top 3 -> {'PASS' if find_eq_found else 'FAIL'}")

    log("\n[Test 4] Searching for: 'gas lock' across all kb_chunks (no domain filter — domain isolation check)")
    hits_gl = search_chunks("gas lock", top_k=5)
    for i, h in enumerate(hits_gl, 1):
        log(f"  Hit {i}: [{h['source_domain']}] {h['chunk_id']} (score: {h['score']:.4f}) — {h['doc_title']}")
    
    gl_no_ui_hits = all(h["source_domain"] != "ui_map" for h in hits_gl)
    log(f"Result: Zero UI map chunks in top 5 gas lock hits -> {'PASS' if gl_no_ui_hits else 'FAIL'}")

    log("\n[Test 5] Searching for UI concept 'total dynamic head' with domain_filter='ui_map'")
    hits_tdh = search_chunks("total dynamic head", domain_filter="ui_map", top_k=3)
    for i, h in enumerate(hits_tdh, 1):
        log(f"  Hit {i}: [{h['source_domain']}] {h['chunk_id']} (score: {h['score']:.4f}) — {h['section_title']}")
    
    tdh_found = (len(hits_tdh) > 0 and hits_tdh[0]["chunk_id"] == "ui_map:concept.tdh")
    log(f"Result: Top hit in ui_map domain is concept.tdh -> {'PASS' if tdh_found else 'FAIL'}")

    t4_4_pass = (top_is_eq and top_is_ws and find_eq_found and gl_no_ui_hits and tdh_found)
    log(f"\nTask 4.4 Overall Result: {'PASS' if t4_4_pass else 'FAIL'}")
    log("-" * 80)

    # 3. Distinct Tag & Idempotency
    log("\nTASK 4.5 — VERIFY DISTINCT TAG COUNTS & IDEMPOTENCY")
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM kb_chunks WHERE source_domain = 'ui_map';")
        ui_count_1 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kb_chunks WHERE source_domain != 'ui_map' OR source_domain IS NULL;")
        esp_count_1 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kb_chunks;")
        total_count_1 = cur.fetchone()[0]

    log(f"Initial Counts:")
    log(f"  - kb_chunks with source_domain = 'ui_map': {ui_count_1}")
    log(f"  - kb_chunks with source_domain != 'ui_map': {esp_count_1}")
    log(f"  - Total kb_chunks: {total_count_1}")

    log("\nRe-running ingestion script to test idempotency...")
    from scripts.ingest_ui_map_to_postgres import ingest_ui_map
    reingest_res = ingest_ui_map()

    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM kb_chunks WHERE source_domain = 'ui_map';")
        ui_count_2 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kb_chunks;")
        total_count_2 = cur.fetchone()[0]

    log(f"Post-reingestion Counts:")
    log(f"  - kb_chunks with source_domain = 'ui_map': {ui_count_2} (Expected: {ui_count_1})")
    log(f"  - Total kb_chunks: {total_count_2} (Expected: {total_count_1})")

    idempotent_pass = (ui_count_2 == ui_count_1 == 3 and total_count_2 == total_count_1)
    log(f"Idempotency Check: {'PASS (0 duplicate rows)' if idempotent_pass else 'FAIL'}")
    log("-" * 80)

    # 4. Exit Criteria Table
    log("\n" + "=" * 80)
    log("SPRINT 4 EXIT CRITERIA EVALUATION")
    log("=" * 80)
    crit = [
        (1, "Working-copy folder & YAML exists", "File present in agent repo", os.path.exists("agent_service/config/ui_map/ui_map.yaml")),
        (2, "Ingestion script runs without error", "Exit code 0, 3 entries", reingest_res == 3),
        (3, "3 entries in kb_chunks tagged ui_map", "SQL count returns 3", ui_count_2 == 3),
        (4, "UI entries retrievable via semantic search", "subsystem equalizer top hit", top_is_eq and top_is_ws and find_eq_found and tdh_found),
        (5, "ESP KB and ui_map don't contaminate each other", "Separate counts, zero false cross-hits", gl_no_ui_hits and esp_count_1 >= 7000),
        (6, "Re-running ingestion is idempotent", "Count stays 3, no duplicates", idempotent_pass),
    ]

    all_pass = True
    log(f"{'#':<3} | {'Check':<48} | {'Pass condition':<32} | {'Status'}")
    log("-" * 97)
    for c_id, name, cond, p in crit:
        if not p:
            all_pass = False
        log(f"{c_id:<3} | {name:<48} | {cond:<32} | {'PASSED [OK]' if p else 'FAILED [X]'}")
    log("-" * 97)
    log(f"\nOVERALL RESULT: {'SPRINT 4 SEALED & VERIFIED — READY FOR SPRINT 5' if all_pass else 'FAILURES DETECTED'}")

    os.makedirs("reports", exist_ok=True)
    report_file = "reports/SPRINT_4_UI_MAP_INGESTION_VERIFICATION_REPORT.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote full verification output to {report_file}")

if __name__ == "__main__":
    main()
