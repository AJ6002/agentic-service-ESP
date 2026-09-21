# Design Conversation History — ESP Agent Service

Chronological record of the design discussion that produced
`ARCHITECTURE.md`. Kept so future readers know *why* a decision was made,
not just what it is. Each entry: the question raised, the conclusion
reached, and what changed as a result.

---

## 1. Starting question: can we build a new agent service from scratch?

Prompted by a hand-drawn boundary sketch (Agent Service ↔ External World)
and the question of whether a clean XAI + recommendation system could be
built that never has the LLM compute anything — only select tools and
narrate — using REST/MQTT/WebSocket exclusively for external access, and
whether LangGraph was required.

**Investigation:** two parallel context-gathering passes over the
existing repo — one on the `esp_agent` implementation itself, one on the
actual data sources and their network reachability.

**Findings:**
- `esp_agent` V2 does **not** use LangGraph's `StateGraph` at runtime
  (confirmed in the codebase's own comment, `observability/tracing.py:4`).
  Orchestration is a 9-stage regex/LLM precedence ladder plus a second
  hand-written router in `bff_routes.py` (~2,700 lines, hardcoded inline
  values). LangGraph appears only as 2–3-node linear "specialist" graphs
  with no checkpointer wired in — decorative, not functional.
- Tool execution is heavily in-process: an MQTT-collector singleton lives
  inside the agent process, and several tools open SQLite files directly
  (one, `get_ml_results`, queries the DB and then discards the result,
  returning a hardcoded string regardless).
- Data source audit: MQTT (`esp/v1/{well}/*` on 155) carries live
  telemetry, VFM, retained asset nameplate, and events — genuinely ready.
  But the historian's only REST endpoint ignores its `range` parameter
  and fabricates synthetic rows under 10; SHAP values exist only in
  `esp_unified_assessments` with zero REST endpoints; the KB is a Python
  library behind a docker stack, not an addressable service; the formula
  catalog has no REST API at all; CMMS/Maintenance doesn't exist anywhere.

**Conclusion:** building fresh is right, but not because the old code is
bad glue — three of the "already ready" sources are not actually
reachable over a network today. LangGraph is not needed for a
single-pass DAG; the existing repo's own unwired LangGraph usage is proof
it added nothing. Reusable: `tool_definitions.json` shape, `contracts/*`
shapes, `section_registry.py` idea, Redis plan-repository pattern,
`formulae_lib.py`/`engineering_service.py` (real physics). Not reusable:
the routing ladder, `bff_routes.py`, the in-process MQTT/SQLite coupling.

---

## 2. First architecture diagram (user-drawn): Conversation → Query Router →
   SIMPLE/WORKFLOW → ... → RESPONSE, with a ReAct execution loop at the
   center and a parallel HITL control plane.

**Tension identified:** this diagram contradicted the "LLM computes
nothing" premise from Step 1. A ReAct loop is the LLM performing search/
reasoning over multiple turns — the opposite of pure tool-select +
narrate.

**Four ordering bugs found:**
1. Policy Gate positioned *before* ReAct, but ReAct generates tool calls
   dynamically inside the loop — nothing to validate yet at that point.
2. Data Quality Gate positioned *after* the full reasoning loop instead of
   on each inbound fetch — bad data could be reasoned over for several
   turns before being caught.
3. MQTT drawn as a directly-callable tool (`GATE → MQTT`) — but MQTT is
   pub/sub with `retain=False` on telemetry/VFM; it needs a subscriber +
   ring buffer, not a request/response call.
4. HITL resume re-entered at the top of the service (`RES → AG`),
   discarding the ReAct loop's accumulated evidence and forcing a
   restart of the investigation.

**LangGraph re-opened:** with a genuine cycle (`REACT ↔ GATE`),
conditional edges, and mid-loop interrupts present, LangGraph's actual
value props (checkpointed cycles, durable interrupts) would apply *if*
ReAct were kept. Recommended middle path instead: objective-declared
parallel fan-out plus at most one conditional gap-fill wave — bounded,
deterministic, ~90% of ReAct's value at a fraction of the LLM calls.

---

## 3. Redraw without ReAct still drawn (before it was formally dropped)

Produced a corrected diagram fixing all four ordering bugs: `PLAN` +
`FETCH` replacing the loop, `GAPQ` as a one-shot diamond (not a cycle)
re-entering through `POL`, `SUB` (MQTT subscriber + ring buffer) feeding
`GATE` instead of being called by it, `SESSION` split into `SESSION` +
`ANA` (hot conversation state vs immutable analysis artifacts) to defuse
a god-object flag, and `RES` re-entering at the interruption point with
two distinct edges (clarification → re-plan at Query Understanding;
approval → continue at Policy).

Added a mechanical enforcement point not present before: `NUM` — a
deterministic numeric-provenance check so "the LLM computes nothing" is
enforced by code, not left as a convention.

LLM call budget at this point: 1 (SIMPLE) / 1 (FOLLOW-UP) / 2 (WORKFLOW)
/ 3 (WORKFLOW + one gap-fill wave) — down from 5–7 under ReAct.

---

## 4. User simplified to a flatter diagram (Direct Handler / Workflow
   Orchestrator / Evidence-QoD-Pack-XAI-VisualizationSpec-RESPONSE spine)

