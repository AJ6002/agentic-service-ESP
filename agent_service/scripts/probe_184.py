"""
Server 184 Endpoint Probe Script.
Hits all 8 domains on Server 184 (:8090), records HTTP status, latency,
and response shape, and saves the baseline report to data/probe_184_report.json.
"""

import json
import os
import sys
import time
from pathlib import Path
import httpx

SERVER184_BASE_URL = os.getenv("SERVER184_BASE_URL", "http://192.168.1.184:8090")
KB_SERVICE_BASE_URL = os.getenv("KB_SERVICE_BASE_URL", "http://192.168.1.184:8085")

PROBE_ENDPOINTS = [
    # 1. Historian Domain
    {"domain": "historian", "name": "health", "method": "GET", "path": "/historian/health"},
    {"domain": "historian", "name": "window", "method": "GET", "path": "/historian/window?well_id=FS-17&start=2026-08-01T00:00:00Z&end=2026-08-30T00:00:00Z&limit=10"},
    {"domain": "historian", "name": "latest", "method": "GET", "path": "/historian/latest?well_id=FS-17"},
    {"domain": "historian", "name": "coverage", "method": "GET", "path": "/historian/coverage?well_id=FS-17"},

    # 2. Live Telemetry Domain
    {"domain": "live", "name": "health", "method": "GET", "path": "/live/health"},
    {"domain": "live", "name": "telemetry", "method": "GET", "path": "/live/telemetry/FS-17"},
    {"domain": "live", "name": "asset", "method": "GET", "path": "/live/asset/FS-17"},
    {"domain": "live", "name": "wells", "method": "GET", "path": "/live/wells"},
    {"domain": "live", "name": "vfm", "method": "GET", "path": "/live/vfm/FS-17"},

    # 3. Events Domain
    {"domain": "events", "name": "health", "method": "GET", "path": "/events/health"},
    {"domain": "events", "name": "timeline", "method": "GET", "path": "/events/timeline?well_id=FS-17"},
    {"domain": "events", "name": "trips", "method": "GET", "path": "/events/trips?well_id=FS-17"},

    # 4. ML Domain
    # NOTE: /ml/health (domain liveness) and /ml/health/{well} (per-well
    # composite health index) are DIFFERENT endpoints. get_ml_results uses
    # the per-well one, so both must be probed.
    {"domain": "ml", "name": "domain_health", "method": "GET", "path": "/ml/health"},
    {"domain": "ml", "name": "well_health", "method": "GET", "path": "/ml/health/FS-17"},
    {"domain": "ml", "name": "fault", "method": "GET", "path": "/ml/fault/FS-17"},
    {"domain": "ml", "name": "anomaly", "method": "GET", "path": "/ml/anomaly/FS-17"},
    {"domain": "ml", "name": "degradation", "method": "GET", "path": "/ml/degradation/FS-17"},
    {"domain": "ml", "name": "explain", "method": "GET", "path": "/ml/explain/FS-17?output=fault"},

    # 5. KPI Domain
    {"domain": "kpi", "name": "well_kpi", "method": "GET", "path": "/kpi/FS-17"},

    # 6. Cards Domain
    {"domain": "cards", "name": "catalog", "method": "GET", "path": "/cards/catalog"},
    {"domain": "cards", "name": "health_card", "method": "GET", "path": "/cards/FS-17/health-score"},
]

# 7. Knowledge Base — SEPARATE service, own base URL (:8085, not :8090).
# search/graph-trace are POST with a JSON body; everything else is GET.
KB_PROBE_ENDPOINTS = [
    {"domain": "kb", "name": "health", "method": "GET", "path": "/health", "body": None},
    {"domain": "kb", "name": "search", "method": "POST", "path": "/api/kb/search",
     "body": {"query": "underload trip fluid starvation current drop", "top_k": 3}},
    {"domain": "kb", "name": "faults", "method": "GET", "path": "/api/kb/faults", "body": None},
    {"domain": "kb", "name": "fault_by_id", "method": "GET", "path": "/api/kb/faults/MOTOR_OVERHEATING", "body": None},
    {"domain": "kb", "name": "standard_by_id", "method": "GET", "path": "/api/kb/standards/API_RP_11S", "body": None},
]


def _probe_one(client: httpx.Client, base_url: str, ep: dict) -> dict:
    url = f"{base_url}{ep['path']}"
    method = ep.get("method", "GET")
    body = ep.get("body")
    t0 = time.time()
    entry = {"domain": ep["domain"], "name": ep["name"], "path": ep["path"], "url": url, "method": method}
    try:
        resp = client.post(url, json=body) if method == "POST" else client.get(url)
        latency_ms = round((time.time() - t0) * 1000, 2)
        entry["status_code"] = resp.status_code
        entry["latency_ms"] = latency_ms
        try:
            resp_body = resp.json()
            entry["is_json"] = True
            entry["sample_keys"] = list(resp_body.keys()) if isinstance(resp_body, dict) else f"list_len_{len(resp_body)}"
            entry["body_preview"] = resp_body
        except Exception:
            entry["is_json"] = False
            entry["body_preview"] = resp.text[:200]
        status_tag = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
        print(f"[{entry['domain']:<9}] {ep['name']:<15} -> {status_tag:<10} ({latency_ms:>6.1f} ms) | keys: {entry.get('sample_keys')}")
    except Exception as ex:
        latency_ms = round((time.time() - t0) * 1000, 2)
        entry["status_code"] = 0
        entry["latency_ms"] = latency_ms
        entry["error"] = f"{type(ex).__name__}: {str(ex)}"
        print(f"[{entry['domain']:<9}] {ep['name']:<15} -> FAILED     ({latency_ms:>6.1f} ms) | {entry['error']}")
    return entry


def run_probe():
    base_url = SERVER184_BASE_URL.rstrip("/")
    kb_base_url = KB_SERVICE_BASE_URL.rstrip("/")
    print(f"================================================================")
    print(f"Probing Server 184 at: {base_url}")
    print(f"Probing KB Service at: {kb_base_url}")
    print(f"================================================================")

    results = []
    with httpx.Client(timeout=5.0) as client:
        for ep in PROBE_ENDPOINTS:
            results.append(_probe_one(client, base_url, ep))
        print(f"----------------------------------------------------------------")
        for ep in KB_PROBE_ENDPOINTS:
            results.append(_probe_one(client, kb_base_url, ep))

    # Save results to data/probe_184_report.json
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "probe_184_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "server_url": base_url,
                "kb_service_url": kb_base_url,
                "timestamp": time.time(),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"================================================================")
    print(f"Probe complete. Report saved to: {report_file}")
    print(f"Total probed: {len(results)} | Successful (200): {sum(1 for r in results if r.get('status_code') == 200)}")
    print(f"================================================================")
    return results


if __name__ == "__main__":
    run_probe()
