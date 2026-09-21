# Implementation Sequence — ESP Agent Service

Companion to `ARCHITECTURE.md`. That doc says *what* each component is and
*why*. This doc says *what order to build in* and, for each component,
the exact **input schema** and **output schema** it must honor — so when
something breaks later, you know which side of which contract broke it.

Starting point assumed: the Query API is done. A request already arrives
as `POST /query {session_id, message}` with `message` as plain text. This
doc starts from there and goes inward.

## Two build axes: slices (which feature first) and stages (what order inside a feature)

There are two different ordering questions, and they answer different
things. Don't mix them up.

- **Vertical slices** decide *which feature* to make work end-to-end
  first. We build a whole path — frontend → API → response — prove it,
  then add the next path.
- **Stages** (the numbered list further down) decide *what order to build
  the pieces* inside any given slice, so nothing breaks halfway through.

### Slice order (feature order)

| Slice | What it delivers | Why this order |
|---|---|---|
| **Slice 1** | Simple path **+ CLARIFY** | Smallest full loop (no Evidence Pack, no Tool Gateway). Builds the hardest part of HITL — pause/resume, pending state, Redis, phase-driven resume — on the simplest query type, where nothing else can go wrong at the same time. |
| **Slice 2** | Workflow path | The big one. Plan Builder, Policy Gate, Tool Gateway, Evidence Pack, XAI. CLARIFY already works from Slice 1, so Workflow reuses it (e.g. missing `asset_id`) rather than inventing it. |
| **Slice 3** | APPROVE | Only fires for `WRITE` actions inside a workflow plan, so it can't exist before Slice 2. Adds the `/decision` door + staleness re-check. |
| **Slice 4** | Follow-up | Needs real sealed analyses from Slice 2 to refer back to — nothing to follow up on before then. |

Key point: **CLARIFY is not a workflow-only feature.** It is a
cross-cutting capability any stage can raise (see `ARCHITECTURE.md` §6.1),
which is exactly why it belongs in Slice 1 on the Simple path. APPROVE is
the only HITL reason that is genuinely workflow-only, because it exists
solely for `WRITE` actions.

## Why the stage order below

Build in dependency order, not diagram order. Each numbered stage below
can be unit-tested with the previous stage's real output as fixture data
— no component before stage 9 needs a live LLM or a live Server3 endpoint
to be testable. That's deliberate: it means routing, policy, and plan
logic are fully verifiable before a single network call exists, and
every schema is pinned before the two riskiest pieces (LLM output
parsing, external API integration) get built against it.

Slices and stages compose: Slice 1 builds stages 1–5, 15, the CLARIFY
parts of 17, and **stage 18 (Response Assembler)** — the last is built
here on purpose, because every route ends at it and building it once in
Slice 1 means Slices 2–4 reuse it unchanged. Slice 2 adds stages 6–14.
Slice 3 adds the APPROVE parts of stage 17. Slice 4 adds stage 16.

```
1. Contracts               (schemas only, no logic)
2. Redis stores            (session / run / pending — CRUD only)
3. Objective Registry      (static config, no logic)
4. Capability Retrieval    (embeddings, no LLM)
5. Query Router            (LLM #1 — first LLM dependency)
6. Plan Builder            (deterministic)
7. Policy Gate             (deterministic — build before Gateway, not after)
8. Tool Gateway + adapters (first external-API dependency)
9. QoD                     (deterministic)
10. Evidence Pack + Seal   (deterministic)
11. Gap-Fill Selector      (LLM #4 — optional path)
11.5 Evidence Formatter    (deterministic — makes numeric provenance enforceable)
12. XAI Synthesizer        (LLM #3)
13. Numeric Provenance     (deterministic — build before shipping XAI to users)
14. Visualization Planner  (deterministic)
15. Direct Handler         (LLM #2 — simplest path, but built late on purpose, see note)
16. Follow-up Handler      (reuses #12)
17. HITL — interrupts, pending, decision API
18. Response Assembler     (terminal stage for every route — build in Slice 1, reused by all)
19. Audit sink             (cross-cutting, wire in from stage 2 onward)
```