**Regressions caught:**
- Direct Handler's output rejoined the main spine before RESPONSE instead
  of bypassing straight to it — a simple glossary lookup would incorrectly
  get a full evidence pack, XAI synthesis, and visualization plan.
- Policy validator dropped entirely — flagged as unacceptable given
  `esp/v1/{well}/commands` is reachable on an unauthenticated LAN broker.
- HITL dropped entirely.
- Follow-up path dropped — collapsing back into SIMPLE/WORKFLOW would
  force a full refetch for "explain that finding," discarding the
  biggest latency win available on this hardware.
- QoD re-drawn after all fetching again (same bug as Step 2, item 2).
- "Workflow Orchestrator" as a single box was flagged as hiding the one
  decision that defines the whole architecture (objective-declared
  fan-out vs. discovery) rather than committing to it.

**Resolution:** kept the flat diagram as an explanatory "L0" view (for
describing the system to someone new) but designated the corrected,
detailed diagram from Step 3 as the normative "L1" contract for
implementation. Both retained, with L1 explicitly the one to build from.

---

## 5. "Where are the LLM calls?" — explicit inference-point audit

Constraint added: all external data access is API-only (no MQTT
subscriber, no DB client, anywhere in the new service).

Produced the definitive LLM touchpoint map: 5 possible calls, at most 3
on any single query path (Understand & Select, Direct Answer OR XAI/
Recommendation, optional Gap-Fill). Everything else — Conversation
Context, Capability Retrieval (embeddings, not inference), Objective
Registry, Policy Gate, Tool Gateway, QoD, Evidence Pack assembly, Numeric
Provenance, VisualizationSpec, HITL templating and decisions — draws no
LLM call, ever.

One ordering fix applied here: Capability Retrieval must run *before*
Query Router/Understand-and-Select, not after — its entire purpose is to
shrink the selection prompt, which only works if it runs first.

Noted as a new requirement (not yet resolved at this point): since MQTT
is now explicitly excluded from the agent process, live telemetry needs
a REST snapshot endpoint on the Server 3 side (`GET /telemetry/{well}/
latest` and a windowed variant) — pub/sub was implicitly doing that job
before.

---

## 6. "Is ReAct needed?" — formal decision

Direct question, direct answer: no. Reasoning restated and locked in:
- Tool space is small (10 known external domains) and known in advance —
  a fan-out problem, not a search problem.
- The Objective Registry declares required evidence per objective up
  front, making a loop unnecessary.
- ReAct on a 3B CPU model has no termination guarantee — iteration caps,
  wall-clock budgets, and no-progress detection would have to be
  hand-built anyway, which is most of the control flow ReAct claims to
  provide.
- Non-deterministic call sequences per identical query are unacceptable
  for audit in a regulated operational context.
- ReAct's loop is the LLM performing search/computation — a direct
  violation of the "LLM computes nothing" invariant.

Gap-fill (bounded to one round) formally established as the mechanism
that covers ReAct's legitimate use case without its costs. Recorded as a
standing architectural decision (later written into ARCHITECTURE.md §8)
so it is not re-argued without new information — specifically: tool
space growing past ~50 unenumerable sources, or a genuine need for
hypothesis-refinement loops (fetch → theory → targeted fetch → revise).
If that ever happens, the stated fallback is a real framework with a
durable checkpointer (e.g. LangGraph), not a hand-rolled loop.

