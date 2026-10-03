"""
Automated 15-Query Compact Regression Suite against FastAPI Agent Service (http://127.0.0.1:8091).
Executes all 6 Tiers from Migration Report Audit.
"""

import asyncio
import json
import time
import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8091"

async def run_query(client: httpx.AsyncClient, payload: dict) -> tuple[list[dict], float, int]:
    t0 = time.perf_counter()
    resp = await client.post(f"{BASE_URL}/query", json=payload, timeout=30.0)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    status_code = resp.status_code
    frames = []
    for line in resp.text.splitlines():
        line = line.strip()
        if line:
            try:
                frames.append(json.loads(line))
            except Exception:
                frames.append({"raw": line})
    return frames, latency_ms, status_code


async def main():
    print("=" * 80)
    print("COMPACT REGRESSION SUITE — 15 QUERIES AGAINST http://127.0.0.1:8091")
    print("=" * 80)
    
    passed_tests = 0
    failed_tests = 0

    async with httpx.AsyncClient() as client:
        # Pre-check: Health & Capabilities
        print("\n[PRE-CHECK] Checking Service Health...")
        h_resp = await client.get(f"{BASE_URL}/health")
        assert h_resp.status_code == 200, f"Health check failed: {h_resp.text}"
        print(f"  ✓ Health Status: {h_resp.json()}")

        # ---------------------------------------------------------------------
        # Tier 1 — Well normalization (Q1, Q2)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 1] Well Normalization (Q1, Q2) ---")
        
        # Q1: Padded form
        q1_payload = {"session_id": "smoke-1", "message": "Current status", "well_id": "FS-017"}
        q1_frames, q1_lat, q1_st = await run_query(client, q1_payload)
        q1_done = next((f for f in q1_frames if f.get("type") == "done"), {})
        q1_ok = q1_st == 200 and q1_done.get("status") in ("OK", "COMPLETED", "completed")
        print(f"  Q1 (Padded 'FS-017'): status_code={q1_st}, done.status={q1_done.get('status')} ({q1_lat:.1f}ms)")
        if q1_ok:
            passed_tests += 1
        else:
            failed_tests += 1

        # Q2: Unpadded form
        q2_payload = {"session_id": "smoke-2", "message": "Current status", "well_id": "FS-17"}
        q2_frames, q2_lat, q2_st = await run_query(client, q2_payload)
        q2_done = next((f for f in q2_frames if f.get("type") == "done"), {})
        q2_ok = q2_st == 200 and q2_done.get("status") in ("OK", "COMPLETED", "completed")
        print(f"  Q2 (Unpadded 'FS-17'): status_code={q2_st}, done.status={q2_done.get('status')} ({q2_lat:.1f}ms)")
        if q2_ok:
            passed_tests += 1
        else:
            failed_tests += 1

        # ---------------------------------------------------------------------
        # Tier 2 — Extended QueryRequest (Q3, Q4)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 2] Extended QueryRequest & Precedence (Q3, Q4) ---")
        
        # Q3: Full payload shape
        q3_payload = {
            "session_id": "smoke-3",
            "message": "What is gas lock?",
            "well_id": "FS-017",
            "asset_id": "ASSET-FS-017",
            "page_route": "/wells/FS-017",
            "time_range": "24h",
            "ui_context": {"active_tab": "Overview"}
        }
        q3_frames, q3_lat, q3_st = await run_query(client, q3_payload)
        q3_done = next((f for f in q3_frames if f.get("type") == "done"), {})
        q3_ok = q3_st == 200 and not any(f.get("type") == "error" and f.get("code") == "422" for f in q3_frames)
        print(f"  Q3 (Full Dashboard Payload): status_code={q3_st}, done.status={q3_done.get('status')} ({q3_lat:.1f}ms)")
        if q3_ok:
            passed_tests += 1
        else:
            failed_tests += 1

        # Q4: Message precedence over payload
        q4_payload = {"session_id": "smoke-4", "message": "Status of FS-016", "well_id": "FS-017"}
        q4_frames, q4_lat, q4_st = await run_query(client, q4_payload)
        q4_text = " ".join(f.get("delta", "") for f in q4_frames if f.get("type") == "text_delta")
        q4_done = next((f for f in q4_frames if f.get("type") == "done"), {})
        q4_has_016 = "FS-016" in q4_text or "FS-16" in q4_text or "016" in str(q4_frames)
        print(f"  Q4 (Precedence msg 'FS-016' > payload 'FS-017'): references FS-016={q4_has_016}, done.status={q4_done.get('status')} ({q4_lat:.1f}ms)")
        if q4_has_016 and q4_st == 200:
            passed_tests += 1
        else:
            failed_tests += 1

        # ---------------------------------------------------------------------
        # Tier 3 — Card IDs and Payloads (Q5, Q6, Q7, Q8)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 3] Card IDs & Omission Rules (Q5, Q6, Q7, Q8) ---")
        
        # Q5: OP01 visual cards
        q5_payload = {"session_id": "smoke-5", "message": "Status of FS-017", "well_id": "FS-017"}
        q5_frames, q5_lat, q5_st = await run_query(client, q5_payload)
        q5_vis = next((f for f in q5_frames if f.get("type") == "visual"), {})
        q5_cards = q5_vis.get("card_ids") or []
        print(f"  Q5 (OP01 Status Cards): visual cards emitted={q5_cards} ({q5_lat:.1f}ms)")
        if q5_cards and any("smart_fault" in c or "subsystem" in c or "ribbon" in c or "health" in c for c in q5_cards):
            passed_tests += 1
        else:
            failed_tests += 1

        # Q6: OP03 fault diagnosis
        q6_payload = {"session_id": "smoke-6", "message": "Why did FS-017 trip?", "well_id": "FS-017"}
        q6_frames, q6_lat, q6_st = await run_query(client, q6_payload)
        q6_adv = next((f for f in q6_frames if f.get("type") == "advisory"), {})
        q6_vis = next((f for f in q6_frames if f.get("type") == "visual"), {})
        print(f"  Q6 (OP03 Diagnostic): advisory frame present={bool(q6_adv)}, visual cards={q6_vis.get('card_ids', [])} ({q6_lat:.1f}ms)")
        if bool(q6_adv):
            passed_tests += 1
        else:
            failed_tests += 1

        # Q7: OP04 health assessment
        q7_payload = {"session_id": "smoke-7", "message": "How healthy is FS-017?", "well_id": "FS-017"}
        q7_frames, q7_lat, q7_st = await run_query(client, q7_payload)
        q7_vis = next((f for f in q7_frames if f.get("type") == "visual"), {})
        print(f"  Q7 (OP04 Health Assessment): visual cards={q7_vis.get('card_ids', [])} ({q7_lat:.1f}ms)")
        if q7_vis.get("card_ids"):
            passed_tests += 1
        else:
            failed_tests += 1

        # Q8: Missing well omission rule
        q8_payload = {"session_id": "smoke-8", "message": "Status of FAKE-999", "well_id": "FAKE-999"}
        q8_frames, q8_lat, q8_st = await run_query(client, q8_payload)
        q8_done = next((f for f in q8_frames if f.get("type") == "done"), {})
        q8_err = next((f for f in q8_frames if f.get("type") == "error"), {})
        print(f"  Q8 (Missing Well FAKE-999): done.status={q8_done.get('status')}, error_code={q8_err.get('code')} ({q8_lat:.1f}ms)")
        if q8_done.get("status") in ("INSUFFICIENT", "ERROR", "PAUSED") or q8_err:
            passed_tests += 1
        else:
            failed_tests += 1

        # ---------------------------------------------------------------------
        # Tier 4 — Advisory Structured Fields (Q9, Q10)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 4] Structured Advisory Fields & Clean Delta (Q9, Q10) ---")
        
        # Q9: Structured fields in advisory
        adv_obj = q6_adv.get("advisory", {}) if q6_adv else {}
        has_pw = "provenance_warnings" in adv_obj and isinstance(adv_obj["provenance_warnings"], list)
        has_ds = "degraded_sources" in adv_obj and isinstance(adv_obj["degraded_sources"], list)
        print(f"  Q9 (Advisory Structured Arrays): provenance_warnings exists={has_pw}, degraded_sources exists={has_ds}")
        if has_pw and has_ds:
            passed_tests += 1
        else:
            failed_tests += 1

        # Q10: No raw [WARNING: in text delta
        q6_delta_text = "".join(f.get("delta", "") for f in q6_frames if f.get("type") == "text_delta")
        has_raw_warning = "[WARNING:" in q6_delta_text
        print(f"  Q10 (Zero [WARNING: in text_delta): raw warning tag present={has_raw_warning}")
        if not has_raw_warning:
            passed_tests += 1
        else:
            failed_tests += 1

        # ---------------------------------------------------------------------
        # Tier 5 — Core Pipeline Sanity (Q11, Q12, Q13)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 5] Core Route Sanity (Q11, Q12, Q13) ---")
        
        # Q11: SIMPLE route (OP06)
        q11_payload = {"session_id": "smoke-11", "message": "What is PIP?"}
        q11_frames, q11_lat, q11_st = await run_query(client, q11_payload)
        q11_done = next((f for f in q11_frames if f.get("type") == "done"), {})
        print(f"  Q11 (SIMPLE Route OP06): status_code={q11_st}, done.status={q11_done.get('status')} ({q11_lat:.1f}ms)")
        if q11_st == 200 and q11_done.get("status") in ("OK", "COMPLETED", "completed"):
            passed_tests += 1
        else:
            failed_tests += 1

        # Q12: Follow-up route
        q12_payload = {"session_id": "smoke-11", "message": "What data did you use?"}
        q12_frames, q12_lat, q12_st = await run_query(client, q12_payload)
        q12_done = next((f for f in q12_frames if f.get("type") == "done"), {})
        print(f"  Q12 (FOLLOW_UP Route): status_code={q12_st}, done.status={q12_done.get('status')} ({q12_lat:.1f}ms)")
        if q12_st == 200 and q12_done.get("status") in ("OK", "COMPLETED", "completed"):
            passed_tests += 1
        else:
            failed_tests += 1

        # Q13: CLARIFY route (ambiguous without well)
        q13_payload = {"session_id": "smoke-13", "message": "Explain that"}
        q13_frames, q13_lat, q13_st = await run_query(client, q13_payload)
        q13_done = next((f for f in q13_frames if f.get("type") == "done"), {})
        q13_clarify = next((f for f in q13_frames if f.get("type") == "clarification"), {})
        print(f"  Q13 (CLARIFY Ambiguous Query): done.status={q13_done.get('status')}, clarify_frame={bool(q13_clarify)} ({q13_lat:.1f}ms)")
        if q13_done.get("status") == "PAUSED" or bool(q13_clarify):
            passed_tests += 1
        else:
            failed_tests += 1

        # ---------------------------------------------------------------------
        # Tier 6 — One Full Diagnostics (Q14, Q15)
        # ---------------------------------------------------------------------
        print("\n--- [TIER 6] Full Diagnostics & History (Q14, Q15) ---")
        
        # Q14: Full OP03 with dashboard payload
        q14_payload = {
            "session_id": "smoke-14",
            "message": "Diagnose FS-017",
            "well_id": "FS-017",
            "time_range": "24h"
        }
        q14_frames, q14_lat, q14_st = await run_query(client, q14_payload)
        q14_adv = next((f for f in q14_frames if f.get("type") == "advisory"), {})
        q14_vis = next((f for f in q14_frames if f.get("type") == "visual"), {})
        q14_done = next((f for f in q14_frames if f.get("type") == "done"), {})
        print(f"  Q14 (Full OP03 Diagnostic): advisory={bool(q14_adv)}, visual_cards={q14_vis.get('card_ids', [])}, done.status={q14_done.get('status')} ({q14_lat:.1f}ms)")
        if bool(q14_adv) and q14_st == 200:
            passed_tests += 1
        else:
            failed_tests += 1

        # Q15: OP14 History
        q15_payload = {"session_id": "smoke-15", "message": "FS-017 history for last 2 hours", "well_id": "FS-017"}
        q15_frames, q15_lat, q15_st = await run_query(client, q15_payload)
        q15_done = next((f for f in q15_frames if f.get("type") == "done"), {})
        print(f"  Q15 (OP14 History): status_code={q15_st}, done.status={q15_done.get('status')} ({q15_lat:.1f}ms)")
        if q15_st == 200 and q15_done.get("status") in ("OK", "COMPLETED", "completed"):
            passed_tests += 1
        else:
            failed_tests += 1

    print("\n" + "=" * 80)
    print(f"TOTAL TESTS: 15 | PASSED: {passed_tests} | FAILED: {failed_tests}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
