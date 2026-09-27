---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
created_at: 2026-09-27T01:05:00+05:30
title: Steps 1-4 Seal, Verification, and Pre-Phase 5 Quality Assurance Plan
product_contract_source: ce-plan-bootstrap
topic: Pre-Phase 5 Quality Assurance and Retroactive Phase 1 & 4.5 Seals
---

# Steps 1–4 Seal, Verification, and Pre-Phase 5 Quality Assurance Plan

---

## Goal Capsule

- **Objective:** Finalize all remaining pre-Phase 5 verification items: verify HQ4 follow-up routing and widen natural follow-up regex patterns, run and verify the full regression test suite across all 430+ tests, retroactively seal Phase 1 (Gap-Fill pipeline), and seal Phase 4.5 (KB Troubleshooting).
- **Means:** Extend `FOLLOWUP_PATTERNS` in `router.py`, execute multi-turn session validation on HQ3->HQ4, run full regression with zero skips, write and execute acceptance tests for Phase 1 Gap-Fill refetch/replan invariants, and validate Phase 4.5 KB troubleshooting contracts.
- **Execution Profile:** Sequential verification and testing with strict empirical validation.
- **Stop Conditions:** All 4 steps fully verified with passing test evidence; stop before Phase 5 Fleet implementation.

---

## Product Contract

### Summary
The system has resolved 18 distinct bugs across Phases 1 through 4.5. Before proceeding to Phase 5 (Fleet Management), four foundational verification steps must be locked down:
1. Verify HQ4 routing behavior across both standalone and chained sessions, ensuring phrases like "what data did you look at" deterministically route to `FOLLOW_UP`.
2. Confirm the complete test suite (430+ tests) is 100% green with zero unexpected skips.
3. Retroactively seal Phase 1 (Gap-Fill) by validating 1-refetch cap, replan cap enforcement, and pack version incrementation ($v1 \to v2$) on missing sources.
4. Formally seal Phase 4.5 (KB Troubleshooting) by confirming certified SOP generation, zero hallucinated citations, and 5/5 KB regression pass.

### Requirements

- R1. `FOLLOWUP_PATTERNS` must capture conversational data inquiry variants including "what data did you (look at|review|check|rely on|consult)" and "what data was (used|looked at|consulted|reviewed)".
- R2. Chained multi-turn execution of HQ3 followed by HQ4 within the same session must execute `FOLLOW_UP` without triggering a fresh gateway fetch or LLM workflow re-execution ($HTTP = 0, LLM = 0$).
- R3. Full test regression suite across `agent_service/tests/` must pass cleanly ($Pass \ge 430$, $Fail = 0$, $Skip = 0$).
- R4. Phase 1 Gap-Fill seal must prove:
  - When a required data source is missing/degraded, Gap-Fill triggers exactly one targeted refetch.
  - Replan cap is strictly enforced ($\text{replan\_count} \le 1$).
  - Evidence pack version increments from $v1 \to v2$.
  - Failure to fill missing required evidence gracefully yields `INSUFFICIENT` with clear error semantics.
- R5. Phase 4.5 KB Troubleshooting seal must prove:
  - Troubleshooting queries yield structured SOP and verification steps grounded in verified knowledge base chunks.
  - Zero unverified manual citations (e.g., `[Baker Hughes FusionPro Manual...]`, `[NFPA 70E...]`) in streamed outputs.
  - Offline KB gracefully falls back without crashing the diagnostic workflow.

---

## Planning Contract

### Key Technical Decisions

- KTD1. **Follow-up Regex Widening (session-settled: user-directed):** Broaden `FOLLOWUP_PATTERNS` to support multi-word natural phrases ("what data did you look at", "how did you figure that out", "what information did you base that on") so conversational phrasing does not inadvertently trigger workflow re-execution.
- KTD2. **Session Context Isolation vs Chaining:** Clarify in test artifacts that standalone HQ4 (Turn 1, no prior) correctly yields `ANALYSIS_EXPIRED` (or clarify if ambiguous), whereas chained HQ4 (Turn 2 after HQ3) accesses the sealed pack with zero HTTP calls.
- KTD3. **Phase 1 Gap-Fill Verification Harness:** Leverage `MockTransport` and synthesized partial packs to deterministically test single-refetch limits, replan gates, and pack version mutations in `agent_service/tests/acceptance/phase1/test_gapfill_seal.py`.
- KTD4. **Pre-Phase 5 Gate Boundary:** Strict stop condition after Step 4; no Phase 5 tool registration or fleet models created until Steps 1-4 reports are complete.

