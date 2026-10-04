import sys
import os
import json
import requests
import subprocess

sys.path.insert(0, os.path.abspath("agent_service"))
from app.stores.redis_client import get_redis_client

out_file = "reports/IDENTITY_ROUTE_SHORT_VERIFICATION_RAW_OUTPUT.txt"
lines = []

def log(s=""):
    lines.append(s)

log("================================================================================")
log("IDENTITY ROUTE INDEPENDENT VERIFICATION — FULL RAW OUTPUT")
log("================================================================================")
log()

# ---------------------------------------------------------
# STEP 1: RAW CURL / QUERY RESPONSES
# ---------------------------------------------------------
log("================================================================================")
log("STEP 1: THREE QUERIES AGAINST http://127.0.0.1:8091/query (RAW NDJSON STREAMS)")
log("================================================================================")

queries = [
    ("Query 1 (Identity)", "v1", "What are you?"),
    ("Query 2 (Disambiguation / KB)", "v2", "What is gas lock?"),
    ("Query 3 (Regression / Workflow)", "v3", "Why did FS-17 trip?"),
]

for title, sid, msg in queries:
    log(f"\n--- {title} ---")
    log("REQUEST: POST http://127.0.0.1:8091/query")
    log(f"BODY: {json.dumps({'session_id': sid, 'message': msg})}")
    log("RESPONSE (raw NDJSON lines):")
    resp = requests.post("http://127.0.0.1:8091/query", json={"session_id": sid, "message": msg}, stream=True)
    for raw_l in resp.iter_lines():
        if raw_l:
            decoded = raw_l.decode("utf-8") if isinstance(raw_l, bytes) else raw_l
            log(decoded)

# ---------------------------------------------------------
# STEP 2: TEST IDENTITY ROUTE VERBOSE
# ---------------------------------------------------------
log("\n================================================================================")
log("STEP 2: PYTEST agent_service/tests/test_identity_route.py -v (RAW OUTPUT)")
log("================================================================================")
res2 = subprocess.run([r"a:\TAS-AI\ESP\.venv\Scripts\python.exe", "-m", "pytest", "agent_service/tests/test_identity_route.py", "-v"], capture_output=True, text=True)
log(res2.stdout)
if res2.stderr:
    log("STDERR:\n" + res2.stderr)

# ---------------------------------------------------------
# STEP 3: ROUTER DEFINITIONAL REGRESSION VERBOSE
# ---------------------------------------------------------
log("\n================================================================================")
log("STEP 3: PYTEST agent_service/tests/test_router_definitional_regression.py -v (RAW OUTPUT)")
log("================================================================================")
res3 = subprocess.run([r"a:\TAS-AI\ESP\.venv\Scripts\python.exe", "-m", "pytest", "agent_service/tests/test_router_definitional_regression.py", "-v"], capture_output=True, text=True)
log(res3.stdout)
if res3.stderr:
    log("STDERR:\n" + res3.stderr)

# ---------------------------------------------------------
# STEP 4: REDIS RUN STORAGE KEYS BEFORE & AFTER
# ---------------------------------------------------------
log("\n================================================================================")
log("STEP 4: REDIS STORAGE KEYS BEFORE & AFTER IDENTITY QUERY")
log("================================================================================")
r = get_redis_client()
before_runs = sorted(list(r.keys("esp:run:*")))
log(f"KEYS esp:run:* BEFORE identity query (count={len(before_runs)}):")
for k in before_runs[-10:]:
    log(f"  {k}")
if len(before_runs) > 10:
    log(f"  ... and {len(before_runs)-10} older runs")

log("\nFIRING IDENTITY QUERY: POST /query {\"session_id\": \"redis-raw-check\", \"message\": \"What are you?\"}")
r_id = requests.post("http://127.0.0.1:8091/query", json={"session_id": "redis-raw-check", "message": "What are you?"})
after_runs = sorted(list(r.keys("esp:run:*")))
new_runs = set(after_runs) - set(before_runs)
session_keys = sorted(list(r.keys("esp:session:redis-raw-check*")))

log(f"\nKEYS esp:run:* AFTER identity query (count={len(after_runs)}):")
log(f"NEW esp:run:* KEYS CREATED: {list(new_runs)}")
log(f"SESSION KEYS FOR redis-raw-check: {session_keys}")
log(f"ZERO PIPELINE LEAKAGE CONFIRMED: {len(new_runs) == 0}")

os.makedirs("reports", exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"Successfully wrote full raw output to {out_file}")