---

## 7. HITL implementation mechanics

Designed as: interrupt + durable run state + resume-at-point, zero LLM
involvement in the control logic itself.

- Three interrupt types defined: `CLARIFY` (post-routing, ambiguous/
  low-confidence), `APPROVE` (Policy Gate, before any mutating call),
  `INSUFFICIENT` (post-Pack-Seal, missing/conflicting required evidence).
- Key structural move: plans split explicitly into `READ` and `WRITE`
  calls. All `READ`s execute in parallel; any `WRITE` triggers `APPROVE`
  before dispatch — detected from the plan's shape up front, never
  discovered mid-run.
- Redis run-state schema defined (`esp:run:{run_id}`) with a `phase`
  field as the resume address — resume must never re-enter at the top of
  the pipeline, which would refetch evidence and could show the operator
  different numbers than the ones they approved against.
- Two safety mechanisms made non-negotiable: an idempotency lock
  (`SET ... NX EX 10`) on resume to prevent double-dispatch of a write
  command, and a staleness re-check on safety-relevant readings before
  executing a WRITE — an approval is bound to the evidence snapshot the
  operator saw, and if that data has aged past tolerance by resume time,
  the approval is voided and a fresh one raised against current data.

---

## 8. "HITL re-query with previous context" — user proposed a model where
   the human's answer becomes a new query through the same Query API,
   carrying session + pending-clarification + prior-analysis context.

**Assessed as directionally correct**, with four required additions:

1. **Bind / Supersede / Meta** — a pending clarification's answer isn't
   always a direct bind. The incoming message might supersede it (a new,
   unrelated query — pending must be explicitly closed as `ABANDONED`,
   audited) or be meta (a question *about* the pending clarification,
   answered without resolving it). Modeled as an explicit 3-way resolver,
   not an assumed bind.
2. **Pending state needs a TTL and a single-slot limit** — without
   expiry, a clarification asked hours earlier (e.g. before a shift
   change) could bind to an unrelated later message from a different
   operator.
3. **Pending must carry `plan_ref` + `pack_ref`**, not just a prior
   analysis id — the difference between resuming an *in-flight* run
   (reusing its plan and evidence) versus merely referencing a *finished*
   one.
4. **Approval must never travel through free text.** Given
   `set_operating_frequency` dispatches to an unauthenticated MQTT
   command topic, parsing "yeah go ahead" through an NLU pass is not an
   acceptable authorization mechanism. Split into two channels: `/query`
   (free text) for `CLARIFY`/`INSUFFICIENT`, and `/decision` (structured
   enum + token, from a UI control only) for `APPROVE`.

Also addressed: slot-fill vs. full re-plan (most clarification answers
should pattern-match the expected slot and patch in place with zero LLM
calls; only off-slot or new-intent answers trigger a full re-plan),
evidence dedup on re-plan via `hash(tool + canonical_args)` with a
per-tool freshness tolerance, pack versioning (`:pack:v1`, `:v2`, ...,
immutable, never mutated in place), and a `replan_count` loop guard.

---

## 9. "We don't care about LLM calls/budget — we have a local LLM"

**Reframed, not dismissed.** Local inference removes *token cost*, not
the three constraints that actually matter: wall-clock latency (serial
calls still stack in real time), contention (one `llama-server` instance
serves every concurrent operator — call count multiplies across users),
and the context ceiling (`-c 8192` is a hard wall regardless of who's
paying for tokens).

**What changed as a result:** the earlier call-minimization design was
reframed as a place to *spend* free inference on quality rather than
count — two-stage tool selection (domain → tool, better accuracy on a 3B
model than a flat 21-way choice), a critic pass on XAI output as a
backstop behind (never a replacement for) the deterministic numeric
check, per-section XAI prompts instead of one mega-prompt, and always
re-narrating on follow-up rather than taking a template shortcut.

**What did not change:** the ReAct decision (Section 6) stands — its
problems were never about token cost. Termination guarantees, path
determinism for audit, and the "LLM computes nothing" invariant are
correctness and safety properties, not budget line items. Free inference
makes ReAct *cheap*, not *correct*. Likewise Policy Gate, QoD, Numeric
Provenance, and the staleness re-check before a WRITE remain fully
deterministic regardless of inference cost.

