# Contracts Plan — ESP Agent Service

**Status: draft for discussion. Not frozen.**

This is the plan for the Pydantic models (Stage 1 of the implementation
sequence). Everything else in the service imports from here and nowhere
re-defines these shapes. Getting this right early is the single highest-
leverage thing we can do — a change here after the adapters are built
means touching every adapter.

Two rules for this whole document:

1. **One shape, one place.** No field is defined twice in two models.
2. **No `dict` where a real shape is known.** A `dict` field is an
   admission we haven't decided the shape yet — every one of them is
   listed in Section 9 as an open item, not left to discover later.

---

## 0. File map

Where each model lives, matching the folder layout in `ARCHITECTURE.md` §9.

| File | Models |
|---|---|
| `app/contracts/api.py` | `QueryRequest`, `DecisionRequest`, request/response envelopes |
| `app/contracts/context.py` | `ContextFrame`, `AssetBinding`, `TimeBinding`, `Mentions`, `SessionSnapshot` |
| `app/contracts/routing.py` | `CandidateTool`, `RouterInput`, `RouteDecision` |
| `app/contracts/objective_manifest.py` | `ObjectiveManifest` |
| `app/contracts/plan.py` | `PlanCall`, `PlanArtifact` |
| `app/contracts/evidence.py` | `EvidenceItem`, `EvidencePack`, `Gap`, `Conflict`, `CallResult`, `QoDResult`, `SealResult` |
| `app/contracts/advisory.py` | `Advisory`, `ProvenanceResult` |
| `app/contracts/visualization.py` | `VisualizationSpec` |
| `app/contracts/hitl.py` | `PendingInterrupt`, `RunState` |
| `app/contracts/events.py` | the NDJSON frame models the Response Assembler emits — one per `FrameType` |
| `app/contracts/enums.py` | all the `Literal`/`Enum` value sets, in one place |

Putting every enum in one file (`enums.py`) matters: `resume_at` values,
`asset.source` values, `route` values, etc. are referenced across many
models, and one source of truth stops them drifting apart.

---

## 1. Shared enums (`enums.py`)

Decide these value sets once. Everything else references them.

```python
Route          = Literal["SIMPLE", "WORKFLOW", "FOLLOW_UP"]   # NOT CLARIFY — see note
AssetSource    = Literal["EXPLICIT", "RESOLVED", "SESSION", "UI", "UNRESOLVED"]
TimeSource     = Literal["EXPLICIT", "UI", "SESSION", "DEFAULT"]
Resolution     = Literal["NEW", "BIND", "SUPERSEDE", "META"]
Scope          = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]
SafetyClass    = Literal["READ", "WRITE"]
CallKind       = Literal["READ", "WRITE"]
CallStatus     = Literal["PENDING", "OK", "FAILED", "TIMEOUT", "SKIPPED"]
RunStatus      = Literal["RUNNING", "PAUSED", "DONE", "ABANDONED", "FAILED"]
InterruptType  = Literal["CLARIFY", "INSUFFICIENT", "APPROVE"]
ResumeAt       = Literal["CONTEXT", "ROUTER", "PLAN_BUILD", "SEAL_CHECK",
                          "GAP_FILL", "WRITE"]
AdapterStatus  = Literal["AVAILABLE", "DEGRADED", "ABSENT"]
DecisionAction = Literal["APPROVE", "REJECT", "MODIFY"]
FrameType      = Literal["status", "text_delta", "evidence", "clarification",
                          "interrupt", "visual", "advisory", "error", "done"]
```

Enum decisions, locked:

- **`Route` does NOT include `CLARIFY`.** Clarification is not a fourth
  route — it is a *flag* (`RouteDecision.clarification_needed`) plus the
  `clarify_*` fields. Having both a `CLARIFY` route value and a
  `clarification_needed` bool would be two ways to say one thing — the
  exact dual-representation trap we removed elsewhere. When the Router
  can't decide, it still emits its best-guess `route` (or leaves it
  workflow-ish) with `clarification_needed=true`; the pipeline pauses on
  the flag, not the route.
- **`InterruptType`** (renamed from `ClarifyReason`) — these are
  interrupt *types* (`CLARIFY | INSUFFICIENT | APPROVE`), not free-text
  reasons. Used as `PendingInterrupt.reason: InterruptType` and
  `RouteDecision.clarify_reason: InterruptType | None`.
- **`RunStatus`** adds `ABANDONED` (a run closed by SUPERSEDE) and
  `FAILED` (unrecoverable error) so neither overloads `DONE` — downstream
  handling differs for each.
