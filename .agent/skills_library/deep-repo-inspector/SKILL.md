---
name: deep-repo-inspector
description: Use when asked to deeply inspect, audit, or understand a repository at code level — trace data flow, find dead/unrelated files, determine if the repo is runnable, or assess actual vs intended implementation state. Triggers on "deep inspect this repo", "trace the data flow", "is this repo runnable", "what files are dead/unused", "audit this codebase end to end", or "tell me what is actually implemented vs planned". Combines static analysis (CFG, call graph, dependency graph, data-flow/taint analysis), reachability analysis, and live execution/testing to produce a verified, file-by-file map of the repository.
argument-hint: "[path to repo] [optional: specific entrypoint or scenario to trace]"
---

# Deep Repository Inspector

## What this does

Performs a full structural + behavioral audit of a repository. It builds
static graphs (dependency graph, call graph, control-flow graph, data-flow
graph), computes reachability from real entrypoints, attempts to actually
run/build/test the app, and cross-validates static findings against
runtime reality. The output classifies every file into a flow role,
flags dead/unrelated files, states whether the repo currently runs,
and separates "what works today" from "what was intended but is
incomplete" with an explicit remaining-work list.

This is a heavy, multi-pass pipeline. Do not shortcut phases. Do not
guess file roles from names alone — verify through actual parsing,
graph construction, and where possible, execution.

## Non-Negotiable Rules

1. NEVER classify a file as "dead" or "unrelated" based on naming
   convention or folder location alone. Classification must come from
   reachability analysis (Phase 3), not intuition.
2. NEVER claim the repo "works" or "is runnable" without actually
   attempting to install dependencies, build, and execute it or its
   tests (Phase 4). If execution is not possible in the current
   environment, state that explicitly as a limitation — do not
   substitute a guess.
3. NEVER silently assume incomplete work is intentional. If a flow
   path terminates in a stub, TODO, mock, or placeholder, flag it as
   incomplete, not as "by design," unless a spec/comment explicitly
   says so.
4. NEVER conflate "intended scope" with "current scope." Always report
   both, separately, even if this makes the answer longer.
5. Completeness outranks brevity. A long, exhaustive, file-by-file
   report is correct output, not a failure.

## Phase 0: Scope and Setup

1. Identify the repository root path. If not given, ask for it.
2. Identify the primary language(s)/framework(s) by scanning for
   manifest files (package.json, requirements.txt, pyproject.toml,
   go.mod, Cargo.toml, pom.xml, *.csproj, etc.).
3. Identify the intended purpose of the app:
   - Read README.md, ARCHITECTURE.md, docs/, or any spec files first.
   - If no docs exist, infer intended purpose from entrypoint code,
     route definitions, and top-level folder naming, and state clearly
     that this is an INFERRED purpose, not a documented one.