---

## 10. Real-world validation against the previous deployment's diagram

User supplied their own hand-drawn diagram naming Conversation/Context,
Fast Query Gate, Query Understanding, Capability/Tool Retriever,
Objective Registry, a ReAct box, Policy/Plan Validator, Typed Tool
Gateway, Data Quality Gate, Evidence Pack, XAI Synthesizer,
Visualization Planner, Direct/Follow-up handlers, Session/Analysis State,
Audit/Trace, and a parallel HITL plane — essentially converging
independently on the same shape reached through this conversation, with
ReAct explicitly present.

Confirmed `all-mpnet-base-v2` (768-dim) already loads locally in the old
repo (`adapters/rag.py`), meaning Capability Retrieval costs nothing new
to add — the embedding infra already exists as a pattern to replicate.
Confirmed `EvidencePack` and `XAIEngine.generate_explanation(pack,
advisory)` already exist as typed contracts in the old repo — useful as
shape reference (per the data-model-only reuse rule established later in
Section 12).

Re-confirmed the god-object and sync-cycle flags from the architecture-
selection rubric against this version, and re-confirmed the four
`EXT` adapters (`ENG`, `MAINT`/CMMS, `CASE`, most of `ML`'s advertised
anomaly/fault/risk/degradation surface, `TWIN`) have nothing real behind
them yet.

---

## 11. Testing strategy — which LLM to test against

Question: for initial testing, use the LLM already running on
`192.168.1.191`, or a local GPU-enabled LLM?

**Decision: both, for different purposes — never conflate.**
- `191:8080` (bare `llama-server`, stateless, OpenAI-compatible) is safe
  to call directly for testing even while `191:8090` (the old agent
  gateway, stateful — Redis plan state, conversation store) is live.
  `agent_service` must never point at `:8090` — different service,
  different contract, would collide with real operational runs.
- Checked `start_gpu_llm.bat`: local GPU box runs the **identical**
  GGUF/quant as prod (`Qwen2.5-Coder-3B-Instruct-Q4_K_M`), just via CUDA
  instead of CPU AVX-512, and with `-c 4096` instead of prod's `-c 8192`.
  Since the weights are identical, local GPU is valid for **correctness**
  testing (routing accuracy, tool-call JSON schema adherence, narration
  quality, provenance-check pass rate) — but only after bumping its
  context window to `-c 8192` to match prod's ceiling, since several
  design decisions (evidence digests, session history, tool schemas)
  assume that budget.
- Local GPU is **not** valid for latency/timeout/concurrency sign-off —
  CUDA throughput (~58 tok/s) versus prod's CPU throughput are not
  comparable, and single-user local testing can't reveal multi-operator
  contention on the one shared `llama-server` instance. Those numbers
  must come from `191:8080` directly.

Two-phase test plan locked in: Phase A/B-correctness on local GPU
(`-c 8192` fixed), Phase B-perf (timeouts, p95 latency, concurrency)
only against the real `191:8080` CPU inference.

---

## 12. "We'll make provision on the local server, but still use API
    methods" — local-hosted LLM confirmed to follow the same rule

Confirmed explicitly: even a same-machine `llama-server` is reached via
HTTP through a config value (`LLM_GATEWAY_URL`), never an in-process
model load or local import of weights. Zero branching in application
code between "local" and "prod" targets — only the URL changes. Added a
corollary: timeout values must be configurable (not hardcoded), since a
timeout tuned against a fast local GPU box will silently fail against
slower CPU inference on 191 and masquerade as an application bug.

---

## 13. "What data models are currently ready?"