- **`AssetSource` priority** and **keeping `intent`** are decided in
  Section 9.

---

## 2. API layer (`api.py`)

### `QueryRequest` — what the frontend sends to `POST /query`

```python
TimeRangeLabel = Literal["last_1h", "last_6h", "last_24h", "last_7d", "last_30d"]

class UIContext(BaseModel):
    selected_asset: str | None = None
    selected_time_range: TimeRangeLabel | None = None   # enum, not free string
    selected_visualization: str | None = None
    selected_finding: str | None = None

class QueryRequest(BaseModel):
    session_id: str
    message: str
    ui_context: UIContext | None = None
```

### `DecisionRequest` — what the frontend sends to `POST /decision`

```python
class DecisionRequest(BaseModel):
    run_id: str
    action: DecisionAction
    token: str                       # idempotency, checked against esp:lock:resume:{run_id}
    modified_args: dict | None = None   # only for action == MODIFY  (see §9 — shape TBD)
```

Hard rule: approvals arrive **only** here, never through `/query`. The
one dict here (`modified_args`) is acceptable for now because its shape
depends on which objective is being modified — but it's on the open list.

---

## 3. Context layer (`context.py`)

`ContextFrame` is the full output of the Context Resolver. It lives for
the **whole request** — `RouterInput` (Section 4) is just a filtered copy
used only for the LLM call.

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
    # how the text was resolved, independent of WHERE it came from (`source`).
    # EXACT_ID (typed the real asset id) -> confidence 1.0
    # ALIAS (matched a nickname/layman term via the alias table) -> confidence ~0.8
    # PRONOUN ("it", "that well") -> confidence tied to session recency
    # NONE -> id is null (UNRESOLVED)

class TimeBinding(BaseModel):
    instant: datetime | None = None
    window_start: datetime | None = None    # see §9 — window shape decision
    window_end: datetime | None = None
    source: TimeSource
    label: str | None = None                 # e.g. "last_24h"
    confidence: float                        # parity with AssetBinding.confidence

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
    needs_clarify: bool                       # see rule below
    clarify_reason: str | None
    session_snapshot: SessionSnapshot
```

**Written rule for `needs_clarify` (this was a real bug risk):**
`needs_clarify = true` at the Context stage should only block the Router
in the rare case where the message is completely unroutable on its own.
An **unresolved asset alone must never block the Router** — the Router can
still identify the objective ("why did it trip" → fault diagnosis) with
`asset.id = None`, and the missing asset gets caught later at Plan Builder
as a CLARIFY. This keeps the "Router always runs exactly once per run"
rule intact.

**Written rule for asset priority (ties to a known old bug):** when more
than one source could supply the asset, the winner order is:

```
EXPLICIT (typed in this message)
  > RESOLVED (just answered via a clarification reply)
  > SESSION (remembered from earlier in the conversation)
  > UI (currently selected on screen)
  > UNRESOLVED
```

The old repo had a bug where the on-screen (`UI`) selection overrode a
well the user actually typed. `UI` ranking below `EXPLICIT` and `SESSION`
is what prevents that.

---

## 4. Routing layer (`routing.py`)

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
    # NOTE: no `flags`, no full `pending`, no full `resolution`, no
    # last_analysis_id — deliberately filtered out so the Router cannot
    # short-circuit itself on a flag. See ARCHITECTURE.md §6.1.

class RouteDecision(BaseModel):
    route: Route
    intent: str | None                # human-readable intent label, e.g. "diagnose" — KEPT (see note)
    objective_id: str | None          # required if route == WORKFLOW
    args: dict                        # see §9 — validated against the objective's arg_schema
    confidence: float
    deferred_intents: list[str] = []  # extra asks in the same message, remembered not run (see §4.1)
    clarification_needed: bool        # clarification is a FLAG, not a route value
    clarify_reason: InterruptType | None   # required if clarification_needed
    clarify_slot: str | None
    clarify_options: list[str] = []
```

Notes:
- `intent` is **kept** (decision confirmed). It may look redundant with
  `objective_id`, but we keep both for now and revisit later; nothing
  downstream is allowed to depend on the two disagreeing.
- The "which output schema to force the LLM into" detail (`schema:
  "RouteDecisionSchema"` in the earlier draft) does **not** belong in
  `RouterInput`. That is a how-we-call-the-LLM concern and lives in the
  router's calling code, not in the data model.