Note on stage 15: Direct Handler is the *simplest* component but is
sequenced late because it must bypass the full pipeline correctly (a
known regression from earlier design review — see `CONVERSATION_HISTORY.md`
§4). Building it after the WORKFLOW path exists makes the bypass
verifiable by contrast, not by assumption.

---

## Stage 1 — Contracts

No behavior. Pure data shapes. Every other stage imports from here and
nowhere else defines these shapes twice. This is the single highest-
leverage place to get right, because a change here after Stage 8 means
touching every adapter.

### `contracts/evidence.py`

```python
class EvidenceItem(BaseModel):
    evidence_id: str          # stable, e.g. "EV-{run_id}-{seq}"
    tool: str                 # e.g. "get_live_telemetry"
    source_domain: str        # asset|telemetry|historian|ml|engineering|twin|events|kb|cases|maintenance
    fetched_at: datetime
    freshness_sec: float | None
    status: Literal["OK", "STALE", "PARTIAL"]
    payload: dict             # tool-specific, validated by the adapter's own schema
    unit_map: dict[str, str]  # field -> unit, required if payload has numeric fields

class EvidencePack(BaseModel):
    run_id: str
    version: int               # v1, v2, ... — packs are never mutated in place
    sealed: bool
    sealed_at: datetime | None
    items: list[EvidenceItem]
    gaps: list[Gap]            # named ABSENT/DEGRADED sources, never silently dropped
    conflicts: list[Conflict]

class Gap(BaseModel):
    source_domain: str
    reason: Literal["ABSENT", "DEGRADED", "TIMEOUT"]
    required: bool             # from objective manifest

class Conflict(BaseModel):
    description: str
    evidence_ids: list[str]
```

### `contracts/plan.py`

```python
class PlanCall(BaseModel):
    seq: int
    kind: Literal["READ", "WRITE"]
    tool: str
    args: dict
    status: Literal["PENDING", "OK", "FAILED", "SKIPPED"]
    evidence_id: str | None    # set once executed

class PlanArtifact(BaseModel):
    run_id: str
    session_id: str
    objective_id: str
    args: dict
    confidence: float
    calls: list[PlanCall]
    requires_approval: bool    # true if any call.kind == WRITE
```

### `contracts/objective_manifest.py`

```python
class ObjectiveManifest(BaseModel):
    objective_id: str                    # "OP03_FAULT_DIAGNOSIS"
    tool: str                            # canonical tool name this objective binds to
    safety_class: Literal["READ", "WRITE"]
    required_evidence: list[str]         # tool names that MUST succeed
    optional_evidence: list[str]         # tool names, gap on failure is non-blocking
    allowed_visuals: list[str]           # widget ids VisualizationPlanner may choose from
    arg_schema: dict                     # JSON schema fragment for expected args
```

### `contracts/events.py` (NDJSON frame types, out to frontend)

```python
class Frame(BaseModel):
    type: Literal["status","text_delta","evidence","clarification",
                   "interrupt","visual","advisory","error","done"]
    run_id: str
    # payload fields vary by type — one Pydantic subclass per type,
    # see ARCHITECTURE.md §5 for which stage emits which type
```

**Output of Stage 1:** nothing runs. Deliverable is these files, plus a
test file per contract that constructs one instance of each and asserts
`.model_dump_json()` round-trips. This is the fixture data every later
stage's unit tests will reuse.

---

## Stage 2 — Redis Stores

Pure CRUD wrappers around the schemas from `ARCHITECTURE.md` §6.2/6.4.
No business logic — `get`, `set`, `patch`, TTL enforcement only.

**Input:** a `run_id` or `session_id` string, plus (on write) a dict
matching the contract shape.

**Output:** the stored dict, deserialized into the matching Pydantic
model, or `None` if missing/expired.

```python
# session_store.py
def get_session(session_id) -> SessionState | None
def get_pending(session_id) -> PendingInterrupt | None       # TTL 15 min, single-slot
def set_pending(session_id, pending: PendingInterrupt) -> None  # overwrites, audits old

# run_store.py
def get_run(run_id) -> RunState | None                        # TTL 24h
def save_run(run: RunState) -> None
def get_pack(run_id, version="latest") -> EvidencePack | None
def save_pack(run_id, pack: EvidencePack) -> None              # writes a new version, never overwrites
```