Inventory taken and split into **ready-as-reference-shape** (MQTT payload
schemas for `telemetry`/`vfm`/`asset`/`events`; SQLite schemas for
`unlabelled.db`, `mlresults.db`, `normalized.db`, `esp_events.db`; the
existing typed contracts — `sse_events.py`, `evidence.py`, `advisory.py`,
`mqtt_payloads.py`, `formulae.py`; the KB's Postgres backing tables; the
21-tool `tool_definitions.json`) versus **not ready, must be authored
fresh** (the objective manifest as structured data — currently only
exists as scattered if/elif logic; `VisualizationSpec` — no type exists
anywhere in the old repo; the HITL pending/bind-supersede-meta run-state
schema — no prior art; the Policy Gate rule schema — current gate is
inline regex, not data; the adapter capability manifest; the CMMS/
Maintenance model, which doesn't exist at all).

---

## 14. "This tool registry — wasn't defined in this session, right?"

Confirmed: `tool_definitions.json` is pre-existing, from
`esp_agent/src/agent/v2/`, first surfaced by the Step 1 context-gathering
pass — not something authored during this conversation. Clarified its
actual scope precisely: it is *only* the 21 OpenAI-function-calling
schema entries (name, description, parameter shape) — no executor
binding lives in that file. The binding was three files of string glue
in the old repo (`TOOL_TO_OBJECTIVE` dict → `_decompose_steps()` if/elif
→ `specialist_executor.py` if/elif), which is exactly the part being
replaced, not reused.

---

## 15. "Nothing would be made use as esp_agent — only the data model is to
    be reused, not the arch" — formal reuse boundary locked

Explicit confirmation and tightening of the rule already implicit since
Step 1: zero code or architecture reuse from `esp_agent/` (or its
duplicate trees under `backend/`, `Server3_Deployment_Package/backend/`
— **note:** this predates the Section 16 decision to migrate the Server3
package itself; see that section for how the boundary applies there).
Concrete table drawn: reuse field names / column names / tool
descriptions / catalog data by retyping fresh in `agent_service`'s own
contracts; never `import` the old `.py` files, never carry over
`orchestrator.py`'s routing ladder, `bff_routes.py`'s per-scenario
coroutines, `plan_node.py`'s decomposition logic, or the LangGraph
specialist graphs. `agent_service/` is a clean room; the old repo is read
like a spec document, never depended upon. This was written into
`ARCHITECTURE.md` as new Section 1.1.

---

## 16. Repo layout decision: migrate `Server3_Deployment_Package`, don't
    reimplement it

Proposal: rather than rebuilding the Server 3 backend/historian/ML/UI
stack from scratch inside the new repo, migrate `Server3_Deployment_
Package` (backend, data, ML, **and UI** — confirmed explicitly) as-is
into a new repo as a sibling folder to `agent_service`.

**Agreed, with one hard rule attached:** same-repo does not mean
same-process. Even as sibling folders in one repository, `agent_service`
must reach `server3_deployment_package` exclusively through its REST API
(`:8090`), with zero `import` across the boundary — no shared venv
assumption, no reaching into `backend_service/app/` for a function. This
preserves the deploy-anywhere property: splitting back onto two physical
servers, or collapsing onto one box, both become a one-line config
change (`AGENT_GATEWAY_URL` / equivalent) with zero code change either
way.

**Explicitly called out:** migration is relocation, not remediation. The
known gaps (historian range query, missing SHAP endpoint, no formula
REST API, KB needing a service wrapper, no CMMS) travel with the
migrated package unchanged and must still be fixed *inside*
`server3_deployment_package/` before `agent_service` can treat those
sources as trustworthy.

This produced the final repo layout and the update to `ARCHITECTURE.md`
Section 0, and is the most recent decision as of this document.

---

## Standing decisions (do not re-litigate without new information)

1. No ReAct loop. Deterministic objective-declared fan-out + one bounded
   gap-fill wave instead. Revisit only if the tool space grows past ~50
   unenumerable sources or genuine hypothesis-refinement reasoning is
   required — and if so, adopt a real framework with a durable
   checkpointer, not a hand-rolled loop.
2. No LangGraph, for the same reason — there is no cycle left to justify
   it once ReAct is dropped.
3. The LLM never computes, authorizes, or validates. Enforced
   mechanically by the Numeric Provenance Check, not left as convention.
4. All external access is API-only — no MQTT client, no DB driver,
   anywhere inside `agent_service`.
5. Approval (`APPROVE`) never travels through free text — structured
   `/decision` endpoint only, distinct from the free-text `/query` path
   used for `CLARIFY`/`INSUFFICIENT`.
6. Resume always re-enters at the interrupted phase with the sealed
   evidence pack intact — never at the top of the pipeline.
7. Zero code/architecture reuse from `esp_agent/`. Data shapes only,
   retyped fresh.
8. `agent_service` and `server3_deployment_package` communicate over
   REST only, even as sibling folders in the same repo.