- `args` stays a `dict` on purpose here: its real shape is per-objective
  and enforced by the objective manifest's `arg_schema`, not by this
  model. It is the one dict we've decided to keep.

### 4.1 Multiple intents in one message

A message can contain more than one ask, e.g. *"why did FS-017 trip and
set it to 58 Hz"* — a diagnostic (READ) plus an actuation (WRITE).

Rules:

1. **Router still returns a single `objective_id`.** It never becomes a
   list. Everything downstream (Plan Builder, Policy Gate) assumes exactly
   one objective per run — do not break that.
2. **Extra asks go in `deferred_intents`** — remembered, not run. After
   the primary answer, the agent offers to run the deferred one as a
   fresh run.
3. **Primary intent priority: READ/diagnostic beats WRITE/actuation.**
   Always answer the question first; defer the action. Matches how an
   engineer works — understand, then act.
4. **Never bundle a WRITE with a READ in one run.** A deferred WRITE
   comes back as its own run, with its own APPROVE and its own
   `/decision` sign-off. A change to a live asset is never auto-executed
   just because it rode along with a question. This is a safety rule, not
   a convenience one.

The Router prompt instructs the model: "pick the single primary intent
(prefer diagnostic over actuation), and list any other asks in
`deferred_intents`."

---

## 5. Objective manifest (`objective_manifest.py`)

Loaded from `config/objectives/OP*.yaml`, not a DB. See
`IMPLEMENTATION_SEQUENCE.md` Stage 3 for the YAML example.

```python
class ObjectiveManifest(BaseModel):
    objective_id: str
    tool: str
    safety_class: SafetyClass
    scope: Scope                      # ASSET | MULTI_ASSET | FLEET | GLOBAL — fixed per objective
    required_evidence: list[str]
    optional_evidence: list[str]
    allowed_visuals: list[str]
    arg_schema: dict                  # JSON-schema fragment; the ONE intended dict here
```

`arg_schema` is intentionally a raw JSON-schema fragment (not a Pydantic
model) because it's data-driven config — each objective declares its own
arg shape, and Plan Builder / Policy Gate validate against it at runtime.

**`scope` moved here from `RouteDecision` (was an open item, now closed):**
scope is a fixed property of the objective — OP03 (fault diagnosis) is
always `ASSET`-scoped, a fleet-summary objective is always `FLEET`-scoped.
It never varies per message, so it has no business being an LLM output
field. Plan Builder / adapter fan-out read it from the manifest, keyed
off the `objective_id` the Router already returned. Nothing consumed
`RouteDecision.scope` before this fix — it was a field with no reader.

---

## 6. Plan layer (`plan.py`)

```python
class PlanCall(BaseModel):
    seq: int
    kind: CallKind
    tool: str
    args: dict                        # bound args for this specific call
    status: CallStatus = "PENDING"
    evidence_id: str | None = None

class PlanArtifact(BaseModel):
    run_id: str
    session_id: str
    objective_id: str
    args: dict
    confidence: float
    calls: list[PlanCall]
    requires_approval: bool           # true iff any call.kind == "WRITE"
```

`requires_approval` is computed mechanically from the calls — never set
by the LLM, never hand-set. This is what makes the APPROVE interrupt
detectable up front from the plan's shape.

---

## 7. Evidence layer (`evidence.py`)

```python
class CallResult(BaseModel):
    seq: int
    status: CallStatus                # OK | FAILED | TIMEOUT
    raw_response: dict | None
    error: str | None = None
    latency_ms: float

class QoDResult(BaseModel):
    accepted: bool
    evidence_item: "EvidenceItem | None"
    rejection_reason: str | None = None

class EvidenceItem(BaseModel):
    evidence_id: str                  # "EV-{run_id}-{seq}"
    tool: str
    source_domain: str
    fetched_at: datetime
    freshness_sec: float | None
    status: Literal["OK", "STALE", "PARTIAL"]
    payload: dict                     # tool-specific; validated by the adapter's own schema
    unit_map: dict[str, str]          # field -> unit, required if payload has numeric fields

class Gap(BaseModel):
    source_domain: str
    reason: Literal["ABSENT", "DEGRADED", "TIMEOUT"]
    required: bool

class Conflict(BaseModel):
    description: str
    evidence_ids: list[str]

class EvidencePack(BaseModel):
    run_id: str
    version: int                      # v1, v2 ... never mutated in place
    sealed: bool
    sealed_at: datetime | None
    items: list[EvidenceItem]
    gaps: list[Gap]
    conflicts: list[Conflict]

class SealResult(BaseModel):
    pack: EvidencePack
    status: Literal["COMPLETE", "INSUFFICIENT"]
    missing_required: list[str]
```

