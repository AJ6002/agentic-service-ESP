import json
import httpx
import sys
from app.stores.run_store import get_run, get_pack

def run_query(message: str, selected_asset: str = "FS-17", session_id: str = "demo-session-last2h"):
    print("=" * 70)
    print(f"QUERY: \"{message}\"")
    print(f"SELECTED ASSET (UI Context): {selected_asset}")
    print(f"SESSION ID: {session_id}")
    print("=" * 70)
    
    payload = {
        "session_id": session_id,
        "message": message,
        "ui_context": {
            "selected_asset": selected_asset
        }
    }
    
    captured_run_id = None
    frames = []
    
    print("\n--- STREAMING RESPONSE FRAMES (NDJSON) ---")
    with httpx.Client(timeout=45.0) as client:
        with client.stream("POST", "http://127.0.0.1:8091/query", json=payload) as resp:
            print(f"HTTP Status: {resp.status_code}")
            for raw_line in resp.iter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    frame = json.loads(line)
                    frames.append(frame)
                    ftype = frame.get("type")
                    rid = frame.get("run_id")
                    if rid and not captured_run_id:
                        captured_run_id = rid
                    
                    if ftype == "status":
                        print(f"-> [status] {frame.get('status')}")
                    elif ftype == "text_delta":
                        print(f"-> [text_delta] {frame.get('delta')}")
                    elif ftype == "visual":
                        print(f"-> [visual] type={frame.get('visual_type')} title=\"{frame.get('title')}\"")
                    elif ftype == "advisory":
                        print(f"-> [advisory] {frame.get('advisory')}")
                    elif ftype == "clarification":
                        print(f"-> [clarification] question=\"{frame.get('question')}\"")
                    elif ftype == "error":
                        print(f"-> [error] {frame.get('message')}")
                    elif ftype == "done":
                        print(f"-> [done] status={frame.get('status')} run_id={rid}")
                    else:
                        print(f"-> [{ftype}] {frame}")
                except Exception as e:
                    print(f"[raw] {line} (parse err: {e})")

    print("\n" + "=" * 70)
    print(f"CAPTURED RUN_ID: {captured_run_id}")
    print("=" * 70)

    if captured_run_id:
        print("\n=== RUN STATE (from Redis) ===")
        run = get_run(captured_run_id)
        if run:
            print(run.model_dump_json(indent=2))
        else:
            print(f"Run {captured_run_id} not found in Redis")

        print("\n=== RAW EVIDENCE PACK (from Redis) ===")
        pack = get_pack(captured_run_id)
        if pack:
            print(json.dumps(pack, indent=2))
        else:
            print(f"Pack for {captured_run_id} not found in Redis")
            
    return captured_run_id

if __name__ == "__main__":
    asset = sys.argv[1] if len(sys.argv) > 1 else "FS-17"
    msg = sys.argv[2] if len(sys.argv) > 2 else "What happened for the last two hours?"
    run_query(msg, selected_asset=asset)
