import sys
import os
import requests
import json

sys.path.insert(0, os.path.abspath("agent_service"))
from app.stores.redis_client import get_redis_client

def main():
    print("=" * 60)
    print("STEP 1: THREE CURL CALLS")
    print("=" * 60)

    # Query 1
    print("\n[Query 1] POST /query message: 'What are you?'")
    r1 = requests.post("http://127.0.0.1:8091/query", json={"session_id": "v1", "message": "What are you?"})
    f1_raw = [l.strip() for l in r1.text.splitlines() if l.strip()]
    f1 = [json.loads(l) for l in f1_raw]
    types1 = [f.get("type") for f in f1]
    text1 = "".join(f.get("delta", "") for f in f1 if f.get("type") == "text_delta")
    has_ev1 = "evidence_id" in r1.text
    print(f"Frames: {types1}")
    print(f"Contains advisory: {'advisory' in types1}")
    print(f"Contains visual: {'visual' in types1}")
    print(f"Contains evidence_id: {has_ev1}")
    print(f"Answer snippet: {text1[:180]}...")
    q1_pass = (types1 == ["text_delta", "done"] and not has_ev1 and "copilot" in text1.lower())
    print(f"Query 1 Result: {'PASS' if q1_pass else 'FAIL'}")

    # Query 2
    print("\n[Query 2] POST /query message: 'What is gas lock?'")
    r2 = requests.post("http://127.0.0.1:8091/query", json={"session_id": "v2", "message": "What is gas lock?"})
    f2_raw = [l.strip() for l in r2.text.splitlines() if l.strip()]
    f2 = [json.loads(l) for l in f2_raw]
    types2 = [f.get("type") for f in f2]
    text2 = "".join(f.get("delta", "") for f in f2 if f.get("type") == "text_delta")
    print(f"Frames: {types2}")
    print(f"Answer snippet: {text2[:180]}...")
    q2_pass = ("gas lock" in text2.lower() and "copilot" not in text2.lower()[:50])
    print(f"Query 2 Result: {'PASS' if q2_pass else 'FAIL'}")

    # Query 3
    print("\n[Query 3] POST /query message: 'Why did FS-17 trip?'")
    r3 = requests.post("http://127.0.0.1:8091/query", json={"session_id": "v3", "message": "Why did FS-17 trip?"})
    f3_raw = [l.strip() for l in r3.text.splitlines() if l.strip()]
    f3 = [json.loads(l) for l in f3_raw]
    types3 = [f.get("type") for f in f3]
    text3 = "".join(f.get("delta", "") for f in f3 if f.get("type") == "text_delta")
    vis3 = next((f for f in f3 if f.get("type") == "visual"), None)
    cards3 = vis3.get("card_ids") if vis3 else []
    print(f"Frames: {types3}")
    print(f"Cards received ({len(cards3)}): {cards3}")
    print(f"Text snippet: {text3[:180]}...")
    q3_pass = (len(cards3) == 4)
    print(f"Query 3 Result: {'PASS' if q3_pass else 'FAIL'}")

    # Redis check
    print("\n" + "=" * 60)
    print("STEP 4: CHECK REDIS FOR PIPELINE LEAKAGE")
    print("=" * 60)
    r = get_redis_client()
    runs_before = set(r.keys("esp:run:*"))
    # Fire identity query
    r_id = requests.post("http://127.0.0.1:8091/query", json={"session_id": "redis-check-1", "message": "What are you?"})
    runs_after = set(r.keys("esp:run:*"))
    new_runs = runs_after - runs_before
    print(f"New esp:run:* keys created by identity query: {list(new_runs)}")
    redis_pass = (len(new_runs) == 0)
    print(f"Redis Storage Result: {'PASS' if redis_pass else 'FAIL'}")

if __name__ == "__main__":
    main()
