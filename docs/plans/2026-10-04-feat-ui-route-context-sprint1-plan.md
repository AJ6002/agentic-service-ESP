---
title: "feat: Carry ui_context.selected_route through the agent (Sprint 1 — plumbing only)"
type: feat
status: draft
date: 2026-10-04
repo: agent_service
branch_base: feat/identity-route
---

# Sprint 1 — Contracts: accept and carry `ui_context.selected_route`

## Summary

The dashboard already sends `ui_context.selected_route`. Sprint 1 makes the agent
**accept it, carry it on the ContextFrame, and prove nothing breaks**. It does not
use the value for routing, does not add `ui_map`, does not add OP15.

## Research Findings (current code, verified by reading)

| Surface | File | Finding |
|---|---|---|
| Request model | `agent_service/app/contracts/api.py` | `QueryRequest` is `extra="allow"`; `ui_context: Optional[Union[UIContext, dict[str, Any]]]`. `UIContext` is a typed model but **`extra="allow"`**, with no `selected_route` field. |
| Frame model | `agent_service/app/contracts/context.py` | `ContextFrame.ui_context: dict[str, Any]` (free-form) and `page_route: str \| None`. No `selected_route` field. |
| Resolver | `agent_service/app/context/resolver.py` (`resolve_context`, ~L440-534) | dict input: whole dict kept in `ui_ctx_dict` and stored as `frame.ui_context`. `UIContext` input: `model_dump(exclude_none=True)` — extras are included. Fallback `except` branch builds `UIContext` from a fixed key list (drops extras) but the raw dict is still preserved in `ui_ctx_dict`. |
| Call site | `agent_service/app/main.py` L204-212 | Passes `req.ui_context` and `req.page_route` straight to `resolve_context`. |
| Redis | session store | `selected_route` is per-query; nothing in the persistence path (`_persist_session_turn`) reads `ui_context`. |

**Conclusion:** `selected_route` very likely already passes through today with no 422
(extras allowed at both levels) and lands in `frame.ui_context["selected_route"]`.
The work is mostly **make it explicit + prove it**, not rewrite.

## Open Decisions (need your call before work starts)

1. **Explicit field vs. rely on extras.** Task 1.1 says add `selected_route` to
   `UIContext` only if typed. It *is* typed, so the plan adds
   `selected_route: Optional[str] = None` to `UIContext` — makes the contract
   self-documenting and lets `ui_ctx_obj.selected_route` be used in later sprints.
   *Recommended: add it.*
2. **`page_route` overlap.** `QueryRequest.page_route` / `ContextFrame.page_route`
   already exist (used by the dashboard contract-sync script, e.g. `/wells/$wellId`).
   `selected_route` is a second, similar concept inside `ui_context`. Plan: **keep
   both, do not merge or reinterpret** in Sprint 1; note the overlap for Sprint 4.
   *Recommended: keep both.*
3. **Frame field.** Add top-level `ContextFrame.selected_route: str | None = None`
   (populated by resolver) vs. only reading `frame.ui_context.get("selected_route")`.
   Task 1.2 asks for the explicit field. *Recommended: add the field.*

## Implementation Units

### U1 — `UIContext` accepts `selected_route`
- **File:** `agent_service/app/contracts/api.py`
- **Change:** add `selected_route: Optional[str] = None` to `UIContext`.
- **Test:** `QueryRequest.model_validate` with `ui_context={"selected_route": "/working-status"}` yields `ui_context.selected_route == "/working-status"`; payload without it still validates.

### U2 — `ContextFrame` carries `selected_route`
- **File:** `agent_service/app/contracts/context.py`
- **Change:** add `selected_route: str | None = None` (ephemeral, default None).

### U3 — Resolver populates it
- **File:** `agent_service/app/context/resolver.py` (`resolve_context`)
- **Change:** after normalizing `ui_context`, set
  `selected_route = ui_ctx_obj.selected_route if ui_ctx_obj else ui_ctx_dict.get("selected_route")`
  and pass it into `ContextFrame(...)`. Also add `selected_route=ui_context.get("selected_route")` to the fallback `except` construction so it is never lost.
- **Not stored in Redis:** no changes to `_persist_session_turn` or stores.
- **Visibility for exit criterion 2:** one `log_stage`/debug field on the existing `context_resolver` log line (or a unit test asserting on the returned frame). Pick the test — it is deterministic; the log is optional.

### U4 — Tests (new file)
- **File:** `agent_service/tests/test_ui_route_context.py`
- Cases:
  1. `resolve_context(..., ui_context={"selected_route": "/working-status"})` → `frame.selected_route == "/working-status"` and `frame.ui_context["selected_route"]` preserved.
  2. Same with a `UIContext` object input.
  3. Absent `ui_context` / absent key → `frame.selected_route is None`.
  4. Malformed `ui_context` (triggers the fallback branch) still carries the route.
  5. HTTP-level (ASGI client, like existing `test_identity_route.py`): POST with `ui_context.selected_route` → 200, not 422.

## Verification (Exit Criteria)

| # | Check | How | Pass |
|---|---|---|---|
| 1 | Request accepts `ui_context.selected_route` | `curl` `{"session_id":"t1","message":"test","ui_context":{"selected_route":"/working-status"}}` + U4 case 5 | HTTP 200, no 422 |
| 2 | Frame carries it | U4 cases 1-4 | assertions pass |
| 3 | Three queries return normally | curls t2 (identity), t3 (KB), t4 (WORKFLOW, `/wells/FS-17`) | all stream `done`; identity = `text_delta`+`done` only; KB = OP06 advisory; workflow = normal frames |
| 4 | No regression | `pytest agent_service/tests/test_identity_route.py agent_service/tests/test_router_definitional_regression.py agent_service/tests/test_ui_route_context.py -q` plus context-resolver tests (`pytest agent_service/tests -k "context" -q`) | green |

Notes:
- Skip the 400+ suite; known pre-existing failures (~59, legacy HTTP-mock adapter tests after the Postgres migration) are unrelated and must not be counted against this sprint.
- Identity isolation check re-run: after t2, no new `esp:run:*` key in Redis.
- `ui_context` is used in curl bodies with Windows quoting pitfalls — run the curls through a small Python script (as in `agent_service/scripts/short_verify.py`).

## Risks

- **Low.** Additive optional fields only. Only real risk: `Union[UIContext, dict]` smart-mode coercion changing which branch is taken — covered by U4 cases 1, 2, 4.
- `selected_route` must not influence routing, policy, or identity short-circuit in this sprint — confirmed by U4 + the 3-curl check.

## Out of Scope (explicit)

- Using `selected_route` in routing/answers (Sprints 4–7)
- `ui_map`, OP15
- Any change to `page_route` semantics
- Dashboard repo changes (Sprint 2+)

## Hand-off

Branch from `feat/identity-route` (or main once merged) → e.g. `feat/ui-route-context`.
Execute with `/ce-work` against this doc after the three open decisions are confirmed.
