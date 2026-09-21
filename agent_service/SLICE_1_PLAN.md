# Slice 1 — Simple Path + CLARIFY — Build Plan

**Status: ready to build.**

One self-contained document. Everything needed to build Slice 1 is here —
prerequisites, the contracts to write, the build order, the CLARIFY
mechanism, and the end-to-end test that proves it works. You should not
need to open the other docs while building, but they are cross-referenced
where deeper detail lives.

Reference docs (only if you need more depth):
- `ARCHITECTURE.md` — full design, all invariants, HITL §6, Assembler §12
- `CONTRACTS_PLAN.md` — every Pydantic model across all slices
- `IMPLEMENTATION_SEQUENCE.md` — all 19 stages, all 4 slices

---

## 1. What Slice 1 delivers

The smallest complete loop: a user sends a message, and either gets a
plain answer back, or gets asked a clarifying question, answers it, and
then gets the answer. End to end, through the real frontend.

```
Frontend → POST /query → Context Resolver → Query Router
   ├── clear + simple  → Direct Handler → Response Assembler → frontend
   └── ambiguous       → CLARIFY (pause) → frontend asks user
                         user replies → BIND → resume → answer
```

**In scope:**
- `POST /query` endpoint, streaming NDJSON response
- Session + run + pending state in Redis
- Objective Registry (minimal — the two Slice 1 objectives, §2.4)
- Context Resolver (asset/time/pending resolution)
- Query Router (LLM #1) — classify + pick objective
- CLARIFY as the uniform pause/resume mechanism (phase-driven)
- Direct Handler (LLM #2) — simple/glossary answers
- Response Assembler — streams frames, ends in `done`
- Audit sink
- Full end-to-end CLARIFY round-trip test

**Explicitly NOT in scope (later slices):**
- Plan Builder, Policy Gate, Tool Gateway, Evidence Pack, QoD, XAI,
  Visualization, Numeric Provenance → Slice 2
- APPROVE / `POST /decision` → Slice 3
- Follow-up handler → Slice 4
- Real embedding search in Capability Retrieval → stubbed here, real in
  Slice 2

---

## 2. Prerequisites — have these ready before writing code

### 2.1 Runtime / infrastructure

| Prereq | Detail |
|---|---|
| Python 3.12 | matches the target deploy runtime |
| Redis running | local instance; `REDIS_URL=redis://127.0.0.1:6379/0` |
| Local `llama-server` | Qwen2.5-Coder-3B-Instruct-Q4_K_M, OpenAI-compatible, on `:8080`. **Set `-c 8192`** (not the 4096 default in `start_gpu_llm.bat`) to match prod context ceiling. |
| FastAPI + uvicorn | the service framework |
| `pydantic` v2 | all contracts |
| `redis` (py client), `httpx` | Redis access + LLM HTTP calls |

**Transport (decided):** `POST /query` returns a FastAPI
`StreamingResponse` with `media_type="application/x-ndjson"` — chunked
HTTP, not SSE, not WebSocket. Each frame is `frame.model_dump_json() +
"\n"`. This matches what the migrated frontend already consumes.

### 2.2 Config (env vars, all read at startup — nothing hardcoded)

```env
LLM_GATEWAY_URL=http://127.0.0.1:8080/v1
LLM_MODEL_NAME=Qwen2.5-Coder-3B-Instruct-Q4_K_M
LLM_TIMEOUT_SEC=30          # generous — CPU inference on prod is slower than local GPU
REDIS_URL=redis://127.0.0.1:6379/0
CONFIDENCE_THRESHOLD=0.6    # below this, Router forces CLARIFY
PENDING_TTL_SEC=900         # 15 min
RUN_TTL_SEC=86400           # 24 h
```

### 2.3 Decisions already locked (do not re-open)

- **Asset priority:** `EXPLICIT > RESOLVED > SESSION > UI > UNRESOLVED`
- **Keep both** `intent` and `objective_id` in `RouteDecision`
- **Multi-intent:** single objective + `deferred_intents`; READ before
  WRITE; a WRITE is never bundled with a READ (Slice 1 rarely hits this,
  but the field exists from day one)
- **`needs_clarify` rule:** an unresolved asset alone must NOT block the
  Router. The Router always runs exactly once per run. Missing asset is
  caught later as a CLARIFY, not by skipping the Router.

### 2.4 Objectives needed for Slice 1

Slice 1 only needs a couple of objectives to route into, since the deep
workflow machinery isn't built yet. At minimum author:
- `OP07_GENERAL_INQUIRY` (or equivalent) → routes to SIMPLE / Direct Handler
- one placeholder WORKFLOW objective (e.g. `OP01_CURRENT_STATUS`) so the
  Router has a real workflow target to classify into — even though the
  workflow pipeline is stubbed to "not built yet" in Slice 1

Full OP00–OP14 manifests are a Slice 2 prerequisite, not Slice 1.

---

## 3. Contracts to write in Slice 1

Only the subset needed for this slice. Full definitions in
`CONTRACTS_PLAN.md`; copied here so this doc stands alone.

### 3.1 `enums.py` (only the values Slice 1 touches)

```python
Route          = Literal["SIMPLE", "WORKFLOW", "FOLLOW_UP"]   # NOT CLARIFY — flag instead
AssetSource    = Literal["EXPLICIT", "RESOLVED", "SESSION", "UI", "UNRESOLVED"]
TimeSource     = Literal["EXPLICIT", "UI", "SESSION", "DEFAULT"]
TimeRangeLabel = Literal["last_1h", "last_6h", "last_24h", "last_7d", "last_30d"]
Resolution     = Literal["NEW", "BIND", "SUPERSEDE", "META"]
Scope          = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]
RunStatus      = Literal["RUNNING", "PAUSED", "DONE", "ABANDONED", "FAILED"]
InterruptType  = Literal["CLARIFY", "INSUFFICIENT", "APPROVE"]
ResumeAt       = Literal["CONTEXT", "ROUTER", "PLAN_BUILD", "SEAL_CHECK",
                          "GAP_FILL", "WRITE"]
FrameType      = Literal["status", "text_delta", "evidence", "clarification",
                          "interrupt", "visual", "advisory", "error", "done"]
```

Note: `Route` has no `CLARIFY` value — clarification is a flag
(`clarification_needed`) plus `clarify_*` fields, not a route.

### 3.2 `api.py`

```python
class UIContext(BaseModel):
    selected_asset: str | None = None
    selected_time_range: TimeRangeLabel | None = None
    selected_visualization: str | None = None
    selected_finding: str | None = None

class QueryRequest(BaseModel):
    session_id: str
    message: str
    ui_context: UIContext | None = None
```

### 3.3 `context.py`

```python
class Mentions(BaseModel):
    assets: list[str] = []
    times: list[str] = []
    analysis: list[str] = []
    pronouns: list[str] = []

class AssetBinding(BaseModel):
    id: str | None
    source: AssetSource
    confidence: float
    match_method: Literal["EXACT_ID", "ALIAS", "PRONOUN", "NONE"] = "NONE"

class TimeBinding(BaseModel):
    instant: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    source: TimeSource
    label: str | None = None
    confidence: float

class SessionSnapshot(BaseModel):
    last_objective: str | None
    last_analysis_id: str | None
    turn_count: int

class ContextFrame(BaseModel):
    session_id: str
    raw_message: str
    mentions: Mentions
    asset: AssetBinding
    time: TimeBinding
    resolution: Resolution
    pending_ref: str | None
    prior_analysis_ref: str | None
    needs_clarify: bool
    clarify_reason: str | None
    session_snapshot: SessionSnapshot
```

### 3.4 `routing.py`

```python
class CandidateTool(BaseModel):
    tool: str
    score: float

class RouterInput(BaseModel):
    raw_message: str
    asset_id: str | None
    asset_source: AssetSource
    time_label: str | None
    time_instant: datetime | None
    has_prior: bool
    prior_objective: str | None
    turn_count: int
    candidate_objectives: list[str]
    candidate_tools: list[str]
    # deliberately NO flags / full pending / full resolution — see §5

class RouteDecision(BaseModel):
    route: Route
    intent: str | None
    objective_id: str | None
    args: dict
    confidence: float
    deferred_intents: list[str] = []
    clarification_needed: bool
    clarify_reason: InterruptType | None
    clarify_slot: str | None
    clarify_options: list[str] = []
```

### 3.5 `hitl.py`

```python
class PendingInterrupt(BaseModel):
    run_id: str
    reason: InterruptType
    resume_at: ResumeAt
    slot: str | None
    options: list[str] = []
    plan_ref: str | None
    pack_ref: str | None
    raised_at: datetime

class RunState(BaseModel):
    run_id: str
    session_id: str
    status: RunStatus
    resume_at: ResumeAt | None
    objective_id: str | None
    args: dict
    confidence: float | None
    plan: list = []               # empty in Slice 1 (no Plan Builder yet)
    evidence_pack_ref: str | None = None
    pending_ref: str | None = None
    decision: dict | None = None
    turn_count: int
    replan_count: int = 0
```

### 3.6 `events.py` (the frames Slice 1 actually emits)

```python
class TextDeltaFrame(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    run_id: str
    delta: str

class ClarificationFrame(BaseModel):
    type: Literal["clarification"] = "clarification"
    run_id: str
    question: str
    options: list[str] = []
    slot: str | None
    pending_ref: str | None

class ErrorFrame(BaseModel):
    type: Literal["error"] = "error"
    run_id: str
    code: str
    message: str

class DoneFrame(BaseModel):
    type: Literal["done"] = "done"
    run_id: str
    status: str | None = None

class StatusFrame(BaseModel):
    type: Literal["status"] = "status"
    run_id: str
    stage: str
    progress: int
    message: str
```

`AdvisoryFrame`, `VisualFrame`, `InterruptFrame` exist in the contracts
but are **not emitted in Slice 1** (workflow / approve routes). Build the
models if convenient, but Slice 1 only needs the five above.

---

## 4. Build order — phases, steps, and handoffs

Same dependency rule as always: contracts → deterministic logic →
LLM/network last. But a flat checklist hides the one failure mode that
actually stalls a build: **a step produces an artifact that no later step
consumes, or a step needs an input that no earlier step produces.** So
every step below declares four things explicitly:

- **Stage** — which of the 19 stages in `IMPLEMENTATION_SEQUENCE.md` this
  maps to (some Slice 1 steps are finer-grained than a stage; noted where
  so).
- **Consumes** — the exact artifact(s) it takes in, and *from which step*.
- **Produces** — the exact artifact it emits, and *which later step reads
  it*. If nothing reads it, the step should not exist yet.
- **Deliverable + Test + DoD** — the file(s), the test, and the pass bar.

Each **phase ends with an integration checkpoint**: wire the steps built
so far together with fixtures and run the chain end-to-end. That
checkpoint is what catches an orphaned producer or a starved consumer —
you do not move to the next phase until the chain flows through.

The handoff chain for the whole slice, one line:

```
message ─▶ ContextFrame ─▶ RouterInput ─▶ RouteDecision ─┬▶ (SIMPLE)  text ─────────▶ AssemblerInput ─▶ NDJSON frames
                                                          └▶ (unroutable/low-conf) CLARIFY ─▶ PendingInterrupt ─▶ [reply turn] ─▶ BIND ─▶ resume
```

Everything below exists to make each arrow in that line a typed, tested
handoff — not an assumption.

---

### Phase 0 — Foundations (no LLM, no network beyond Redis)

Nothing here talks to an LLM or an external API. All of it is testable
with hand-written fixtures alone.

#### Step 0.1 — Contracts
- **Stage:** 1.
- **Consumes:** nothing (root of the dependency tree).
- **Produces:** the Pydantic models in §3 (`enums`, `api`, `context`,
  `routing`, `hitl`, `events`). **Read by every other step.**
- **Deliverable:** `app/contracts/*.py` exactly as §3, `enums.py` the sole
  home of every `Literal` set.
- **Test:** construct one instance of each model from realistic data;
  assert `.model_dump_json()` round-trips back to an equal instance.
- **DoD:** every §3 model imports and round-trips; no enum value defined
  in two files.

#### Step 0.2 — Redis stores
- **Stage:** 2.
- **Consumes:** the contract models from 0.1 (`SessionState`, `RunState`,
  `PendingInterrupt`).
- **Produces:** `get/save_session`, `get/save_run`,
  `get/set_pending` (TTL 15 min, single-slot),
  `clear_pending`. **Read by 1.1, 1.2, 2.1, 3.1, 4.1.**
- **Deliverable:** `app/run/run_store.py`, `app/context/session_store.py`,
  `app/hitl/pending_store.py`.
- **Test:** save a `RunState` fixture from 0.1, load, assert equality;
  assert TTL is actually set (`TTL` command returns > 0, not just
  "didn't error"); assert an expired pending returns `None`.
- **DoD:** CRUD + TTL proven against a live local Redis, using only 0.1
  fixtures as data.

#### Step 0.3 — Objective Registry (minimal) — *new step, was missing*
- **Stage:** 3.
- **Consumes:** `config/objectives/*.yaml`.
- **Produces:** `Dict[str, ObjectiveManifest]` loaded at startup, plus
  `list_objective_descriptions()` returning `[{objective_id,
  description}]`. **Read by 1.3 (candidate list) and 2.1 (Router
  validates `objective_id` against this map).**
- **Why it's called out:** the old flat checklist had no step that loaded
  objectives, yet the Router (2.1) consumes `candidate_objectives` and
  must reject any `objective_id` not in the registry. Without this step,
  2.1 has nothing to validate against — the exact starved-consumer bug
  this restructure is meant to prevent.
- **Deliverable:** `app/routing/objective_registry.py` + the two Slice 1
  manifests from §2.4 (`OP07_GENERAL_INQUIRY`, one placeholder WORKFLOW
  objective e.g. `OP01_CURRENT_STATUS`).
- **Test:** load both YAML files; assert each parses into an
  `ObjectiveManifest`; assert `list_objective_descriptions()` returns a
  non-empty entry per file.
- **DoD:** registry loads at startup; a lookup by unknown `objective_id`
  returns `None` (so 2.1 can treat it as a router defect, not a crash).

> **Phase 0 checkpoint:** from a `RunState` fixture, save → load → confirm
> equality through the real stores; load the registry; confirm a Router
> would find `OP07` present and `OP99` absent. No orphan: every model in
> 0.1 is now either stored (0.2) or looked up (0.3).

---

### Phase 1 — Request entry & context (deterministic)

Turns a raw `POST /query` message into a typed `ContextFrame` and the
filtered `RouterInput` the LLM will see. Still no LLM call.

#### Step 1.1 — Context Resolver
- **Stage:** part of request-entry; uses Stage 2 stores. (Not its own
  numbered stage — it's the front door.)
- **Consumes:** `QueryRequest` (0.1) + session state (0.2).
- **Produces:** a full `ContextFrame` — `asset` (with `source` +
  `match_method`), `time`, `mentions`, `resolution`, `pending_ref`,
  `needs_clarify`. **Read by 1.2 (pending), 1.3 (candidate retrieval),
  2.1 (RouterInput is derived from it).**
- **Deliverable:** `app/context/resolver.py` + `config/asset_aliases.yaml`
  for the deterministic alias/nickname table (feeds `match_method=ALIAS`).
- **Test:** asset priority order honored (`EXPLICIT > RESOLVED > SESSION >
  UI > UNRESOLVED` — message "FS-091" beats `ui_context.selected_asset`
  "FNW-01"); alias hit ("the flowstation" → FS-017) sets
  `match_method=ALIAS`, confidence ~0.8; unresolved pronoun ("it", no
  session asset) sets `id=None, source=UNRESOLVED` and **`needs_clarify=
  false`** (must not block the Router — §5.1).
- **DoD:** every branch of asset/time resolution covered; the
  unresolved-asset case explicitly proven not to set blocking clarify.

#### Step 1.2 — Pending resolution (BIND / SUPERSEDE / META)
- **Stage:** 17 (HITL, the CLARIFY-resolve half).
- **Consumes:** the incoming message + the `PendingInterrupt` for the
  session (0.2), surfaced by 1.1.
- **Produces:** a `Resolution` verdict (`BIND | SUPERSEDE | META`) and, on
  BIND, the patched slot value. **Read by 4.1 (endpoint routes the reply
  turn) and 3.1 (BIND calls resume).**
- **Deliverable:** `app/context/pending_resolve.py`.
- **Test:** each branch — BIND (message matches slot type/options),
  SUPERSEDE (new unrelated objective; asserts old pending closed as
  `ABANDONED` + audit record written), META (question about the pending;
  pending stays open). Expired pending → treated as new query.
- **DoD:** all three branches + the expiry path covered; SUPERSEDE proven
  to audit and close, never silently bind.

#### Step 1.3 — Capability Retrieval (**stub in Slice 1**)
- **Stage:** 4 (stubbed; real embedding search is a Slice 2 prerequisite).
- **Consumes:** `raw_message` from the `ContextFrame` (1.1) + objective
  descriptions from the registry (0.3).
- **Produces:** `candidate_objectives` + `candidate_tools` (fixed list in
  the stub). **Read by 2.1 (Router prompt shrink).**
- **Deliverable:** `app/routing/capability_retrieval.py` returning a
  deterministic candidate list keyed off the two Slice 1 objectives.
- **Test:** returns a non-empty candidate list containing both Slice 1
  objectives; interface signature matches what Slice 2 will replace
  (`retrieve(query, top_k) -> list[CandidateTool]`), so the swap later is
  drop-in.
- **DoD:** stub returns a stable list; nothing downstream depends on it
  being *smart*, only on it being *present and correctly shaped*.

> **Phase 1 checkpoint:** feed a `QueryRequest` fixture end-to-end through
> 1.1 → 1.3, assemble a `RouterInput`, and assert it carries `asset_id`,
> `candidate_objectives`, and **none of** `flags`/full `pending`/full
> `resolution` (§5.2). No orphan: `ContextFrame` is consumed by the
> RouterInput builder; candidates are attached. A reply-turn fixture with
> a live pending must route through 1.2 and produce a `BIND`.

---

### Phase 2 — Routing & answering (LLM)

First LLM calls. Correctness-tested against the local GPU `llama-server`
(§2.1), never latency-tested there.

#### Step 2.1 — Query Router (LLM #1)
- **Stage:** 5.
- **Consumes:** `RouterInput` (built from 1.1 + 1.3).
- **Produces:** a validated `RouteDecision` — `route`, `objective_id`,
  `args`, `confidence`, `clarification_needed` + `clarify_*`. **Read by
  4.1 (dispatch), 2.2 (SIMPLE), 3.1 (CLARIFY).**
- **Deliverable:** `app/routing/router.py` — LLM call + strict JSON parse
  + the deterministic post-checks below.
- **Test:** 20–30 hand-verified query→route pairs. Every failure mode
  proven to fall back to `clarification_needed=true`, never crash:
  malformed JSON → one stricter retry then CLARIFY; `objective_id` not in
  registry (0.3) → CLARIFY + logged as router defect; `confidence` below
  `CONFIDENCE_THRESHOLD` → forced CLARIFY; `args` fail the manifest
  `arg_schema` → CLARIFY naming the missing `clarify_slot`.
- **DoD:** runs exactly once per run (§5.1); every non-happy path lands on
  CLARIFY; no `route="CLARIFY"` value ever emitted (flag only).

#### Step 2.2 — Direct Handler (LLM #2)
- **Stage:** 15.
- **Consumes:** `RouteDecision` with `route == SIMPLE` + `raw_message`.
- **Produces:** plain narrated `text`. **Read by 3.2 (Assembler) as
  `AssemblerInput.text`.**
- **Deliverable:** `app/synthesis/direct_handler.py`; exact-glossary-hit
  shortcut checked first (skips LLM #2 on a direct KB match).
- **Test:** the bypass proof — assert Evidence Pack / XAI / Visualization
  modules are **never** imported or called on this path (not just that
  the answer looks right — §ARCHITECTURE regression from `CONVERSATION_
  HISTORY.md` §4).
- **DoD:** SIMPLE answers produced; bypass proven by a no-call assertion,
  not by inspection.

> **Phase 2 checkpoint:** message → 1.1 → 1.3 → 2.1 → (SIMPLE) → 2.2 →
> `text`. Assert a clean SIMPLE query produces text with no pending
> written; assert a low-confidence query produces a `RouteDecision` with
> `clarification_needed=true` and **no** `text` (it must fall to Phase 3,
> not answer). No orphan: `RouteDecision` is consumed on both branches.

---

### Phase 3 — Pause/resume & streaming (deterministic)

The HITL machinery and the single exit every route funnels through.

#### Step 3.1 — CLARIFY engine (pause + phase-driven resume)
- **Stage:** 17.
- **Consumes:** a CLARIFY trigger from 1.1 (unroutable) or 2.1 (low
  confidence / bad args), plus the BIND verdict from 1.2 on the reply
  turn.
- **Produces:** on raise — a `PendingInterrupt` (0.2) + a run set to
  `PAUSED` with `resume_at`; on reply — a `resume(run, bound_value)` call
  dispatched through the `RESUME_TABLE`. **Pending read by 4.1; the
  emitted `ClarificationFrame` read by 3.2.**
- **Deliverable:** `app/hitl/clarify.py` (the `raise_clarify` /
  `RESUME_TABLE` / `resume` from §6).
- **Test:** raise → pause → reply → resume returns to the correct
  `resume_at`; an unregistered `resume_at` raises a **hard error** (fail
  loud, never silently continue); BIND resume never re-invokes the Router
  (§5.1).
- **DoD:** round-trip proven; unknown-phase path proven to hard-fail.

#### Step 3.2 — Response Assembler
- **Stage:** 18.
- **Consumes:** `AssemblerInput` — `text` from 2.2, or a
  `PendingInterrupt`/`ClarificationFrame` from 3.1, tagged by `route`.
- **Produces:** a **stream** of NDJSON frames (0.1 `events`), always
  ending in exactly one `DoneFrame`. **Read by 4.1 (the endpoint streams
  it to the frontend).**
- **Deliverable:** `app/synthesis/response_assembler.py` — a generator
  that *yields* frames, never returns a blob.
- **Test:** one input per route → assert the exact frame sequence and a
  single terminating `DoneFrame`; empty/whitespace `text` → `ErrorFrame(
  code="EMPTY_LLM_OUTPUT")` then `DoneFrame`, never a blank answer;
  CLARIFY → `ClarificationFrame`; frame `type` only ever from the enum.
- **DoD:** every route's frame sequence pinned by test; no path can emit
  zero frames or two `DoneFrame`s.

> **Phase 3 checkpoint:** drive both a SIMPLE answer and a CLARIFY pause
> through 3.2 and assert the emitted frame sequences match exactly. Raise
> a CLARIFY, confirm a `PendingInterrupt` lands in Redis and the stream
> carries a `ClarificationFrame` + `DoneFrame`. No orphan: every frame
> type Slice 1 emits has a producer, and the Assembler is the sole exit.

---

### Phase 4 — Integration & endpoint

Wires the pieces into the live door and proves the whole loop.

#### Step 4.1 — `POST /query` endpoint
- **Stage:** wire-up (no new stage).
- **Consumes:** an HTTP `QueryRequest`; internally drives 1.1 → 1.3 →
  2.1 → {2.2 | 3.1} → 3.2. On a reply turn with live pending, routes
  through 1.2 first.
- **Produces:** a FastAPI `StreamingResponse`,
  `media_type="application/x-ndjson"`, one `frame.model_dump_json()+"\n"`
  per line (§2.1 transport decision).
- **Deliverable:** `app/main.py` with the `/query` route + a `/health`.
- **Test:** a new-query request streams NDJSON ending in `done`; a
  reply-turn request with a stored pending resolves via BIND and resumes.
- **DoD:** the endpoint streams; both turn types flow through without the
  Router running twice on a BIND.

#### Step 4.2 — Audit sink
- **Stage:** 19.
- **Consumes:** `audit.record(event_type, payload)` calls **already
  dropped into steps 0.2–4.1 as they were built** (not bolted on now).
- **Produces:** append-only records; write-only; never blocks the main
  path.
- **Deliverable:** `app/audit/audit_sink.py`.
- **Test:** run the §7 round-trip; assert a record exists at every stage
  boundary (context, router, clarify, resume, answer).
- **DoD:** every boundary crossed in the e2e test left an audit record.

#### Step 4.3 — End-to-end acceptance test
- **Stage:** the acceptance gate (§7).
- **Consumes:** the whole assembled service.
- **Produces:** pass/fail on the Slice 1 contract.
- **Deliverable:** `tests/test_slice1_e2e.py`.
- **Test / DoD:** the two-turn CLARIFY round-trip in §7 passes, plus the
  three unit-level acceptance checks (clean SIMPLE, empty-LLM →
  ErrorFrame, asset priority EXPLICIT-beats-UI).

> **Phase 4 checkpoint = Slice 1 done (§8).** The full loop runs through
> the real frontend contract, switching only on frame `type`.

---

### Handoff summary (every arrow must have both ends)

| Producer step | Artifact | Consumer step(s) |
|---|---|---|
| 0.1 Contracts | Pydantic models | all |
| 0.2 Redis stores | session/run/pending CRUD | 1.1, 1.2, 2.1, 3.1, 4.1 |
| 0.3 Objective Registry | `Dict[objective_id, ObjectiveManifest]` | 1.3, 2.1 |
| 1.1 Context Resolver | `ContextFrame` | 1.2, 1.3, 2.1 |
| 1.2 Pending resolution | `Resolution` verdict + bound value | 3.1, 4.1 |
| 1.3 Capability Retrieval (stub) | candidate lists | 2.1 |
| 2.1 Query Router | `RouteDecision` | 2.2, 3.1, 4.1 |
| 2.2 Direct Handler | `text` | 3.2 |
| 3.1 CLARIFY engine | `PendingInterrupt` + `ClarificationFrame` | 3.2, 4.1 |
| 3.2 Response Assembler | NDJSON frame stream | 4.1 |
| 4.1 `/query` endpoint | `StreamingResponse` | frontend |
| 4.2 Audit sink | append-only records | out-of-band (audit/trace) |

If a row's consumer column is empty, that step is premature — do not
build it in Slice 1. If a step needs an input absent from every
producer's artifact column, a producer step is missing (this is exactly
how 0.3 was found).

---

## 5. The two rules that prevent the known bugs

### 5.1 Router always runs exactly once — missing asset does NOT skip it

An unresolved asset (e.g. "why did *it* trip" with no session asset) must
**not** set `needs_clarify=true` at the Context stage in a way that skips
the Router. Flow instead:

1. Context Resolver: `asset.id = None`, `asset.source = UNRESOLVED`,
   `needs_clarify = false`.
2. Router runs, still identifies the objective (fault diagnosis) with
   `args.asset_id = None`.
3. The missing asset is caught **after** the Router (at Plan Builder in
   Slice 2, or by the Router itself flagging `clarification_needed` if it
   can't proceed) — raised as a CLARIFY.

`needs_clarify=true` at the Context stage is reserved for messages that
are completely unroutable on their own.

### 5.2 RouterInput is a filtered copy — never the full ContextFrame

The Router receives `RouterInput`, which deliberately omits `flags`,
full `pending`, full `resolution`, and `last_analysis_id`. This stops the
Router from short-circuiting itself on a flag. The **full `ContextFrame`
stays alive for the whole request** — later stages (and Follow-up in
Slice 4) read from it; `RouterInput` is only the LLM's view.

---

## 6. CLARIFY mechanism (build it uniform, use it narrow)

Even though only Context Resolver and Query Router raise CLARIFY in Slice
1, build the engine as the general phase-driven mechanism so Slices 2–4
reuse it unchanged.

```python
def raise_clarify(run_id, session_id, reason, slot, options, resume_at):
    pending = PendingInterrupt(run_id=run_id, reason=reason, resume_at=resume_at,
                               slot=slot, options=options, raised_at=now())
    save_pending(session_id, pending)          # TTL 15 min, single-slot, overwrites+audits old
    run = load_run(run_id); run.status = "PAUSED"; run.resume_at = resume_at
    save_run(run)
    return ClarificationFrame(run_id=run_id, question=template(reason, slot),
                              options=options, slot=slot,
                              pending_ref=pending_key(session_id))

RESUME_TABLE = {
    "CONTEXT":    continue_after_context,
    "ROUTER":     continue_after_router,
    # PLAN_BUILD / SEAL_CHECK / GAP_FILL / WRITE registered in later slices
}

def resume(run_id, bound_value):
    run = load_run(run_id)
    fn = RESUME_TABLE.get(run.resume_at)
    if fn is None:
        raise HardError(f"no resume handler for {run.resume_at}")   # fail loud
    return fn(run, bound_value)
```

On the reply turn, Context Resolver sees the pending and calls
`resolve(message, pending)` → BIND / SUPERSEDE / META (§3.4 `Resolution`).
BIND patches the slot and calls `resume(...)`. BIND is fully
deterministic — it never calls the Router again.

---

## 7. Acceptance test — the whole point of Slice 1

If this passes, the hardest machinery (pause/resume, Redis, streaming,
frontend contract) is proven on the simplest path.

```
Turn 1:
  POST /query {session_id:"S1", message:"why did it trip?"}
  (no session asset, "it" is an unbound pronoun)
  EXPECT: stream contains one ClarificationFrame
          (question about which asset, options listed),
          then a DoneFrame.
  ASSERT: pending state written for S1; run status = PAUSED;
          Router ran exactly once; audit has records for context+router+clarify.

Turn 2:
  POST /query {session_id:"S1", message:"FS-017"}
  EXPECT: Context Resolver sees pending → BIND;
          run resumes at resume_at; Direct Handler (or stubbed workflow)
          produces an answer; stream contains TextDeltaFrame(s) then DoneFrame.
  ASSERT: pending cleared; run status = DONE;
          Router did NOT run again on this turn;
          audit has records for resume + answer.
```

Plus unit-level acceptance:
- Simple query with no ambiguity ("what does underload mean?") → straight
  to Direct Handler → answer, no clarification, no pending written.
- Empty/garbage LLM output → Assembler emits ErrorFrame, never blank.
- Asset priority: message says "FS-091" while `ui_context.selected_asset`
  = "FNW-01" → resolved asset is FS-091 (EXPLICIT beats UI).

---

## 8. Definition of done for Slice 1

Each phase in §4 must pass its **integration checkpoint** before the next
phase starts — that gating is what keeps an orphaned producer or starved
consumer from surfacing three phases later. Slice 1 is done when all four
phase checkpoints pass and:

- All §3 contracts exist with round-trip tests (Phase 0).
- Redis stores + Objective Registry load and are proven (Phase 0).
- `POST /query` streams NDJSON, every stream ends in exactly one `done`
  (Phase 3/4).
- CLARIFY round-trip acceptance test (§7) passes (Phase 4).
- Direct Handler proven to bypass Evidence/XAI/Visual by no-call
  assertion (Phase 2).
- Asset priority order (`EXPLICIT > … > UI`) proven by test (Phase 1).
- Router proven to run exactly once per run, even with missing asset
  (Phase 1/2).
- Every step's **handoff** verified — the §4 handoff-summary table has no
  empty consumer column, and every consumed input has a named producer.
- Audit records exist at every stage boundary (Phase 4).
- Frontend can drive the whole loop switching only on frame `type`.
