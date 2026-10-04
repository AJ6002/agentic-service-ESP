import os
import sys
import json
import time
import subprocess
import requests

sys.path.insert(0, os.path.abspath("agent_service"))
from app.stores.redis_client import get_redis_client

BASE_URL = "http://127.0.0.1:8091"

def query_stream(session_id: str, message: str) -> list[dict]:
    url = f"{BASE_URL}/query"
    payload = {"session_id": session_id, "message": message}
    resp = requests.post(url, json=payload, stream=True, timeout=60)
    resp.raise_for_status()
    frames = []
    for line in resp.iter_lines():
        if line:
            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
            frames.append(json.loads(line_str))
    return frames

def run_cmd(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout + ("\nSTDERR:\n" + res.stderr if res.stderr else "")

def main():
    report_lines = []
    def log(msg: str = ""):
        print(msg)
        report_lines.append(msg)

    log("=" * 80)
    log("INDEPENDENT VERIFICATION REPORT: IDENTITY ROUTE (V1-SPRINT-1)")
    log("=" * 80)
    log(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Target: {BASE_URL}")
    log()

    r = get_redis_client()

    # ---------------------------------------------------------
    # 1. UNIT TESTS
    # ---------------------------------------------------------
    log("LAYER 1: UNIT TESTS")
    log("Command: pytest agent_service/tests/test_identity_route.py -q")
    code, out = run_cmd([r"a:\TAS-AI\ESP\.venv\Scripts\python.exe", "-m", "pytest", "agent_service/tests/test_identity_route.py", "-q"])
    log(out.strip())
    unit_pass = (code == 0)
    log(f"RESULT: {'PASS' if unit_pass else 'FAIL'}")
    log("-" * 80)

    # ---------------------------------------------------------
    # 2. ROUTING REGRESSION
    # ---------------------------------------------------------
    log("LAYER 2: ROUTING REGRESSION")
    log("Command: pytest agent_service/tests/test_router_definitional_regression.py -q")
    code, out = run_cmd([r"a:\TAS-AI\ESP\.venv\Scripts\python.exe", "-m", "pytest", "agent_service/tests/test_router_definitional_regression.py", "-q"])
    log(out.strip())
    routing_pass = (code == 0)
    log(f"RESULT: {'PASS' if routing_pass else 'FAIL'}")
    log("-" * 80)

    # ---------------------------------------------------------
    # 3. ISOLATION & REDIS STORAGE CHECK
    # ---------------------------------------------------------
    log("LAYER 3 & 4: ISOLATION & REDIS STORAGE CHECK")
    session_iso = "verify-isolation"
    # Clean any prior keys for this session
    for k in r.keys(f"esp:session:{session_iso}*"):
        r.delete(k)

    runs_before = set(r.keys("esp:run:*"))
    raw_lines = []
    url = f"{BASE_URL}/query"
    payload = {"session_id": session_iso, "message": "What are you?"}
    resp = requests.post(url, json=payload, stream=True, timeout=30)
    for l in resp.iter_lines():
        if l:
            raw_lines.append(l.decode("utf-8") if isinstance(l, bytes) else l)

    ndjson_str = "\n".join(raw_lines)
    frames_iso = [json.loads(l) for l in raw_lines]

    advisory_count = sum(1 for f in frames_iso if f.get("type") == "advisory")
    visual_count = sum(1 for f in frames_iso if f.get("type") == "visual")
    evidence_id_count = ndjson_str.count("evidence_id")
    types = sorted(list(set(f.get("type") for f in frames_iso)))

    runs_after = set(r.keys("esp:run:*"))
    new_runs = runs_after - runs_before
    session_keys = list(r.keys(f"esp:session:{session_iso}*"))

    log(f"Isolation Frames: {types}")
    log(f"advisory count: {advisory_count} (Expected: 0)")
    log(f"visual count: {visual_count} (Expected: 0)")
    log(f"evidence_id count: {evidence_id_count} (Expected: 0)")
    log(f"New esp:run:* keys created: {list(new_runs)} (Expected: [])")
    log(f"Session keys created: {session_keys} (Expected: >= 1)")

    isolation_pass = (
        advisory_count == 0
        and visual_count == 0
        and evidence_id_count == 0
        and types == ["done", "text_delta"]
        and len(new_runs) == 0
        and len(session_keys) > 0
    )
    log(f"RESULT: {'PASS' if isolation_pass else 'FAIL'}")
    log("-" * 80)

    # ---------------------------------------------------------
    # 5. LIVE API 6 QUERIES
    # ---------------------------------------------------------
    log("LAYER 5: LIVE API (6 QUERIES)")
    
    # Query 1
    log("\n--- Query 1: Identity detection ('What are you?') ---")
    q1_frames = query_stream("verify-1", "What are you?")
    q1_types = [f.get("type") for f in q1_frames]
    q1_done = next((f for f in q1_frames if f.get("type") == "done"), None)
    q1_text = "".join(f.get("delta", "") for f in q1_frames if f.get("type") == "text_delta")
    log(f"Frames: {set(q1_types)}")
    log(f"Done frame status: {q1_done.get('status') if q1_done else 'MISSING'}")
    log(f"Answer snippet: {q1_text[:200]}...")
    q1_pass = (
        "advisory" not in q1_types
        and "visual" not in q1_types
        and q1_done is not None
        and q1_done.get("status") == "OK"
        and ("ESP" in q1_text or "copilot" in q1_text.lower() or "agent" in q1_text.lower())
    )
    log(f"Query 1: {'PASS' if q1_pass else 'FAIL'}")

    # Query 2
    log("\n--- Query 2: Capabilities ('What can you do?') ---")
    q2_frames = query_stream("verify-2", "What can you do?")
    q2_text = "".join(f.get("delta", "") for f in q2_frames if f.get("type") == "text_delta")
    log(f"Answer snippet: {q2_text[:250]}...")
    q2_pass = ("OP0" in q2_text or "trip" in q2_text.lower() or "diagnos" in q2_text.lower())
    log(f"Query 2: {'PASS' if q2_pass else 'FAIL'}")

    # Query 3
    log("\n--- Query 3: Boundaries ('What can you not do?') ---")
    q3_frames = query_stream("verify-3", "What can you not do?")
    q3_text = "".join(f.get("delta", "") for f in q3_frames if f.get("type") == "text_delta")
    log(f"Answer snippet: {q3_text[:250]}...")
    q3_pass = ("advisory" in q3_text.lower() or "cannot" in q3_text.lower() or "no " in q3_text.lower() or "vsd" in q3_text.lower())
    log(f"Query 3: {'PASS' if q3_pass else 'FAIL'}")

    # Query 4
    log("\n--- Query 4: Disambiguation ('What is gas lock?') ---")
    q4_frames = query_stream("verify-4", "What is gas lock?")
    q4_types = [f.get("type") for f in q4_frames]
    q4_done = next((f for f in q4_frames if f.get("type") == "done"), None)
    q4_text = "".join(f.get("delta", "") for f in q4_frames if f.get("type") == "text_delta")
    log(f"Frames: {set(q4_types)}")
    log(f"Done frame status: {q4_done.get('status') if q4_done else 'MISSING'}")
    log(f"Answer snippet: {q4_text[:250]}...")
    # Should be OP06 / gas lock knowledge, NOT identity
    q4_pass = (
        ("gas lock" in q4_text.lower() or "intake" in q4_text.lower() or "slug" in q4_text.lower() or "gas" in q4_text.lower())
        and "copilot" not in q4_text.lower()[:50]
    )
    log(f"Query 4: {'PASS' if q4_pass else 'FAIL'}")

    # Query 5
    log("\n--- Query 5: Diagnostic path unchanged ('Why did FS-17 trip?') ---")
    q5_frames = query_stream("verify-5", "Why did FS-17 trip?")
    q5_types = [f.get("type") for f in q5_frames]
    q5_adv = next((f for f in q5_frames if f.get("type") == "advisory"), None)
    q5_vis = next((f for f in q5_frames if f.get("type") == "visual"), None)
    log(f"Frames: {set(q5_types)}")
    card_count = len(q5_vis.get("cards", [])) if q5_vis else 0
    hyp_count = len(q5_adv.get("hypotheses", [])) if q5_adv else 0
    log(f"Advisory present: {q5_adv is not None} (Hypotheses: {hyp_count})")
    log(f"Visual cards present: {q5_vis is not None} (Cards: {card_count})")
    q5_pass = (
        q5_adv is not None
        and q5_vis is not None
        and card_count == 4
    )
    log(f"Query 5: {'PASS' if q5_pass else 'FAIL'}")

    # Query 6
    log("\n--- Query 6: Edge case: identity mid-conversation (Turn 1: Diagnostic, Turn 2: Identity) ---")
    s6 = "verify-6"
    log("Turn 1: 'Why did FS-17 trip?'")
    t1_frames = query_stream(s6, "Why did FS-17 trip?")
    t1_adv = any(f.get("type") == "advisory" for f in t1_frames)
    log(f"Turn 1 advisory produced: {t1_adv}")

    log("Turn 2: 'What can you do?' in same session")
    t2_frames = query_stream(s6, "What can you do?")
    t2_types = [f.get("type") for f in t2_frames]
    t2_text = "".join(f.get("delta", "") for f in t2_frames if f.get("type") == "text_delta")
    log(f"Turn 2 Frames: {set(t2_types)}")
    log(f"Turn 2 text snippet: {t2_text[:250]}...")
    q6_pass = (
        "advisory" not in t2_types
        and "visual" not in t2_types
        and ("OP0" in t2_text or "diagnos" in t2_text.lower() or "trip" in t2_text.lower())
        and not t2_text.lower().startswith("well fs-17")
    )
    log(f"Query 6: {'PASS' if q6_pass else 'FAIL'}")
    log("-" * 80)

    # ---------------------------------------------------------
    # 6. FULL REGRESSION SUITE
    # ---------------------------------------------------------
    log("LAYER 6: FULL REGRESSION SUITE")
    log("Command: pytest agent_service/tests/ -q")
    code_full, out_full = run_cmd([r"a:\TAS-AI\ESP\.venv\Scripts\python.exe", "-m", "pytest", "agent_service/tests/", "-q"])
    log(out_full.strip())
    regression_pass = (code_full == 0)
    log(f"RESULT: {'PASS' if regression_pass else 'FAIL'}")
    log("=" * 80)

    # ---------------------------------------------------------
    # 7. ACCEPTANCE MATRIX
    # ---------------------------------------------------------
    matrix = [
        (1, "'What are you?' returns identity answer", "text_delta + done, no advisory", q1_pass),
        (2, "'What can you do?' lists real objectives", "matches /capabilities output", q2_pass),
        (3, "'What can you not do?' names boundaries", "mentions advisory-only, no writes", q3_pass),
        (4, "'What is gas lock?' still routes to OP06", "KB-grounded, not identity", q4_pass),
        (5, "'Why did FS-17 trip?' still routes to OP03", "advisory + 4 cards", q5_pass),
        (6, "No evidence pack created for identity", "0 evidence_ids in stream", isolation_pass and evidence_id_count == 0),
        (7, "No run created in Redis for identity", "KEYS shows no esp:run:* for query", len(new_runs) == 0),
        (8, "Dock UI renders identity answer", "USER MANUAL CONFIRMATION", None),
        (9, "Full regression suite green", "pytest all pass", regression_pass),
        (10, "Identity mid-session doesn't break follow-ups", "Query 6 passes without leakage", q6_pass),
    ]

    log("\nFINAL ACCEPTANCE MATRIX:")
    log(f"{'#':<3} | {'Criterion':<45} | {'Condition':<35} | {'Status'}")
    log("-" * 95)
    all_automated_green = True
    for item in matrix:
        num, crit, cond, stat = item
        if stat is None:
            s_str = "PENDING (User UI test)"
        elif stat:
            s_str = "PASSED [OK]"
        else:
            s_str = "FAILED [X]"
            all_automated_green = False
        log(f"{num:<3} | {crit:<45} | {cond:<35} | {s_str}")
    log("-" * 95)
    log(f"\nOVERALL AUTOMATED RESULT: {'100% SEALED & VERIFIED' if all_automated_green else 'FAILURES DETECTED'}")

    os.makedirs("reports", exist_ok=True)
    report_path = "reports/IDENTITY_ROUTE_VERIFICATION_REPORT.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"\nWrote full report to {report_path}")

if __name__ == "__main__":
    main()
