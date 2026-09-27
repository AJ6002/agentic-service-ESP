---
title: "ESP APM Semantic Integrity: Four Bug Fixes - Plan"
type: fix
date: 2026-09-26
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
origin: FOUR_PROBLEMS_DIAGNOSTIC_REPORT.txt
---

# ESP APM Semantic Integrity: Four Bug Fixes - Plan

---

## Goal Capsule

**Objective:** The ESP APM Agent Service produces zero self-contradicting assessments, routes empty-session follow-ups to ANALYSIS_EXPIRED, and includes no unverified numbers or steps anywhere in the user-facing response.

**Means:** Targeted deterministic fixes in kpi_alarm_check.py, xai.py, router.py, runner.py, followup_handler.py, and citation_check.py, with test suite hardening to prevent Redis-state masking of future regressions. (KTD1, KTD2, KTD3, KTD4)

**Stop conditions:**
- All 4 semantic regressions pass with fresh session UUIDs.
- Contradiction assertions for Q4, Q10, Q18, Q15, Q20 are automated and deterministic.
- test_followup_boundary is isolated so Redis state cannot mask the bug again.

---

## Product Contract

### Summary

The 20/20 transport-integrity test run exposed four semantic integrity failures. The well-state assessment can claim a producing well is not producing. The decline-RCA can call a stable well declining. A follow-up on a fresh session asks which well instead of returning ANALYSIS_EXPIRED. Unverified numbers and uncited troubleshooting steps appear in the final response despite strip attempts. All four have confirmed causal chains with file-and-line evidence.

### Problem Frame

Root causes per FOUR_PROBLEMS_DIAGNOSTIC_REPORT.txt:

1. Q4 (Problem 1): kpi_alarm_check.py does not evaluate health_score. With oil_rate=399.10 and health_score=44.0, has_critical=False, so the Stage 7a override in runner.py does not fire. The 3B LLM writes not producing when it sees 0 events in the window, regardless of numeric rates.

2. Q10 (Problem 2): xai.py lines 157-160 prepend the stability sentence even when the LLM already wrote a decline sentence. The guard creates, not catches, the contradiction.

3. Q18 (Problem 3): router.py lines 306-317 fire CLARIFY when FOLLOWUP_PATTERNS matches and has_prior=False and turn_count<=1. The prior test passed only because Redis accumulated turn_count=7 on the fixed session ID sess-empty-fup.

4. Q15/Q20 (Problem 4): runner.py appends warning banners echoing unverified numbers and step text verbatim. citation_check.py never inspects advisory.verification_steps, so uncited steps leak through that field.

### Requirements

R1. If oil_rate_bopd > 0 or liquid_rate_bpd > 0, final assessment must not contain not producing or zero production.
R2. If health_score < 50 or alarm_result.has_critical, assessment must not contain operating within normal parameters or equivalent.
R3. For OP02: if production_trend == STABLE, assessment must not contain declining. If DECLINING, must not contain stable or no abnormal decline.
R4. A follow-up query on a session with no prior analysis (fresh UUID) must return status=INSUFFICIENT, code=ANALYSIS_EXPIRED, and emit no ClarificationFrame.
R5. A follow-up on a session with an expired pack must also return ANALYSIS_EXPIRED.
R6. No unverified number may appear in the response body. Sentences containing unverified numbers must be stripped.
R7. No uncited troubleshooting step or verification step may appear anywhere in the final response, including in warning text. advisory.verification_steps must be checked and stripped.
R8. Test isolation: test_followup_boundary must use a freshly generated UUID session ID per test run.

### Scope Boundaries

In scope:
- kpi_alarm_check.py: add health_score alarm rule; add producing-oil semantic label.
- xai.py: replace naive prepend guard for OP02 with contradiction-aware detector.
- router.py: split AMBIGUOUS vs FOLLOWUP guard paths; route FOLLOWUP_PATTERNS always to FOLLOW_UP.
- runner.py / followup_handler.py: strip unverified-number sentences; reformat banners to count-only.
- citation_check.py: extend check to advisory.verification_steps.
- Test suite: add fresh-UUID isolation; add deterministic contradiction assertions.

Deferred to Follow-Up Work:
- narrator_v1.txt prompt engineering for 0-events misreading.
- Upgrading from 3B to larger model.
- End-to-end seal matrix run in CI (separate PR).

Outside scope:
- New objectives, routes, or tool gateway changes.
- Qdrant retrieval or pack sealing changes.

---

## Planning Contract

### Key Technical Decisions

