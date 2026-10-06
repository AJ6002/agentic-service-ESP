---
title: Router Three-Layer Misroute Defense Architecture - Plan
type: refactor
date: 2026-10-06
artifact_contract: ce-unified-plan/v1
artifact_readiness: deferred-architectural-debt
execution: code
status: deferred-pending-diagnostic-upgradation
---

# Router Three-Layer Misroute Defense Architecture - Plan

> [!IMPORTANT]
> **Architectural Debt & Sequencing Record (Deferred)**:
> Execution of the full Three-Layer Misroute Defense (demoting regexes to hints, adding Layer 2 entry-condition validators, and wiring Layer 1 confidence gating) is **explicitly deferred** to minimize blast radius until after the **Diagnostic Upgradation** is completed.
>
> **Logged Technical Debt**:
> 1. **Brittle Regex Gates (Latency vs Fragility)**: The router continues to rely on sequential deterministic regexes (`GREETING`, `IDENTITY`, `FLEET`, `PLATFORM_GUIDE`, `FOLLOWUP`, `DEFINITIONAL`) before calling the LLM to avoid ~2-second routing latency on the 3B model. While fast, unexpected human phrasing or unlisted typos risk falling into broad definitional patterns.
> 2. **Unvalidated LLM Decisions (Missing Layer 2)**: When the query bypasses regexes and reaches the LLM, proposed routes are not yet validated against structural invariants (e.g. verifying an asset is present before executing `OP03`, or checking for well IDs inside `OP06`).
> 3. **Interim Mitigation Applied (Active)**:
>    - `IDENTITY_PATTERNS` regex widened to cover common typos (`capabilties`, `capablities`, `capabillities`, `fetures`, `funcions`) and word orderings (`"your all"`, `"all your"`, `"all of your"`).
>    - `router_v1.txt` updated to document `IDENTITY` and `OP15_PLATFORM_GUIDE` in the schema and rules.
>    - Unified router decision logging added to every code path (`path_fired`, `llm_said`, `final_route`) to build empirical misroute logs for future regression testing.
> 4. **Resumption Trigger**: Fully execute Units U1–U4 in this plan once Diagnostic Upgradation is stabilized.

## Goal Capsule

- **Objective**: Ensure 100% dependable query routing across natural language variations, typos, and phrasing orders, so that generic requests never hijack diagnostic workflows and specific queries never collapse into silent failures.
- **Means**: Transition from brittle regex bouncers to an LLM-first classification architecture backed by three structural defense layers: confidence gating, route entry-condition validators, and deterministic regex fallbacks.
- **Authority Hierarchy**:
  1. Safety Gate (unconditional deterministic block on hardware actuation/writes)
  2. Route Entry-Condition Validators (Layer 2 structural evidence requirements)
  3. LLM Router (primary natural-language intent classifier)
  4. Deterministic Fallback / Clarification (Layer 3 floor)
- **Stop Conditions**: The router reliably handles typos, reordered syntax, asset diagnostics, fleet queries, platform guide queries, and self-knowledge requests without unhandled exceptions or misrouting dangerous queries into generic buckets.
- **Execution Profile**: `code`
- **Tail Ownership**: `ce-work` / unit test verification suites.

---

## Product Contract

### Summary
The current query router relies on seven sequential regular expressions that act as rigid gates before the language model is ever invoked. When an operator types natural variations with typos or non-standard syntax (such as *"what are your all capabilties ?"*), the query misses the strict regex, falls into an overly broad definitional pattern (`DEFINITIONAL_PATTERNS`), and routes to `OP06_KNOWLEDGE_LOOKUP`, triggering an embarrassing `INSUFFICIENT_EVIDENCE` error against physical ESP manuals.

This plan shifts the router to an **LLM-first architecture** with **three structural defense layers**. The 3B model serves as the primary semantic interpreter, while six deterministic entry-condition validators ensure that every route satisfies its prerequisite evidence before dispatch.

### Problem Frame
Misroutes in an industrial APM copilot carry asymmetric severity:
- **Catastrophic / Credibility-Destroying**: Routing a specific diagnostic question (e.g., *"why did the well trip"*) into generic manual definitions (`OP06`), returning an encyclopedic definition instead of a well RCA.
- **Embarrassing**: Routing assistant self-knowledge questions (*"what are your features"*) into engineering manuals, causing the assistant to report missing sensor data.
- **Confusing**: Routing platform navigation questions into well diagnostics.

