---
name: holistic-change-validation
description: Use immediately before declaring an implementation complete. Performs a project-wide consistency review covering dependency impact, interface contracts, DTO consistency, imports, test coverage, and end-to-end flow to catch downstream issues before compile or test run.
---

# Holistic Change Validation

## Purpose

A pre-completion verification gate. Use this skill immediately before declaring any implementation complete. It forces a project-wide consistency review so that downstream issues are caught before the first compile or test run, not after.

This skill addresses the core failure mode of iterative patch-and-repair cycles caused by local reasoning — fixing one error only to introduce another, repeating until the codebase converges by accident rather than by design.

---

## When to Use

Invoke this skill:

- Before saying "the implementation is complete"
- Before handing back control after a multi-file change
- After any refactoring that touches shared interfaces, DTOs, services, or contracts
- After adding a new feature that crosses architectural boundaries
- After modifying a method signature, return type, or data model

---

## Validation Protocol

Execute every step below in order. Do not skip steps. Do not declare completion until all steps pass.

### Step 1: Architecture Impact Analysis

Map all components affected by the change.

- Identify the primary change (the file or function that was the direct target).
- Trace every component that imports, extends, implements, or calls the changed component.
- Build a mental dependency graph: top-level entry points → services → repositories → DTOs → database models.
- Note every node in this graph that is touched by the change.

Ask yourself: *Have I touched every node that needs to change, or only the ones I noticed first?*

### Step 2: Interface Contract Review

For every changed method, function, class, or type:

- Verify the signature (name, parameters, return type) is consistent across all call sites.
- Verify every interface that declares this method has been updated.
- Verify every class that implements this interface has been updated.
- Verify every mock, stub, or test double that mimics this signature has been updated.

Ask yourself: *Is there any caller or implementer I have not yet updated?*

### Step 3: DTO and Data Model Consistency

For every changed data structure (DTO, model, schema, type, struct):

- Verify all serialization and deserialization logic matches the new shape.
- Verify all mappers and transformers are updated.
- Verify all database migrations or schema changes are reflected.
- Verify all API response and request shapes align with frontend or consumer expectations.

Ask yourself: *Does every layer that touches this data agree on its shape?*

### Step 4: Dependency and Import Audit

For every file modified:

- Verify all imports and dependencies are present and correctly referenced.
- Verify no import refers to a path or symbol that no longer exists.
- Verify no circular dependencies were introduced.
- Verify build configuration files (package.json, pom.xml, build.gradle, Cargo.toml, etc.) are updated if new dependencies were added.

Ask yourself: *Will every file compile cleanly in isolation?*

### Step 5: Test Coverage Validation

For every changed behavior:

- Identify existing tests that cover the changed code paths.
- Verify those tests still reflect the current behavior, not the old behavior.
- Identify test helpers, fixtures, and factories that reference changed types and verify they are updated.
- If new behavior was added, confirm whether new tests are needed.

Ask yourself: *Will the test suite pass, or will it fail on stale assertions or type mismatches?*

### Step 6: End-to-End Flow Trace

Trace one full request or operation through the system from entry point to output:

- Start at the API endpoint, CLI command, UI event, or message consumer.
- Walk through every layer: controller → service → repository → data store.
- Confirm that data flows correctly at each boundary without type mismatches, missing fields, or broken assumptions.

Ask yourself: *If I traced a real request through this system right now, where would it break?*

### Step 7: Completeness Self-Check

Before declaring done, explicitly answer:

1. Are there any `TODO`, `FIXME`, or placeholder implementations left behind?
2. Are there any `throw new NotImplementedException()` or equivalent stubs?
3. Are there any methods referenced but not yet implemented?
4. Are there any configuration values, environment variables, or secrets required that are not documented?
5. Is there anything I planned to do but did not finish?

If the answer to any of these is yes, complete the work before declaring done.

---

## Failure Modes This Skill Prevents

| Failure Mode | How This Skill Catches It |
|---|---|
| Fix one file, break another | Step 1 (Architecture Impact Analysis) |
| Interface updated, implementation not updated | Step 2 (Interface Contract Review) |
| DTO field added, mapper not updated | Step 3 (DTO and Data Model Consistency) |
| Import removed, still referenced elsewhere | Step 4 (Dependency and Import Audit) |
| Behavior changed, test still asserts old behavior | Step 5 (Test Coverage Validation) |
| Works in isolation, breaks when integrated | Step 6 (End-to-End Flow Trace) |
| Claimed done, unimplemented methods remain | Step 7 (Completeness Self-Check) |

---

## Output Format

After completing the protocol, produce a brief validation summary:

```
## Validation Summary

Architecture Impact: [components reviewed]
Interface Contracts: [pass / issues found and resolved]
DTO Consistency: [pass / issues found and resolved]
Imports and Dependencies: [pass / issues found and resolved]
Test Coverage: [pass / issues found and resolved]
End-to-End Trace: [pass / issues found and resolved]
Completeness: [pass / items resolved]

Status: READY / BLOCKED
```

If status is BLOCKED, list the remaining issues before proceeding.

---

## Guiding Principle

Local correctness is not global correctness. A file that compiles is not a system that works. This skill shifts the process from reactive debugging to proactive engineering — catching the entire failure graph before it manifests as a sequence of compile errors.