`payload` is a `dict` here because each of the ~10 source domains returns
a different shape. The right move (Section 9) is a **per-adapter payload
model** so each domain's shape is pinned separately, with `payload` typed
as a union — but that can wait until the adapters are built in Slice 2.
`unit_map` is what makes the Numeric Provenance Check possible, so it is
required, not optional, whenever the payload carries numbers.

---

## 8. Advisory, visualization, HITL, run state

### `advisory.py`

```python
class FormattedValue(BaseModel):      # from the Evidence Formatter (Stage 11.5)
    value_str: str                    # e.g. "395.4"
    unit: str | None                  # e.g. "psi"
    evidence_id: str                  # the pack item this number came from

class FormattedEvidence(BaseModel):
    run_id: str
    values: list[FormattedValue]      # every numeric fact, each tied to an evidence_id
    narrative_context: dict           # non-numeric context strings for the prompt

class Advisory(BaseModel):
    objective_id: str
    assessment: str
    hypotheses: list[str]
    recommendation: str
    verification_steps: list[str]
    confidence: float
    cited_evidence_ids: list[str]     # model must list which evidence it used

class ProvenanceResult(BaseModel):
    passed: bool
    unattributed_numbers: list[str]   # numbers in prose with no matching evidence_id
```

### `visualization.py`

```python
class VisualizationSpec(BaseModel):
    widget_id: str                    # must be in the objective's allowed_visuals
    evidence_ids: list[str]
    data: dict                        # widget-specific; values sourced from the pack only
```

### `events.py` — frames the Response Assembler emits (NDJSON, one per line)

Every route ends at the Response Assembler (see `ARCHITECTURE.md` §12),
which *yields* these frames — it never returns one blob. All frames share
`type` (from the single `FrameType` enum) and `run_id`. The frontend
switches only on `type`.

```python
class StatusFrame(BaseModel):
    type: Literal["status"] = "status"
    run_id: str
    stage: str
    progress: int
    message: str

class TextDeltaFrame(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    run_id: str
    delta: str

class AdvisoryFrame(BaseModel):
    type: Literal["advisory"] = "advisory"
    run_id: str
    advisory: Advisory                 # from advisory.py
    source_refs: list[str] = []

class VisualFrame(BaseModel):
    type: Literal["visual"] = "visual"
    run_id: str
    visualization: VisualizationSpec

class ClarificationFrame(BaseModel):
    type: Literal["clarification"] = "clarification"
    run_id: str
    question: str
    options: list[str] = []
    slot: str | None
    pending_ref: str | None

class InterruptFrame(BaseModel):           # APPROVE — answered via /decision only
    type: Literal["interrupt"] = "interrupt"
    run_id: str
    reason: InterruptType                  # "APPROVE" here
    pending_call: PlanCall                 # the WRITE awaiting sign-off
    options: list[DecisionAction]          # [APPROVE, MODIFY, REJECT]

class ErrorFrame(BaseModel):
    type: Literal["error"] = "error"
    run_id: str
    code: str                              # e.g. "EMPTY_LLM_OUTPUT", "PROVENANCE_FAILED"
    message: str

class DoneFrame(BaseModel):
    type: Literal["done"] = "done"
    run_id: str
    status: str | None = None              # e.g. "ERROR" when the run ended badly

Frame = Union[StatusFrame, TextDeltaFrame, AdvisoryFrame, VisualFrame,
              ClarificationFrame, InterruptFrame, ErrorFrame, DoneFrame]
```

Rules baked in here:
- `type` values come **only** from `FrameType` — no `answer`/`clarify`
  words. `answer` → `advisory` or `text_delta`; `clarify` →
  `clarification`.
- `InterruptFrame` (APPROVE) is emitted here but resolved through the
  `/decision` door, never `/query`.
- Every stream ends with exactly one `DoneFrame`.
- `evidence` exists in the `FrameType` enum for later richer streaming
  (emitting each evidence item as it lands) but its frame model is **not
  built in v1** — noted so the enum and the built set don't silently
  diverge.

### `hitl.py`

