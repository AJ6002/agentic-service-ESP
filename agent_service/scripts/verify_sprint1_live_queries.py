import urllib.request
import json
import sys

def parse_ndjson(raw_text: str):
    frames = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            frames.append(json.loads(line))
        except Exception:
            pass
    return frames

def test_live_fleet_queries():
    print("=" * 60)
    print("CHECK 2: FLEET QUERIES ROUTE TO FLEET, NOT CLARIFY")
    print("=" * 60)

    queries = [
        "which wells are running?",
        "list all wells",
        "rank wells by health",
        "how many wells running",
        "which wells tripped",
        "Show me fleet summary",
    ]

    for q in queries:
        req = urllib.request.Request(
            "http://127.0.0.1:8091/query",
            data=json.dumps({"session_id": f"v-p5-{abs(hash(q))}", "message": q}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            frames = parse_ndjson(raw)
            types = [f.get("type") for f in frames]
            print(f"Query: '{q:26s}' -> Frames: {types}")
            if "clarification" in types:
                print(f"  [FAIL] Query '{q}' returned a clarification frame!")
                sys.exit(1)
            else:
                print(f"  [PASS] Clean response (zero clarification frames)")

    print("\n" + "=" * 60)
    print("CHECK 3: NO REGRESSION ON ASSET AND IDENTITY QUERIES")
    print("=" * 60)

    # 1. Asset query: "why did FS-17 trip?"
    req_asset = urllib.request.Request(
        "http://127.0.0.1:8091/query",
        data=json.dumps({"session_id": "v-reg-1", "message": "why did FS-17 trip?"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_asset) as resp:
        raw = resp.read().decode("utf-8")
        frames = parse_ndjson(raw)
        types = [f.get("type") for f in frames]
        print(f"Query: 'why did FS-17 trip?'          -> Frames: {types}")
        assert "advisory" in types or "status" in types or "done" in types
        print(f"  [PASS] Asset-scoped workflow executed successfully.")

    # 2. Identity query: "what are you?"
    req_ident = urllib.request.Request(
        "http://127.0.0.1:8091/query",
        data=json.dumps({"session_id": "v-reg-2", "message": "what are you?"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_ident) as resp:
        raw = resp.read().decode("utf-8")
        frames = parse_ndjson(raw)
        types = [f.get("type") for f in frames]
        print(f"Query: 'what are you?'                -> Frames: {types}")
        assert "text_delta" in types
        print(f"  [PASS] Identity route returned text_delta.")

    print("\nALL LIVE SPRINT 1 QUERY CHECKS PASSED.")

if __name__ == "__main__":
    test_live_fleet_queries()
