"""
Inspection script for Q5, Q14, and the 5 missing wells (FS-018 through FS-022).
Queries the live Agent Service at http://127.0.0.1:8091/query via NDJSON streaming.
"""

import asyncio
import json
import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8091"

async def stream_query(payload: dict) -> list[dict]:
    frames = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", f"{BASE_URL}/query", json=payload) as response:
            assert response.status_code == 200, f"HTTP {response.status_code}: {await response.aread()}"
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        frames.append(json.loads(line))
                    except json.JSONDecodeError:
                        frames.append({"raw_line": line})
    return frames

async def inspect_q5():
    print("=" * 80)
    print("INSPECTING Q5 RAW OUTPUT (OP01 - Current Operating Status of FS-017)")
    print("=" * 80)
    payload = {
        "session_id": "sess-q5-inspect",
        "message": "What is the current operating status of FS-017?",
        "well_id": "FS-017",
        "page_route": "/wells/$wellId",
    }
    frames = await stream_query(payload)
    print(f"Total frames received: {len(frames)}")
    visual_cards = []
    advisory_frame = None
    done_frame = None
    text_deltas = []

    for f in frames:
        ftype = f.get("type")
        if ftype == "visual":
            visual_cards.extend(f.get("card_ids", []))
            print(f"  [VISUAL FRAME] card_ids = {f.get('card_ids')}")
        elif ftype == "advisory":
            advisory_frame = f
            print(f"  [ADVISORY FRAME] objective={f.get('objective_id')}, warnings={f.get('provenance_warnings')}, degraded={f.get('degraded_sources')}")
        elif ftype == "done":
            done_frame = f
            print(f"  [DONE FRAME] status={f.get('status')}, run_id={f.get('run_id')}")
        elif ftype == "text_delta":
            text_deltas.append(f.get("delta", ""))
        elif ftype == "status":
            print(f"  [STATUS FRAME] step={f.get('step')}, desc={f.get('description')}")

    full_text = "".join(text_deltas)
    print(f"\nProse synthesis summary ({len(full_text)} chars):\n{full_text[:300]}...\n")
    print(f"Q5 Verification Result:")
    print(f"  ✓ OP01 Emits visual cards: {visual_cards} (Count: {len(visual_cards)})")
    assert len(visual_cards) >= 1, "ERROR: OP01 emitted zero cards for FS-017!"
    assert done_frame and done_frame.get("status") == "OK", "ERROR: Q5 did not complete with status OK"
    print("  ✓ Q5 PASS: OP01 emitted at least one card and status OK for FS-017.")
    return frames

async def inspect_q14():
    print("\n" + "=" * 80)
    print("INSPECTING Q14 RAW OUTPUT (OP03 - Fault Diagnosis for FS-017)")
    print("=" * 80)
    payload = {
        "session_id": "sess-q14-inspect",
        "message": "Why did FS-017 trip?",
        "well_id": "FS-017",
        "page_route": "/wells/$wellId",
    }
    frames = await stream_query(payload)
    print(f"Total frames received: {len(frames)}")
    visual_cards = []
    advisory_frame = None
    done_frame = None

    for f in frames:
        ftype = f.get("type")
        if ftype == "visual":
            visual_cards.extend(f.get("card_ids", []))
            print(f"  [VISUAL FRAME] card_ids = {f.get('card_ids')}")
        elif ftype == "advisory":
            advisory_frame = f
            print(f"  [ADVISORY FRAME] objective={f.get('objective_id')}")
            print(f"    provenance_warnings (list): {f.get('provenance_warnings')} (type: {type(f.get('provenance_warnings')).__name__})")
            print(f"    degraded_sources (list): {f.get('degraded_sources')} (type: {type(f.get('degraded_sources')).__name__})")
            print(f"    actions: {len(f.get('recommended_actions', []))} actions")
        elif ftype == "done":
            done_frame = f
            print(f"  [DONE FRAME] status={f.get('status')}, run_id={f.get('run_id')}")
        elif ftype == "status":
            print(f"  [STATUS FRAME] step={f.get('step')}, desc={f.get('description')}")

    print("\nQ14 Frame Set Confirmation:")
    assert advisory_frame is not None, "Missing advisory frame!"
    assert isinstance(advisory_frame.get("provenance_warnings"), list), "provenance_warnings must be list"
    assert isinstance(advisory_frame.get("degraded_sources"), list), "degraded_sources must be list"
    assert len(visual_cards) >= 1, "Missing visual card IDs!"
    assert done_frame and done_frame.get("status") == "OK", "Done status must be OK"
    print("  ✓ Full frame set confirmed: advisory with structured fields, visual with dashboard card IDs, done with OK.")
    return frames

async def test_missing_wells():
    print("\n" + "=" * 80)
    print("TESTING 5 MISSING WELLS (FS-018 through FS-022) - DATA GAP VERIFICATION")
    print("=" * 80)
    missing_wells = ["FS-018", "FS-019", "FS-020", "FS-021", "FS-022"]
    results = {}

    for well in missing_wells:
        payload = {
            "session_id": f"sess-missing-{well}",
            "message": f"What is the status of {well}?",
            "well_id": well,
        }
        frames = await stream_query(payload)
        done_frame = next((f for f in frames if f.get("type") == "done"), None)
        error_frame = next((f for f in frames if f.get("type") == "error"), None)
        visual_frame = next((f for f in frames if f.get("type") == "visual"), None)
        status = done_frame.get("status") if done_frame else "NO_DONE"
        
        results[well] = {
            "status": status,
            "error_code": error_frame.get("code") if error_frame else None,
            "has_visual_cards": bool(visual_frame and visual_frame.get("card_ids")),
            "frame_types": [f.get("type") for f in frames],
        }
        print(f"  ✓ {well}: done.status='{status}', error_code='{results[well]['error_code']}', visual_cards={results[well]['has_visual_cards']}")
        assert status == "INSUFFICIENT", f"Expected {well} to return INSUFFICIENT cleanly, got {status}"
        assert not results[well]["has_visual_cards"], f"{well} should emit zero visual cards on data gap"

    print("\n  ✓ 5 Missing Wells (FS-018..FS-022) return INSUFFICIENT cleanly without fabricating cards or crashing.")
    return results

async def main():
    await inspect_q5()
    await inspect_q14()
    await test_missing_wells()

if __name__ == "__main__":
    asyncio.run(main())