KTD1. Health-score alarm rule added to kpi_alarm_check.py rather than inline in runner.py.
All KPI-derived semantic constraints live in one deterministic gate module. Adding the health_score rule here injects the alarm summary into the narrator prompt before synthesis. (session-settled: user-approved - chosen over inline runner.py check: narrating the alarm to the LLM before synthesis is more effective than post-synthesis detection alone)

KTD2. OP02 guard in xai.py replaced with a contradiction detector, not a prepend guard.
Only prepend when the existing assessment does NOT already state the correct trend. If the LLM text contradicts the deterministic trend signal, strip the contradicting sentence. Deterministic; no second LLM call. (session-settled: user-approved - chosen over LLM re-inference: re-calling the LLM is non-deterministic and brittle)

KTD3. Router guard narrowed: FOLLOWUP_PATTERNS queries always route to FOLLOW_UP; followup_handler.py returns ANALYSIS_EXPIRED when no prior analysis exists.
Remove the router responsibility for the dead-session case. The has_prior + turn_count <= 1 guard is removed from the FOLLOWUP path. (session-settled: user-approved - chosen over router-side ANALYSIS_EXPIRED return: followup_handler already has the correct dead-session gate; routing there is the minimal change)

KTD4. Provenance enforcement: strip, not warn.
Unverified-number sentences stripped from assessment. Warning banners emit count only. Uncited steps stripped from both troubleshooting_steps and verification_steps. Warning text never echoes step content. (session-settled: user-directed - chosen over flag-and-show: user mandate is zero-fabrication; banners echoing unverified content defeat that mandate)

### Assumptions

- check_numeric_provenance returns .unattributed_numbers as a list of raw number strings.
- Sentence-boundary stripping via [.!?]+\s+ split is sufficient for LLM prose assessment text.
- advisory.verification_steps has the same list-of-strings structure as advisory.troubleshooting_steps.

### Sequencing

Phases are independent and individually testable. Implement in order U1 through U7. Phase 4 (U4/U5) benefits from U3 being in place so Q18 test assertions are not polluted by the CLARIFY path.

---

## Implementation Units

### U1. Add health_score and producing-well rules to kpi_alarm_check.py

**Goal:** Ensure health_score < 50 raises CRITICAL alarm; ensure oil_rate > 0 injects correct semantic label so Stage 7a override fires in runner.py.

**Requirements:** R1, R2

**Dependencies:** none

**Files:**
- agent_service/app/synthesis/kpi_alarm_check.py
- agent_service/tests/test_kpi_alarm_check.py

**Approach:**
1. Add health_score CRITICAL rule: lambda v: v < 50.0, label health score < 50 - well is in CRITICAL health band.
2. Add health_score WARN rule: lambda v: 50.0 <= v < 70.0 for DEGRADED band.
3. Add producing-oil semantic label: if oil_rate_bopd > 0.0 (inverse of _is_zero), emit CRITICAL alarm labeled oil is flowing - well is producing; NOT a shut-in. This is an injection into the alarm summary block sent to the narrator prompt, ensuring the LLM cannot write not producing when rates are present.
4. With health_score=44 and oil_rate=399.10, has_critical=True; Stage 7a override fires.

**Test scenarios:**
- health_score=44.0: has_critical=True, label contains CRITICAL health band.
- health_score=65.0: has_high=True, label contains DEGRADED.
- health_score=85.0: no health alarm.
- oil_rate_bopd=399.1: CRITICAL alarm with oil is flowing fires.
- oil_rate_bopd=0.0: no producing-oil alarm (existing _is_zero zero-production alarm fires).
- alarm_summary() contains ASSESSMENT CONSTRAINT block when has_critical=True.

**Verification:** pytest agent_service/tests/test_kpi_alarm_check.py -v


### U2. Replace OP02 prepend guard in xai.py with contradiction-aware fix

**Goal:** Eliminate Q10-style self-contradiction where xai.py prepends a stable sentence to LLM text that already claims declining.

**Requirements:** R3

**Dependencies:** U1

**Files:**
- agent_service/app/synthesis/xai.py
- agent_service/tests/test_xai_guards.py

**Approach:**
1. In the OP02 block (lines 142-160), replace the else-branch with a contradiction detector.
2. If trend == STABLE: scan advisory.assessment for declining-trend sentences (regex matching declin\w+, falling, drop\w+ combined with a rate-number pattern). Strip contradicting sentences using sentence splitter. Prepend stability sentence only if stable/no decline is still absent.
3. If trend == DECLINING: strip any sentence containing stable or no abnormal decline if declining already appears.
4. Sentence splitter: split on [.!?]+\s+ boundaries, filter, rejoin.

