"""
Phase 4 Live Verification Script using curl.exe as primary execution engine.
Executes the full 11-Query Seal Matrix against the running Agent Service (http://127.0.0.1:8091/query).
"""
import subprocess
import json
import uuid
import time
import sys

BASE_URL = "http://127.0.0.1:8091/query"

def run_curl(session_id: str, message: str, print_raw: bool = False):
    payload = json.dumps({"session_id": session_id, "message": message})
    cmd = [
        "curl.exe", "-s", "-N", "-X", "POST", BASE_URL,
        "-H", "Content-Type: application/json",
        "-d", payload
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    elapsed_ms = (time.perf_counter() - t0) * 1000

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    frames = []
    for line in lines:
        try:
            frames.append(json.loads(line))
        except Exception:
            frames.append({"raw": line})

    frame_types = [f.get("type", "unknown") for f in frames]
    done_status = next((f.get("status") for f in frames if f.get("type") == "done"), "NONE")
    has_clarify = any(f.get("type") == "clarification" for f in frames)
    has_evidence = any(f.get("type") == "evidence" for f in frames)
    has_advisory = any(f.get("type") == "advisory" for f in frames)
    has_viz = any(f.get("type") == "visualization" for f in frames)
    
    text_deltas = "".join(f.get("delta", "") for f in frames if f.get("type") == "text_delta")
    
    print(f"\n========================================================", flush=True)
    print(f"Session:  {session_id}", flush=True)
    print(f"Query:    '{message}'", flush=True)
    print(f"Latency:  {elapsed_ms:.1f}ms", flush=True)
    print(f"Frames:   {frame_types}", flush=True)
    print(f"Outcome:  Done Status = {done_status} | Clarify = {has_clarify} | Evidence = {has_evidence}", flush=True)
    if has_clarify:
        for f in frames:
            if f.get("type") == "clarification":
                print(f"Clarify:  Reason={f.get('reason')} | Question='{f.get('custom_question') or f.get('slot')}'", flush=True)
    if text_deltas:
        snippet = text_deltas[:200] + ("..." if len(text_deltas) > 200 else "")
        print(f"Summary:  {snippet}", flush=True)
    print(f"========================================================", flush=True)
    return frames

def main():
    print("Starting Live Phase 4 Verification via curl.exe...")
    
    # 1. Regression Queries (R1 - R6)
    print("\n>>> REGRESSION MATRIX (R1 - R6)")
    run_curl("sess_reg_r1", "What is underload protection?")
    run_curl("sess_reg_r2", "What's the current status of FS-17?")
    run_curl("sess_reg_r3", "Why did FS-17 trip?")
    run_curl("sess_reg_r4", "How healthy is FS-17?")
    run_curl("sess_reg_r5", "Any early warnings for FS-17?")
    run_curl("sess_reg_r6", "Why has FS-17 production declined?")

    # 2. Follow-Up Matrix (F1 - F5)
    print("\n>>> PHASE 4 FOLLOW-UP MATRIX (F1 - F5)")
    followup_sess = f"sess_followup_{uuid.uuid4().hex[:6]}"
    
    print("\n[Turn 1] Baseline Analysis Query to seed session state:")
    run_curl(followup_sess, "Why did FS-17 trip?")
    
    print("\n[F1] Turn 2 - Follow-Up WHY (0 data calls):")
    run_curl(followup_sess, "Why did you say gas interference?")
    
    print("\n[F2] Turn 3 - Follow-Up DATA / EVIDENCE:")
    run_curl(followup_sess, "What data did you use?")
    
    print("\n[F3] Turn 4 - Follow-Up VISUALIZATION:")
    run_curl(followup_sess, "What does that graph mean?")
    
    print("\n[F4] Turn 5 - Re-scope Time Window (routes to fresh WORKFLOW):")
    run_curl(followup_sess, "Recheck the last 2 hours")
    
    print("\n[F5] Turn 1 on Empty Session - Orphan Pronoun (routes to CLARIFY):")
    empty_sess = f"sess_empty_{uuid.uuid4().hex[:6]}"
    run_curl(empty_sess, "Why did that happen?")

if __name__ == "__main__":
    main()
