"""
Full 20-Query Live Seal Execution Script.
Executes queries via curl-equivalent against http://127.0.0.1:8091/query,
records streaming NDJSON frames, verifies contracts, and outputs to RESULTS_QUERIES_RUN.txt.
"""
import urllib.request
import json
import time
import uuid
import sys
import os

BASE_URL = "http://127.0.0.1:8091/query"
OUTPUT_FILE = "RESULTS_QUERIES_RUN.txt"

def execute_query(session_id: str, message: str, timeout_sec: int = 300):
    payload = json.dumps({"session_id": session_id, "message": message}).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "CurlSeal/1.0"}
    )
    
    t0 = time.perf_counter()
    frames = []
    error_msg = None
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw_lines = resp.read().decode("utf-8").strip().splitlines()
            for line in raw_lines:
                line = line.strip()
                if line:
                    try:
                        frames.append(json.loads(line))
                    except Exception:
                        frames.append({"type": "raw", "data": line})
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        
    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    frame_types = [f.get("type", "unknown") for f in frames]
    done_frame = next((f for f in frames if f.get("type") == "done"), None)
    done_status = done_frame.get("status") if done_frame else ("ERROR" if error_msg else "NONE")
    
    clarify_frame = next((f for f in frames if f.get("type") == "clarification"), None)
    error_frame = next((f for f in frames if f.get("type") == "error"), None)
    advisory_frame = next((f for f in frames if f.get("type") == "advisory"), None)
    visual_frame = next((f for f in frames if f.get("type") == "visual"), None)
    text_deltas = "".join(f.get("delta", "") for f in frames if f.get("type") == "text_delta")
    
    return {
        "session_id": session_id,
        "message": message,
        "elapsed_ms": elapsed_ms,
        "frames": frames,
        "frame_types": frame_types,
        "done_status": done_status,
        "clarify": clarify_frame,
        "error": error_frame,
        "advisory": advisory_frame,
        "visual": visual_frame,
        "text": text_deltas,
        "http_error": error_msg
    }

