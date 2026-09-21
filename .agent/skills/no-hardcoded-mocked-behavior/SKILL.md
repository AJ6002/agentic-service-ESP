---
name: no-hardcoded-mocked-behavior
description: Guidelines for building and reviewing agentic IDEs, multi-agent pipelines, and AI-generated app code so they don't silently fall back to hardcoded values or mocked/fabricated behavior. Use this skill whenever generating code for an agentic IDE or agent orchestration system, wiring a frontend to a backend, designing "run this script" / execute-code features, writing tests for LLM or agent calls, reviewing a PR or codebase for hardcoded config or fake integrations, or when the user asks how to make sure their app is "actually working" and not just faking it. Also use when the user mentions handoff hallucinations, mocked test responses, backend-driven config, context orchestration, or debugging multi-agent trajectories.
---

# Eliminating Hardcoded and Mocked Behavior in Agentic IDEs

## Why this matters

Agentic IDEs and multi-agent systems are prone to producing code and UI that *look* correct but are secretly backed by placeholder logic: canned responses, literals copied from a backend, or agents that fabricate an output instead of calling the tool that would produce it. These failures are silent — tests pass, demos work — until real data or real usage exposes them. Treat "did this actually execute / actually integrate" as a first-class correctness question, not an afterthought.

Apply the guidance below whenever you (a) generate code for an agentic IDE, app builder, or multi-agent pipeline, (b) wire a frontend to a backend, (c) design or review a "run/execute" feature, (d) write or review tests that touch LLM calls or agent behavior, or (e) are asked to audit a codebase for this class of bug.

## Core principle

**Every value, every "it worked," and every inter-agent handoff needs a traceable source.** If a number, config value, or execution result can't be traced back to a config provider, a real script execution, or a verified upstream agent output, it's either hardcoded or mocked — flag it.

---

## 1. No-hardcode policy for generated code

- Never embed environment-specific values, credentials, thresholds, or business config as literals in generated code. Load them from a config provider, secret manager, or context store instead.
- Treat a hardcoded/mocked response as its own class of agent error (akin to "constraint ignorance" or "format error"), not just a style nit — flag it explicitly rather than silently fixing it and moving on.
- If scaffolding or a placeholder is genuinely needed (e.g., for a demo or local test), mark it explicitly in code and comments — never let it look indistinguishable from a real integration.

## 2. Backend-driven configuration over hardcoded frontends

- The backend is the single source of truth for pipeline stages, form fields, feature flags, and plan limits. The frontend fetches this via an API and renders generically from the schema — it does not keep its own copy.
- When you generate or edit UI code (dashboards, forms, feature panels), drive it from config/schema APIs rather than defining independent local constants. Any change to config should require zero frontend code edits.
- When migrating existing hardcoded frontend config: expose an API returning config in the shape the frontend expects, refactor the UI to be schema-driven, then remove the local constants — in that order, so nothing breaks mid-migration.

## 3. Context layer instead of ad-hoc runtime fetching

- Prefer a dedicated context layer that pre-materializes data into an indexed, typed, permission-aware store, over agents making scattered API calls at runtime to assemble context.
- Use governed connectors (MCP-style or equivalent) for tool/data access instead of ad-hoc, hardcoded integrations.
- Reserve live API calls for writes and freshness-critical reads; use the pre-materialized context store as the default read path.

## 4. Handoff verification between agents and pipeline stages

Multi-agent pipelines fail at the boundaries: a downstream agent treats an upstream agent's fabricated or distorted output as ground truth ("handoff hallucination"). Instrument every boundary, not just the final output:

- Key boundaries to verify: planning → code generation, code generation → execution, execution results → UI rendering, and any agent-to-agent handoff in between.
- At each boundary: extract the concrete claims in the output, ground them against the source (spec, script, context store), calibrate confidence, and block or flag anything inconsistent or low-confidence rather than passing it through.
- Log both the pre- and post-transformation state at each boundary (e.g., the input spec alongside the generated code, not just the final code) so a verification or debugging pass later has full context to work with.

## 5. Separate "generate" from "execute" — always

This is the single most common source of faked behavior in agentic IDEs:

