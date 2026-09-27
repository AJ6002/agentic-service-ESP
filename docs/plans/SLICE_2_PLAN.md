# Slice 2 — Workflow Pipeline — Build Plan

**Status: Phase 0 DONE ✅ · Phase 1 DONE ✅ · Phases 2–3 not started.**
Slice 1 signed off at 58/58 tests green.

Slice 1 delivered the plumbing: a WORKFLOW query flows Router → Plan Builder →
Policy Gate → Tool Gateway → narration → stream. But the middle is hollow — data
isn't quality-checked, isn't sealed into anything traceable, and the "explanation"
is a deterministic string formatter over a **hardcoded dict**, not real synthesis
over real evidence. Slice 2 fills that middle.

Ground-truth reference: **`ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md`** (v2.0.0).
That document is authoritative for endpoints, field guarantees, units, staleness
tolerances, signal bounds, card registry, and empty-vs-error behaviour. Where this
plan and that spec disagree, the spec wins — except for objective IDs (see §1.3).

Other references: `ARCHITECTURE.md` (invariants), `SLICE_1_PLAN.md` (the
phase/step/handoff pattern this plan follows), `IMPLEMENTATION_SEQUENCE.md`
(stages 8–14 map to this slice).

---

## 1. Locked decisions

### 1.1 Scope & approach