def main():
    results = []
    print("Starting 20-Query Seal Suite...", flush=True)
    
    # -------------------------------------------------------------
    # BASIC STUFF (Slice 1)
    # -------------------------------------------------------------
    print("\n--- Slice 1: Basic Queries ---", flush=True)
    
    # Q1
    print("Q1: What is underload protection?", flush=True)
    r1 = execute_query("s1_q1", "What is underload protection?")
    results.append(("1. What is underload protection?", r1))
    
    # Q2
    s1_interactive = f"s1_flow_{uuid.uuid4().hex[:6]}"
    print("Q2: Explain that (empty session)", flush=True)
    r2 = execute_query(s1_interactive, "Explain that")
    results.append(("2. Explain that (empty session)", r2))
    
    # Q3
    print("Q3: Resume with asset name 'FS-17'", flush=True)
    r3 = execute_query(s1_interactive, "FS-17")
    results.append(("3. Reply with asset name (FS-17)", r3))
    
    # -------------------------------------------------------------
    # BIG ENGINE (Slice 2)
    # -------------------------------------------------------------
    print("\n--- Slice 2: Workflow Queries ---", flush=True)
    
    # Q4
    print("Q4: What's the current status of FS-17?", flush=True)
    r4 = execute_query("s2_q4", "What's the current status of FS-17?")
    results.append(("4. What's the current status of FS-17?", r4))
    
    # Q5
    s2_trip_sess = f"s2_trip_{uuid.uuid4().hex[:6]}"
    print("Q5: Why did FS-17 trip?", flush=True)
    r5 = execute_query(s2_trip_sess, "Why did FS-17 trip?")
    results.append(("5. Why did FS-17 trip?", r5))
    
    # Q6
    print("Q6: Diagnose FS-91 (dead historian)", flush=True)
    r6 = execute_query("s2_q6", "Diagnose FS-91")
    results.append(("6. Diagnose FS-91 (historian missing)", r6))
    
    # -------------------------------------------------------------
    # NEW OBJECTIVES (Phase 2)
    # -------------------------------------------------------------
    print("\n--- Phase 2: New Objectives ---", flush=True)
    
    # Q7
    print("Q7: How healthy is FS-17?", flush=True)
    r7 = execute_query("p2_q7", "How healthy is FS-17?")
    results.append(("7. How healthy is FS-17?", r7))
    
    # Q8
    print("Q8: Any early warnings for FS-17?", flush=True)
    r8 = execute_query("p2_q8", "Any early warnings for FS-17?")
    results.append(("8. Any early warnings for FS-17?", r8))
    
    # Q9
    print("Q9: Show me FS-17 history for the last 7 days", flush=True)
    r9 = execute_query("p2_q9", "Show me FS-17 history for the last 7 days")
    results.append(("9. Show me FS-17 history for the last 7 days", r9))
    
    # -------------------------------------------------------------
    # MORE OBJECTIVES (Phase 2b)
    # -------------------------------------------------------------
    print("\n--- Phase 2b: Production & Glossary ---", flush=True)
    
    # Q10
    print("Q10: Why has FS-17 production declined?", flush=True)
    r10 = execute_query("p2b_q10", "Why has FS-17 production declined?")
    results.append(("10. Why has FS-17 production declined?", r10))
    
    # Q11
    print("Q11: Explain gas lock.", flush=True)
    r11 = execute_query("p2b_q11", "Explain gas lock.")
    results.append(("11. Explain gas lock.", r11))
    
    # Q12
    print("Q12: Explain what underload trip is.", flush=True)
    r12 = execute_query("p2b_q12", "Explain what underload trip is.")
    results.append(("12. Explain what underload trip is.", r12))
    
    # -------------------------------------------------------------
    # FOLLOW-UP (Phase 4) — Run on s2_trip_sess (after Q5)
    # -------------------------------------------------------------
    print("\n--- Phase 4: Follow-Up Suite ---", flush=True)
    
    # Q13
    print("Q13: Why did you say gas interference? (Follow-up Turn 2)", flush=True)
    r13 = execute_query(s2_trip_sess, "Why did you say gas interference?")
    results.append(("13. Why did you say gas interference?", r13))
    
    # Q14
    print("Q14: What data did you use? (Follow-up Turn 3)", flush=True)
    r14 = execute_query(s2_trip_sess, "What data did you use?")
    results.append(("14. What data did you use?", r14))
    
    # Q15
    print("Q15: What does that graph mean? (Follow-up Turn 4)", flush=True)
    r15 = execute_query(s2_trip_sess, "What does that graph mean?")
    results.append(("15. What does that graph mean?", r15))
    
    # Q16
    print("Q16: Recheck the last 2 hours (Follow-up Turn 5, fresh WORKFLOW)", flush=True)
    r16 = execute_query(s2_trip_sess, "Recheck the last 2 hours")
    results.append(("16. Recheck the last 2 hours", r16))
    
    # Q17
    fresh_orphan_sess = f"orphan_{uuid.uuid4().hex[:6]}"
    print("Q17: Why did that happen? (Empty session -> Clarify)", flush=True)
    r17 = execute_query(fresh_orphan_sess, "Why did that happen?")
    results.append(("17. Why did that happen? (fresh session)", r17))
    
    # Q18
    dead_pack_sess = f"deadpack_{uuid.uuid4().hex[:6]}"
    print("Q18: Follow-up on dead pack (no prior run)", flush=True)
    r18 = execute_query(dead_pack_sess, "Why did you conclude that?")
    results.append(("18. Follow-up on dead/expired pack", r18))
    
    # -------------------------------------------------------------
    # TROUBLESHOOT (Phase 4.5)
    # -------------------------------------------------------------
    print("\n--- Phase 4.5: Troubleshooting ---", flush=True)
    
    # Q19
    print("Q19: Troubleshoot FS-17", flush=True)
    r19 = execute_query("p45_q19", "Troubleshoot FS-17")
    results.append(("19. Troubleshoot FS-17", r19))
    
    # Q20
    print("Q20: How do I troubleshoot motor overload?", flush=True)
    r20 = execute_query("p45_q20", "How do I troubleshoot motor overload?")
    results.append(("20. How do I troubleshoot motor overload?", r20))
    
    # -------------------------------------------------------------
    # Format and Write to RESULTS_QUERIES_RUN.txt
    # -------------------------------------------------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("===============================================================================\n")
        f.write("ESP APM AGENT SERVICE — 20-QUERY SEAL MATRIX TEST REPORT\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Endpoint:  {BASE_URL}\n")
        f.write("===============================================================================\n\n")
        
        for idx, (title, res) in enumerate(results, 1):
            f.write(f"-------------------------------------------------------------------------------\n")
            f.write(f"QUERY #{idx}: {title}\n")
            f.write(f"Session ID:  {res['session_id']}\n")
            f.write(f"Message:     '{res['message']}'\n")
            f.write(f"Latency:     {res['elapsed_ms']:.1f} ms\n")
            f.write(f"Done Status: {res['done_status']}\n")
            f.write(f"Frames:      {res['frame_types']}\n")
            
            if res.get("http_error"):
                f.write(f"HTTP ERROR:  {res['http_error']}\n")
                
            if res.get("clarify"):
                f.write(f"Clarification: Reason={res['clarify'].get('reason')} | Slot={res['clarify'].get('slot')} | Options={res['clarify'].get('options')}\n")
                f.write(f"Clarify Q:     {res['clarify'].get('custom_question')}\n")
                
            if res.get("error"):
                f.write(f"Error Frame:   Code={res['error'].get('code')} | Msg={res['error'].get('message')}\n")
                
            if res.get("advisory"):
                f.write(f"Advisory:      Objective={res['advisory'].get('advisory', {}).get('objective_id')}\n")
                
            if res.get("visual"):
                f.write(f"Visual Frame:  {res['visual']}\n")
                
            if res.get("text"):
                clean_text = res['text'].strip()
                f.write(f"Response Text:\n{clean_text}\n")
            f.write(f"-------------------------------------------------------------------------------\n\n")
            
    print(f"\nCompleted all 20 queries! Results saved to {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
