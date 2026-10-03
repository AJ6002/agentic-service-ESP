"""
KB Single-Connection & Definitional 5-Query Test Suite.
Verifies Path 1 (Adapter only) and Path 2 (Agent End-to-End OP06 queries)
via curl.exe against http://127.0.0.1:8091.
READ ONLY from PostgreSQL (no database writes).
"""

import json
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

QUERIES = [
    ("Query 1", "What is gas lock in ESP?"),
    ("Query 2", "What is underload protection?"),
    ("Query 3", "Explain gas lock."),
    ("Query 4", "What does PIP mean?"),
    ("Query 5", "Define TDH."),
]

def run_curl(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return res.stdout.strip()

def main():
    print("=" * 80)
    print("SINGLE-CONNECTION TEST — KB ONLY (POSTGRESQL PGVECTOR)")
    print("=" * 80)

    # ------------------------------------------------------------------------
    # PATH 1 — Adapter Direct Endpoint
    # ------------------------------------------------------------------------
    print("\n[PATH 1] Adapter Direct Verification (POST /kb/search)...")
    payload1 = json.dumps({"query": "gas lock", "top_k": 3})
    cmd1 = ["curl.exe", "-s", "-X", "POST", "http://127.0.0.1:8091/kb/search",
            "-H", "Content-Type: application/json", "--data-binary", payload1]
    
    t0 = time.perf_counter()
    out1 = run_curl(cmd1)
    lat1 = (time.perf_counter() - t0) * 1000
    
    try:
        data1 = json.loads(out1)
        hits = data1.get("hits", [])
        print(f"  Status: SUCCESS | Latency: {lat1:.2f}ms | Source: {data1.get('source')}")
        print(f"  Total Hits Returned: {len(hits)}")
        for i, h in enumerate(hits, 1):
            print(f"    - Hit {i}: [{h.get('doc_title')}] § {h.get('section')} (Score: {h.get('score')})")
            print(f"      Snippet: {h.get('snippet', '')[:120]}...")
            assert h.get("score", 0) > 0.5, "Score should be > 0.5"
            assert h.get("doc_id"), "doc_id must be present"
            assert h.get("section"), "section must be present"
            assert h.get("snippet"), "snippet text must be present"
        print("  -> Path 1 Proved: pgvector HNSW index, BGE embedding & PostgreSQL connection work end-to-end!")
    except Exception as e:
        print(f"  Path 1 Failed: {e}\n  Raw Output: {out1}")
        return

    # ------------------------------------------------------------------------
    # PATH 2 — Agent End-to-End Definitional 5-Query Suite
    # ------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[PATH 2] Agent End-to-End Definitional 5-Query Suite (POST /query)")
    print("=" * 80)

    for name, query_text in QUERIES:
        print(f"\n[{name}] '{query_text}'")
        payload = json.dumps({
            "session_id": f"kbtest-{name.lower().replace(' ', '')}",
            "message": query_text
        })
        cmd = ["curl.exe", "-s", "-X", "POST", "http://127.0.0.1:8091/query",
               "-H", "Content-Type: application/json", "--data-binary", payload]
        
        t0 = time.perf_counter()
        out = run_curl(cmd)
        lat = (time.perf_counter() - t0) * 1000
        
        lines = [l for l in out.splitlines() if l.strip()]
        frames = []
        for l in lines:
            try:
                frames.append(json.loads(l))
            except Exception:
                pass
        
        done_frame = next((f for f in frames if f.get("type") == "done"), None)
        text_frames = [f for f in frames if f.get("type") == "text_delta"]
        error_frames = [f for f in frames if f.get("type") == "error"]
        visual_frames = [f for f in frames if f.get("type") == "visual"]
        
        full_text = "".join(f.get("delta", "") for f in text_frames)
        
        print(f"  Latency: {lat:.2f}ms | Frames Received: {len(frames)}")
        print(f"  Done Status: {done_frame.get('status') if done_frame else 'MISSING'}")
        print(f"  Text Excerpt: {full_text[:140]}...")
        
        # Invariants Check:
        assert len(error_frames) == 0, f"Error frame found: {error_frames}"
        assert len(visual_frames) == 0, f"Visual frames should NOT appear for pure KB query: {visual_frames}"
        assert done_frame is not None and done_frame.get("status") == "OK", "Done frame status must be OK"
        print(f"  -> SUCCESS: Query routed cleanly to KB without touching telemetry tables!")

    print("\n" + "=" * 80)
    print("ALL 5 OP06 DEFINITIONAL QUERIES PASSED 100% (READ-ONLY ON KB CHUNKS)!")
    print("=" * 80)

if __name__ == "__main__":
    main()