**Test scenarios:**
- trend=STABLE, LLM says DECLINING at a rate of 10.00 BPD/day: declining sentence stripped, stable statement present, DECLINING absent.
- trend=STABLE, LLM already says stable: no change.
- trend=STABLE, LLM says neither: stability statement prepended.
- trend=DECLINING, LLM has both stable and declining: stable sentence stripped.
- trend=DECLINING, LLM correctly says declining only: unchanged.

**Verification:** pytest agent_service/tests/test_xai_guards.py -v


### U3. Narrow router follow-up guard to eliminate dead-session CLARIFY hijack

**Goal:** FOLLOWUP_PATTERNS queries on fresh sessions route to FOLLOW_UP (which returns ANALYSIS_EXPIRED) rather than CLARIFY on asset_id.

**Requirements:** R4, R5

**Dependencies:** none

**Files:**
- agent_service/app/routing/router.py
- agent_service/tests/test_router_followup_boundary.py

**Approach:**
1. Split the combined guard (lines 305-317) into two independent checks.
2. Block A - Ambiguous follow-up (AMBIGUOUS_FOLLOWUP_PATTERNS only): keep CLARIFY for not has_prior case. These are pronoun-only queries like Explain that with no output referent.
3. Block B - Explicit follow-up (FOLLOWUP_PATTERNS only): always route to FOLLOW_UP regardless of has_prior or turn_count. Remove the not has_prior and turn_count <= 1 gate from this path.
4. followup_handler.py already returns ANALYSIS_EXPIRED when no analysis_id is found - no changes needed there.

**Test scenarios:**
- Fresh UUID session, Why did you conclude that: status=INSUFFICIENT, code=ANALYSIS_EXPIRED, no ClarificationFrame.
- Session with expired pack (has last_analysis_id), FOLLOWUP_PATTERNS query: ANALYSIS_EXPIRED.
- Session with valid prior analysis, FOLLOWUP_PATTERNS query: routes to FOLLOW_UP, returns advisory narrative.
- Fresh UUID session, Explain that (AMBIGUOUS): still CLARIFY on asset_id.
- All tests use uuid.uuid4().hex as session ID.

**Verification:** pytest agent_service/tests/test_router_followup_boundary.py -v


### U4. Extend citation check to advisory.verification_steps

**Goal:** advisory.verification_steps receives the same citation-check-and-strip enforcement as advisory.troubleshooting_steps.

**Requirements:** R7

**Dependencies:** none

**Files:**
- agent_service/app/synthesis/citation_check.py
- agent_service/app/workflow/runner.py
- agent_service/tests/test_citation_check.py

**Approach:**
1. In check_citation_provenance, add a second pass against advisory.verification_steps using the same per-step citation regex.
2. Add flagged_verification_steps: list[str] to CitationCheckResult dataclass.
3. In runner.py step 8b: after stripping troubleshooting_steps, also filter verification_steps using flagged_verification_steps.
4. CitationCheckResult.passed is False when either field has unverified citations.

**Test scenarios:**
- verification_steps with one uncited step: flagged_verification_steps contains it; step absent from result.
- verification_steps with one properly cited step: passes, step retained.
- troubleshooting_steps empty, verification_steps has uncited step: only verification flagged.
- Both fields have uncited steps: both flagged and stripped independently.
- passed=False when either field unverified.

**Verification:** pytest agent_service/tests/test_citation_check.py -v


### U5. Strip unverified-number sentences and silence warning banners

**Goal:** Sentences containing unverified numbers removed from advisory.assessment before assembly; warning banners become count-only notices with no content echoed.

**Requirements:** R6, R7 (banner content)

**Dependencies:** U4

**Files:**
- agent_service/app/workflow/runner.py
- agent_service/app/routing/followup_handler.py
- agent_service/tests/test_provenance_strip.py

**Approach:**
1. Numeric sentence stripping: after check_numeric_provenance returns unverified numbers, for each number n split advisory.assessment into sentences on [.!?]+\s+ and strip any sentence containing \bn\b as a word-boundary match. Rejoin remaining sentences.
2. If all sentences stripped: set advisory.assessment = Insufficient evidence to complete assessment - key figures are unverified.
3. Record strip via record_audit(numeric_sentence_stripped, ...) with sentence text and number.
4. Runner.py line 118: replace banner with [{len(provenance.unattributed_numbers)} unverified figure(s) removed from assessment].
5. Runner.py line 121: replace with [{len(citation_res.unverified_citations)} unverified citation(s) removed].
6. followup_handler.py lines 177-181: same count-only reformatting.

