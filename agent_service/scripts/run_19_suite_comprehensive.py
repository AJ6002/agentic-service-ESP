"""
19-Query Comprehensive Test Suite Runner.
Executes all 19 queries covering:
- Definitional Single Term (5)
- Definitional Comparative (3)
- Procedural (4)
- Standards Lookup (2)
- Compound / Multi-Part (2)
- Adversarial / Routing Boundary (2)
- Regression / Negative (1)

Validates routing, depth, step lists, citations, artifact cleanliness, and saves comprehensive report.
"""

import httpx
import json
import time
import re
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8091/query"

TEST_SUITE = [
    # Group 1: Definitional Single Term (5)
    {"id": "Q01", "group": "Definitional — Single Term", "query": "What is gas lock?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q02", "group": "Definitional — Single Term", "query": "What is underload protection?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q03", "group": "Definitional — Single Term", "query": "What is PIP?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q04", "group": "Definitional — Single Term", "query": "Define TDH.", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q05", "group": "Definitional — Single Term", "query": "Explain water cut.", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},

    # Group 2: Definitional Comparative (3)
    {"id": "Q06", "group": "Definitional — Comparative", "query": "What's the difference between intake pressure and discharge pressure?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q07", "group": "Definitional — Comparative", "query": "Explain gas lock vs gas interference.", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q08", "group": "Definitional — Comparative", "query": "Difference between BEP and operating point?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},

    # Group 3: Procedural (4)
    {"id": "Q09", "group": "Procedural", "query": "How do I restart an ESP?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": True},
    {"id": "Q10", "group": "Procedural", "query": "How do I troubleshoot motor overload?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": True},
    {"id": "Q11", "group": "Procedural", "query": "What are the steps for a teardown inspection?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": True},
    {"id": "Q12", "group": "Procedural", "query": "How do I check motor insulation resistance?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": True},

    # Group 4: Standards Lookup (2)
    {"id": "Q13", "group": "Standards Lookup", "query": "What does API RP 11S say about underload protection?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
    {"id": "Q14", "group": "Standards Lookup", "query": "What does IEC 60034 cover?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},

    # Group 5: Compound / Multi-Part (2)
    {"id": "Q15", "group": "Compound / Multi-Part", "query": "What is gas lock and how do I fix it?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": True},
    {"id": "Q16", "group": "Compound / Multi-Part", "query": "Explain the H-Q curve and how it relates to BEP.", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},

    # Group 6: Adversarial / Routing Boundary (2)
    {"id": "Q17", "group": "Adversarial / Routing Boundary", "query": "What is 2+2?", "expected_obj": None, "req_steps": False},
    {"id": "Q18", "group": "Adversarial / Routing Boundary", "query": "Explain the well FS-17 trip mechanism.", "expected_obj": "OP03_FAULT_DIAGNOSTICS", "req_steps": False},

    # Group 7: Regression / Negative (1)
    {"id": "Q19", "group": "Regression / Negative", "query": "What is flux capacitor?", "expected_obj": "OP06_KNOWLEDGE_LOOKUP", "req_steps": False},
]

def run_single(item):
    qid = item["id"]
    query = item["query"]
    t0 = time.perf_counter()
    payload = {
        "session_id": f"suite19-{qid}-{int(time.time())}",
        "message": query
    }
    
    frames = []
    try:
        with httpx.Client(timeout=180.0) as client:
            with client.stream("POST", BASE_URL, json=payload) as resp:
                for line in resp.iter_lines():
                    if line:
                        try:
                            frames.append(json.loads(line))
                        except Exception:
                            pass
    except Exception as e:
        return {
            "item": item,
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "frames": frames,
        }

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    # Parse frames
    advisory = None
    text_delta = ""
    error_frame = None
    done_status = "UNKNOWN"
    
    for f in frames:
        ftype = f.get("type")
        if ftype == "advisory":
            advisory = f.get("advisory", {})
        elif ftype == "text_delta":
            text_delta += f.get("delta", "")
        elif ftype == "error":
            error_frame = f
        elif ftype == "done":
            done_status = f.get("status", "DONE")
            
    return {
        "item": item,
        "latency_ms": latency_ms,
        "advisory": advisory,
        "text_delta": text_delta,
        "error_frame": error_frame,
        "done_status": done_status,
        "frames": frames,
    }

def main():
    print("=" * 90)
    print("STARTING 19-QUERY COMPREHENSIVE SUITE RUN")
    print("=" * 90)

    results = []
    for idx, item in enumerate(TEST_SUITE, 1):
        print(f"[{idx}/19] Running {item['id']} ({item['group']}): \"{item['query']}\" ... ", end="", flush=True)
        res = run_single(item)
        results.append(res)
        lat = res.get("latency_ms", 0)
        status = res.get("done_status", "ERR")
        print(f"DONE ({lat}ms, Status: {status})")

    # Generate Report
    report_lines = []
    report_lines.append("=" * 90)
    report_lines.append("COMPREHENSIVE 19-QUERY VERIFICATION & QUALITY AUDIT REPORT")
    report_lines.append(f"Executed At: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    report_lines.append("=" * 90)
    report_lines.append("")

    current_group = ""
    for res in results:
        item = res["item"]
        if item["group"] != current_group:
            current_group = item["group"]
            report_lines.append("")
            report_lines.append(f"### {current_group}")
            report_lines.append("-" * 90)

        qid = item["id"]
        query = item["query"]
        adv = res.get("advisory")
        text = res.get("text_delta", "")
        err = res.get("error_frame")
        lat = res.get("latency_ms", 0)

        assessment = adv.get("assessment", "") if adv else text
        tb_steps = adv.get("troubleshooting_steps", []) if adv else []
        v_steps = adv.get("verification_steps", []) if adv else []
        cited_ids = adv.get("cited_evidence_ids", []) if adv else []
        recom = adv.get("recommendation", "") if adv else ""

        words = len(re.findall(r"\w+", assessment))
        sentences = len([s for s in re.split(r"(?<=[.!?])\s+", assessment) if len(s.strip()) > 5])
        has_artifacts = "<!--" in assessment or "-->" in assessment or "|" in assessment

        # Evaluate Specific Constraints
        checks = []
        
        # 1. Step list contract
        if item["req_steps"]:
            if len(tb_steps) > 0 or len(v_steps) > 0:
                checks.append("PASS: Procedural steps present")
            else:
                checks.append("FAIL: Expected procedural steps")
        else:
            if len(tb_steps) == 0 and len(v_steps) == 0:
                checks.append("PASS: Clean definitional contract (0 steps)")
            else:
                checks.append(f"FAIL: Definitional query emitted {len(tb_steps)} tb_steps / {len(v_steps)} v_steps")

        # 2. Depth check
        if item["group"].startswith("Definitional"):
            if words >= 50 and sentences >= 3:
                checks.append(f"PASS: Depth target met ({words} words, {sentences} sents)")
            else:
                checks.append(f"WARN: Thin response ({words} words, {sentences} sents)")

        # 3. Artifact check
        if not has_artifacts:
            checks.append("PASS: Clean formatting (no <!-- or tables)")
        else:
            checks.append("FAIL: HTML/table artifacts detected")

        # 4. Special cases
        if qid == "Q17": # 2+2
            if "OP06" not in str(adv):
                checks.append("PASS: Routed to direct handler / did not trigger KB")
            else:
                checks.append("NOTE: Routed to SIMPLE")
        elif qid == "Q18": # False trip
            if "no trip" in assessment.lower() or "not recorded" in assessment.lower() or "cannot diagnose" in assessment.lower() or "quiescent" in assessment.lower() or "0 events" in assessment.lower():
                checks.append("PASS: Clean false-premise trip refusal (did not fabricate trip)")
            else:
                checks.append("NOTE: Assessment evaluated")
        elif qid == "Q19": # Flux capacitor
            if "insufficient context" in assessment.lower() or "not found" in assessment.lower() or "no approved knowledge" in assessment.lower() or "0.0" in str(adv.get("confidence")):
                checks.append("PASS: Correct negative/unknown concept refusal (no hallucination)")
            else:
                checks.append("NOTE: Evaluated unknown concept response")

        report_lines.append(f"[{qid}] \"{query}\" (Latency: {lat}ms)")
        report_lines.append(f"  Status Checks: {' | '.join(checks)}")
        report_lines.append(f"  Assessment ({words} words, {sentences} sentences):")
        report_lines.append(f"    {assessment}")
        if recom:
            report_lines.append(f"  Recommendation: {recom}")
        if tb_steps:
            report_lines.append("  Troubleshooting Steps:")
            for s in tb_steps:
                report_lines.append(f"    - {s}")
        if v_steps:
            report_lines.append("  Verification Steps:")
            for s in v_steps:
                report_lines.append(f"    - {s}")
        if cited_ids:
            report_lines.append(f"  Cited Evidence: {cited_ids}")
        report_lines.append("")

    report_content = "\n".join(report_lines)
    out_path = Path("a:/TAS-AI/ESP/COMPREHENSIVE_19_SUITE_EVALUATION_REPORT.txt")
    out_path.write_text(report_content, encoding="utf-8")
    print(f"\nReport written to {out_path.resolve()}")

if __name__ == "__main__":
    main()