4. Identify candidate entrypoints:
   - main files (main.py, index.js, app.py, cmd/*/main.go, etc.)
   - CLI commands, HTTP route registrations, scheduled job definitions
   - test suite entrypoints (these count as roots too — code only
     reached by tests is still "reachable," just not reachable in
     production flow; label it accordingly)
5. State the scope and plan in 3-5 lines before proceeding: purpose,
   detected stack, candidate entrypoints, what will be done next.

## Phase 1: Static Structural Pass

Build three graphs across the ENTIRE repository, not a sample:

### 1a. Dependency Graph
- Parse every import/require/include/use statement in every source file.
- Build a graph: nodes = files/modules, edges = "A imports B."
- Detect circular dependencies; flag them.
- Detect orphan files: never imported by anything AND not an entrypoint.

### 1b. Call Graph
- For every function/method/class in every file, extract its
  definition and every call site inside it.
- Build a graph: nodes = functions/methods, edges = "A calls B."
- Where static analysis cannot resolve a call target (e.g. dynamic
  dispatch, reflection, string-based routing), mark the edge as
  UNRESOLVED and note it — do not silently drop it or silently guess.

### 1c. Control-Flow Graph (per function, as needed)
- For functions on candidate execution paths (Phase 2), build CFGs to
  understand branching, error handling, and early returns.
- Use CFGs to check whether a function actually completes its intended
  logic on all paths, or whether some branches are unreachable/stubbed.

Output of Phase 1: three raw graphs (can be represented as adjacency
lists/tables) plus a first-pass orphan-file candidate list.

## Phase 2: Data-Flow Tracing

For each entrypoint identified in Phase 0 (or the specific scenario the
user asked about):

1. Trace the actual data path step by step:
   - Where does input enter (HTTP request, CLI arg, file read, queue
     message, UI event)?
   - Which functions/files transform it, in what order?
   - Where does it terminate (DB write, API call, file write, UI
     render, response)?
2. Use the call graph (Phase 1b) plus manual variable/parameter tracing
   to follow the data itself, not just function call order — note
   where data is transformed, validated, dropped, or duplicated.
3. Produce one explicit flow diagram per entrypoint/scenario, in this
   form:

```
[Input source] -> file_a.py:function_x() -> file_b.py:function_y()
   -> [transformation: describe it] -> file_c.py:function_z()
   -> [DB/API/output]: describe destination
```

4. Mark any point in the flow where:
   - a function is a stub, mock, or hardcoded placeholder
   - error handling is missing where the flow could plausibly fail
   - the flow silently diverges from what Phase 0's stated/inferred
     purpose implies it should do

## Phase 3: Reachability & Dead-File Classification

1. Define ROOT SET = all entrypoints from Phase 0 (production
   entrypoints AND test entrypoints, labeled separately).
2. Using the call graph + dependency graph, compute the reachable set
   of files/functions from the ROOT SET.
3. Classify every file in the repository into exactly one category:

| Category | Definition |
|---|---|
| CORE FLOW | Reachable from a production entrypoint; on a real user-facing data path |
| SUPPORTING | Reachable from a production entrypoint; utility/helper/config, not itself a data path |
| TEST-ONLY | Reachable only from test entrypoints, not from production entrypoints |
| CONFIG/BUILD | Build tooling, CI config, linting config, env files — not part of runtime flow by nature |
| UNREACHABLE / DEAD | Not reachable from any entrypoint (production or test) |
| UNRESOLVED | Reachability could not be determined statically (dynamic dispatch, reflection, etc.) — flag for manual/dynamic verification |

4. Produce a full file-by-file table with this classification. Do not
   omit any file in the repository from this table.
5. For every DEAD file, state WHY it appears dead (never imported,
   imported only by another dead file, superseded by a newer file,
   etc.) — do not just label it, justify it.

## Phase 4: Execution Verification (Do Not Skip)

This is what separates this skill from a purely static report.

1. Attempt to install/resolve dependencies exactly as the repo
   specifies (package manager lockfiles, requirements files, etc.).
2. Attempt to build the project if a build step exists.
3. Attempt to start/run the application using its documented or
   inferred entrypoint.
4. Attempt to run the test suite if one exists.
5. Record the ACTUAL outcome of each step: success, failure with
   exact error message, or skipped with reason (e.g. requires external
   service/credentials not available).
6. If any step fails, do not stop the whole analysis — this itself is
   a finding. State explicitly: "Current repo state is UNRUNNABLE at
   [step], because [exact error]." Continue Phases 1-3 and 5-6 fully
   regardless — static analysis and gap analysis are still valuable
   and must still be delivered in full.
7. If execution succeeds, use runtime instrumentation (logs, print
   tracing, or debugger stepping if available) to confirm at least the
   primary entrypoint's data flow from Phase 2 actually executes as
   traced. Note any divergence between static trace and actual runtime
   behavior.

## Phase 5: Intended vs Actual Scope Analysis

1. Restate the intended purpose from Phase 0 (documented or inferred,
   labeled accordingly).
2. For each major intended capability (derived from docs, route lists,
   UI screens, or stated feature set), determine:
   - IMPLEMENTED AND WORKING: confirmed via Phase 4 execution or, if
     execution wasn't possible, via complete non-stubbed code path
     from Phase 2.
   - IMPLEMENTED BUT BROKEN: code exists but fails at runtime or has
     an incomplete/incorrect logic path per Phase 1c/Phase 2.
   - PARTIALLY IMPLEMENTED: some of the flow exists, but terminates in
     a stub, TODO, or missing integration.
   - NOT IMPLEMENTED: intended per docs/purpose but no corresponding
     code path found anywhere in the call/dependency graph.
3. Never mark something "PARTIALLY IMPLEMENTED" as if it were complete
   just because a POC-level version exists — always name the specific
   missing piece.

## Phase 6: Final Report Assembly

Produce a single structured report with these sections, in order:

1. **Repository Overview** — purpose (documented/inferred), stack,
   entrypoints identified.
2. **Runnability Verdict** — RUNNABLE / PARTIALLY RUNNABLE / UNRUNNABLE,
   with the exact evidence from Phase 4.
3. **Data Flow Diagrams** — one per entrypoint/scenario from Phase 2.
4. **File Classification Table** — full file-by-file table from Phase 3
   (CORE FLOW / SUPPORTING / TEST-ONLY / CONFIG-BUILD / DEAD /
   UNRESOLVED), with justification column.
5. **Dead & Unrelated Files** — pulled out separately as its own list
   with counts: "X files in core flow, Y files dead/unrelated," plus
   the justification for each dead file.
6. **Intended vs Actual Capability Matrix** — table from Phase 5:
   capability | status | evidence | what's missing.
7. **Remaining Work To Reach Intended Scope** — concrete, specific,
   file-referenced list of what needs to be built/fixed/wired to move
   from current state to fully intended state.
8. **Confidence & Limitations** — state anywhere static analysis had
   UNRESOLVED edges, anywhere execution could not be verified (missing
   credentials/services), and anywhere purpose had to be inferred
   rather than read from docs.

## Anti-Patterns to Actively Resist

- Do NOT skip Phase 4 execution attempt because "it looks like it
  would work." Attempt it. Report the real outcome.
- Do NOT mark a file dead without tracing why in the dependency/call
  graph — a guess based on file name or folder is not acceptable.
- Do NOT say "the repo is complete" if any capability in Phase 5 is
  PARTIALLY IMPLEMENTED or NOT IMPLEMENTED — always report the gap.
- Do NOT compress the file classification table for brevity — every
  file gets a row.
- Do NOT treat "it's a POC" as license to skip verifying whether even
  the POC-scope claims actually run.
