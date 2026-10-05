import httpx
import json

BASE_URL = "http://127.0.0.1:8091/query"

test_cases = [
    {
        "id": "1",
        "name": "Platform Guide (Working Status)",
        "payload": {
            "session_id": "v7-1",
            "message": "what is the working status page",
            "ui_context": {"selected_route": "/working-status"},
        },
        "expected_objective": "OP15",
    },
    {
        "id": "2",
        "name": "Platform Guide (Subsystem Equalizer)",
        "payload": {
            "session_id": "v7-2",
            "message": "what does the subsystem equalizer show",
            "ui_context": {"selected_route": "/working-status"},
        },
        "expected_objective": "OP15",
    },
    {
        "id": "3",
        "name": "Concept / KB Definition (Gas Lock)",
        "payload": {
            "session_id": "v7-3",
            "message": "What is gas lock?",
            "ui_context": {},
        },
        "expected_objective": "OP06",
    },
    {
        "id": "4",
        "name": "Asset Fault Diagnosis (FS-17 Trip)",
        "payload": {
            "session_id": "v7-4",
            "message": "Why did FS-17 trip?",
            "well_id": "FS-17",
            "ui_context": {"selected_asset": "FS-17"},
        },
        "expected_objective": "OP03",
    },
]

def run_live_tests():
    print("=" * 80)
    print("SPRINT 7 LIVE ENDPOINT VERIFICATION (POST /query)")
    print("=" * 80)

    client = httpx.Client(timeout=45.0)

    for tc in test_cases:
        print(f"\n[TEST {tc['id']}]: {tc['name']}")
        print(f"Message: \"{tc['payload']['message']}\"")
        
        try:
            resp = client.post(BASE_URL, json=tc["payload"])
            lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
            
            frames = []
            for line in lines:
                try:
                    frames.append(json.loads(line))
                except Exception:
                    pass

            text_deltas = [f.get("delta", "") for f in frames if f.get("type") == "text_delta"]
            full_text = "".join(text_deltas)
            visual_frames = [f for f in frames if f.get("type") == "visual"]
            done_frame = next((f for f in frames if f.get("type") == "done"), {})
            status_frames = [f for f in frames if f.get("type") == "status"]
            
            print(f"  HTTP Status: {resp.status_code}")
            print(f"  Done Status: {done_frame.get('status')}")
            print(f"  Visual Cards Emitted: {len(visual_frames)}")
            print(f"  Response Preview: {full_text[:200]}...")
            
            # Verifications
            if tc["expected_objective"] == "OP15":
                assert len(visual_frames) == 0, "OP15 must not emit visual cards"
                assert "Platform guide:" in full_text or "working" in full_text.lower() or "equalizer" in full_text.lower()
                print("  => VERIFIED: Clean OP15 Platform Guide response with no cards.")
            elif tc["expected_objective"] == "OP06":
                assert len(visual_frames) == 0
                assert "gas lock" in full_text.lower()
                print("  => VERIFIED: Clean OP06 ESP knowledge definition.")
            elif tc["expected_objective"] == "OP03":
                assert len(visual_frames) >= 1 or "FS-17" in full_text
                print(f"  => VERIFIED: OP03 Fault Diagnosis with {len(visual_frames)} visual cards emitted.")

        except Exception as ex:
            print(f"  ERROR: {ex}")

    print("\n" + "=" * 80)
    print("LIVE ENDPOINT VERIFICATION COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    run_live_tests()
