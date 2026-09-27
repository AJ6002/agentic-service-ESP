import httpx
import json
import os
from datetime import datetime, timedelta, timezone

base = "http://192.168.1.184:8090"
wells = [
    "FS-17", "FS-21", "FS-91", "FS-96", "FS-06",
    "FS-121", "FS-129", "FNW-01", "FNW-06",
    "FWS-02", "FWS-04", "FWS-06", "ULFA-5"
]

lines = []
lines.append("=" * 80)
lines.append("ESP APM HISTORIAN API CURL VERIFICATION OUTPUT")
lines.append(f"Executed at (UTC): {datetime.now(timezone.utc).isoformat()}")
lines.append(f"Server Base URL: {base}")
lines.append("=" * 80 + "\n")

with httpx.Client(timeout=30.0) as client:
    # 1. Latest (live data, no hardcode)
    url1 = f"{base}/api/historian/latest?well_id=FS-17"
    lines.append("#" * 80)
    lines.append("1. LATEST (live data, no hardcode)")
    lines.append(f"Command: curl -s \"{url1}\"")
    lines.append("#" * 80)
    try:
        r1 = client.get(url1)
        lines.append(f"HTTP Status: {r1.status_code}")
        lines.append(json.dumps(r1.json(), indent=2))
    except Exception as e:
        lines.append(f"Error: {e}")
    lines.append("\n")

    # 2. Coverage for FS-17 (Step 1)
    url2 = f"{base}/api/historian/coverage?well_id=FS-17"
    lines.append("#" * 80)
    lines.append("2. WINDOW - Step 1: get actual data range")
    lines.append(f"Command: curl -s \"{url2}\"")
    lines.append("#" * 80)
    cov_data = {}
    try:
        r2 = client.get(url2)
        lines.append(f"HTTP Status: {r2.status_code}")
        cov_data = r2.json()
        lines.append(json.dumps(cov_data, indent=2))
    except Exception as e:
        lines.append(f"Error: {e}")
    lines.append("\n")

    # 3. Window using system time (now - 2min)
    now_dt = datetime.now(timezone.utc)
    start_now = (now_dt - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    signals = "amp_a,freq_hz,motor_temp_c,int_prs_psi,disch_prs_psi,vibration_g,vfd_sts"
    url3_now = f"{base}/api/historian/window?well_id=FS-17&start={start_now}&end={end_now}&signals={signals}"

    lines.append("#" * 80)
    lines.append("3. WINDOW - Step 2 (Option A: Using Current System Time minus 2min)")
    lines.append(f"START: {start_now}")
    lines.append(f"END:   {end_now}")
    lines.append(f"Command: curl -s \"{url3_now}\"")
    lines.append("#" * 80)
    try:
        r3_now = client.get(url3_now)
        lines.append(f"HTTP Status: {r3_now.status_code}")
        lines.append(json.dumps(r3_now.json(), indent=2))
    except Exception as e:
        lines.append(f"Error: {e}")
    lines.append("\n")

    # 3b. Window using server's own last_ts/latest_ts minus 2min
    latest_ts_str = (cov_data.get("last_ts") or cov_data.get("latest_ts")) if isinstance(cov_data, dict) else None
    if latest_ts_str:
        try:
            clean_ts = latest_ts_str.replace("Z", "+00:00")
            server_latest_dt = datetime.fromisoformat(clean_ts)
            server_start_dt = server_latest_dt - timedelta(minutes=2)
            s_start = server_start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            s_end = server_latest_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            url3_server = f"{base}/api/historian/window?well_id=FS-17&start={s_start}&end={s_end}&signals={signals}"

            lines.append("#" * 80)
            lines.append("3b. WINDOW - Step 2 (Option B: Using Server's Own latest_ts minus 2min)")
            lines.append(f"START: {s_start}")
            lines.append(f"END:   {s_end}")
            lines.append(f"Command: curl -s \"{url3_server}\"")
            lines.append("#" * 80)
            r3_server = client.get(url3_server)
            lines.append(f"HTTP Status: {r3_server.status_code}")
            lines.append(json.dumps(r3_server.json(), indent=2))
            lines.append("\n")
        except Exception as e:
            lines.append(f"Error parsing server latest_ts: {e}\n")

    # 4. All wells coverage
    lines.append("#" * 80)
    lines.append("4. ALL WELLS COVERAGE (match SQLite table)")
    lines.append(f"Command: for w in {' '.join(wells)}; do curl -s \"{base}/api/historian/coverage?well_id=$w\"; done")
    lines.append("#" * 80)
    for w in wells:
        lines.append(f"=== {w} ===")
        url_w = f"{base}/api/historian/coverage?well_id={w}"
        try:
            rw = client.get(url_w)
            lines.append(f"HTTP Status: {rw.status_code}")
            lines.append(json.dumps(rw.json(), indent=2))
        except Exception as e:
            lines.append(f"Error: {e}")
        lines.append("")

content = "\n".join(lines)
out_file = r"x:\TAS\ESP_APM_server\historian_curl_output.txt"
with open(out_file, "w", encoding="utf-8") as f:
    f.write(content)

# Also write to agent_service for easy access
out_file_agent = r"x:\TAS\ESP_APM_server\agent_service\historian_curl_output.txt"
with open(out_file_agent, "w", encoding="utf-8") as f:
    f.write(content)

print(f"SUCCESS: Output written to:\n  - {out_file}\n  - {out_file_agent}")