**Test without any other stage:** write a `RunState` fixture from Stage
1's test data, save, load, assert equality. Verify TTL is actually set
(`TTL` command, not just "doesn't error").

---

## Stage 3 — Objective Registry

Static YAML per objective, loaded at startup into `ObjectiveManifest`
instances, keyed by `objective_id`. This is data, not code — editing an
objective's required evidence should never require a code change.

**Input:** `config/objectives/OP00.yaml` ... `OP14.yaml`, one file per
objective, shape matching `ObjectiveManifest`.

**Output:** `Dict[str, ObjectiveManifest]`, plus `list_tool_descriptions()`
returning `[{tool, description}]` for Stage 4 to embed.

```yaml
# config/objectives/OP03.yaml
objective_id: OP03_FAULT_DIAGNOSIS
tool: diagnose_fault
safety_class: READ
scope: ASSET
required_evidence: [get_asset_context, get_live_telemetry, get_historian_window]
optional_evidence: [get_ml_results, search_knowledge]
allowed_visuals: [forensics-timeline, subsystem-equalizer]
arg_schema:
  type: object
  properties:
    asset_id: {type: string}
    trip_ts: {type: string, format: date-time}
  required: [asset_id]
```

**Test:** load all 15 files, assert every `tool` value in
`required_evidence`/`optional_evidence` exists in the (yet-to-be-built)
adapter registry — this test will fail until Stage 8, which is correct;
it's the contract check that keeps the two in sync going forward.

---

## Stage 4 — Capability Retrieval

**Input:** raw query text (`message` from the Query API), plus the tool
description list from Stage 3.

**Output:**

```python
class CandidateTool(BaseModel):
    tool: str
    score: float

def retrieve(query: str, top_k: int = 5) -> list[CandidateTool]
```

Embedding model loads once at startup (`all-mpnet-base-v2` or equivalent,
768-dim — see `ARCHITECTURE.md` §1.1, this is the one piece confirmed
already runnable locally). Tool descriptions embedded once at startup
and cached in memory; only the query is embedded per request.

**Test without LLM:** assert that for a handful of hand-written queries
("why did FS-017 trip", "show fleet maintenance priority"), the correct
tool appears in the top-5. This is the first stage where you're
validating against judgment, not just schema — write down the expected
answer per test query before running it.

---

## Stage 5 — Query Router (first LLM dependency)

**Input:**

The exact `RouterInput` and `RouteDecision` shapes are the canonical ones
in `CONTRACTS_PLAN.md` §4 — this stage builds against those, not a second
copy. Summarized here for convenience:

```python
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
    # deliberately NO flags / full pending / full resolution — the Router
    # must not be able to short-circuit itself on a flag (CONTRACTS_PLAN §5.2)
```

**Output — `RouteDecision`, the highest-risk schema in the service,
because it's the first thing an LLM produces and everything downstream
trusts it:**

```python
class RouteDecision(BaseModel):
    route: Route                  # SIMPLE | WORKFLOW | FOLLOW_UP  (NOT CLARIFY — see below)
    intent: str | None
    objective_id: str | None      # required if route == WORKFLOW
    args: dict                    # must validate against the objective's arg_schema
    confidence: float
    deferred_intents: list[str] = []
    clarification_needed: bool    # clarification is a FLAG, not a route value
    clarify_reason: InterruptType | None
    clarify_slot: str | None
    clarify_options: list[str] = []
```

Note: clarification is expressed by `clarification_needed=true` +
`clarify_*` fields, **not** by a `route="CLARIFY"` value. See the enum
note in `CONTRACTS_PLAN.md` §1.

**Failure modes to handle explicitly, not implicitly** (all set
`clarification_needed=true` rather than a `route` value):
- malformed JSON from the model → retry once with a stricter system
  prompt, then fall back to `clarification_needed=true` with a generic
  question — never crash the request.
- `objective_id` not in the registry → same fallback, log as a router
  defect (this should trend to zero, not be silently patched).