**Test scenarios:**
- Assessment The threshold is generally around 2000 psi or higher, unverified number 2000: sentence stripped, 2000 absent.
- Assessment with one verified and one unverified-number sentence: only unverified sentence stripped.
- All sentences unverified: Insufficient evidence substituted.
- Warning banner text does not contain any raw number from unattributed_numbers; contains only count.
- Citation warning text does not contain step content; contains only count.
- Q15 scenario end-to-end: 2000 not in response body.
- Q20 scenario end-to-end: no uncited step text in any field.

**Verification:** pytest agent_service/tests/test_provenance_strip.py -v


### U6. Harden test isolation in follow-up boundary tests

**Goal:** Prevent Redis state accumulation from masking router boundary bugs in future runs.

**Requirements:** R8

**Dependencies:** U3

**Files:**
- agent_service/tests/test_router_followup_boundary.py
- agent_service/tests/conftest.py

**Approach:**
1. Replace all fixed session-ID strings with f"test-fup-{uuid.uuid4().hex}" generated per-test.
2. Add pytest fixture that either flushes the test-scoped Redis namespace before each test or uses unique key prefix per test run.
3. Add smoke assertion in each test: assert turn_count as seen by router is 0 or 1 before the test query fires.

**Test scenarios:**
- Running the test module twice in succession produces identical pass/fail behavior.
- Deliberately setting turn_count=7 on session before test: still returns ANALYSIS_EXPIRED (guard no longer checks turn_count on FOLLOWUP path).

**Verification:** pytest agent_service/tests/test_router_followup_boundary.py -v -p no:randomly run twice - same result.


### U7. Add semantic contradiction assertions to the seal matrix

**Goal:** Automate the four contradiction assertions from the diagnostic report so future regressions are caught before manual review.

**Requirements:** R1, R2, R3, R4, R5, R6, R7

**Dependencies:** U1, U2, U3, U5

**Files:**
- agent_service/tests/test_seal_matrix_semantic.py (new)

**Approach:**
1. Q4 scenario: OP01 with oil_rate=399.10, health_score=44.0. Assert not producing not in response.lower(), zero production not in response.lower(), operating within normal not in response.lower().
2. Q10 scenario: OP02 with production_trend=STABLE. Assert not (stable and declining both in assessment.lower()); declining not in assessment if trend=STABLE.
3. Q18 scenario: fresh UUID session, FOLLOWUP_PATTERNS query. Assert done.status==INSUFFICIENT, error.code==ANALYSIS_EXPIRED, no ClarificationFrame in stream.
4. Q15 scenario: OP04 with unverified number situation. Assert no raw unverified numbers in response body.
5. Q20 scenario: OP03 with uncited steps. Assert no uncited step content in any response field.

**Patterns to follow:** agent_service/tests/test_seal_matrix.py for the NDJSON streaming test harness pattern.

**Verification:** pytest agent_service/tests/test_seal_matrix_semantic.py -v with Qdrant running.

---

## Verification Contract

```
# Phase 1 - KPI alarm
pytest agent_service/tests/test_kpi_alarm_check.py -v

# Phase 2 - xai guards
pytest agent_service/tests/test_xai_guards.py -v

# Phase 3 - router boundary
pytest agent_service/tests/test_router_followup_boundary.py -v

# Phase 4 - citation extension
pytest agent_service/tests/test_citation_check.py -v

# Phase 4 - provenance strip
pytest agent_service/tests/test_provenance_strip.py -v

# Semantic regression suite
pytest agent_service/tests/test_seal_matrix_semantic.py -v

# Full suite - must not regress transport tests
pytest agent_service/tests/ -v --timeout=60
```

No test may rely on a fixed session ID. Confirm turn_count is 0 at the start of each fresh-session test.

---

## Definition of Done

Global:
- All unit tests in the Verification Contract pass with exit code 0.
- test_seal_matrix_semantic.py passes all 5 semantic assertions.
- No existing transport tests in test_seal_matrix.py are broken.
- Q4, Q10, Q18, Q15, Q20 behaviors verified by automated assertions, not manual inspection.
- No unverified number or step content appears in any user-facing response path.
- Abandoned experimental code removed from the diff.

Per-unit done criteria:

U1: has_critical=True for health_score < 50; producing-oil alarm fires; all new tests pass.
U2: No contradiction between trend signal and assessment text for any STABLE or DECLINING input.
U3: Fresh-UUID FOLLOWUP_PATTERNS query returns ANALYSIS_EXPIRED; no ClarificationFrame.
U4: Uncited verification_steps stripped; flagged_verification_steps populated.
U5: Unverified-number sentences stripped from assessment; banners are count-only.
U6: Tests pass identically on two consecutive runs; turn_count does not affect routing outcome.
U7: All 5 semantic scenario tests pass on a live service with Qdrant running.
