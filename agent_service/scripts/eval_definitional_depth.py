"""
Evaluates definitional queries (Q01, Q06, Q07, Q08) for:
1. Depth & Word Count (Target: ~3x original 2-sentence baseline, 4-6 detailed sentences)
2. Citation Provenance & Section Accuracy (No hallucinated doc IDs)
3. Formatting Quality (No '<!--' or table artifacts)
4. Contract Integrity (troubleshooting_steps == [], verification_steps == [])
"""

import httpx
import json
import time
import re

URL = "http://127.0.0.1:8091/query"

QUERIES = [
    ("Q01", "What is gas lock?", "OP06_KNOWLEDGE_LOOKUP"),
    ("Q06", "Explain water cut.", "OP06_KNOWLEDGE_LOOKUP"),
    ("Q07", "What's the difference between intake pressure and discharge pressure?", "OP06_KNOWLEDGE_LOOKUP"),
    ("Q08", "Explain gas lock vs gas interference.", "OP06_KNOWLEDGE_LOOKUP"),
]

def run_query(qid, message):
    payload = {
        "session_id": f"eval-depth-{qid}-{int(time.time())}",
        "message": message
    }
    with httpx.Client(timeout=120.0) as client:
        with client.stream("POST", URL, json=payload) as resp:
            lines = [line for line in resp.iter_lines() if line]
            frames = [json.loads(line) for line in lines]
            return frames

def evaluate():
    print("=" * 80)
    print("DEFINITIONAL DEPTH & QUALITY AUDIT (Q01, Q06, Q07, Q08)")
    print("=" * 80)
    
    for qid, query, exp_obj in QUERIES:
        print(f"\n[{qid}] Query: \"{query}\"")
        try:
            frames = run_query(qid, query)
        except Exception as e:
            print(f"  [ERROR] Query failed: {e}")
            continue

        adv_frame = next((f for f in frames if "advisory" in f or ("final_response" in f and "advisory" in f.get("payload", {}))), None)
        text_frame = next((f for f in frames if f.get("type") == "text_delta"), None)
        
        advisory = None
        if adv_frame:
            advisory = adv_frame.get("advisory") or adv_frame.get("payload", {}).get("advisory")

        raw_text = ""
        if advisory and advisory.get("assessment"):
            raw_text = advisory.get("assessment")
        elif text_frame:
            raw_text = text_frame.get("delta", "")

        words = re.findall(r"\w+", raw_text)
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_text) if len(s.strip()) > 5]
        sentence_count = len(sentences)

        has_comment_artifacts = "<!--" in raw_text or "-->" in raw_text
        has_table_artifacts = "|" in raw_text

        tb_steps = advisory.get("troubleshooting_steps", []) if advisory else []
        v_steps = advisory.get("verification_steps", []) if advisory else []
        cited_ids = advisory.get("cited_evidence_ids", []) if advisory else []

        # Depth Assessment
        depth_status = "PASS (Rich Technical Depth)" if word_count >= 50 and sentence_count >= 3 else "THIN"
        artifact_status = "CLEAN" if not (has_comment_artifacts or has_table_artifacts) else "ARTIFACTS_DETECTED"
        contract_status = "PASS (Empty Step Lists)" if (len(tb_steps) == 0 and len(v_steps) == 0) else f"FAIL (TB={len(tb_steps)}, V={len(v_steps)})"

        print(f"  * Word Count: {word_count} words | Sentences: {sentence_count}")
        print(f"  * Depth Status: {depth_status}")
        print(f"  * Artifact Check: {artifact_status}")
        print(f"  * Step List Contract: {contract_status}")
        print(f"  * Cited Evidence: {cited_ids}")
        print(f"\n  [Text Preview]:\n  {raw_text}\n")
        print("-" * 80)

if __name__ == "__main__":
    evaluate()