- `confidence` below a configured threshold (start at 0.6, tune from
  logs) → force `clarification_needed=true` regardless of what the model
  picked.
- `args` fails the objective's `arg_schema` → force
  `clarification_needed=true` with the specific missing field named as
  `clarify_slot`.

**Test:** run Stage 4's candidate lists through the real LLM (local GPU
is fine here, correctness only — see `ARCHITECTURE.md` §11 item 11) and
hand-verify 20-30 query/route pairs before trusting this stage. This is
where the two-stage domain→tool selection from `ARCHITECTURE.md` §3
gets implemented — build it as two calls to this same output schema
internally, not as a schema change.

---

## Stage 6 — Plan Builder (deterministic)

**Input:** `RouteDecision` (route == WORKFLOW) + the matching
`ObjectiveManifest` from Stage 3.

**Output:** `PlanArtifact` (Stage 1 schema), fully populated —
`required_evidence` entries become `READ` calls, the objective's `tool`
becomes the final call (`READ` or `WRITE` per `safety_class`),
`requires_approval` set mechanically from whether any call is `WRITE`.

No LLM. No network call. Pure function: `manifest + args → PlanArtifact`.
This is the easiest stage to get 100% test coverage on — one test per
objective, asserting the exact call list.

---

## Stage 7 — Policy Gate (deterministic, build before the Gateway)

Built before Stage 8 deliberately: the Gateway should be *incapable* of
receiving an unvalidated call, so write the validator first and make the
Gateway's only entry point require a `PolicyGate.validate()` pass to have
already run.

**Input:** `PlanArtifact`.

**Output:**

```python
class PolicyResult(BaseModel):
    approved: bool
    plan: PlanArtifact          # unchanged if approved
    violations: list[str]       # populated if not approved — argument validation failures,
                                 # disallowed tool, safety-class mismatch, etc.
```

Runs against the **whole plan**, not per-call — this is what makes a
`WRITE` call's approval requirement detectable before any `READ` fires
(`ARCHITECTURE.md` §5.2). Also re-invoked, unchanged, at Gap-Fill
(Stage 11) and at Decision API (Stage 17) — same function, same schema,
every time a plan is about to be executed.

**Test:** table of (plan, expected approved/violations) pairs, including
adversarial cases — an arg that violates `arg_schema`, a tool not on the
objective's evidence list, a `WRITE` with a `safety_class` mismatch.

---

## Stage 8 — Tool Gateway + Adapters (first external-API dependency)

**Input:** an approved `PlanArtifact`.

**Output:**

```python
class CallResult(BaseModel):
    seq: int
    status: Literal["OK", "FAILED", "TIMEOUT"]
    raw_response: dict | None
    error: str | None
    latency_ms: float
```

