# ESP Agent Service — Architecture Document

Version: 0.3 (updated: CLARIFY as cross-cutting capability, phase-driven resume)
Scope: everything under `agent_service/`. This service is built from scratch,
with no code dependency on `esp_agent/`. It talks to the outside world only
over REST/HTTP (and a WebSocket/NDJSON stream out to the frontend). There is
no direct MQTT subscription, no direct SQLite/Postgres access, and no
in-process import of other services' Python modules. Every external fact
enters through the Typed Tool Gateway as an HTTP call to an owned API.

See Section 0 for the target repository layout — `agent_service` is one of
three siblings in a new repo, and the boundary rule in Section 1.1 applies
even though they now live in the same repo.

---

## 0. Target Repository Layout

Decision: rather than reimplementing the Server 3 backend/historian/ML/UI
stack from scratch, **migrate `Server3_Deployment_Package` as-is** into a
new repo as a sibling of `agent_service`. Migration is relocation, not
remediation — known gaps in that package (Section 10) travel with it
unchanged and must still be fixed before `agent_service` can trust those
endpoints.

```
new-repo/
├── server3_deployment_package/     # migrated as-is: 184's backend + data + ML + UI
│   ├── backend_service/            # FastAPI, MQTT ingest, historian, ML, REST API :8090
│   ├── frontend_service/           # React SPA + reverse proxy :3000 (UI migrates too)
│   ├── data/                       # unlabelled.db, mlresults.db, normalized.db
│   └── winsw/                      # service wrappers
├── agent_service/                  # this document's scope, clean build
│   ├── ARCHITECTURE.md
│   ├── app/
│   └── config/
└── README.md                       # documents the API boundary below
```

**Boundary rule — same repo does not mean same process.** Even though
`server3_deployment_package/` and `agent_service/` are now folders in the
same repo, there is zero `import` across that boundary. `agent_service`
reaches `server3_deployment_package` only via
`http://<host>:8090/api/esp/*` (and the telemetry/WS surface once added),
exactly as if they were still on separate physical servers. No shared
virtualenv assumption, no shared `PYTHONPATH`, no reaching into
`backend_service/app/` for a function call.

Reason this is non-negotiable: it preserves deploy-anywhere. Split back
into two servers later → zero code change, just an IP in an env var.
Collapse onto one box → zero code change, just `localhost`. The only
thing that should ever change is `AGENT_GATEWAY_URL` / the equivalent
config value on either side.

`esp_agent/` (the old agent) is not part of this repo at all. It is
reference material only — see Section 1.1.

---

## 1. Design Principles

These are invariants, not preferences. Any change to the design must not
violate them without an explicit decision recorded in this doc.

1. **All external data access is via API only.** REST for request/response,
   WebSocket/SSE only for the outbound stream to the frontend. No file
   handles, no DB drivers, no MQTT client inside `agent_service`. If a
   source (historian, ML, KB, formulae) does not yet expose a network API,
   that is a blocking dependency, not something this service works around.
2. **The LLM never computes, authorizes, or validates.** It selects and it
   narrates. Every number in a response must trace back to an
   `evidence_id` in a sealed Evidence Pack. Authorization, policy, and data
   quality are deterministic code, never a model decision.
3. **No ReAct loop.** The tool space is small (10 known external domains)
   and the required evidence per objective is declared up front in the
   Objective Registry. This makes evidence-gathering a deterministic
   parallel fan-out, not a search problem. A single optional gap-fill
   round covers the case ReAct would otherwise loop for.
4. **HITL pauses a workflow; the next message resumes it.** No separate
   mental model for "clarification" vs "continuing a conversation" —
   both go through the same Query API and are resolved by session +
   pending-state, except for actuation approval, which never goes through
   free text.
5. **Local LLM inference is free (no token cost), not free of latency or
   contention.** One `llama-server` instance serving all operators. Spend
   inference on quality (two-stage tool selection, critic passes,
   per-section narration), not on search (ReAct) or on things that must be
   deterministic (policy, math).
6. **Everything is resumable from durable state, not from memory.** Redis
   holds run state, pending clarifications, and sealed evidence packs.
   Any node in the pipeline can crash and be resumed from what's on disk.
7. **Any stage may raise CLARIFY when confidence is low or input is
   ambiguous.** Asking the operator with options beats guessing an
   arbitrary value. The pause/resume mechanism is uniform across every
   stage — it is keyed on the run's phase, not on the reason for pausing.
   CLARIFY, INSUFFICIENT, and APPROVE are the same pause/resume mechanism
   with different reasons (and, for APPROVE, a different entry door — see
   Section 6).
