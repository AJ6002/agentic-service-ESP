import requests
import json

def main():
    print("=== 1. Testing False-Premise Refusal: 'Why did FS-17 trip?' ===")
    r1 = requests.post("http://127.0.0.1:8091/query", json={"session_id": "verify-refusal-1", "message": "Why did FS-17 trip?"})
    frames1 = [json.loads(l) for l in r1.text.splitlines() if l.strip()]
    types1 = [f["type"] for f in frames1]
    print("Frame types received:", types1)
    for f in frames1:
        print(f"  [{f['type']}]:", {k: v for k, v in f.items() if k != "run_id"})

    assert "visual" not in types1, "FAIL: Visual frame must NOT be present on refusal!"
    assert any(f["type"] == "text_delta" and "No trip or fault events recorded for FS-17" in f["delta"] for f in frames1), "FAIL: Refusal text missing!"
    done1 = next(f for f in frames1 if f["type"] == "done")
    assert done1["status"] == "OK", "FAIL: Done frame must be status=OK!"
    print("Refusal Check: PASSED (Zero visual frames, refusal text intact, status=OK)\n")

    print("=== 2. Testing Normal Path with Events: 'Why did FS-16 trip?' ===")
    r2 = requests.post("http://127.0.0.1:8091/query", json={"session_id": "verify-normal-1", "message": "Why did FS-16 trip?"})
    frames2 = [json.loads(l) for l in r2.text.splitlines() if l.strip()]
    types2 = [f["type"] for f in frames2]
    print("Frame types received:", types2)
    vis2 = next((f for f in frames2 if f["type"] == "visual"), None)
    assert vis2 is not None, "FAIL: Visual frame must be present on normal path!"
    print(f"  [visual card_ids]: {vis2.get('card_ids')}")
    assert len(vis2.get("card_ids", [])) == 4, "FAIL: Normal path must emit 4 cards!"
    print("Normal Path Check: PASSED (Visual frame present with 4 cards)\n")

    print("=== ALL VERIFICATION CHECKS PASSED ===")

if __name__ == "__main__":
    main()
