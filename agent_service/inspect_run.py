import json
import sys
from app.stores.run_store import get_run, get_pack

# Get RUN_ID from command line argument if provided, else use default
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "R-d33375c3"

# 1. View the Run State
run = get_run(RUN_ID)
print("=== RUN STATE ===")
print(run.model_dump_json(indent=2) if run else f"Run '{RUN_ID}' not found in Redis")

# 2. View the Complete Evidence Pack (Every single raw API payload)
pack = get_pack(RUN_ID)
print("\n=== RAW EVIDENCE PACK (UPSTREAM APIS) ===")
print(json.dumps(pack, indent=2) if pack else f"Pack for '{RUN_ID}' not found in Redis")