8. **One run = one objective. A WRITE is never bundled with a READ.**
   If a single message contains more than one ask (e.g. "why did it trip
   and set 58 Hz"), the Router picks one primary objective — preferring
   the diagnostic/READ intent — and defers the rest. A deferred
   actuation comes back as its own run with its own approval. A change to
   a live asset is never executed just because it rode along with a
   question. See Section 6.7 and the asset-resolution priority below.

### Asset resolution priority

When more than one source could supply the target asset, the winner order
is fixed (this prevents the known bug where an on-screen selection
overrode a well the operator actually typed):

```
EXPLICIT (typed in this message)
  > RESOLVED (just answered via a clarification reply)
  > SESSION (remembered earlier in the conversation)
  > UI (currently selected on screen)
  > UNRESOLVED
```

### 1.1 Data model reuse — data only, never architecture or code

`esp_agent/` (and the duplicate trees under `backend/`,
`Server3_Deployment_Package/backend/`) are **reference material only**.
Nothing is imported, nothing is copied as `.py`. What is reused is the
*shape of data* it already discovered — retyped fresh in `agent_service`'s
own contracts:

| Reuse (shape only, retype fresh) | Do not reuse |
|---|---|
| MQTT payload field names (`STD_INT_PRS_PSI`, etc.) — retype as own Pydantic models in `agent_service/app/contracts/` | `esp_agent/src/contracts/mqtt_payloads.py` itself |
| DB column names (`opg_well_telemetry`, `ml_results`, etc.) — reference only, needed once Server3's historian/SHAP endpoints are fixed | any direct DB access — `agent_service` never opens a `.db` file |
| The 21 tool names + descriptions + arg shapes from `tool_definitions.json` — retype as `agent_service/config/objectives/*.yaml` | `tool_definitions.json` itself, and all its binding code (`TOOL_TO_OBJECTIVE`, `_decompose_steps`, `specialist_executor.py` if/elif chains) |
| The 43-row formula catalog data (CSV) | `esp_agent/src/contracts/formulae.py` module |
| The *idea* of `EvidencePack` / `StandardAdvisoryPayload` shapes | importing `esp_agent/src/contracts/evidence.py` or `advisory.py` |

No LangGraph specialist graphs, no `orchestrator.py` routing ladder, no
`bff_routes.py` per-scenario coroutines, no `plan_node.py` if/elif
decomposition — none of the old arch carries over. `agent_service/` is a
clean room. The old repo is read like the MQTT spec doc: a reference,
never a dependency.

---

## 2. High-Level Flow (L0)

```
                        USER
                          │
                          ▼
                 Conversation / Context ──────────┐
                          │                       │
                          ▼                       │
                 Capability Retrieval              │
                 (embeddings, top-k, no LLM)       │
                          │                       │
                          ▼                       │
                 Query Router  ★ LLM #1            │
                          │                       │
        ┌─────────────────┼─────────────────┐     │
     SIMPLE          FOLLOW-UP          WORKFLOW  │
        │                 │                 │     │
        ▼                 ▼                 ▼     │
  Direct Handler   Sealed Analysis   Objective Registry
     ★ LLM #2        (no refetch)     (deterministic)
        │                 │                 │     │
        │                 │                 ▼     │
        │                 │            Policy Gate│      H
        │                 │           (never LLM) │      I
        │                 │                 │     │      T
        │                 │                 ▼     │      L
        │                 │           Tool Gateway│
        │                 │           (HTTP only) │
        │                 │                 │     │
        │                 │                 ▼     │
        │                 │           QoD (inbound)
        │                 │                 │     │
        │                 │                 ▼     │
        │                 └──────────▶ Evidence Pack
        │                                   │     │
        │                              gap? ★LLM#4│
        │                                   │     │
        │                                   ▼     │
        │                          XAI / Recommend★LLM#3
        │                                   │     │
        │                                   ▼     │
        │                        Numeric Provenance Check
        │                          (deterministic)
        │                                   │
        │                                   ▼
        │                          VisualizationSpec
        │                          (deterministic)
        │                                   │
        └───────────────────┬───────────────┘
                            ▼
                        RESPONSE
```

This is the explanatory diagram. Section 4 (component inventory) and
Section 6 (LLM touchpoints) are the normative contract for implementation.

---

## 3. LLM Call Budget

Local inference, so this is not a cost table — it is a latency and
contention table. One `llama-server` (Qwen2.5-Coder-3B-Instruct, CPU,
`-c 8192` context ceiling) serves every concurrent operator. Every call
here is real wall-clock time and a real slot in that queue.

| Call | Node | Fires | Purpose |
|---|---|---|---|
| LLM #1 | Query Router | always | domain select → tool select (two-stage), objective_id + args + confidence |
| LLM #2 | Direct Handler | SIMPLE route, unless exact glossary hit | narrate over KB prose |
| LLM #3 | XAI / Recommendation | WORKFLOW and FOLLOW-UP routes | narration only, over pre-formatted evidence |
| LLM #4 | Gap-Fill Selector | only if Pack Seal reports missing/conflicting required evidence | selects follow-up calls, fires once, never loops |
| (critic) | optional, post-XAI | quality gate, not correctness gate | re-reads narrative against pack, flags unsupported claims — backstop behind the deterministic Numeric Provenance Check, never a replacement for it |

Because inference is free, use it for **quality**: two-stage tool selection
(domain → tool, not a flat 21-way choice), per-section XAI prompts instead
of one mega-prompt, always re-narrate on clarify instead of a slot-fill
shortcut. Do not use it for **search** — that is what ReAct would do, and
it is explicitly excluded (Section 8).

What must never call the LLM: Capability Retrieval (embeddings only),
Objective Registry (table lookup), Policy Gate, Tool Gateway, QoD,
Numeric Provenance Check, VisualizationSpec, HITL clarification templating,
HITL decision handling, Response Assembler.

---

## 4. Component Inventory

| Component | Owned State | LLM? | Responsibility |
|---|---|---|---|
| Conversation / Context Resolver | session (Redis) | no | session lookup, reference binding, pending-state check, current-asset tracking |
| Capability Retrieval | tool embeddings (in-memory, built at startup) | no | cosine top-k over pre-embedded objective/tool descriptions; shrinks LLM #1's prompt |
| Query Router | none | LLM #1 | classify SIMPLE / FOLLOW-UP / WORKFLOW; for WORKFLOW, select objective + bind args + confidence |
| Objective Registry | static manifest (config, not DB) | no | per-objective required/optional evidence list, allowed visuals, safety class (READ/WRITE) |
| Policy Gate | none (reads run state) | **never** | authorization, allowed-tool check, argument validation, safety-class enforcement; runs before every outbound call, not just the first |
| Tool Gateway | per-adapter capability manifest | no | HTTP-only fan-out to external domain APIs; parallel, per-source timeout, partial-failure tolerant; exposes `AVAILABLE / DEGRADED / ABSENT` per adapter |
| QoD (Data Quality Gate) | none | no | inbound validation per fetch: freshness, completeness, unit consistency, range checks — runs before data enters the pack, not after |
| Evidence Pack | Redis (`esp:run:{run_id}:pack:v{n}`) | no | assembled, versioned, sealed evidence container; immutable once sealed |
| Pack Seal Check | none | no | cross-signal consistency, source conflicts, required-evidence coverage; raises `INSUFFICIENT` or proceeds |
| Gap-Fill Selector | none | LLM #4 (optional) | selects a bounded follow-up call set when Seal Check reports a gap; result re-enters Policy Gate; fires at most once per run |
| XAI / Recommendation Synthesizer | none | LLM #3 | narrates assessment, hypotheses, recommendation, verification — over pre-formatted evidence strings only |
| Numeric Provenance Check | none | no | rejects/flags any numeric token in narration not traceable to an `evidence_id`; runs **before** the Response Assembler and hands it a pass/fail |
| Visualization Planner | none | no | pure function of objective_id + available evidence → VisualizationSpec (allowed widget set from Objective Registry) |
| Response Assembler | none | no | single terminal stage for **every** route; wraps output in the standard frame envelope, attaches source refs, applies fallback on empty/garbage LLM output, streams frames as NDJSON ending in `done`. See Section 12. |
| Direct Handler | none | LLM #2 | glossary/general inquiry; bypasses Evidence Pack / XAI / VisualizationSpec entirely |
| Follow-up Handler | reads sealed pack | reuses LLM #3 | re-narrates a sealed analysis, zero refetch |
| HITL Control Plane | Redis (`esp:session:{sid}:pending`, `esp:run:{run_id}`) | no | interrupt raising, pending-state, resume routing, actuation approval |
| Session State | Redis (`esp:session:{sid}`) | no | hot per-turn conversation state, current_asset, last objective |
| Analysis Artifacts | Redis (`esp:run:{run_id}`, TTL) | no | sealed packs, findings, visuals — referenced by follow-up and audit, not mutated |
| Audit / Trace | append-only store | no | write-only sink: query, plan, calls, evidence, decisions, HITL events; never blocks the main path |

---

## 5. Request Lifecycle

### 5.1 New query, no pending state

```
POST /query {session_id, message}
  → Context Resolver: load session, check pending (none)
  → Capability Retrieval: embed message, top-k candidate tools
  → Query Router (LLM #1): classify route
      SIMPLE      → Direct Handler (LLM #2) → RESPONSE
      WORKFLOW    → Objective Registry → Policy Gate (plan-level)
                    → Tool Gateway (parallel HTTP) → QoD (per-fetch)
                    → Evidence Pack → Seal Check
                        complete → XAI (LLM #3) → Numeric Check
                                 → VisualizationSpec → RESPONSE
                        gap      → Gap-Fill (LLM #4, once) → Policy Gate
                                 → (fetch delta) → Seal Check → XAI → ...
```

### 5.2 Plan structure (WORKFLOW route)

The plan is built deterministically from the Objective Registry manifest,
not discovered. Reads and writes are split explicitly so approval is
detected before any call executes:

```json
{
  "run_id": "R456",
  "objective_id": "OP03_FAULT_DIAGNOSIS",
  "calls": [
    {"seq": 1, "kind": "READ",  "tool": "get_asset_context",   "args": {...}},
    {"seq": 2, "kind": "READ",  "tool": "get_live_telemetry",  "args": {...}},
    {"seq": 3, "kind": "READ",  "tool": "get_historian_window", "args": {...}},
    {"seq": 4, "kind": "WRITE", "tool": "set_operating_frequency", "args": {"hz": 58}}
  ]
}
```

Policy Gate validates the **whole plan** before execution starts. All
`READ` calls run in parallel through the Tool Gateway. Any `WRITE` call
triggers an `APPROVE` interrupt (Section 6.2) before it is dispatched —
approval is known up front from the plan shape, not discovered mid-run.

### 5.3 Follow-up (sealed analysis exists)

```
POST /query {session_id, message}
  → Context Resolver: session has last analysis_id, no pending
  → Query Router (LLM #1): classifies FOLLOW-UP
  → Follow-up Handler: load esp:run:{analysis_id}:pack:v{latest}
  → XAI (LLM #3): re-narrate over sealed pack, zero fetch
  → RESPONSE
```

### 5.4 HITL clarification round-trip

```
Turn N:   "Check FS-017"        → WORKFLOW → Seal Check → INSUFFICIENT
                                   (which trip: 10:42 or 14:18)
          → pending state written, run paused, RESPONSE = clarification

Turn N+1: "14:18"                → Context Resolver sees pending
                                   → resolve(message, pending):
                                       BIND      → patch slot, resume at run.resume_at, 0 LLM
                                       SUPERSEDE → close pending (ABANDONED), new query
                                       META      → answer question, pending stays open
                                   BIND path: RESUME_TABLE[resume_at] re-enters the run
                                       → Tool Gateway (delta only) → Seal Check
                                       → XAI (LLM #3) → RESPONSE
```

### 5.5 Actuation approval (never free text)

```
Plan contains a WRITE call
  → Policy Gate flags it during plan-level validation
  → RESPONSE = interrupt frame, run paused, run_id returned
  → Frontend renders explicit APPROVE / MODIFY / REJECT buttons

POST /decision {run_id, action: APPROVE|REJECT|MODIFY, token, modified_args?}
  → SET esp:lock:resume:{run_id} NX EX 10   (idempotency)
  → staleness re-check on safety-relevant readings in the sealed pack
       stale  → void approval, raise fresh APPROVE with current evidence
       fresh  → APPROVE: dispatch WRITE via Tool Gateway
                REJECT:  mark WRITE SKIPPED, continue to XAI
                MODIFY:  re-validate new args at Policy Gate, re-raise APPROVE
  → XAI (LLM #3) narrates outcome → RESPONSE
```

`action` is a structured enum from a UI control, never parsed from a chat
message. This is the one hard boundary between the Query API and the
Decision API.

---

## 6. HITL Design

HITL is **one uniform pause/resume mechanism**, not three separate gates.
Any stage that cannot confidently proceed pauses the run, records where
to resume, and asks the operator — with structured options wherever
possible. `CLARIFY`, `INSUFFICIENT`, and `APPROVE` are the same mechanism
with different reasons.

### 6.1 CLARIFY is a capability, not a stage

Any stage may call the same helper:

```
raise_clarify(reason, slot, options, resume_at):
  → write pending to esp:session:{sid}:pending
  → set run.status = PAUSED, run.resume_at = <this stage>
  → return a clarification template + options to the operator
```

Stages that can raise it, and their v1 status (the *mechanism* exists
everywhere from day one; this column is only about which stages actually
use it in v1, so testing scope is clear):

| Stage | Example trigger | v1 status |
|---|---|---|
| Context Resolver | unbound pronoun, ambiguous asset, missing required context | **Active** |
| Query Router | low confidence on route / objective / args | **Active** |
| Plan Builder | objective needs an arg that wasn't bound (e.g. `trip_ts` with multiple trips) | **Active** |
| Policy Gate | arg validation fails and can't be fixed deterministically | Wired, rarely fires |
| Seal Check | required evidence missing → `INSUFFICIENT` (same mechanism) | **Active** |
| Gap-Fill Selector | multiple plausible follow-up calls, no clear winner | Wired, rarely fires |
| XAI | narrative needs a human framing decision | Mechanism exists, unused in v1 |

### 6.2 Three reasons, two entry doors — one resume engine

| Reason | Raised at | Comes back through |
|---|---|---|
| `CLARIFY` | any stage above | `/query` (free text or structured option) |
| `INSUFFICIENT` | Seal Check | `/query` (free text or structured option) |
| `APPROVE` | Policy Gate (plan has a `WRITE`) | **`/decision` only** (structured buttons + token, never free text) |

The resume *engine* is shared and phase-driven (Section 6.5). The *entry
door* is not: approvals never arrive as chat text. This is a hard safety
boundary — a `WRITE` to a live asset must never be authorized by parsing
prose.

### 6.3 Pending state

One pending per session, TTL-bound, always superseded (never stacked):

```
esp:session:{sid}:pending    TTL 15 min, max 1 entry
{
  "run_id": "R456",
  "reason": "CLARIFY",              # CLARIFY | INSUFFICIENT | APPROVE
  "resume_at": "PLAN_BUILD",        # which stage to re-enter — see 6.5
  "slot": "trip_ts",
  "options": ["10:42", "14:18"],    # structured; free text allowed but options preferred
  "plan_ref": "esp:run:R456",
  "pack_ref": "esp:run:R456:pack:v1",
  "raised_at": "..."
}
```

`plan_ref` and `pack_ref` make resume cheap — the run's plan and sealed
evidence are reused, not rebuilt. An expired pending is discarded silently
and the incoming message is treated as a new query.

### 6.4 Bind / Supersede / Meta (for `/query` resumes)

```
resolve(message, pending):
  matches slot type/options?   → BIND       (patch slot, resume at resume_at)
  parses as a new objective?   → SUPERSEDE  (close pending as ABANDONED, new query)
  neither?                     → META       (answer directly, pending stays open)
```

Every SUPERSEDE writes an audit record so a dangling pending never
silently binds to an unrelated later message.

### 6.5 Run state — resume is phase-driven, not type-driven

```
esp:run:{run_id}    TTL 24h
{
  "run_id", "session_id",
  "status": "RUNNING",              # RUNNING | PAUSED | DONE
  "resume_at": "PLAN_BUILD",        # which stage to re-enter when PAUSED; null when RUNNING
  "objective_id", "args", "confidence",
  "plan": [ {seq, kind, tool, args, status} ],
  "evidence_pack_ref": "esp:run:{run_id}:pack:v{n}",
  "pending_ref": "esp:session:{sid}:pending" | null,
  "decision": {"action", "actor", "at", "modified_args"} | null,
  "turn_count": 1,
  "replan_count": 0
}
```

Two separate ideas, deliberately named apart so they don't get confused:
- `status` — is the run waiting or not (`RUNNING` / `PAUSED` / `DONE`).
- `resume_at` — *where to continue* when a paused run is resumed.

Resume is a **lookup table**, never a growing if/elif chain (that pattern
is exactly what bloated the old repo):

```python
RESUME_TABLE = {
  "CONTEXT":    continue_after_context,
  "ROUTER":     continue_after_router,
  "PLAN_BUILD": continue_after_plan,
  "SEAL_CHECK": continue_after_seal,
  "GAP_FILL":   continue_after_gapfill,
  "WRITE":      continue_after_approve,   # runs staleness re-check first — see below
}

def resume(run_id, bound_value):
    run = load_run(run_id)
    fn = RESUME_TABLE.get(run.resume_at)
    if fn is None:
        raise HardError(f"no resume handler for {run.resume_at}")   # fail loud, never guess
    return fn(run, bound_value)
```

Resume never re-enters at the top of the pipeline — that would refetch
evidence and could hand the operator different numbers than the ones they
were shown.

**Safety rule that must survive the merge:** `continue_after_approve`
(resuming into the `WRITE` phase) is not a plain "continue." It first
re-runs the freshness check on the safety-relevant readings in the sealed
pack. If they went stale while waiting for approval, it voids the approval
and raises a **fresh** `APPROVE` against current data instead of executing
the stale one.

### 6.6 Loop guard

`replan_count` capped (e.g. 3) per run. Hitting the cap returns a
best-effort response with declared gaps and closes the run rather than
clarifying indefinitely.

### 6.7 Deferred intents (multiple asks in one message)

The Router returns a **single** `objective_id` plus a
`deferred_intents` list for any other asks in the same message. The run
executes only the primary objective. After the answer, the agent offers
to run each deferred intent as a fresh run.

- **Primary priority:** diagnostic/READ intent beats actuation/WRITE.
  Answer the question first, defer the action.
- **A deferred WRITE always becomes its own run** — its own plan, its own
  `APPROVE` interrupt, its own `/decision` sign-off. It is never chained
  automatically off the back of a READ. (Invariant #8.)

This keeps every run single-objective, so Plan Builder and Policy Gate
never have to reason about more than one objective at a time.

---

## 7. Evidence & Data Quality

- **QoD runs on the inbound edge.** Every fetch is validated (freshness,
  completeness, unit consistency, range) before it is added to the pack.
  Bad data must never reach the narrator.
- **Pack Seal Check runs once per pack version.** Cross-signal consistency,
  source conflicts, required-evidence coverage. This is the only place
  `INSUFFICIENT` is raised.
- **Packs are versioned, not mutated.** `esp:run:{run_id}:pack:v1`,
  `:v2`, etc. A re-plan after clarification produces a new version that
  reuses unchanged items (by `hash(tool + canonical_args)`, subject to a
  per-tool freshness tolerance — e.g. asset nameplate reused indefinitely,
  live telemetry never reused past ~5s, historian window reused if the
  requested range is unchanged) and only fetches the delta.
- **Adapter capability manifest.** Every external domain (asset, telemetry,
  historian, ML, engineering, twin, events, KB, cases, maintenance) is
  registered with a status: `AVAILABLE / DEGRADED / ABSENT`. `ABSENT`
  sources are named as explicit gaps in the pack, never silently omitted
  — the failure mode this avoids is a source returning `[]` and the
  narrator having no way to distinguish "nothing found" from "offline."
- **Numeric Provenance Check is the enforcement mechanism** for "the LLM
  computes nothing." Every numeric token in the narration output must
  match an `evidence_id` in the sealed pack, or the response is rejected
  and regenerated / flagged.

---

## 8. Why Not ReAct

Considered and rejected as the core loop. Recorded here so it isn't
re-litigated without new information.

ReAct earns its cost when the tool space is large/unenumerable and the
next fetch genuinely depends on the previous result (hypothesis refine
loops). Neither is true here: 10 known external domains, and the
Objective Registry declares required evidence up front — this is a
fan-out problem, not a search problem.

Cost of ReAct anyway:
- Multiple sequential LLM calls per query, context growing each turn,
  against an `-c 8192` ceiling.
- No termination guarantee on a 3B model — needs iteration cap, wall
  clock, and no-progress detection hand-built regardless, which is most
  of the control flow ReAct was supposed to provide.
- Non-deterministic call sequence per identical query — bad for audit in
  a regulated operational context.
- Violates the core invariant: ReAct's loop is the LLM doing search/
  computation, not narration.

The Gap-Fill Selector (LLM #4) covers the realistic ReAct use case —
"we're missing something, go get it" — in a single bounded round instead
of an open loop, and re-enters through Policy Gate like any other call.

If the tool space grows past ~50 unenumerable sources, or genuine
hypothesis-refinement reasoning is required (fetch → theory → targeted
fetch → revise), revisit this decision — and if so, adopt a real
framework with a durable checkpointer (e.g. LangGraph), not a hand-rolled
loop.

---

## 9. Folder Layout (proposed)

```
agent_service/
├── ARCHITECTURE.md              # this document
├── app/
│   ├── main.py                  # FastAPI app, POST /query, POST /decision, GET /health
│   ├── context/
│   │   ├── resolver.py          # session + pending lookup, bind/supersede/meta
│   │   └── session_store.py     # Redis session state
│   ├── routing/
│   │   ├── capability_retrieval.py   # embedding top-k over tool descriptions
│   │   ├── router.py                  # LLM #1 call + structured-output parsing
│   │   └── objective_registry.py      # static manifest: required/optional evidence, safety class, allowed visuals
│   ├── planning/
│   │   └── plan_builder.py       # deterministic plan from objective manifest + bound args
│   ├── policy/
│   │   └── policy_gate.py        # authz, allowed-tool check, arg validation, WRITE detection
│   ├── gateway/
│   │   ├── tool_gateway.py       # parallel HTTP fan-out, per-source timeout
│   │   └── adapters/             # one file per external domain (asset, telemetry, historian, ml, engineering, twin, events, kb, cases, maintenance)
│   ├── evidence/
│   │   ├── qod.py                # inbound per-fetch validation
│   │   ├── pack.py                # Evidence Pack build/version/seal
│   │   └── seal_check.py          # cross-signal consistency, gap detection
│   ├── gapfill/
│   │   └── gapfill_selector.py   # LLM #4, single bounded round
│   ├── synthesis/
│   │   ├── evidence_format.py     # deterministic: EvidencePack → FormattedEvidence (Stage 11.5)
│   │   ├── xai.py                 # LLM #3, per-section narration
│   │   ├── numeric_check.py       # provenance enforcement (checks XAI output vs FormattedEvidence)
│   │   └── direct_handler.py     # LLM #2, SIMPLE route
│   ├── visualization/
│   │   └── visualization_planner.py  # deterministic VisualizationSpec
│   ├── hitl/
│   │   ├── interrupts.py          # CLARIFY / APPROVE / INSUFFICIENT
│   │   ├── pending_store.py       # Redis pending state, TTL, bind/supersede/meta
│   │   └── decision_api.py        # POST /decision, lock + staleness re-check
│   ├── run/
│   │   ├── run_store.py           # esp:run:{run_id} state, phase tracking
│   │   └── analysis_store.py     # sealed pack references for follow-up
│   ├── audit/
│   │   └── audit_sink.py          # write-only, never blocks main path
│   └── contracts/
│       ├── plan.py                 # PlanCall, PlanArtifact
│       ├── evidence.py             # EvidenceItem, EvidencePack
│       ├── events.py               # NDJSON frame types (status, interrupt, text_delta, visual, done)
│       └── objective_manifest.py  # schema for OP00–OP14 entries
├── config/
│   └── objectives/                # OP00.yaml ... OP14.yaml — required/optional evidence, allowed visuals, safety class
└── tests/
```

---

## 10. External Dependencies — Status Going In

`agent_service`'s only backend dependency is `server3_deployment_package`
(Section 0), reached exclusively over its REST API on `:8090` (and
telemetry/WS surface once added). These gaps were carried over unchanged
by the migration and must be fixed **inside
`server3_deployment_package/`** — never worked around inside
`agent_service`. `agent_service` should treat every one of these as
`AVAILABLE / DEGRADED / ABSENT` via the adapter capability manifest
(Section 7), never assume `AVAILABLE`.

| Domain | Status | Note |
|---|---|---|
| Asset / nameplate | usable | retained MQTT payload also available via REST snapshot |
| Live telemetry / VFM | needs REST snapshot endpoint | source is MQTT pub/sub; agent_service is API-only, so a `GET /telemetry/{well}/latest` (and windowed variant) must exist in front of it — this is a new integration point, not reused code |
| Historian (range query) | **blocking** | existing `/history?range=` ignores the range parameter and fabricates synthetic points under 10 rows — needs a real implementation before "max past 1 hour" is trustworthy |
| ML results (health/fault) | usable | `health_score`, `fault_diagnosis`, `is_anomalous` available |
| ML results (SHAP/explanation) | **blocking** | SHAP lives in `esp_unified_assessments.shap_contributions`, zero REST endpoints today |
| Engineering / formulae | **blocking** | in-process Python module only, no REST API |
| Digital Twin / what-if | unverified | claimed on Server 1 `:8080`, not confirmed implemented |
| Events / alarms | usable | MQTT-sourced, needs REST snapshot endpoint same as telemetry |
| Knowledge Base | needs service wrap | hybrid BM25 + pgvector exists as a library behind `datamodelservices.bat`'s docker stack; needs to be an addressable, health-checked service with honest degraded-mode signaling |
| Case / RCA history | usable, conditional | Postgres table, needs the docker stack up |
| Maintenance / CMMS | **does not exist** | no implementation anywhere in the current repo |

---

## 11. Open Items For Next Pass

- Structured-output schema for LLM #1 (route, objective_id, args,
  confidence) and failure-mode handling (low confidence, unknown
  objective, malformed output).
- Objective manifest schema detail: `required_evidence` /
  `optional_evidence` / `allowed_visuals` / `safety_class` per OP00–OP14.
- Policy Gate rule schema: what marks a call `WRITE`, per-tool argument
  validation rules, per-sensor freshness tolerance table.
- Load test plan against `llama-server` at realistic concurrency to find
  p95 latency under the two-stage tool-selection prompt size — sets the
  real operational ceiling, since local inference removes cost but not
  contention.

---

## 12. Response Assembler

Single terminal stage that **every** route ends at. Raw LLM text never
goes to the frontend directly — it always passes through here first.
Built in Slice 1 (with the Simple path) precisely because every later
route reuses it unchanged.

### 12.1 Why it exists

If raw LLM text went straight out, all of the following would leak into
the frontend with no single place to enforce them:

| Need | Owned by the Assembler |
|---|---|
| One consistent envelope for every response type | yes |
| Source attribution (which KB refs / evidence backed the answer) | yes |
| Audit trail (every response recorded) | yes |
| Fallback on empty / garbage LLM output | yes |
| Numeric-provenance enforcement result carried through | yes |
| Streaming (NDJSON frames) vs single response | yes |
| Same output consumed by both the chat UI and other services | yes |

### 12.2 It streams frames — it does not return one blob

Output is **NDJSON** (per Section 1, invariant): a sequence of frames,
one JSON object per line, terminated by a `done` frame. The Assembler
*yields* frames; it does not build one dict and return it. This is what
drives the typewriter `text_delta` effect the frontend expects.

**Transport (decided):** chunked HTTP via a FastAPI `StreamingResponse`
with `media_type="application/x-ndjson"` — not SSE, not WebSocket. This
matches what the migrated frontend already consumes. Each yielded frame
is `frame.model_dump_json() + "\n"`.

Frame `type` values come from the **single `FrameType` enum** already
defined in the contracts (`status | text_delta | evidence |
clarification | interrupt | visual | advisory | error | done`). The
Assembler must not invent new type words (no `answer` / `clarify` — those
map to `advisory`/`text_delta` and `clarification` respectively). One
vocabulary, shared by contracts and frontend.

### 12.3 Inputs per route — same stage, different feed

| Route | What feeds the Assembler |
|---|---|
| SIMPLE | LLM #2 text + KB source refs |
| FOLLOW-UP | LLM #3 text + sealed-pack refs |
| WORKFLOW | LLM #3 text + sealed pack + VisualizationSpec + Numeric Provenance result |
| CLARIFY | pending state only (no LLM) → `clarification` frame |
| APPROVE | pending state + pending WRITE call → `interrupt` frame (out the `/decision` door) |

### 12.4 Ordering rule — provenance runs before the Assembler

The Numeric Provenance Check is **not** something the Assembler does
alongside emitting text. It runs first and hands the Assembler a
pass/fail:
- **pass** → Assembler streams the `text_delta` / `advisory` / `visual`
  frames.
- **fail** → Assembler does not emit the bad text; it emits an `error`
  frame (or triggers a single regeneration), never the unverified
  numbers.

### 12.5 Always-on checks (not optional, even for SIMPLE)

- **Empty/garbage guard** — empty or whitespace-only LLM output → `error`
  frame with a fallback message, never a blank answer.
- **Numeric provenance hook** — kept always-on. SIMPLE rarely produces
  numbers, but if LLM #2 invents one it must still be caught. Cost is
  near-zero when there are no numeric tokens; it is never skipped.

### 12.6 Frame shapes (illustrative — canonical defs live in `contracts/events.py`)

```json
// advisory (workflow / follow-up answer)
{ "type": "advisory", "run_id": "R456", "advisory": { ... }, "source_refs": [...] }

// text_delta (streamed prose, simple or workflow)
{ "type": "text_delta", "run_id": "R456", "delta": "..." }

// clarification (CLARIFY route)
{ "type": "clarification", "run_id": "R456", "question": "Which asset?",
  "options": ["FS-017","FS-012","FS-009"], "slot": "asset_id",
  "pending_ref": "esp:session:S123:pending" }

// interrupt (APPROVE — resolved via /decision, never /query)
{ "type": "interrupt", "run_id": "R456", "reason": "APPROVE",
  "pending_call": {"tool":"set_operating_frequency","args":{"hz":58}},
  "options": ["APPROVE","MODIFY","REJECT"] }

// error / fallback
{ "type": "error", "run_id": "R456", "code": "EMPTY_LLM_OUTPUT",
  "message": "I couldn't produce a clear answer. Could you rephrase?" }

// terminal — always last
{ "type": "done", "run_id": "R456" }
```

The frontend switches only on `type`. That is the entire contract it
needs to understand.