One adapter file per external domain (per `ARCHITECTURE.md` §9's folder
layout). Each adapter's job: call one Server3 REST endpoint, return
`CallResult`. Fan-out over all `READ` calls via `asyncio.gather`, per-call
timeout, partial failure tolerated (one `FAILED` doesn't abort the batch).

**Capability manifest**, checked before dispatch:

```python
ADAPTER_STATUS: dict[str, Literal["AVAILABLE","DEGRADED","ABSENT"]]
```

Cross-reference against `ARCHITECTURE.md` §10 — historian range query,
SHAP endpoint, engineering/formulae, and CMMS start `ABSENT` or
`DEGRADED` by design, not by bug. Build the adapter for each even if the
Server3 endpoint isn't ready yet: return `status=ABSENT` deterministically
rather than failing unpredictably, so QoD (Stage 9) has something honest
to react to.

**Test:** mock the HTTP layer, feed a plan with 3 `READ`s where one
adapter is `ABSENT`, assert `CallResult` list has the right statuses and
the batch completes rather than hanging.

---

## Stage 9 — QoD (deterministic, inbound edge)

**Input:** one `CallResult` at a time, as it comes back from the Gateway
— not the whole batch. This is the ordering fix from earlier design
review: validation happens per-fetch, not after all reasoning is done.

**Output:**

```python
class QoDResult(BaseModel):
    accepted: bool
    evidence_item: EvidenceItem | None   # populated if accepted
    rejection_reason: str | None          # freshness/unit/range/completeness failure
```

Checks: freshness (per-tool tolerance table — asset nameplate: no
expiry, live telemetry: ~5s, historian window: matches requested range),
completeness (required fields present), unit consistency (values match
`unit_map`), range sanity (e.g. `motor_temperature_c` between plausible
bounds).

**Test:** feed a `CallResult` with a stale timestamp, a missing field,
and an out-of-range value as three separate cases; assert each is
rejected with the right reason.

---

## Stage 10 — Evidence Pack + Seal Check (deterministic)

**Input:** the list of `QoDResult` items accepted for a run, plus the
objective's `required_evidence`/`optional_evidence` lists.

**Output:**

```python
class SealResult(BaseModel):
    pack: EvidencePack           # sealed=True if complete
    status: Literal["COMPLETE", "INSUFFICIENT"]
    missing_required: list[str]  # tool names still missing
```

Assembles accepted items into `EvidencePack.items`, builds `gaps` from
anything `ABSENT`/rejected, checks required-evidence coverage, runs
cross-signal consistency (e.g. flag if telemetry and ML results disagree
on operating state) into `conflicts`. `sealed=True` only when
`status=COMPLETE`.

**Test:** three cases — all required evidence present (seals),
one required item missing (returns `INSUFFICIENT` + names it), two items
in direct conflict (populates `conflicts`, still can seal if all required
items are present — conflicts are surfaced to XAI, not necessarily
blocking).

---

## Stage 11 — Gap-Fill Selector (LLM #4, optional path)

**Input:**

```python
class GapFillInput(BaseModel):
    missing_required: list[str]
    pack_so_far: EvidencePack
    objective_id: str
```

**Output:** a delta `PlanArtifact` (same schema as Stage 6's output,
just smaller) — re-enters Stage 7 (Policy Gate) before Stage 8 runs
again. Capped at one round per run (`replan_count`, `ARCHITECTURE.md`
§6.5) — enforce the cap here, not by trusting the caller.

**Test:** feed a `missing_required` list, assert the returned plan only
proposes calls for tools in that list (never invents new required
evidence, never re-requests something already `OK` in the pack).

---

## Stage 11.5 — Evidence Formatter (deterministic)

This is the small piece that makes the whole "LLM computes nothing"
invariant actually enforceable, so it is its own named module with its
own tests — **not** an inline step buried inside the XAI prompt builder.

Why it must be separate: Stage 13 (Numeric Provenance) checks the XAI
output against attributed numbers. That only works if there is a single,
tested definition of how a number becomes an attributed string. If that
formatting lives inline in the XAI call, no one owns the invariant and
Stage 13 has nothing stable to check against.

**Input:** a sealed `EvidencePack`.

**Output:**

```python
class FormattedValue(BaseModel):
    value_str: str        # e.g. "395.4"
    unit: str | None      # e.g. "psi"
    evidence_id: str      # the item this number came from

class FormattedEvidence(BaseModel):
    run_id: str
    values: list[FormattedValue]     # every numeric fact, each tied to an evidence_id
    narrative_context: dict          # non-numeric context strings for the prompt
```

Pure function, no LLM. Walks `pack.items[*].payload` using each item's
`unit_map`, turns every numeric field into a `FormattedValue` carrying
its `evidence_id`. The XAI prompt is built from `FormattedEvidence`, never
from raw floats.

**Test:** feed a pack with several numeric fields; assert every number
appears exactly once as a `FormattedValue` with the correct `evidence_id`
and unit. This is the test that later lets Stage 13 be trustworthy.

---

## Stage 12 — XAI Synthesizer (LLM #3)

**Input:**

```python
class XAIInput(BaseModel):
    objective_id: str
    formatted: FormattedEvidence   # from Stage 11.5 — NOT the raw pack
    query: str                     # original user text, for tone/framing only
```

The model receives `FormattedEvidence` (pre-attributed strings from Stage
11.5), never raw floats. This is what makes Stage 13 possible — do not
hand the model raw numbers and ask it to reproduce them.

**Output:**

```python
class Advisory(BaseModel):
    assessment: str
    hypotheses: list[str]
    recommendation: str
    verification_steps: list[str]
    confidence: float
    cited_evidence_ids: list[str]   # model must list which evidence_ids it used
```

Per-section prompting (`ARCHITECTURE.md` §3) — call this once per
section rather than one mega-prompt, still one logical `XAIInput` →
`Advisory` contract either way.

**Test:** cannot be fully automated pre-launch (it's narration quality),
but the schema itself — every field present, `cited_evidence_ids`
non-empty when the pack is non-empty — is testable immediately.

---

## Stage 13 — Numeric Provenance Check (deterministic — build before shipping XAI to real users)

**Input:** `Advisory` (Stage 12 output) + the `EvidencePack` it was built
from.

**Output:**

```python
class ProvenanceResult(BaseModel):
    passed: bool
    unattributed_numbers: list[str]   # numeric tokens found in prose with no matching evidence_id
```

Regex-extract numeric tokens from every string field in `Advisory`,
cross-check each against the numeric values actually present in
`pack.items[*].payload`. Any number not traceable → `passed=False`.
Caller's responsibility (Stage 12's wrapper) to regenerate or flag on
failure — this stage only detects, never fixes.

**Test:** feed a hand-written `Advisory` with one fabricated number not
in the pack; assert it's caught. This is the test that enforces the
project's core invariant — do not skip it, do not weaken it later.

---

## Stage 14 — Visualization Planner (deterministic)

**Input:** `objective_id` + sealed `EvidencePack`.

**Output:**

```python
class VisualizationSpec(BaseModel):
    widget_id: str                 # must be in the objective's allowed_visuals
    evidence_ids: list[str]        # which evidence backs this widget
    data: dict                     # widget-specific payload, values sourced from pack only
```

Pure function, no LLM. `widget_id` selection is a lookup, not a
decision — pick the first `allowed_visuals` entry whose required data is
present in the pack; if none qualify, return no visual rather than a
degraded one.

**Test:** for each objective, one pack with full evidence (produces a
visual), one pack missing the data a visual needs (produces none).

---

## Stage 15 — Direct Handler (LLM #2 — built late on purpose)

**Input:** raw query text, route == SIMPLE.

**Output:** plain narrated text, straight to `RESPONSE` — **must not**
touch `EvidencePack`, `XAI`, or `VisualizationSpec` at all. This was a
concrete regression caught in earlier design review
(`CONVERSATION_HISTORY.md` §4): verify by writing a test that asserts
none of Stages 10/12/14 are ever called on this path, not just that the
output looks right.

Exact-glossary-hit shortcut (skip LLM #2 entirely) checked first against
the KB adapter (Stage 8); only calls the LLM if no exact match.

---

## Stage 16 — Follow-up Handler

**Input:** `session_id` with a `last_analysis_id` in session state, route
== FOLLOW_UP.

**Output:** reuses Stage 12's `Advisory` schema — loads the sealed pack
by `esp:run:{analysis_id}:pack:v{latest}`, calls the same XAI Synthesizer
with `pack` already populated. Zero calls to Stage 8. This is the
"don't start from zero" contract from `ARCHITECTURE.md` §6 — test it by
asserting zero Gateway calls occur on this path, same style as Stage 15.

---

## Stage 17 — HITL: Interrupts, Pending, Decision API

Three interrupt-raising points, wired into the stages that already
exist by this point:

- `CLARIFY` — raised in Stage 5 (Router) on low confidence / arg-schema
  failure. Writes `PendingInterrupt` (Stage 2 schema) and returns a
  `clarification` frame.
- `APPROVE` — raised in Stage 7 (Policy Gate) when `requires_approval`
  is true. Returns an `interrupt` frame; execution pauses, no Gateway
  call happens yet.
- `INSUFFICIENT` — raised in Stage 10 (Seal Check) when `status !=
  COMPLETE` and Stage 11's single gap-fill round didn't resolve it.

**Resume input (`/query`, for CLARIFY/INSUFFICIENT):**

```python
def resolve(message: str, pending: PendingInterrupt) -> Literal["BIND","SUPERSEDE","META"]
```
BIND patches the run's args and resumes at `pending.resume_at`, reusing
`plan_ref`/`pack_ref` — no re-run of Stages 4-10 for unchanged items.

**Resume input (`/decision`, for APPROVE only):**

Input is `DecisionRequest`, the canonical model from `CONTRACTS_PLAN.md`
§2 — not redefined here. Summarized for convenience:

```python
class DecisionRequest(BaseModel):
    run_id: str
    action: DecisionAction        # APPROVE | REJECT | MODIFY
    token: str                    # idempotency, checked against esp:lock:resume:{run_id}
    modified_args: dict | None = None
```

Never accepts free text — this is the one hard channel split in the
whole service (`ARCHITECTURE.md` §5.5). Before dispatching a `WRITE` on
`APPROVE`, re-run Stage 9's freshness check against the pack's
safety-relevant readings; if stale, void the approval and re-raise
`APPROVE` with a fresh pack instead of executing.

**Test:** the full round-trip per interrupt type, using Stage 1-16's
existing fixtures — this stage has no new data shapes, only new control
flow over the ones already built.

---

## Stage 18 — Response Assembler (terminal stage, built in Slice 1)

Every route ends here. Raw LLM text never reaches the frontend without
passing through this stage first. Built early (Slice 1) even though it's
"last" in the flow, because every later route reuses it unchanged.

**Input:** varies by route, but always resolves to a small set —

```python
class AssemblerInput(BaseModel):
    run_id: str
    route: Route
    text: str | None                 # LLM #2 or #3 output; None for CLARIFY/APPROVE
    source_refs: list[str] = []       # KB refs or sealed-pack refs
    advisory: Advisory | None = None  # WORKFLOW / FOLLOW_UP
    visualization: VisualizationSpec | None = None
    provenance: ProvenanceResult | None = None
    pending: PendingInterrupt | None = None   # CLARIFY / APPROVE
```

**Output:** a **stream** of frames (`contracts/events.py`), one JSON
object per line (NDJSON), always ending in exactly one `DoneFrame`. This
is a generator that *yields* frames — not a function that returns a dict.

**Rules it enforces (all always-on, none optional):**
- Empty / whitespace-only `text` → emit `ErrorFrame(code="EMPTY_LLM_OUTPUT")`
  then `DoneFrame`, never a blank answer.
- `provenance.passed == False` → do not emit the text; emit
  `ErrorFrame(code="PROVENANCE_FAILED")` (or trigger one regeneration
  upstream), never the unverified numbers.
- `type` values come only from the `FrameType` enum — no invented words.
- CLARIFY → `ClarificationFrame`; APPROVE → `InterruptFrame` (destined
  for the `/decision` door); SIMPLE/FOLLOW_UP text → `TextDeltaFrame`
  stream; WORKFLOW → `AdvisoryFrame` (+ `VisualFrame` if a spec exists).

**Test:** feed one input per route, assert the exact frame sequence and
that it always terminates with a single `DoneFrame`. Add adversarial
cases: empty text (→ error), failed provenance (→ error, no text leaked),
and an invented `type` value (should be impossible because frames are
typed models, but assert it).

---

## Stage 19 — Audit Sink (cross-cutting)

**Input:** an event at every stage boundary — plan created, call
dispatched, call result, pack sealed, interrupt raised, decision made.

**Output:** append-only records, write-only, never blocks. Retrofit into
Stages 2-17 as a single `audit.record(event_type, payload)` call added at
each boundary already built — this is the one component intentionally
built last even though it's referenced throughout, because its schema
is just "whatever already flows through the other 17 stages, timestamped."

---

## What to actually verify before moving to the next stage

At every stage boundary, the concrete regression test is: **take the
Stage 1 fixture data, run it through Stages 1..N, and assert the output
matches the Pydantic schema for stage N — not just that it "looks
right."** The moment a schema is loosened informally (e.g. an adapter
starts returning a field not in `EvidenceItem`, or the router starts
emitting a `route` value not in the `Literal`), tests should fail loudly
at that stage, not surface three stages later as an XAI hallucination or
a broken frontend render.