```python
class PendingInterrupt(BaseModel):
    run_id: str
    reason: InterruptType             # CLARIFY | INSUFFICIENT | APPROVE
    resume_at: ResumeAt               # which stage to re-enter
    slot: str | None
    options: list[str] = []
    plan_ref: str | None
    pack_ref: str | None
    raised_at: datetime

class RunState(BaseModel):
    run_id: str
    session_id: str
    status: RunStatus                 # RUNNING | PAUSED | DONE
    resume_at: ResumeAt | None        # null while RUNNING
    objective_id: str | None
    args: dict
    confidence: float | None
    plan: list[PlanCall]
    evidence_pack_ref: str | None
    pending_ref: str | None
    decision: dict | None             # see §9 — shape TBD
    turn_count: int
    replan_count: int
```

Matches `ARCHITECTURE.md` §6.3 and §6.5 exactly. `status` and `resume_at`
are the two deliberately-separated ideas (is it waiting / where to
continue).

---

## 9. Open items — every `dict` and every undecided value, in one place

Nothing below is a blocker for starting Stage 1, but each must be closed
before the stage that first depends on it.

| Open item | Where | Decide before |
|---|---|---|
| `AssetSource` priority order | `enums.py` / §3 | **DECIDED: `EXPLICIT > RESOLVED > SESSION > UI > UNRESOLVED`** (signed off) |
| Drop `RouteDecision.intent`? | §4 | **DECIDED: keep both `intent` and `objective_id`** for now, revisit later (signed off) |
| Multi-intent handling | §4.1 | **DECIDED: single objective + `deferred_intents`, READ before WRITE, WRITE never bundled** (signed off) |
| `RouteDecision.args` shape | §4 | stays a dict, validated by manifest `arg_schema` — **decision: keep as dict** |
| `RouteDecision.scope` — no consumer, LLM output or lookup? | §4/§5 | **DECIDED: moved to `ObjectiveManifest.scope`, dropped from `RouteDecision` — it's a fixed per-objective property, never a per-message LLM output** (signed off) |
| Asset alias/nickname match provenance dropped from `AssetSource` | §3 | **DECIDED: added `AssetBinding.match_method` (`EXACT_ID / ALIAS / PRONOUN / NONE`), separate from `source` — source = where the value came from, match_method = how the text was resolved** (signed off) |
| `TimeBinding` window: start/end vs label-only | §3 | Context Resolver build |
| `time` confidence field | §3 | **DECIDED: added, parity with asset** |
| `EvidenceItem.payload` per-adapter models | §7 | Tool Gateway build (Slice 2) |
| `VisualizationSpec.data` shape per widget | §8 | Visualization build (Slice 2) |
| `DecisionRequest.modified_args` shape | §2 | APPROVE build (Slice 3) |
| `RunState.decision` shape | §8 | APPROVE build (Slice 3) |
| `clarify_reason` free string vs enum | §3/§4 | **DECIDED: `InterruptType` enum** |
| `CLARIFY` in `Route` enum | §1 | **DECIDED: removed; use `clarification_needed` flag** |
| `ClarifyReason` → `InterruptType` rename | §1 | **DECIDED: renamed** |
| `RunStatus` terminal states | §1 | **DECIDED: added `ABANDONED`, `FAILED`** |
| `UIContext.selected_time_range` type | §2 | **DECIDED: `TimeRangeLabel` enum, not free string** |
| **NDJSON transport** (SSE vs WebSocket vs chunked HTTP) | events / §12 | **DECIDED: chunked HTTP `StreamingResponse`, `media_type=application/x-ndjson`** — matches what the migrated frontend already consumes; not SSE, not WebSocket |
| Embedding model language coverage | Capability Retrieval | Slice 2 — `all-mpnet-base-v2` is English-only; revisit if Hindi/mixed-language operator input is expected before real retrieval is built |
| `session_id` origin / caller auth | api | not a v1 blocker — note who issues `session_id` and whether the caller is authenticated before production |

The pattern: dicts tied to **per-objective** or **per-adapter** shapes
(args, payload, visual data) are allowed to stay dicts until the slice
that builds those objectives/adapters — because that's when their real
shape is actually known. Dicts tied to **fixed** shapes (decision) should
be turned into models before the feature that uses them ships.

---

## 10. What "done" looks like for Stage 1

- Every model above exists in its file.
- `enums.py` is the only place enum value sets are defined.
- One test per model that constructs an instance from realistic data and
  asserts `.model_dump_json()` round-trips cleanly.
- That test fixture data becomes the input for every later stage's tests
  (per `IMPLEMENTATION_SEQUENCE.md` — no stage before 9 needs a live LLM
  or network call to be tested).
- Section 9 items that are due "before Slice 1" are signed off.
