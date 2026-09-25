---
title: KB Retrieval Quality Fix - Plan
type: fix
date: 2026-09-25
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
---

# KB Retrieval Quality Fix — Plan

---

## Goal Capsule

**Objective:** Definitional and procedural KB queries (e.g. "what is underload protection", "explain gas lock") return accurate, on-topic answers grounded in the correct KB documents — not boilerplate diagnostic text from unrelated chunks.

**Means:** Triage the bug to its layer (retrieval vs. narration), then apply the narrowest correct fix. (KTD1)

**Stop conditions:**
- Q1, Q11, Q12, Q20 (KB definitional queries) each return on-topic content when tested via the 5-query regression (U5).
- No regression on previously passing queries.

---

## Product Contract

### Summary

The ESP agent's KB-backed answers are wrong. When asked definitional questions ("what is underload protection?", "explain gas lock"), the agent returns off-topic boilerplate — diagnostic procedure text rather than the requested definition. The root cause is unknown at planning time and must be triaged. Two candidate layers exist: the KB search endpoint returning irrelevant hits (Bug A), or the XAI narrator hallucinating despite receiving correct hits (Bug B).

### Problem Frame

Observed behaviour in the 20-query seal matrix run:

- Q1 "What is underload protection?" returned "To diagnose a well, follow the BP troubleshooting guidelines." (boilerplate diagnostic, not a definition)
- Q12 "Explain gas lock" returned "review the minimum tag universe for useful monitoring." (unrelated KB chunk)

The `narrator_procedure_v1.txt` prompt says "Answer ONLY using approved KB citations." If the KB search returns wrong documents, the narrator is faithfully narrating those wrong documents. If the KB search returns correct documents, the narrator is ignoring them. The triage test settles which layer to fix.

### Requirements

**Triage**

R1. Before any code change, hit `POST /api/kb/search` directly with the failing queries and inspect the `hits[].snippet` values. The triage result determines all subsequent work.

**Bug A — Retrieval fix (if KB returns wrong hits)**

R2. Apply a minimum relevance score filter at the agent-side adapter (`adapters/kb.py`) so hits below the threshold are dropped before they reach the formatter.

R3. If low-score filtering alone is insufficient, apply a domain-specific query prefix (`"ESP well operations: "`) to shift embedding alignment toward the technical domain vocabulary.

**Bug B — Narration fix (if KB returns correct hits)**

R4. Tighten `narrator_procedure_v1.txt` to instruct the LLM to respond with `INSUFFICIENT CONTEXT` in `assessment` when no on-topic KB citation matches the query.

**Regression gate**

R5. After the fix, run the 5 KB-targeted queries against the live agent endpoint (`:8091`). All 5 must return on-topic content before this plan is declared done.

### Scope Boundaries

**In scope:** KB definitional/procedural query quality (OP06, Q1, Q11, Q12, Q20, one additional definitional query).

**Out of scope:** Full 20-query seal matrix re-run. Historian/telemetry paths. KB corpus re-ingestion. Qdrant/Neo4j re-indexing (owned by KB microservice on server 184).

---

## Planning Contract

### Key Technical Decisions

KTD1. **Triage gate is mandatory before any code change** (session-settled: user-directed — chosen over "fix both layers simultaneously": simultaneous fixes conflate error signals and make regression ambiguous).

KTD2. **Score threshold for Bug A fix: 0.65** — Hits with `score < 0.65` are off-topic noise. The KB spec shows on-topic hits scoring 0.845+ in the worked example. A 0.65 floor retains ambiguous-but-relevant hits while dropping clear mismatches. Tunable post-fix.

KTD3. **Query prefix for Bug A (if needed): `"ESP well operations: "`** — Nudges Qdrant embedding toward the ESP domain without changing semantics. Applies only if filtering alone is insufficient.

KTD4. **Bug B fix targets the prompt file, not adapter or formatter** — Formatter and evidence contract are correct. The prompt controls how the LLM uses evidence.

KTD5. **`search_kb` top_k stays at 5** — Increasing top_k adds noise. Reducing risks dropping the correct hit. 5 is sufficient once the score floor is applied.

### High-Level Technical Design

```
User query ("what is underload protection?")
        │
        ▼
  [Router] → OP06_KNOWLEDGE_LOOKUP
        │
        ▼
  [tool_gateway.py] → search_knowledge tool
        │
        ▼
  [adapters/kb.py: search_kb(query, top_k=5)]
        │  POST /api/kb/search  →  192.168.1.184:8085
        ▼
  [KB Microservice: Qdrant vector + BM25, 3657 chunks]
        │  returns hits[] with scores
        ▼
  [formatter.py: _extract_from_item]
        │  item.tool == "search_knowledge" → FormattedKbHit[]
        ▼
  [xai.py: format_evidence_for_prompt §3]
        │  "APPROVED KB CITATIONS" block injected
        ▼
  [calls.py: narrate()] → narrator_procedure_v1.txt (OP06)
        │
        ▼
  Advisory.assessment  →  user response
```

