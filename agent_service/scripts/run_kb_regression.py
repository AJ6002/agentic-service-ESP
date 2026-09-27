"""
KB Regression Test — 5 targeted KB-dependent queries.
Run after any fix to KB retrieval or narration quality.

Usage:
    .venv\\Scripts\\python.exe run_kb_regression.py

Exit code:
    0 — all 5 queries pass
    1 — one or more queries fail

Output:
    Prints PASS/FAIL per query and writes KB_REGRESSION_RESULTS.txt
"""

import json
import time
import datetime
import urllib.request
import urllib.error

AGENT_URL = "http://127.0.0.1:8091/query"
TIMEOUT_SEC = 240
MAX_RETRIES = 1

QUERIES = [
    {
        "id": "Q1",
        "query": "What is underload protection?",
        "description": "Definitional — underload protection mechanism",
    },
    {
        "id": "Q11",
        "query": "Explain gas lock.",
        "description": "Definitional — gas lock phenomenon",
    },
    {
        "id": "Q12",
        "query": "Explain what underload trip is.",
        "description": "Definitional — underload trip",
    },
    {
        "id": "Q20",
        "query": "How do I troubleshoot motor overload?",
        "description": "Procedural — motor overload troubleshooting",
    },
    {
        "id": "Q-pip",
        "query": "What does PIP stand for?",
        "description": "Definitional — PIP acronym lookup",
    },
]

# Responses containing these strings are boilerplate failures.
BOILERPLATE_FAIL_STRINGS = [
    "BP troubleshooting guidelines",
    "minimum tag universe",
    "follow the diagnostic procedure",
    "troubleshooting guidelines",
    "tag universe",
]

# Good responses contain at least one document citation or evidence reference.
CITATION_PATTERNS = [
    "[API_RP",
    "[Takacs",
    "[SPE",
    "[IEC",
    "[Baker",
    "[Weatherford",
    "[SLB",
    "[ESP_Components",
    "[BP_ESP",
    "[ADVAIT",
    "Cited Evidence: EV-",
    "EV-R-",
    "API_RP",
    "Takacs",
    "Baker_Hughes",
    "Weatherford",
]


def _post_query(query: str, session_id: str, attempt: int = 1) -> str:
    """Post a query and return the full response text, collected from NDJSON stream."""
    payload = json.dumps({"session_id": session_id, "message": query}).encode("utf-8")
    req = urllib.request.Request(
        AGENT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8")
            # Response is NDJSON (application/x-ndjson) — one JSON object per line
            text_parts = []
            for line in raw.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    # Collect text_delta frames
                    if obj.get("type") == "text_delta":
                        text_parts.append(obj.get("delta") or obj.get("text", ""))
                    # Also collect advisory.assessment from done/advisory frames
                    elif obj.get("type") in ("advisory", "done") and obj.get("advisory"):
                        adv = obj["advisory"]
                        if isinstance(adv, dict) and adv.get("assessment"):
                            text_parts.append(adv["assessment"])
                        if isinstance(adv, dict) and adv.get("recommendation"):
                            text_parts.append(adv["recommendation"])
                        if isinstance(adv, dict) and adv.get("cited_evidence_ids"):
                            text_parts.append("Cited Evidence: " + ", ".join(adv["cited_evidence_ids"]))
                    # Collect error message text
                    elif obj.get("type") == "error":
                        text_parts.append(obj.get("message", ""))
                except json.JSONDecodeError:
                    text_parts.append(line)
            return "\n".join(text_parts) if text_parts else raw
    except urllib.error.URLError as e:
        if attempt <= MAX_RETRIES:
            print(f"  [RETRY] Network error on attempt {attempt}: {e}. Retrying...")
            time.sleep(3)
            return _post_query(query, session_id, attempt + 1)
        raise


def _check_response(text: str) -> tuple[bool, str, str]:
    """
    Returns (pass, reason, full_text).
    text is the collected NDJSON response text from the agent.
    """

    text_lower = text.lower()

    # Check boilerplate failures
    for fail_str in BOILERPLATE_FAIL_STRINGS:
        if fail_str.lower() in text_lower:
            return False, f"Contains boilerplate: '{fail_str}'", text

    # Check for INSUFFICIENT CONTEXT
    if "insufficient context" in text_lower:
        return False, "Returned INSUFFICIENT CONTEXT instead of real definition", text

    # Check for substantive response length (tightened threshold > 100 chars)
    if len(text.strip()) < 100:
        return False, f"Response too short ({len(text.strip())} chars < 100)", text

    # Check for at least one citation (tightened: mandatory citation)
    has_citation = any(pat in text for pat in CITATION_PATTERNS)
    if not has_citation:
        return False, "Missing verified document citation or evidence reference", text

    return True, "Has on-topic substantive content with citation", text


def main():
    results = []
    print(f"\nKB Regression Test — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Agent: {AGENT_URL}")
    print("=" * 70)

    session_id = f"KB-REG-{datetime.datetime.now().strftime('%H%M%S')}"
    for q in QUERIES:
        print(f"\n[{q['id']}] {q['query']}")
        print(f"      {q['description']}")
        try:
            text = _post_query(q["query"], session_id)
            passed, reason, full_text = _check_response(text)
            status = "PASS" if passed else "FAIL"
            print(f"      [{status}] {reason}")
            if not passed:
                print(f"      Response: {full_text[:300]}")
            results.append({
                "id": q["id"],
                "query": q["query"],
                "status": status,
                "reason": reason,
                "response_preview": full_text[:500],
            })
        except Exception as e:
            print(f"      [FAIL] Exception: {e}")
            results.append({
                "id": q["id"],
                "query": q["query"],
                "status": "FAIL",
                "reason": str(e),
                "response_preview": "",
            })

    print("\n" + "=" * 70)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\nRESULT: {passed_count}/{total} PASSED")

    # Write results file
    out_path = "KB_REGRESSION_RESULTS.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"KB Regression Results — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Agent: {AGENT_URL}\n")
        f.write("=" * 70 + "\n\n")
        for r in results:
            f.write(f"[{r['status']}] {r['id']}: {r['query']}\n")
            f.write(f"  Reason: {r['reason']}\n")
            f.write(f"  Response: {r['response_preview']}\n\n")
        f.write(f"\nSUMMARY: {passed_count}/{total} PASSED\n")

    print(f"Results written to {out_path}")

    if passed_count < total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