---

## Implementation Units

### U1. Verify HQ4 & Widen Conversational Follow-up Patterns
- **Goal:** Widen `FOLLOWUP_PATTERNS` in `agent_service/app/routing/router.py` to match conversational data inquiries, and test chained execution of HQ3 $\to$ HQ4 in a shared session.
- **Files:**
  - `agent_service/app/routing/router.py`
  - `agent_service/tests/test_router_followup_boundary.py`
  - `agent_service/tests/acceptance/phase4/test_followup_happy_path.py`
- **Patterns:** Regex extension with unit tests asserting deterministic `FOLLOW_UP` classification.
- **Test Scenarios:**
  - `test_conversational_data_inquiry_routes_to_follow_up`: "What data did you look at to figure that out?" routes to `FOLLOW_UP`.
  - `test_chained_hq3_then_hq4_zero_refetch`: Turn 1 runs HQ3 diagnostic, Turn 2 runs HQ4 on same session ID; verify Turn 2 produces zero HTTP calls and answers from prior pack.

### U2. Full Pytest Suite Regression & Zero-Skip Verification
- **Goal:** Run the full 430+ test regression suite across unit, integration, and acceptance directories; verify zero failures and zero unmanaged skips.
- **Files:**
  - `agent_service/tests/`
- **Patterns:** Subprocess test execution with short tracebacks.
- **Test Scenarios:**
  - Full suite execution: `pytest agent_service/tests/ -q --tb=short`.
  - Assert total passed $\ge 430$, total failed $= 0$.

### U3. Phase 1 Gap-Fill Retroactive Seal
- **Goal:** Create formal acceptance tests validating the Gap-Fill pipeline contracts (single refetch, replan cap, pack version increment $v1 \to v2$, graceful degradation).
- **Files:**
  - `agent_service/tests/acceptance/phase1/test_gapfill_seal.py`
  - `agent_service/app/workflow/gapfill.py`
- **Patterns:** Mock adapter injection simulating missing mandatory telemetry, asserting retry count and pack metadata.
- **Test Scenarios:**
  - `test_gapfill_single_refetch_success`: Missing required signal triggers exactly 1 refetch attempt; pack version becomes $v2$.
  - `test_gapfill_replan_cap_enforced`: Second failure does not trigger recursive loop; terminates with `INSUFFICIENT`.
  - `test_gapfill_pack_versioning`: Verify `run.evidence_pack.version` increments appropriately.

### U4. Phase 4.5 KB Troubleshooting Seal
- **Goal:** Formally execute and record the Phase 4.5 acceptance test suite for knowledge-grounded troubleshooting.
- **Files:**
  - `agent_service/tests/acceptance/phase4_5/test_kb_troubleshooting.py`
- **Patterns:** End-to-end integration test with live/mock KB assertions.
- **Test Scenarios:**
  - `test_ac45_1_troubleshoot_well_routes_to_op03`: "Troubleshoot FS-17" routes to OP03.
  - `test_ac45_5_e2e_troubleshoot_advisory_includes_cited_steps`: Advisory contains cited troubleshooting steps.
  - `test_ac45_6_kb_down_renders_without_troubleshooting_steps`: Graceful degradation on KB timeout/error.

---

## Verification Contract

| Step | Scope | Command / Validation | Success Threshold |
| :--- | :--- | :--- | :--- |
| **Step 1** | Follow-up Router & Chained HQ4 | `pytest agent_service/tests/test_router_followup_boundary.py -k "data"` | 100% Pass |
| **Step 2** | Full Repo Regression | `pytest agent_service/tests/ -q --tb=short` | $\ge 430$ Pass, 0 Fail |
| **Step 3** | Phase 1 Gap-Fill Seal | `pytest agent_service/tests/acceptance/phase1/` | 100% Pass |
| **Step 4** | Phase 4.5 KB Troubleshooting | `pytest agent_service/tests/acceptance/phase4_5/` | 100% Pass |

---

## Definition of Done

1. HQ4 routing verified: "What data did you look at..." matches `FOLLOWUP_PATTERNS`.
2. Chained HQ3 $\to$ HQ4 verified in a single session with zero HTTP gateway calls on Turn 2.
3. Full regression suite passes cleanly across all 430+ tests.
4. Phase 1 Gap-Fill acceptance suite created and passing (single refetch, replan cap, $v1 \to v2$ pack versioning).
5. Phase 4.5 KB Troubleshooting acceptance suite confirmed 100% green.
6. Execution halts before Step 5 (Phase 5 Fleet).