**Bug A intervention point:** `adapters/kb.py` — filter before formatter.
**Bug B intervention point:** `agent_service/app/llm/prompts/narrator_procedure_v1.txt` — add context-gap guard.

### Assumptions

- KB corpus content is correct (correctly chunked and indexed). Re-ingestion is a separate track.
- `search_kb` is called with `top_k=5` (confirmed in `adapters/kb.py`).
- Agent service at `:8091` resolves `KB_SERVICE_BASE_URL` to `http://192.168.1.184:8085`.

---

## Implementation Units

### U1. Triage: hit the KB search endpoint directly

**Goal:** Determine Bug A or Bug B by inspecting raw KB hits — before touching any production file.

**Requirements:** R1

**Dependencies:** None

**Files:** No production changes. Optional scratch: `run_kb_triage.py` at repo root (delete after).

**Approach:**
1. Run `POST http://192.168.1.184:8085/api/kb/search` for each failing query: "what is underload protection", "explain gas lock", "what causes ESP underload trip", "ESP production decline definition".
2. Inspect `hits[].snippet` and `hits[].score` in each response.
3. Decision gate:
   - Snippets off-topic → **Bug A**. Proceed to U2.
   - Snippets on-topic → **Bug B**. Proceed to U4. Skip U2 and U3.
   - Scores near 0.0 or empty hits → **Bug A + corpus/embedding issue**. Proceed to U2; flag U3 may also be needed.

**Test scenarios:**
- Each of the 4 queries returns a `hits` list with at least one entry containing a `snippet` and a numeric `score`.
- Triage decision recorded before any code change.

**Verification:** Triage decision documented. Outcome: one of {Bug A, Bug B, Bug A + corpus issue}.

---

### U2. Bug A fix: minimum score filter in KB adapter

**Goal:** Drop KB hits below the relevance threshold before they enter the formatter.

**Requirements:** R2

**Dependencies:** U1 (Bug A confirmed)

**Files:**
- `agent_service/app/gateway/adapters/kb.py`
- `agent_service/tests/` (add or extend KB adapter unit test)

**Approach:**
1. Add `min_score: float = 0.65` parameter to `search_kb()`.
2. Filter `hits` in-place after receiving the raw response: drop entries where `hit.get("score", 0.0) < min_score`.
3. If all hits are filtered, return `{"hits": [], "filtered": True}` — no crash. The xai.py guard at line 164 (`if not evidence.kb_hits: advisory.troubleshooting_steps = []`) already handles empty KB hits.
4. `tool_gateway.py` and `formatter.py` require no changes.

**Patterns to follow:** `adapters/historian.py` — module-level constant default, parameter carries it with a safe value.

**Test scenarios:**
- All hits above 0.65: none filtered; `hits` list unchanged.
- Mixed hits (3 above, 2 below): only the 3 above-threshold hits returned.
- All hits below threshold: `{"hits": [], "filtered": True}` returned; no exception.
- Score exactly 0.65: hit retained (inclusive lower bound).

**Verification:** Unit tests pass. Live spot-check: agent `/chat` "what is underload protection" returns on-topic snippet citation or clean "no KB context" — not boilerplate diagnostic text.

---

### U3. Bug A fix (conditional): domain query prefix

**Goal:** If score filtering alone is insufficient, prepend a domain prefix to steer the embedding search.

**Requirements:** R3

**Dependencies:** U2 (filtering applied; confirmed insufficient by re-running live spot-check)

**Files:**
- `agent_service/app/gateway/adapters/kb.py` (add `query_prefix` parameter), OR
- `agent_service/app/gateway/tool_gateway.py` (inject prefix at dispatch if cleaner)

**Approach:**
1. Determine injection point: if `tool_gateway.py` constructs the query string before calling `search_kb`, inject there scoped to OP06 calls; otherwise inject inside `search_kb` as `query_prefix: str = ""`.
2. Prefix value: `"ESP well operations: "`. Apply only when `objective_id` contains `"OP06"`. Do not apply to OP03 fault diagnosis calls.
3. Prefix must not appear in user-facing advisory text.

**Test scenarios:**
- OP06 query "what is underload protection" → KB receives "ESP well operations: what is underload protection".
- OP03 query "Why did FS-17 trip?" → KB receives query unchanged.
- Advisory text does not contain the prefix string.

**Verification:** Re-run live spot-check; hits now include on-topic snippets with scores > 0.65.

---

### U4. Bug B fix: context-gap guard in procedure narrator prompt

**Goal:** When KB hits are off-topic, instruct the LLM to report `INSUFFICIENT CONTEXT` rather than narrate boilerplate.

