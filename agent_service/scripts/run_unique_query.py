"""
Executes a unique query against the live Agent Service and LLM Gateway,
records both raw NDJSON stream frames and parsed advisory output,
and writes the full audit report to the standardized 'reports/' directory.
"""

import httpx
import json
import time
import os
from pathlib import Path

LLM_URL = "http://192.168.1.188:8080/v1/models"
AGENT_SERVICE_URL = "http://127.0.0.1:8091/query"
REPORTS_DIR = Path("a:/TAS-AI/ESP/reports")
OUTPUT_FILE = REPORTS_DIR / "UNIQUE_QUERY_GLR_RAW_OUTPUT.txt"

UNIQUE_QUERY = "Explain how gas-liquid ratio (GLR) impacts ESP pump head and motor load."

def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("1. PINGING LLM GATEWAY (http://192.168.1.188:8080/v1/models)")
    print("=" * 80)
    try:
        r_llm = httpx.get(LLM_URL, timeout=5.0)
        print(f"LLM Status: {r_llm.status_code}")
        print(f"LLM Payload: {r_llm.text[:200]}")
    except Exception as e:
        print(f"LLM Ping Failed: {e}")
        return

    print("\n" + "=" * 80)
    print(f"2. EXECUTING UNIQUE QUERY ON AGENT SERVICE: \"{UNIQUE_QUERY}\"")
    print("=" * 80)
    
    payload = {
        "session_id": f"unique-glr-test-{int(time.time())}",
        "message": UNIQUE_QUERY
    }
    
    t0 = time.perf_counter()
    raw_lines = []
    frames = []
    
    with httpx.Client(timeout=120.0) as client:
        with client.stream("POST", AGENT_SERVICE_URL, json=payload) as resp:
            for line in resp.iter_lines():
                if line:
                    raw_lines.append(line)
                    try:
                        frames.append(json.loads(line))
                    except Exception:
                        pass
                        
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    print(f"Query Completed in {latency_ms} ms with {len(frames)} stream frames.")

    # Parse key frames
    advisory_frame = next((f for f in frames if f.get("type") == "advisory"), None)
    text_frame = next((f for f in frames if f.get("type") == "text_delta"), None)
    done_frame = next((f for f in frames if f.get("type") == "done"), None)
    
    advisory = advisory_frame.get("advisory", {}) if advisory_frame else {}
    assessment = advisory.get("assessment", "") or (text_frame.get("delta", "") if text_frame else "")
    recommendation = advisory.get("recommendation", "")
    tb_steps = advisory.get("troubleshooting_steps", [])
    v_steps = advisory.get("verification_steps", [])
    cited_ids = advisory.get("cited_evidence_ids", [])
    
    words = len(assessment.split())
    
    # Format Text Report
    report = []
    report.append("=" * 80)
    report.append("ESP APM AGENT SERVICE — UNIQUE QUERY EXECUTION AUDIT REPORT")
    report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    report.append(f"LLM Gateway Target: {LLM_URL}")
    report.append(f"Agent Service Target: {AGENT_SERVICE_URL}")
    report.append("=" * 80)
    report.append("")
    report.append(f"QUERY: \"{UNIQUE_QUERY}\"")
    report.append(f"LATENCY: {latency_ms} ms")
    report.append(f"STATUS: {done_frame.get('status') if done_frame else 'UNKNOWN'}")
    report.append(f"WORD COUNT: {words} words")
    report.append(f"STEP CONTRACT CHECK: TB Steps={len(tb_steps)}, Verification Steps={len(v_steps)} (Expected [] for definitional query)")
    report.append(f"CITED EVIDENCE IDS: {cited_ids}")
    report.append("")
    report.append("-" * 80)
    report.append("PARSED ADVISORY ASSESSMENT (4-PART TECHNICAL DEPTH):")
    report.append("-" * 80)
    report.append(assessment)
    report.append("")
    if recommendation:
        report.append(f"RECOMMENDATION: {recommendation}")
        report.append("")
    if tb_steps:
        report.append("TROUBLESHOOTING STEPS:")
        for s in tb_steps:
            report.append(f"  - {s}")
        report.append("")
    if v_steps:
        report.append("VERIFICATION STEPS:")
        for s in v_steps:
            report.append(f"  - {s}")
        report.append("")
    report.append("-" * 80)
    report.append("RAW NDJSON STREAM FRAMES (AS RECEIVED BY FRONTEND / CALLER):")
    report.append("-" * 80)
    for idx, raw_l in enumerate(raw_lines, 1):
        report.append(f"[Frame {idx:02d}] {raw_l}")
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    
    print(f"\nReport successfully saved to: {OUTPUT_FILE.resolve()}")
    print("\n" + "=" * 80)
    print("REPORT PREVIEW:")
    print("=" * 80)
    print(report_text)

if __name__ == "__main__":
    main()