Hardcoded regex bouncers create an illusion of safety while introducing fragility against ordinary human language. Conversely, bare LLM routing without guardrails risks hallucinatory dispatch on small edge models (3B). The defense must combine the linguistic flexibility of the LLM with deterministic entry-condition invariants.

### Requirements

#### Routing Core & Prompts
- **R1. Schema & Capability Expansion**: Update `router_v1.txt` to explicitly include `IDENTITY` and `OP15_PLATFORM_GUIDE` in the routing schema and intent enumeration.
- **R2. Source-of-Truth Decision Training**: Structure the LLM router prompt around the data source required to answer the query (Agent Self, Platform UI, Engineering KB, Single Well Telemetry, Fleet Aggregates).
- **R3. Contrasting Pair Instruction**: Provide the router with explicit disambiguation pairs (e.g., *"what is gas lock"* vs *"is FS-17 gas locked"*; *"what are your capabilities"* vs *"what are pump capabilities"*).

#### Defense Layers
- **R4. Layer 1 Confidence Gate**: If the LLM router confidence score is below `0.70`, reject the direct choice and fall through to Layer 3 deterministic fallback.
- **R5. Layer 2 Structural Entry Validators**: Execute six deterministic entry-condition validation checks on every LLM-proposed route:
  - *Check 1 (Asset Diagnostics)*: If route is `OP01`-`OP05` or `OP14` but no asset is resolvable from text or context, trigger `CLARIFY`.
  - *Check 2 (Knowledge Lookup Protection)*: If route is `OP06` but the query references a specific well ID, re-route to `OP03_FAULT_DIAGNOSIS`.
  - *Check 3 (Identity Protection)*: If route is `IDENTITY` but query contains no identity or agent-capability markers, re-route to `OP06` / `SIMPLE`.
  - *Check 4 (Platform Guide Protection)*: If route is `OP15` but `selected_route` is absent and the query contains no UI elements, re-route to `OP06`.
  - *Check 5 (Fleet Scope Protection)*: If route is a fleet objective (`OP08`, `OP09`, `OP13`) but query contains no fleet scope indicator, trigger `CLARIFY`.
  - *Check 6 (Confidence Floor)*: Low confidence (< 0.70) triggers fallback routing.
- **R6. Layer 3 Deterministic Fallback**: When the LLM is unavailable, low confidence, or structurally invalid, evaluate regex hints, trigger clarification, or apply safe defaults.

#### Regression & Testing
- **R7. Zero-Discrepancy Regression Suite**: Expand `tests/test_router_*.py` to evaluate 50+ real-world operator phrasings, syntax inversions, and spelling mistakes.

---

## Planning Contract

### Key Technical Decisions
- **KTD1. LLM-First with Structural Post-Validation**: The LLM evaluates the raw prompt first. Regexes are demoted from blocking gates to Layer 3 fallbacks and Layer 1 context hints.
  *(session-settled: user-directed — chosen over regex-first bouncers to prioritize quality and typo-resilience over microsecond latency).*
- **KTD2. Model Pinning (3B Coder Q4)**: Maintain the current local `Qwen2.5-Coder-3B-Instruct` endpoint as the router engine, optimizing prompt clarity and token economy rather than migrating model architectures.
  *(session-settled: user-directed — constrained by available local deployment resources).*
- **KTD3. Six Dedicated Validator Functions**: Implement modular, discrete validator functions per route in `app/routing/validators.py` rather than nested conditional blocks inside `router.py`.

### High-Level Technical Design

```
                         Incoming User Message
                                   │
                                   ▼
                 [0. Deterministic Safety Gate]
                 (Actuation / Write protection)
                                   │
                                   ▼
                       [1. LLM Semantic Router]
                  (Qwen2.5-Coder-3B with router_v2)
                                   │
                                   ▼
                     [2. Layer 1: Confidence Gate]
                         Is confidence >= 0.70?
                         ┌─────────┴─────────┐
                        YES                  NO
                         │                   │
                         ▼                   │
            [3. Layer 2: Route Validators]   │
            - Asset required for OP01-05?    │
            - Well ID in OP06?               │
            - Identity markers for IDENTITY? │
            - UI markers for OP15?           │
            - Fleet markers for OP08/09/13?  │
                         │                   │
                    All Valid?               │
                   ┌─────┴─────┐             │
                  YES          NO            │
                   │           │             │
                   ▼           └──────┬──────┘
            [Execute Route]           ▼
                             [4. Layer 3: Fallback]
                             - Evaluate Regex Hints
                             - Clarify Asset / Scope
                             - Safe Default Dispatch
```