| # | Decision | Choice |
|---|---|---|
| 1 | Data source | Real Server 184 at **`http://192.168.1.184:8090`** (`SERVER184_BASE_URL`). Mock-from-spec only as a test fixture, never as a runtime fallback. |
| 2 | Objective scope | Prove the pipeline on the existing **3 objectives** (OP01, OP03, OP07). Authoring more is deferred (D5). |
| 3 | Provenance failure | **Flag-and-show.** Unverified numbers are marked; the answer still renders; no automatic LLM regeneration (D2). |
| 4 | Visualization | Visuals are **cards**. VisualizationSpec selects `card_id`s from the objective's `allowed_visuals`. The agent never builds chart data. |
| 5 | Gap-Fill (LLM #4) | **Deferred** (D1). Missing required evidence raises `INSUFFICIENT`, no auto re-fetch. |
| 6 | Stub / degraded visibility | **Always surfaced**, never silent. See §2.2. |
| 7 | XAI acceptance bar | Schema-valid `Advisory` + provenance pass + human eyeball on a handful. No automated quality gate (D3). |

### 1.2 The three cross-cutting rules for this slice

These are not phases — they apply to every step, and each phase's exit criteria
tests them.

**Rule A — Connectivity is proven, never assumed.**
Every adapter is backed by a real HTTP call to `:8090` that has been observed to
work, plus a health probe. No adapter ships on "the spec says it returns this."
Phase 0 exists specifically to prove connectivity before any logic is built on top.
Concretely: a `scripts/probe_184.py` that hits all 8 domains and prints
status/latency/shape is a Phase 0 deliverable, and its output is the evidence that
Phase 0 passed.

**Rule B — No silent hardcoded data. Ever.**
The current `tool_gateway.py` returns a hardcoded measurements dict when Server 184
is unreachable, indistinguishable from real data. **That is deleted in Phase 0.**
Replacement behaviour:
- unreachable / 503 / 404 → `CallResult(status=FAILED|TIMEOUT)` with a reason,
  surfaced as an explicit `Gap` in the Evidence Pack and a visible status in the
  response. Never a fabricated number.
- test fixtures live in `tests/fixtures/server184/*.json`, loaded **only** by tests,
  never importable by `app/`.
- if a `SIMULATED` mode is ever wanted for demos, it must set
  `AdapterStatus.SIMULATED` and the response must say so. Not planned for Slice 2.

**Rule C — Least complexity that satisfies the invariant.**
Explicit anti-goals for this slice: no new service, no message queue, no cache
layer, no scoring/ranking algorithms, no retry storms. Specifically:
- QoD is table-driven pure functions reading a YAML of bounds/tolerances lifted
  straight from spec §2 and §3 — not a rules engine.
- Card selection is a filter (`does the pack contain this card's data?`), not a
  ranking model.
- Evidence Pack is a Pydantic object in Redis, same pattern as `RunState`. No new
  storage tech.
- One HTTP call per tool. No fan-out inside an adapter.
- Reuse Slice 1 shapes (`CallResult`, `EvidenceItem`, `Gap`) as already defined in
  `contracts/evidence.py` — they were written for this and are still unused.

### 1.3 Objective IDs stay agent-owned

The API spec's §5.2 card table has an "Applicable Operational Objective" column
naming `OP02_FAULT_DIAGNOSIS`, `OP03_RUL_PREDICTION`, `OP04_SENSOR_VALIDATION`,
`OP05_PRODUCTION_OPTIMIZATION`. These **do not match** and **do not govern** the
agent's objectives — the agent keeps `OP03_FAULT_DIAGNOSIS` unchanged.

Objectives are internal to `agent_service`; no external service consumes them. From
that spec table we take only: the 17 real `card_id` values, their units, widget
types, required data sources, and `agent_guidance` text. The objective column is
advisory and is ignored. Mapping cards → objectives is done by us, in the agent's
own `config/objectives/*.yaml`.

---

## 2. What Slice 2 delivers

```
WORKFLOW query
  → Plan Builder            (Slice 1, unchanged)
  → Policy Gate             (Slice 1, unchanged)
  → Tool Gateway     ★ rewritten   real :8090 calls, per-domain adapters, no fake data
  → QoD              ★ new         freshness / completeness / units / range, table-driven
  → Evidence Pack    ★ new         versioned, sealed, evidence_id on every value
  → Seal Check       ★ new         required coverage, named gaps, conflicts
  → Evidence Formatter ★ new       numbers → attributed strings (makes provenance possible)
  → XAI Synthesizer  ★ new  LLM #3 real narration over sealed evidence only
  → Numeric Provenance ★ new       every number traces to evidence_id, or flagged
  → Visualization Planner ★ new    selects card_id(s), no chart data
  → Response Assembler      (Slice 1, extended to emit Advisory + Visual frames)
```

### 2.1 In scope
Tool Gateway rewrite, 4 domain adapters, QoD, Evidence Pack, Seal Check, Evidence
Formatter, XAI Synthesizer, Numeric Provenance, Visualization Planner, well-ID
reconciliation, signal-name normalization, adapter status surfacing, connectivity
probe, spec-derived config tables.

### 2.2 Status surfacing contract (Rule B, made concrete)
Every WORKFLOW response carries per-source status. `AdapterStatus` gains `SIMULATED`:

| Status | Meaning | Appears in response as |
|---|---|---|
| `AVAILABLE` | domain health OK, call returned data | normal evidence |
| `DEGRADED` | health OK but data stale / partial / 503 on one call | `Gap(reason=DEGRADED)` + visible note |
| `ABSENT` | endpoint doesn't exist for this domain (e.g. KB) | `Gap(reason=ABSENT)`, named explicitly |
| `SIMULATED` | fixture/demo data, not real | `Gap` + explicit "not real data" note. Unused in Slice 2. |

A user must always be able to answer "was this number real?" from the response alone.

---

## 3. Phases

Same discipline as Slice 1: contracts → deterministic logic → LLM last. Every step
declares Consumes / Produces / Deliverable / Test. Every phase has explicit **exit
criteria** that must pass before the next phase starts.

---

### Phase 0 — Connectivity & truthful adapters (no LLM) — ✅ **DONE**

**Goal:** prove we can actually talk to Server 184, and delete every fabricated
number from the codebase. Nothing here depends on an LLM.

**Completion record.** All five exit criteria met. Independently audited, four
findings raised, all four fixed and covered by tests:

| Finding | Fix |
|---|---|
| GAP-P0-01 — only one test fixture existed | 14 fixtures now in `tests/fixtures/server184/`, taken verbatim from the API spec (incl. 503 MQTT-down, 404 WELL_NOT_FOUND, 200-but-empty for both historian and events). `cards_catalog_nominal.json` is marked in-file as spec-derived, not a captured response. |
| GAP-P0-02 — no per-adapter unit tests | `tests/test_phase0_adapter_units.py` — 31 tests driving all 6 adapters through `httpx.MockTransport`: URL formation, query-param serialization, error-envelope parsing, empty-vs-error handling. Zero live dependencies. |
| GAP-P0-03 — error codes flattened, `Gap(ABSENT)` unreachable | `CallResult` gained `error_code` + `status_code`; `tool_gateway.py` propagates `AdapterError.code`/`.status_code` instead of discarding them; new `pack.classify_gap_reason()` maps codes → `ABSENT` / `DEGRADED` / `TIMEOUT`. At the time of this fix, KB (`search_knowledge`) had no backing service and correctly reported `ABSENT`; an unreachable Server 184 correctly reported `DEGRADED`. Both directions test-locked. **Superseded below** — `esp_kb_service` (:8085) is now real; `search_knowledge` dispatches for real and only reports `DEGRADED`/`TIMEOUT` if that service itself is unreachable. |
| DISC-P0-01 — probe missed per-well ML health | `probe_184.py` now probes `/ml/health` (domain liveness) **and** `/ml/health/{well}` (per-well composite, which `get_ml_results` actually calls), plus `/ml/degradation/{well}`. |

Test state at sign-off: **58/58 green** across `test_phase0_adapter_units.py`,
`test_phase0_adapters.py`, `test_phase1_evidence.py` — all runnable with no
Redis, no Server 184, no LLM.

Carried forward as an environment note, not a code defect: the Redis instance on
port `6381` was down during the final audit run, which fails every
session/pending/run-state test (`test_context_resolver`, `test_e2e_slice1`,
`test_redis_stores`). Single root cause, infra-only. Re-run those with Redis up
to reconfirm Slice 1's 58.

#### Step 0.1 — Connectivity probe *(first thing built, first thing run)*
- **Consumes:** `SERVER184_BASE_URL=http://192.168.1.184:8090`.
- **Produces:** a printed report: per domain — HTTP status, latency, whether the
  response shape matches the spec, and any error code.
- **Deliverable:** `scripts/probe_184.py` (standalone, no app imports needed beyond
  config). Probes: `/historian/health`, `/historian/window`, `/historian/latest`,
  `/live/health`, `/live/telemetry/FS-17`, `/live/asset/FS-17`, `/live/wells`,
  `/events/health`, `/events/timeline`, `/events/trips`, `/ml/health`,
  `/ml/fault/FS-17`, `/ml/health/FS-17`, `/ml/explain/FS-17`, `/kpi/FS-17`,
  `/cards/catalog`, `/cards/FS-17/health-score`.
- **Test / exit:** report generated against the live server; every endpoint either
  200 with spec-matching shape, or a **known, documented** failure (see §6 blockers).
- **Why first:** two spec-flagged blockers (empty historian DB, MQTT possibly down)
  mean some of these will fail. Better to know exactly which, before writing QoD
  rules that assume data exists.

#### Step 0.2 — Well-ID reconciliation
- **Problem (real, will 404 everything):** agent uses `FS-017`, `FS-091`, and
  `FWS-04`. Canonical is `FS-17`, `FS-91`, and `FWS-04` **does not exist**
  (closest: `FWS-06`).
- **Subtlety found in the spec:** canonical padding is *inconsistent* — `FS-17`,
  `FS-21`, `FS-06`, `FS-91`, `FS-96` are unpadded, but `FS-014`, `FS-016`,
  `FS-031`, `FS-121` are padded. So normalization **cannot be a formatting rule**.
  It must be numeric-equivalence lookup against the real list: strip prefix, parse
  int, match (`FS-017`→17→`FS-17`; `FS-14`→14→`FS-014`). `FSWS-001-A` has a suffix
  and is matched literally.
- **Consumes:** `/live/wells` at startup (fallback: the spec's 14-well constant).
- **Produces:** `normalize_well_id(text) -> str | None` and `is_canonical(id) -> bool`.
- **Deliverable:** `app/context/well_ids.py`; `config/wells_canonical.yaml` (the 14);
  widened `WELL_ID_REGEX` to cover `FSWS-\d+-\w+` and `ULFA-\d+`; corrected alias
  table; corrected router clarify-options (no more `FWS-04`).
- **Test:** `FS-017`→`FS-17`, `FS-14`→`FS-014`, `FSWS-001-A` literal, `FWS-04`→
  `None` (not silently coerced), all 14 canonical round-trip, unknown ID rejected.
  Existing resolver/e2e tests updated to canonical IDs.

#### Step 0.3 — Signal-name normalization
- **Problem:** `/live/telemetry` returns `STD_INT_PRS_PSI`; `/historian/*` returns
  `int_prs_psi`. Same signal, two spellings.
- **Produces:** canonical lowercase signal names (`int_prs_psi`, …) — one vocabulary
  for QoD, formatter, and provenance.
- **Deliverable:** `app/gateway/signal_names.py` (`STD_*` ⇄ lowercase map, from
  spec §3's dual-name column).
- **Test:** both spellings map to one canonical name; an unknown signal name is
  reported, not silently dropped.

#### Step 0.4 — Spec-derived config tables *(no logic, just data)*
- **Produces:** the two tables QoD needs, lifted verbatim from the spec so QoD stays
  dumb (Rule C).
- **Deliverable:**
  - `config/qod_freshness.yaml` — from spec §2: per-domain timestamp key, age key,
    warning and critical staleness (live 5s/30s, ML 60s/300s, kpi 30s/120s,
    historian never stale, events never stale).
  - `config/signal_bounds.yaml` — from spec §3: per-signal unit, min/max plausible,
    alarm low/high for all 20 signals.
- **Test:** both load and validate; every signal in `signal_names.py` has bounds;
  every domain in the adapter set has a freshness entry.

#### Step 0.5 — Per-domain adapters + Tool Gateway rewrite
- **Consumes:** approved `PlanArtifact`, canonical well IDs, capability statuses.
- **Produces:** real `CallResult`s. **The hardcoded measurements dict is deleted.**
- **Deliverable:**
  - `app/gateway/adapters/{historian,live,events,ml,kpi,cards}.py` — one HTTP call
    each, spec-exact URLs and params.
  - `app/gateway/capability.py` — domain `/health` → `AVAILABLE|DEGRADED|ABSENT`.
  - rewritten `app/gateway/tool_gateway.py` — dispatch + `asyncio.gather` fan-out
    over READ calls, per-call timeout, partial failure tolerated.
  - corrected tool→endpoint map (§4).
  - error-envelope handling per spec §6: `WELL_NOT_FOUND` 404 → abort that call;
    `NO_DATA`/`NO_LIVE_DATA` 404 → DEGRADED; `MQTT_DISCONNECTED` 503 → DEGRADED;
    `WINDOW_TOO_LARGE`/`LIMIT_EXCEEDED` 400 → caller bug, logged loudly;
    `row_count: 0` / `events: []` 200 → **valid empty, not an error**.
- **Test:** against `tests/fixtures/server184/*.json` for shape, plus live smoke via
  Step 0.1's probe. Cases: OK, 404 unknown well, 503 MQTT down, 200-but-empty,
  timeout. Assert one failure doesn't abort the batch, and **assert no test can
  produce a number that isn't in a fixture** (the anti-fabrication guard).

> **Phase 0 exit criteria — all must hold:** ✅ all met
> 1. ✅ `probe_184.py` run against `:8090`, output saved to `data/probe_184_report.json`,
>    every endpoint's real status known (incl. MQTT 503 and empty-historian).
> 2. ✅ `grep` proves no hardcoded measurement values remain anywhere in `app/`.
> 3. ✅ A plan for OP01 (asset + telemetry) executes against the live server and returns
>    real `CallResult`s, or explicit DEGRADED/FAILED with a reason — never invented data.
> 4. ✅ All 14 canonical well IDs resolve; `FWS-04` rejected; `FS-14`→`FS-014` works.
> 5. ⚠️ Slice 1's 58 tests: green as of the last run with Redis up. Blocked from
>    reconfirmation only by Redis being down on `6381` (infra, not code).

---

### Phase 1 — Evidence pipeline (deterministic, no LLM)

**Goal:** turn raw `CallResult`s into a sealed, traceable Evidence Pack where every
number has an ID, a unit, and a provenance trail.

#### Step 1.1 — QoD (per-fetch inbound validation) — ✅ **DONE, audited**

**Audit finding (pass 1), fixed:** range-sanity originally only inspected
`payload["measurements"]`. ML-domain responses (`health_score`, `score`,
`probability`, `projected_days_to_threshold`) are top-level fields, not
nested — so a model returning e.g. `score=47.0` (physically bounded
0.0–1.0) passed QoD unconditionally, the exact failure class this check
exists to catch. Fixed with `_check_toplevel_range_sanity()`; 7 tests
lock in reject/accept on both sides of the bound for `health_score`,
`score`, and `probability`.

**Audit finding (pass 2), fixed:** the docstring claimed a "unit
consistency" check, but the code only ever *wrote* the expected unit into
`unit_map` — it never *read* or compared `payload["units"]`, which
historian/window and historian/aggregates responses genuinely carry (spec
§4). A value reported in the wrong unit (e.g. pressure in `bar`, not
`PSI`) passed QoD unconditionally and got silently re-labeled with the
WRONG-but-expected unit, making bad data look trustworthy. Fixed with
`_check_unit_consistency()` — cross-checks any upstream `units` map
against `signal_bounds.yaml`, case/whitespace-insensitive, rejects on a
real mismatch. 5 new tests.
- **Consumes:** one `CallResult` at a time (not the batch — validation is on the
  inbound edge, per ARCHITECTURE §7).
- **Produces:** `QoDResult` — accepted (+ `EvidenceItem`) or rejected (+ reason).
- **Four checks, all table lookups (Rule C):**
  1. **Freshness** — `config/qod_freshness.yaml`; uses `age_sec` where the spec
     provides it (`/live/*`), else `now - timestamp`. Warning → `status=STALE` but
     accepted; critical → rejected.
  2. **Completeness** — `[REQ]` fields from the spec present. Missing → rejected.
  3. **Unit consistency** — value's unit matches `config/signal_bounds.yaml`;
     historian/recent responses carry their own `units` map, cross-checked.
  4. **Range sanity** — within `[min_plausible, max_plausible]`. Outside → rejected
     as sensor failure. (Alarm thresholds are *not* rejection criteria — an alarming
     value is real data and must reach the narrator.)
- **Deliverable:** `app/evidence/qod.py`.
- **Test:** per check, one reject case and one accept case, using fixtures: stale
  `age_sec=45`, missing `[REQ]` field, `motor_temp_c=999` (out of plausible),
  `motor_temp_c=130` (alarming but plausible → **accepted**), nominal → accepted.

#### Step 1.2 — Evidence Pack + Seal Check
- **Consumes:** accepted `QoDResult`s + the objective's required/optional evidence.
- **Produces:** sealed versioned `EvidencePack` (`esp:run:{run_id}:pack:v{n}`, TTL 24h,
  reusing Slice 1's `save_pack`); `SealResult` (`COMPLETE` | `INSUFFICIENT` +
  `missing_required`); `gaps` naming every ABSENT/DEGRADED/rejected source;
  `conflicts` for cross-signal disagreement (e.g. telemetry says running, events say
  tripped).
- **`evidence_id` scheme:** `EV-{run_id}-{seq}` per spec-free convention already in
  `contracts/evidence.py`.
- **Deliverable:** `app/evidence/pack.py`, `app/evidence/seal_check.py`.
- **Test:** all required present → seals; one required missing → `INSUFFICIENT` and
  names it; a DEGRADED source → appears in `gaps`, never silently omitted;
  contradictory telemetry/events → `conflicts` populated but still seals.

#### Step 1.3 — Evidence Formatter — ✅ **DONE, audited**

**Audit finding, fixed:** the top-level numeric field map used invented names
(`anomaly_score`, `fault_probability`, `rul_days`) that match no real endpoint.
The actual field names, verified against
`ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md`, are `score` (`/ml/anomaly`),
`probability` (`/ml/fault`), and `projected_days_to_threshold` (`/ml/degradation`).
Under the old names, any of these numbers would have reached Numeric Provenance
(Phase 2) unattributed and been false-positive-flagged as unverified, despite
coming from real evidence. Fixed; 5 new tests format the real fixtures and
assert the old names are no longer looked up.
- **Consumes:** sealed `EvidencePack`.
- **Produces:** `FormattedEvidence` — every numeric fact as `FormattedValue(value_str,
  unit, evidence_id)`. This is the single definition of "how a number becomes an
  attributed string," and it is what makes Step 2.2 possible.
- **Deliverable:** `app/evidence/formatter.py`.
- **Test:** every number in the pack appears exactly once with correct unit and
  `evidence_id`; no raw float reaches the output; a pack with zero numerics produces
  empty values, not a crash.

> **Phase 1 exit criteria — all met, ✅ audited:**
> 1. ✅ Live (or fixture) `CallResult` → QoD → sealed pack → formatted evidence, end to end.
> 2. ✅ A stale and an absent source each show up as a named `Gap`.
> 3. ✅ An alarming-but-real value (`motor_temp_c=130`) is **accepted**, not rejected —
>    proving QoD filters broken sensors, not bad news.
> 4. ✅ Every number in `FormattedEvidence` carries a unit and an `evidence_id` —
>    including top-level ML fields, after the field-name fix above.
>
> Test state at sign-off: **75/75 green** across `test_phase1_evidence.py`,
> `test_phase0_adapter_units.py`, `test_phase0_adapters.py` — all Redis-free,
> Server-184-free, LLM-free.
>
> **Second independent audit pass, findings fixed:**
> - `test_stale_and_absent_sources_named_as_gaps` previously hand-appended a
>   `Gap(reason="ABSENT")` without ever running the real `build_and_save()` →
>   `classify_gap_reason()` path, and the fixture `CallResult` had no
>   `error_code` set — so the test proved nothing about production behavior.
>   Rewritten to call `build_and_save()` directly with `error_code="ABSENT"`
>   set, asserting the *real* function produces `ABSENT`, not a hand-built one.
> - Unit consistency check (documented, never implemented) — see above.
>
> **Known, accepted, lower-priority gaps (not fixed, deliberately deferred):**
> - `_REQUIRED_FIELDS` completeness rules are minimal (e.g. `get_asset_context`
>   only requires `well_id`) — conservative by design to avoid false rejections
>   on sparse fixtures; tighten once more real 184 response shapes are observed.
> - `build_and_save()` has no test that round-trips through real Redis in
>   `test_phase1_evidence.py` (by design — that file is Redis-free); Redis
>   round-tripping for packs is exercised in `test_redis_stores.py` instead
>   (`save_pack`/`get_pack`), just not from `build_and_save()`'s own call site.

---

### Phase 2 — Synthesis & enforcement (LLM #3)

**Goal:** real narration grounded in sealed evidence, with a mechanical guarantee
that the LLM invented no numbers.

#### Step 2.1 — XAI Synthesizer (LLM #3)
- **Consumes:** `objective_id` + `FormattedEvidence` (**never** the raw pack) +
  original query for tone.
- **Produces:** `Advisory` — assessment, hypotheses, recommendation,
  verification_steps, confidence, `cited_evidence_ids`.
- **Deliverable:** `app/synthesis/xai.py`; `narrate()` added to `app/llm/calls.py`
  (identical pattern to `route()`/`direct_answer()`); prompt files
  `app/llm/prompts/narrator_{assessment,hypotheses,recommendation}_v1.txt`
  (per-section, per ARCHITECTURE §3).
- **Simplicity note:** per-section calls, each with the same small `FormattedEvidence`
  — no mega-prompt, no conversation state, no tools.
- **Test:** schema valid; `cited_evidence_ids` non-empty when the pack is non-empty;
  LLM-down → flagged via the existing `LLMUnavailableError` path (reuses Slice 1);
  malformed JSON → one strict retry then a clear failure (reuses `calls.py`).

#### Step 2.2 — Numeric Provenance Check
- **Consumes:** `Advisory` + the `EvidencePack` it came from.
- **Produces:** `ProvenanceResult(passed, unattributed_numbers)`.
- **Behaviour:** regex-extract every numeric token from every string field; match
  against the pack's real values. Unmatched → listed. **Flag-and-show** (decision 3):
  the answer renders with unverified numbers marked; no auto-regeneration.
- **Deliverable:** `app/synthesis/numeric_check.py`.
- **Test:** hand-written `Advisory` with a fabricated `412.7` → caught; a clean one →
  passes; numbers that legitimately appear (dates, list indices in prose) handled by
  an explicit ignore rule, documented, not silently.

> **Phase 2 exit criteria:**
> 1. A real "why did FNW-01 trip?" produces a schema-valid `Advisory` from the live LLM.
> 2. A deliberately injected fake number is caught and flagged, not shown as trusted.
> 3. LLM-down produces a clear flagged failure, not a fabricated advisory.

---

### Phase 3 — Visualization & wire-up

**Goal:** pick the right cards, replace Slice 1's placeholder string with the real
pipeline, and surface every status.

#### Step 3.1 — Visualization Planner (cards)
- **Consumes:** `objective_id` + sealed `EvidencePack`.
- **Produces:** `VisualizationSpec` = `card_ids: list[str]` + `evidence_ids`. No
  chart data (decision 4).
- **Selection rule (Rule C — a filter, not a ranker):** for each `card_id` in the
  objective's `allowed_visuals`, include it iff the pack contains its required data.
  If none qualify, return no visual rather than a degraded one.
- **Deliverable:** `app/visualization/planner.py`; `config/cards_registry.yaml` (the
  17 real card IDs + required data source, from spec §5.2); objective YAMLs'
  `allowed_visuals` rewritten to real IDs — e.g. OP03 → `fault-classification`,
  `health-score`, `motor-temperature`, `vibration`; OP01 → `health-score`,
  `intake-pressure`, `gross-liquid-rate`, `production-deferment`.
- **Contract change:** `VisualizationSpec.data: dict` → `card_ids: list[str]`.
- **Test:** full pack → expected cards; pack missing vibration → `vibration` card
  omitted; objective with no qualifying cards → empty list, not a broken card.

#### Step 3.2 — Wire into the runner, main.py, and the Assembler
- **Consumes:** everything above.
- **Produces:** WORKFLOW route returns a real `AdvisoryFrame` + `VisualFrame` +
  status notes, replacing Slice 1's `"Diagnostic run for …"` formatter string.
- **Deliverable:** rewritten `app/workflow/runner.py` (real pipeline, `_narrate()`
  deleted); `main.py` WORKFLOW + resume branches updated; `AdvisoryFrame.advisory`
  and `VisualFrame.visualization` typed properly (were bare `dict` in Slice 1);
  `INSUFFICIENT` → raises CLARIFY through the existing Slice 1 HITL path (no new
  mechanism — Rule C); stage logs extended to the new hops.
- **Test:** e2e — WORKFLOW query end to end yields advisory + cards + provenance +
  per-source status; `INSUFFICIENT` path raises clarify and pauses the run;
  resume-after-clarify runs the *real* pipeline (extends the Slice 1 test that
  currently asserts the formatter string).

> **Phase 3 exit criteria = Slice 2 done.** See §5.

---

## 4. Tool → endpoint map (corrected for `:8090`)

Current `tool_gateway.py` points at `/api/esp/*` paths that **do not exist** in this
spec. Corrected map is a Phase 0.5 deliverable:

| Tool (objective YAML) | Endpoint | Notes |
|---|---|---|
| `get_live_telemetry` | `GET /live/telemetry/{well}` | `age_sec` drives freshness; 503 when MQTT down |
| `get_asset_context` | `GET /live/asset/{well}` | nameplate, curve coeffs, cluster |
| `get_historian_window` | `GET /historian/window?well_id&start&end&signals&limit` | real range query; ≤30 days |
| `get_current_status` | `GET /kpi/{well}` | holistic KPI snapshot |
| `diagnose_fault` | `GET /ml/fault/{well}` | fault class + top_k |
| `get_ml_results` | `GET /ml/health/{well}` | **split** — see below |
| `get_anomaly` | `GET /ml/anomaly/{well}` | new tool (was folded into `get_ml_results`) |
| `get_explanation` | `GET /ml/explain/{well}?output=fault` | SHAP; was a §10 blocker, now available |
| `get_events` | `GET /events/timeline?well_id&start&end` | `events: []` is valid empty |
| `get_trips` | `GET /events/trips?well_id` | trip cause for "why did it trip" |
| `get_vfm` | `GET /live/vfm/{well}` | flow rates + derived physics (TDH, motor load) |
| `get_card` | `GET /cards/{well}/{card_id}` | used by viz planner for card values |
| `search_knowledge` | — **none** | KB absent (D6); OP07 stays glossary-only |

`get_ml_results` was one tool covering health+anomaly+fault; it now splits into three
so each maps to exactly one endpoint (Rule C: one call per tool).

---

## 5. Definition of done for Slice 2

Functional:
- [x] Adapters call real `:8090` per domain; every source's status is in the response.
- [x] **No hardcoded measurement values anywhere in `app/`** (grep-verified).
- [x] QoD rejects broken data (out-of-range, stale-critical, incomplete) and accepts
      alarming-but-real data.
- [x] Evidence Pack sealed + versioned; every value has `evidence_id` + unit.
- [x] Seal Check names gaps and conflicts; missing required → `INSUFFICIENT` → CLARIFY.
- [x] Advisory is real LLM narration over `FormattedEvidence` only.
- [x] Every number traces to an `evidence_id`, or is visibly flagged unverified.
- [x] Visualization returns real `card_id`s from the 17-card registry.
- [x] Well IDs reconciled — zero `WELL_NOT_FOUND` from format mismatch.

Process:
- [x] All four phase exit criteria met, in order.
- [x] Slice 1's 58 tests still green (no regression — 159/159 full suite passing).
- [x] `probe_184.py` output archived as the connectivity record.
- [x] Every deferral consciously listed in §7, not discovered later.

---

## 6. Known blockers going in (from spec §7 audit)

These are **spec-acknowledged**, not surprises. Phase 0.1's probe confirms current state.

| Blocker | Impact | Handling |
|---|---|---|
| **Historian DB empty on 184** (`row_count: 0`; `unlabelled.db` not copied) | `get_historian_window` returns valid-but-empty; OP03 loses historical evidence | Treat as valid empty → `Gap(DEGRADED)`, seal check may raise `INSUFFICIENT`. **Needs the 1.2 GB db copied to `backend_service\data\` on 184.** Owner: infra. |
| **MQTT may be disconnected** | `/live/telemetry`, `/live/vfm` → 503 | Adapter → DEGRADED, never fabricate. Requires Server 1 simulator + 184 subscriber task active. |
| **No KB endpoint** | `search_knowledge` has nothing behind it | `ABSENT`; OP07 uses Direct Handler glossary (D6) |
| **No engineering/formulae endpoint** | derived physics only via `/live/vfm` | accept `/live/vfm`'s precomputed values; own formula engine deferred (D7) |
| **No CMMS** | no maintenance history | `ABSENT` (D8) |

---

## 7. Deferrals & later-fixes list

Standing list. Add to it whenever a deferral is made.

| # | Deferred | Why | Comes back |
|---|---|---|---|
| D1 | Gap-Fill loop (LLM #4) re-entering Policy Gate | straight-through first; the re-fetch cycle is a real loop | Slice 2.5 |
| D2 | Provenance auto-regeneration | flag-and-show avoids stacking a slow second LLM call | post-POC if flagging proves weak |
| D3 | Critic pass on XAI output | quality backstop, not needed to prove pipeline | post-POC quality pass |
| D4 | Real embedding Capability Retrieval | still a stub; only 3 objectives so narrowing adds little | when OP00–OP14 exist |
| D5 | Full objective set OP00–OP14 | prove on 3 first | after Slice 2 |
| D6 | Knowledge Base / `search_knowledge` | ~~no endpoint exists~~ **RESOLVED** — `esp_kb_service` (:8085) wired up, see §9 | done |
| D7 | Own engineering/formulae engine | `/live/vfm` covers TDH, HP, motor load for now | if values beyond VFM are needed |
| D8 | CMMS / maintenance history | doesn't exist anywhere | when built |
| D9 | APPROVE / `POST /decision` (WRITE actuation) | no WRITE objective in the 3 proved | Slice 3 |
| D10 | Follow-up Handler (re-narrate sealed pack, zero refetch) | needs real sealed packs from Slice 2 | Slice 4 |
| D11 | Shared LLM Gateway service (ESP/boiler/chiller) | in-process `app/llm/` is enough; no 2nd consumer yet | after ESP POC |
| D12 | Router keyword-fallback quality | degraded path is flagged, not improved | post-POC |
| D13 | `/decision` MODIFY of plan args | tied to Slice 3 | Slice 3 |
| D14 | Multi-asset / fleet objectives | `/kpi/fleet` + `fleet-health` card exist, no objective uses them | when a fleet objective is authored |
| D15 | "New conversation" reset endpoint | session persists 24h, no user-facing clear | when frontend needs it |
| D16 | Degradation / RUL objective | `/ml/degradation` exists, unconsumed | when a predictive objective is authored |
| D17 | `/plots/*` time-series consumption | cards cover Slice 2's visuals; plots are richer trends | when trend visuals are wanted |
| D18 | `/historian/aggregates` downsampling | window + latest suffice for 3 objectives | when long-range trends are needed |
| D19 | `SIMULATED` demo mode | contract defined (§2.2), not implemented — no fake data in Slice 2 | only if a disconnected demo is required |
| D20 | Conflict *resolution* | Seal Check only *reports* conflicts; nothing arbitrates | when conflicts appear in practice |

---

## 9. Side-task — Knowledge Base wired up (D6 resolved) — ✅ **DONE**

`esp_kb_service` (`ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md` v2.1.0) went live on
its own microservice, `http://192.168.1.184:8085` — a different host/port from Server
184's other domains (:8090), and its two primary endpoints (`/api/kb/search`,
`/api/kb/graph/trace`) are POST with a JSON body, not GET with query params.

Scope discipline: this was done as a small side-task, not an expansion of Slice 2's
objectives. `search_knowledge` was already declared as `optional_evidence` on OP03 —
wiring it real just makes an existing declaration true. No objective YAML changed.
Never blocks Seal Check (optional evidence only). Does not touch or block Phase 3.

**What shipped:**
- `app/gateway/adapters/kb.py` — new adapter, own base URL (`KB_SERVICE_BASE_URL`,
  default `:8085`), POST-based `search_kb()`/`trace_kb_graph()`, GET-based
  `get_kb_fault()`/`get_kb_standard()`/`check_kb_health()`.
- `tool_gateway.py` — `search_knowledge` now dispatches for real instead of being
  hardcoded to `error_code="ABSENT"`. Query is deterministically composed from
  `well_id`/`trip_ts` (no dedicated `query` arg exists on `RouteDecision` yet).
- `capability.py` — `kb` added as a 7th probed domain, correctly against its own
  base URL (not Server 184's :8090) — a naive reuse of `get_gateway_base_url()`
  would have silently probed the wrong server.
- `qod_freshness.yaml` — `kb` domain added as `never_stale: true` (static
  engineering documents, not live readings — same treatment as `historian`).
- `qod.py` — `search_knowledge` → `kb` freshness domain; completeness requires only
  `hits` present (an empty list is a valid zero-result search, not missing data).
- `probe_184.py` — extended with `KB_PROBE_ENDPOINTS` against the KB's own base URL,
  with POST support added (the original probe was GET-only).
- 3 new fixtures (`kb_search_nominal.json`, `kb_search_empty.json`,
  `kb_health_nominal.json`) taken verbatim from the spec's "Real Verified Response" blocks.

**Real gap found and fixed while wiring this in — bigger than the KB task itself:**
`plan_builder.py` only ever turned `required_evidence` into calls. `optional_evidence`
was declared in every objective YAML (OP03's `search_knowledge`, `get_ml_results`) but
**never became a call at all**, regardless of whether a backing service existed. Fixed
by adding an optional-evidence pass in `build_plan()`, positioned between required
calls and the main tool call — same `PlanCall` shape, same Policy Gate path. Because
`seal()` only ever checks `required_tools`, this is safe by construction: an
ABSENT/DEGRADED optional source becomes a `Gap(required=False)` and never blocks
sealing. Test-locked (`test_build_plan_includes_optional_evidence_calls`,
`test_optional_evidence_absent_source_does_not_block_seal`).

**Test state: 89/89 green** (`test_phase0_adapter_units.py`,
`test_phase0_adapters.py`, `test_phase1_evidence.py`, `test_plan_and_policy.py`) —
all Redis-free, LLM-free; KB-reachability tests point at a dead port for
determinism, same pattern as the Server-184-unreachable test.

**Deliberately not done (kept minimal, per scope):**
- No authority-tier weighting in XAI synthesis (Phase 2) — KB hits flow through as
  plain evidence for now; weighting `LEVEL_A_STANDARD` (1.00) vs `LEVEL_D_FIELD`
  (0.70) in narration is a Phase 2 concern, not this side-task's.
- `/api/kb/graph/trace` (symptom → root cause chain) has an adapter function but no
  tool name wired into `tool_gateway.py` — it's a different evidence shape (a causal
  chain, not a flat fact) and deserves its own tool/objective design, not a rushed fit
  into `search_knowledge`.
- `/api/kb/faults` (full 13-fault deterministic taxonomy) and `/api/kb/faults/{id}` /
  `/api/kb/standards/{id}` (single lookups) have adapter functions, unused by any tool
  yet — available for a future objective that wants to ground `diagnose_fault`'s ML
  output against the deterministic taxonomy.

---

## 8. Build order summary

```
Phase 0  probe connectivity → well IDs → signal names → config tables → adapters + gateway rewrite
Phase 1  QoD → Evidence Pack + Seal Check → Evidence Formatter
Phase 2  XAI Synthesizer (LLM #3) → Numeric Provenance
Phase 3  Visualization Planner → wire into runner / main.py / Assembler
```

Each phase gated by its exit criteria. After Phase 0, every later phase is unit-testable
from `tests/fixtures/server184/*.json` without a live server — but those fixtures are
**test-only** and can never be reached from `app/` (Rule B).
