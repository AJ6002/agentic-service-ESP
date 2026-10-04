import sys
import os
import json
import requests
import subprocess

sys.path.insert(0, os.path.abspath("agent_service"))
from app.stores.redis_client import get_redis_client

out_file = "reports/SPRINT_1_UI_ROUTE_CONTEXT_VERIFICATION_REPORT.txt"
lines = []

def log(s=""):
    print(s)
    lines.append(s)

def query_endpoint(sid, msg, ui_ctx):
    url = "http://127.0.0.1:8091/query"
    payload = {"session_id": sid, "message": msg}
    if ui_ctx is not None:
        payload["ui_context"] = ui_ctx
    resp = requests.post(url, json=payload, stream=True, timeout=30)
    raw_lines = []
    for l in resp.iter_lines():
        if l:
            raw_lines.append(l.decode("utf-8") if isinstance(l, bytes) else l)
    frames = [json.loads(l) for l in raw_lines]
    return resp.status_code, raw_lines, frames

def main():
    log("=" * 80)
    log("SPRINT 1 — UI ROUTE CONTEXT CONTRACT VERIFICATION REPORT")
    log("=" * 80)
    log()

    # Task 1.1: Verification of request model accepting ui_context.selected_route
    log("TASK 1.1 — VERIFY REQUEST MODEL ACCEPTS ui_context.selected_route")
    log("Sending POST http://127.0.0.1:8091/query with ui_context.selected_route = '/working-status'")
    status, raw1, frames1 = query_endpoint("t1", "test", {"selected_route": "/working-status"})
    log(f"HTTP Status: {status}")
    log(f"Frames count: {len(frames1)}")
    t1_pass = (status == 200)
    log(f"Task 1.1 Result: {'PASS (HTTP 200, no 422)' if t1_pass else 'FAIL'}")
    log("-" * 80)

    # Task 1.2: Context frame carries selected_route
    log("\nTASK 1.2 — VERIFY CONTEXT FRAME CARRIES selected_route")
    from app.context.resolver import resolve_context
    cf1 = resolve_context("test-cf-1", "test message", ui_context={"selected_route": "/working-status"})
    log(f"ContextFrame.selected_route from dict: {cf1.selected_route}")
    log(f"ContextFrame.ui_context['selected_route']: {cf1.ui_context.get('selected_route')}")

    from app.contracts.api import UIContext
    cf2 = resolve_context("test-cf-2", "test message", ui_context=UIContext(selected_route="/wells/FS-17"))
    log(f"ContextFrame.selected_route from UIContext obj: {cf2.selected_route}")

    t1_2_pass = (cf1.selected_route == "/working-status" and cf2.selected_route == "/wells/FS-17")
    log(f"Task 1.2 Result: {'PASS (Frame carries selected_route)' if t1_2_pass else 'FAIL'}")
    log("-" * 80)

    # Task 1.3: Verify flow without breaking anything (Three queries)
    log("\nTASK 1.3 — VERIFY QUERIES FLOW WITHOUT BREAKING ANYTHING")

    # 1. Identity with route context
    log("\n--- Query t2: Identity with route context ('What are you?') ---")
    log("BODY: {'session_id':'t2','message':'What are you?','ui_context':{'selected_route':'/working-status'}}")
    s2, raw2, f2 = query_endpoint("t2", "What are you?", {"selected_route": "/working-status"})
    log(f"HTTP Status: {s2}")
    types2 = [f.get("type") for f in f2]
    log(f"Frame types: {types2}")
    text2 = "".join(f.get("delta", "") for f in f2 if f.get("type") == "text_delta")
    log(f"Answer snippet: {text2[:160]}...")
    q_t2_pass = (s2 == 200 and types2 == ["text_delta", "done"] and "advisory" not in types2 and "visual" not in types2)
    log(f"Query t2 Result: {'PASS' if q_t2_pass else 'FAIL'}")

    # 2. KB lookup with route context
    log("\n--- Query t3: KB lookup with route context ('What is gas lock?') ---")
    log("BODY: {'session_id':'t3','message':'What is gas lock?','ui_context':{'selected_route':'/working-status'}}")
    s3, raw3, f3 = query_endpoint("t3", "What is gas lock?", {"selected_route": "/working-status"})
    log(f"HTTP Status: {s3}")
    types3 = [f.get("type") for f in f3]
    log(f"Frame types: {types3}")
    text3 = "".join(f.get("delta", "") for f in f3 if f.get("type") == "text_delta")
    log(f"Answer snippet: {text3[:160]}...")
    q_t3_pass = (s3 == 200 and "gas lock" in text3.lower() and "advisory" in types3)
    log(f"Query t3 Result: {'PASS' if q_t3_pass else 'FAIL'}")

    # 3. WORKFLOW with route context (refusal path for FS-17)
    log("\n--- Query t4: WORKFLOW with route context ('Why did FS-17 trip?') ---")
    log("BODY: {'session_id':'t4','message':'Why did FS-17 trip?','ui_context':{'selected_route':'/wells/FS-17'}}")
    s4, raw4, f4 = query_endpoint("t4", "Why did FS-17 trip?", {"selected_route": "/wells/FS-17"})
    log(f"HTTP Status: {s4}")
    types4 = [f.get("type") for f in f4]
    log(f"Frame types: {types4}")
    text4 = "".join(f.get("delta", "") for f in f4 if f.get("type") == "text_delta")
    log(f"Answer snippet: {text4[:160]}...")
    q_t4_pass = (s4 == 200 and "No trip or fault events recorded for FS-17" in text4 and "visual" not in types4)
    log(f"Query t4 Result: {'PASS' if q_t4_pass else 'FAIL'}")

    # 4. WORKFLOW with route context (normal path with events for FS-16)
    log("\n--- Query t5: WORKFLOW normal with route context ('Why did FS-16 trip?') ---")
    log("BODY: {'session_id':'t5','message':'Why did FS-16 trip?','ui_context':{'selected_route':'/wells/FS-16'}}")
    s5, raw5, f5 = query_endpoint("t5", "Why did FS-16 trip?", {"selected_route": "/wells/FS-16"})
    log(f"HTTP Status: {s5}")
    types5 = [f.get("type") for f in f5]
    log(f"Frame types: {types5}")
    vis5 = next((f for f in f5 if f.get("type") == "visual"), None)
    cards5 = vis5.get("card_ids") if vis5 else []
    log(f"Visual cards ({len(cards5)}): {cards5}")
    q_t5_pass = (s5 == 200 and len(cards5) == 4)
    log(f"Query t5 Result: {'PASS' if q_t5_pass else 'FAIL'}")
    log("-" * 80)

    # Unit Tests and Regression
    log("\nUNIT TESTS & REGRESSION EXECUTION:")
    cmd = [
        r"a:\TAS-AI\ESP\.venv\Scripts\python.exe",
        "-m",
        "pytest",
        "agent_service/tests/test_ui_route_context.py",
        "agent_service/tests/test_identity_route.py",
        "agent_service/tests/test_router_definitional_regression.py",
        "-v"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    log(res.stdout)
    if res.stderr:
        log("STDERR:\n" + res.stderr)
    reg_pass = (res.returncode == 0)

    # Redis check
    log("-" * 80)
    log("REDIS STORAGE CHECK:")
    r = get_redis_client()
    runs_before = set(r.keys("esp:run:*"))
    requests.post("http://127.0.0.1:8091/query", json={"session_id": "redis-check-sprint1", "message": "What are you?", "ui_context": {"selected_route": "/working-status"}})
    runs_after = set(r.keys("esp:run:*"))
    new_runs = runs_after - runs_before
    log(f"New esp:run:* keys created by identity query: {list(new_runs)}")
    redis_pass = (len(new_runs) == 0)

    # Exit Criteria Table
    log("\n" + "=" * 80)
    log("SPRINT 1 EXIT CRITERIA EVALUATION")
    log("=" * 80)
    crit = [
        (1, "Request model accepts ui_context.selected_route", "HTTP 200, no 422", t1_pass),
        (2, "Context frame carries selected_route", "Frame field populated", t1_2_pass),
        (3, "Three test queries return normally", "Identity + KB + WORKFLOW succeed", q_t2_pass and q_t3_pass and q_t4_pass and q_t5_pass),
        (4, "No regression in existing routes", "Targeted test suites all green", reg_pass and redis_pass),
    ]

    all_pass = True
    log(f"{'#':<3} | {'Check':<46} | {'Pass condition':<32} | {'Status'}")
    log("-" * 95)
    for c_id, name, cond, p in crit:
        if not p:
            all_pass = False
        log(f"{c_id:<3} | {name:<46} | {cond:<32} | {'PASSED [OK]' if p else 'FAILED [X]'}")
    log("-" * 95)
    log(f"\nOVERALL RESULT: {'SPRINT 1 SEALED — READY FOR SPRINT 2' if all_pass else 'FAILURES DETECTED'}")

    os.makedirs("reports", exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote verification output to {out_file}")

if __name__ == "__main__":
    main()