---

## Implementation Units

### U1. LLM Router Prompt Overhaul (`router_v2.txt`)
- **Goal**: Rebuild the router prompt to comprehensively teach the 3B model all valid routes, source-of-truth mappings, and contrasting pairs.
- **Files**:
  - `agent_service/app/llm/prompts/router_v1.txt`
  - `agent_service/app/llm/calls.py`
- **Approach**:
  - Update output schema to include `"IDENTITY"` route and `"self_knowledge"` / `"platform_guide"` intents.
  - Define the 5 fundamental source categories: Assistant Capabilities, Platform UI Guide, Engineering Manuals/KB, Single-Well SCADA/Events, Fleet Aggregates.
  - Add explicit contrasting few-shot examples to prevent definitional hijack.
- **Verification**: `pytest tests/test_llm_standalone_inference.py` confirming valid JSON and classification.

### U2. Structural Route Entry Validators Module
- **Goal**: Implement Layer 2 entry-condition validators as standalone, testable functions.
- **Files**:
  - `agent_service/app/routing/validators.py` *(New)*
  - `agent_service/tests/test_route_validators.py` *(New)*
- **Approach**:
  - Implement `validate_route_decision(decision: RouteDecision, raw_message: str, router_input: RouterInput) -> ValidationResult`.
  - Implement individual checks: `check_asset_presence`, `check_no_asset_in_kb`, `check_identity_markers`, `check_ui_context`, `check_fleet_indicators`.
  - Return clean re-route targets or clarification metadata upon invalid conditions.
- **Verification**: Dedicated unit tests asserting all 6 invalid edge cases are corrected.

### U3. Router Pipeline Re-Architecture (`router.py`)
- **Goal**: Wire the 3-layer defense pipeline in `route_query_full`.
- **Files**:
  - `agent_service/app/routing/router.py`
- **Approach**:
  - Keep safety gate for hardware actuation blocks.
  - Demote `IDENTITY_PATTERNS`, `PLATFORM_GUIDE_PATTERNS`, and `DEFINITIONAL_PATTERNS` to soft hints passed into context block.
  - Invoke `llm_route` as primary classifier.
  - Pass result through Layer 1 confidence gate (`conf >= 0.70`).
  - Pass result through Layer 2 entry validators.
  - Fall back to Layer 3 deterministic regex hint resolution if Layer 1 or Layer 2 fails or if LLM is unavailable.
- **Verification**: `pytest tests/test_router_*.py` and `tests/test_identity_route.py`.

### U4. Comprehensive Misroute Regression Suite
- **Goal**: Establish a durable test suite with real operator typos, reversed word orders, and tricky edge queries.
- **Files**:
  - `agent_service/tests/test_router_misroute_defense.py` *(New)*
- **Approach**:
  - Test typo resilience: `"what are your all capabilties"`, `"what can u do"`, `"list featurs"`.
  - Test diagnostic vs definitional disambiguation: `"what is gas lock"` (OP06) vs `"is FS-17 gas locked"` (OP03).
  - Test UI guide disambiguation: `"what is working status screen"` (OP15) vs `"what is the status of FS-004"` (OP01).
- **Verification**: 100% pass rate across all test cases.

---

## Verification Contract

- **Unit Test Command**:
  ```powershell
  & "A:\TAS-AI\ESP\.venv\Scripts\python.exe" -m pytest tests/test_route_validators.py tests/test_router_misroute_defense.py tests/test_identity_route.py tests/test_router_op15.py -v
  ```
- **Live HTTP Query Verification**:
  ```powershell
  & "A:\TAS-AI\ESP\.venv\Scripts\python.exe" -c "import asyncio, httpx; ... query test script ..."
  ```
- **Quality Gates**:
  1. 0% of identity queries routed to `OP06_KNOWLEDGE_LOOKUP`.
  2. 0% of diagnostic queries without assets dispatched without clarification.
  3. 100% pass on offline fallback when LLM gateway is stopped.

---

## Definition of Done

- All 4 Implementation Units (`U1`–`U4`) implemented and verified.
- The 6 structural entry validators are active and logging any corrected misroutes.
- `router_v1.txt` is updated with full `IDENTITY` and `OP15` routing logic.
- Full pytest test suite passes with zero regressions.