**Requirements:** R4

**Dependencies:** U1 (Bug B confirmed)

**Files:**
- `agent_service/app/llm/prompts/narrator_procedure_v1.txt`
- `agent_service/tests/` (add or update test for no-on-topic-context path)

**Approach:**
1. Append rule 7 to the existing 6-rule block:
   ```
   7. Context Gap Guard: If none of the provided KB citations contain
      information directly relevant to the user's query, your assessment
      MUST begin with "INSUFFICIENT CONTEXT:" followed by what was asked
      and what was found. Set confidence to 0.0. Do NOT fabricate a
      definition. Do NOT narrate unrelated procedural steps as an answer.
   ```
2. Verify existing on-topic scenarios still produce correct output.
3. Confirm `confidence: 0.0` emitted when INSUFFICIENT CONTEXT fires.

**Patterns to follow:** `narrator_v1.txt` rule 3 ("If an evidence source is missing or marked with an error/gap, mention what is unavailable and do not speculate.") — same grounding discipline extended to KB topic mismatch.

**Test scenarios:**
- On-topic hits (snippet contains "underload protection"): narrator produces a definition; no INSUFFICIENT CONTEXT prefix.
- Off-topic hits (snippet contains unrelated procedure text): narrator emits "INSUFFICIENT CONTEXT: …"; `confidence: 0.0`.
- Empty hits list: narrator emits "INSUFFICIENT CONTEXT: no knowledge base citations were found."; `confidence: 0.0`.

**Verification:** Manual test with seeded off-topic evidence block confirms LLM emits "INSUFFICIENT CONTEXT". On-topic test result unchanged.

---

### U5. Regression: 5-query KB targeted test run

**Goal:** Confirm the fix works end-to-end against the live agent (`:8091`) for the 5 KB-dependent queries.

**Requirements:** R5

**Dependencies:** U2 or U4 (whichever fix branch was taken)

**Files:**
- `run_kb_regression.py` at repo root (new, retained as CI reference)
- `KB_REGRESSION_RESULTS.txt` at repo root (output artifact)

**Approach:**
1. Create `run_kb_regression.py` following the same structure as `run_full_seal_suite.py`.
2. Target exactly these 5 queries against `POST http://127.0.0.1:8091/api/agent/chat`:
   - Q1: "What is underload protection?"
   - Q11: "Why has FS-17 production declined?" (KB-backed context)
   - Q12: "Explain gas lock"
   - Q20: "What standard covers ESP vibration limits?"
   - Q-bonus: "What is the definition of pump-off condition?"
3. Assert each response does NOT contain boilerplate failure strings: `"BP troubleshooting guidelines"`, `"minimum tag universe"`, `"follow the diagnostic procedure"`.
4. Assert each passing response contains at least one citation pattern: `[API_RP`, `[Takacs`, `[SPE`, `[IEC`, or `[Baker`.
5. Retry once on network timeout (60 s) before marking FAIL.
6. Print PASS / FAIL per query. Write full results to `KB_REGRESSION_RESULTS.txt`. Exit non-zero on any failure.

**Test scenarios:**
- All 5 queries return on-topic answers with citations → script exits 0.
- Any query returns boilerplate → script exits 1; failing query and response printed.
- VPN timeout → retry once; mark PASS if retry succeeds.

**Verification:** Script exits 0. `KB_REGRESSION_RESULTS.txt` shows 5/5 PASS.

---

## Verification Contract

```powershell
# U1 — triage (manual, no code change)
curl -s -X POST http://192.168.1.184:8085/api/kb/search `
  -H "Content-Type: application/json" `
  -d '{"query": "what is underload protection", "top_k": 5}'

# U2 / U4 — unit tests
.\.venv\Scripts\python.exe -m pytest agent_service/tests/ -v -k "kb"

# U5 — end-to-end KB regression
.\.venv\Scripts\python.exe run_kb_regression.py
```

Environment note: `LLM_TIMEOUT_SEC=60` in `agent_service/.env` (already set). VPN must be active and `192.168.1.184:8085` reachable before any curl or regression commands.

---

## Definition of Done

- [x] U1 triage completed. Bug A or Bug B documented.
- [x] Bug A path: U2 score filter applied. U3 prefix applied if U2 alone insufficient.
- [x] Bug B path: U4 context-gap guard added to `narrator_procedure_v1.txt`.
- [x] U5 script exits 0. `KB_REGRESSION_RESULTS.txt` shows 5/5 PASS.
- [x] Spot-check 3 non-KB queries from the seal matrix (e.g. Q4 FS-17 status, Q7 health band, Q9 history) — none regressed.
- [x] Triage scratch files removed. `run_kb_regression.py` retained.
- [x] Agent service restarted and health check returns `200 OK` before regression run.