- Never let an agent synthesize what an execution result "would look like" instead of actually invoking the runner. Generation and execution are distinct steps with a hard boundary between them.
- Instrument the script runner to emit execution traces (start, end, status, dynamic outputs). Any IDE response claiming a script ran should have a corresponding runner trace — a response without one is suspicious and should be treated as a bug, not a feature.
- Feature tests should assert the coupling explicitly: the test should fail if the IDE's reported result doesn't reference the latest runner output (e.g., it's a static template that doesn't vary with input).

## 6. Layered fixtures for tests involving LLM/agent calls

Use a three-tier fixture strategy rather than one flat layer of mocks:

| Tier | Purpose | Use for |
|---|---|---|
| Stub fakes | Fast, deterministic plumbing checks | Control-flow tests unrelated to model/script correctness |
| Recorded cassettes | Deterministic but faithful to real behavior | Regression tests on reasoning/output correctness |
| Live canaries | Small number of real, end-to-end calls | Catching drift the recordings would miss |

- Don't collapse "does the control flow around the agent work" and "is the agent's reasoning/script output correct" into the same mock-based assertion — they test different things and a passing mock-only test can hide a broken integration.
- For "run this script" features specifically, fixtures must include dynamic elements (timestamps, counts, side effects) that a hardcoded response *couldn't* reproduce — if a canned string would pass the test, the test isn't proving anything.
- Schedule live-execution canary tests (nightly or pre-merge) against real data to catch cases where logic has silently reverted to hardcoded responses over time.

## 7. Detecting hardcoded/mocked behavior (checklist)

When reviewing generated code, a PR, or a running system, check for:

- **Static red flags**: hardcoded URLs, IDs, credentials, or magic numbers in generated code — add lint rules to catch these in the code-generation pipeline itself.
- **Constant-output smell**: does the output change when the input changes? An output that's constant regardless of input is either mocked or the code path isn't actually being exercised.
- **Missing runner correlation**: does every "it ran" response have a matching execution trace? If not, the agent may be fabricating results instead of calling the runner.
- **Exact-match tests**: tests that only pass when strings are exactly equal to a canned response are themselves a smell — they reward hardcoding rather than catching it.
- **UI transparency**: does the UI distinguish "this is real execution output" from "this is a scaffolded/demo view"? If not, add that instrumentation so users (and you) aren't fooled by it either.

## 8. Trajectory-level debugging and regression

- Record full agent trajectories (prompts, intermediate plans, tool calls, execution attempts, final response) rather than just final outputs, so failures can be localized to the step where things went wrong.
- When diagnosing a failure, find the *earliest* critical error in the trajectory (e.g., the step where the agent chose to hardcode/fabricate instead of executing) rather than only looking at the final wrong output.
- Once a hardcoded/mocked-behavior bug is found, convert it into a versioned regression fixture (prompt + expected real-execution behavior) so future changes are tested against it — don't let the same failure mode silently reappear after a prompt or orchestration change.
- Tag regressions by failure family (e.g., "hardcoded UI", "mocked test response", "missing runner invocation") with severity and suggested repair, so they can be triaged systematically.

## 9. Governance

- State explicitly (in docs, PR templates, or CI policy) that hardcoded environment-specific values, credentials, and business thresholds are forbidden in production code paths.
- Any automated repair that changes routing between execution and UI (e.g., an auto-fix from a debugging tool) should get human or policy review before merging — automated fixes can introduce new hidden mocks just as easily as they remove old ones.
- Document what scaffolding/mocking *is* acceptable (demos, local/offline tests) versus what's production-safe, so contributors aren't guessing.

---

## Quick reference: what to do with this skill

- **Generating code for an agentic IDE feature?** Apply §1, §2, §5 as you write it — don't wait for review to catch a hardcoded literal or a faked execution path.
- **Reviewing/auditing existing code or a PR?** Walk the §7 checklist.
- **Designing tests for LLM/agent/script behavior?** Use the §6 fixture tiers; make sure at least one tier can't be satisfied by a hardcoded response.
- **Debugging a multi-agent pipeline that produced a wrong or fabricated result?** Use §8 to localize the earliest bad step, then §4 to figure out which handoff boundary should have caught it.
- **Setting up config or context flow?** Apply §2 and §3 so agents and UI never need their own copy of business data.

When you flag an instance of hardcoded or mocked behavior, say so explicitly and name which pattern above it violates — don't quietly patch it without surfacing that it was there.
