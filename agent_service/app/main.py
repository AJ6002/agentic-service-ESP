import os
import time
from uuid import uuid4
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from app.audit.audit_sink import record_audit
from app.contracts.api import QueryRequest, DecisionRequest
from app.contracts.context import ContextFrame, SessionSnapshot
from app.contracts.events import StatusFrame, DoneFrame, ErrorFrame
from app.contracts.hitl import RunState
from app.contracts.routing import RouterInput
from app.context.resolver import resolve_context
from app.context.well_ids import normalize_well_id
from app.hitl.interrupts import raise_clarify, register_resume_handler, resume
from app.observability.stage_log import log_stage
from app.routing.capability_retrieval import retrieve_candidates
from app.routing.router import route_query_full
from app.synthesis.direct_handler import handle_direct_query
from app.synthesis.response_assembler import ResponseAssembler
from app.stores.run_store import get_run, save_run
from app.stores.session_store import delete_pending, get_pending, get_session, save_session
from app.workflow.runner import run_workflow

load_dotenv()

app = FastAPI(title="ESP APM Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Resume handlers — real continuations, not placeholder LLM prompts.
#
# `run.objective_id` / `run.args` are populated by raise_clarify() at pause
# time, so resuming here has everything needed to actually run the
# diagnosis, not just a bound string with no context.
# ---------------------------------------------------------------------------

async def continue_after_context(run: RunState, bound_val: str):
    """Resume from a CONTEXT-phase pause (e.g. empty/unroutable message)."""
    answer = await handle_direct_query(bound_val)
    return answer


async def continue_after_router(run: RunState, bound_val: str):
    """
    Resume from a ROUTER/PLAN_BUILD-phase pause — the common case: the
    Router already picked an objective (e.g. OP03_FAULT_DIAGNOSIS) but was
    missing a required arg (e.g. asset_id). `bound_val` is the value the
    user just supplied for that slot; patch it into the run's args and
    actually execute the workflow (Plan Builder -> Policy Gate -> Tool
    Gateway), not a generic LLM explanation.
    """
    if not run.objective_id:
        # No objective was ever bound (e.g. a CONTEXT-only pause routed
        # here by mistake) — fall back to a direct answer rather than
        # crashing the resume.
        answer = await handle_direct_query(bound_val)
        return answer

    norm_asset = normalize_well_id(bound_val) if isinstance(bound_val, str) else None
    if norm_asset:
        args = {**run.args, "asset_id": norm_asset}
    elif isinstance(bound_val, str) and (
        bound_val.strip().lower().startswith("proceed") or "partial" in bound_val.lower()
    ):
        args = {**run.args, "allow_partial": True}
    else:
        args = {**run.args}

    run.args = args
    save_run(run)

    _t0 = time.perf_counter()
    result = await run_workflow(
        run_id=run.run_id,
        session_id=run.session_id,
        objective_id=run.objective_id,
        args=args,
        confidence=run.confidence or 0.9,
    )
    log_stage(
        "workflow_runner",
        (time.perf_counter() - _t0) * 1000,
        "OK" if result.ok else "ERROR",
        run_id=run.run_id,
        session_id=run.session_id,
        objective_id=run.objective_id,
        via="resume",
    )
    return result


register_resume_handler("CONTEXT", continue_after_context)
register_resume_handler("ROUTER", continue_after_router)
register_resume_handler("PLAN_BUILD", continue_after_router)


async def _timed_stream(stream, run_id: str, route: str):
    """
    Wraps ResponseAssembler's frame generator so the stage log covers the
    WHOLE stream (first frame to last), not just the setup call — the
    assembler is an async generator, so timing only the constructor call
    would measure ~0ms regardless of how long streaming actually took.
    Outcome is read off each frame's `type`/`status` field as it passes
    through (parsed, not string-matched, since these are the real NDJSON
    lines going to the frontend).
    """
    import json as _json

    _t0 = time.perf_counter()
    outcome = "OK"
    async for line in stream:
        try:
            parsed = _json.loads(line)
            if parsed.get("type") == "error":
                outcome = "ERROR"
            elif parsed.get("type") == "done" and parsed.get("status"):
                outcome = parsed["status"]
        except (ValueError, AttributeError):
            pass
        yield line
    log_stage(
        "response_assembler",
        (time.perf_counter() - _t0) * 1000,
        outcome,
        run_id=run_id,
        route=route,
    )


def _persist_session_turn(
    session_id: str,
    frame: ContextFrame,
    objective_id: str | None = None,
    asset_id: str | None = None,
    analysis_id: str | None = None,
) -> None:
    """
    Writes session state back to Redis after a turn completes.

    This is the missing write-side of the Context Resolver contract: the
    resolver's read path (resolve_context -> get_session) had a full
    producer/consumer contract from day one, but nothing ever carried the
    turn's outcome back into session state — so pronoun/session-asset
    resolution ("why did it trip?" on a later turn) could never actually
    fire through the real endpoint, even though it was implemented and
    unit-tested in isolation.

    Called once per response, right before the stream is returned, from
    every branch of handle_query — new query, BIND resume, SUPERSEDE, and
    META all count as a turn.
    """
    session = get_session(session_id) or SessionSnapshot()
    updated = session.model_copy(
        update={
            "turn_count": session.turn_count + 1,
            "last_asset_id": asset_id or session.last_asset_id,
            "last_objective": objective_id or session.last_objective,
            "last_analysis_id": analysis_id or session.last_analysis_id,
        }
    )
    save_session(session_id, updated)


@app.get("/health")
async def health_check():
    return {"status": "HEALTHY", "service": "agent_service", "slice": 2}


@app.post("/query")
async def handle_query(req: QueryRequest):
    session_id = req.session_id.strip() if req.session_id else f"S-{uuid4().hex[:8]}"
    raw_msg = req.message

    record_audit("query_received", session_id=session_id, payload={"message": raw_msg})

    # 1. Context Resolution
    _t0 = time.perf_counter()
    frame = resolve_context(session_id, raw_msg, req.ui_context)
    log_stage(
        "context_resolver",
        (time.perf_counter() - _t0) * 1000,
        "CLARIFY" if frame.needs_clarify else frame.resolution,
        session_id=session_id,
        asset_source=frame.asset.source,
    )
    record_audit(
        "context_resolved",
        session_id=session_id,
        payload={
            "resolution": frame.resolution,
            "asset_id": frame.asset.id,
            "asset_source": frame.asset.source,
            "match_method": frame.asset.match_method,
            "needs_clarify": frame.needs_clarify,
        },
    )

    # 2. Check BIND Resolution (Resume paused run into a REAL continuation)
    if frame.resolution == "BIND":
        pending = get_pending(session_id)
        if pending:
            run_id = pending.run_id
            bound_val = frame.asset.id or raw_msg
            resume_outcome = await resume(run_id, bound_val)
            delete_pending(session_id)

            run = get_run(run_id)
            if run:
                run.status = "DONE"
                save_run(run)

            record_audit("run_resumed", run_id=run_id, session_id=session_id, payload={"bound_value": bound_val})
            record_audit("query_completed", run_id=run_id, session_id=session_id, payload={"route": "RESUME"})
            resumed_asset_id = (
                frame.asset.id
                or (normalize_well_id(bound_val) if isinstance(bound_val, str) else None)
                or (run.args.get("asset_id") if run and run.args else None)
            )
            _persist_session_turn(
                session_id,
                frame,
                objective_id=run.objective_id if run else None,
                asset_id=resumed_asset_id,
                analysis_id=run_id,
            )

            if hasattr(resume_outcome, "text"):
                resume_text = resume_outcome.text
                adv = getattr(resume_outcome, "advisory", None)
                viz = getattr(resume_outcome, "visualization", None)
                insufficient = getattr(resume_outcome, "insufficient_evidence", False)
                wf_ok = getattr(resume_outcome, "ok", True)
            else:
                resume_text = str(resume_outcome)
                adv = None
                viz = None
                insufficient = False
                wf_ok = True

            if insufficient:
                err = ErrorFrame(
                    run_id=run_id,
                    code="INSUFFICIENT_EVIDENCE",
                    message=resume_text,
                )
                stream = ResponseAssembler.assemble_stream(
                    run_id=run_id,
                    route="WORKFLOW",
                    error=err,
                    done_status="INSUFFICIENT",
                )
                return StreamingResponse(
                    _timed_stream(stream, run_id, "WORKFLOW"), media_type="application/x-ndjson"
                )
            elif not wf_ok:
                err = ErrorFrame(
                    run_id=run_id,
                    code="WORKFLOW_FAILED",
                    message=resume_text,
                )
                stream = ResponseAssembler.assemble_stream(
                    run_id=run_id,
                    route="WORKFLOW",
                    error=err,
                    done_status="FAILED",
                )
                return StreamingResponse(
                    _timed_stream(stream, run_id, "WORKFLOW"), media_type="application/x-ndjson"
                )

            stream = ResponseAssembler.assemble_stream(
                run_id=run_id,
                route="WORKFLOW",
                text=resume_text,
                advisory=adv,
                visualization=viz,
            )
            return StreamingResponse(
                _timed_stream(stream, run_id, "WORKFLOW"), media_type="application/x-ndjson"
            )

    # 3. Check SUPERSEDE Resolution — the pending clarification is closed
    # as abandoned (not resumed, not answered) because the user asked
    # something unrelated instead. The old run's own state must reflect
    # that too, not just sit as "PAUSED" in Redis until its TTL expires —
    # otherwise an audit lookup on that run would misleadingly suggest it
    # is still waiting to be resumed.
    if frame.resolution == "SUPERSEDE":
        superseded_pending = get_pending(session_id)
        delete_pending(session_id)
        if superseded_pending:
            abandoned_run = get_run(superseded_pending.run_id)
            if abandoned_run:
                abandoned_run.status = "ABANDONED"
                abandoned_run.resume_at = None
                save_run(abandoned_run)
        record_audit(
            "pending_superseded",
            run_id=superseded_pending.run_id if superseded_pending else None,
            session_id=session_id,
        )

    # 4. Check META Resolution
    if frame.resolution == "META":
        meta_answer = await handle_direct_query(raw_msg)
        run_id = f"R-{uuid4().hex[:8]}"
        record_audit("meta_query_answered", run_id=run_id, session_id=session_id)
        # META answers a question ABOUT the pending clarification without
        # resolving it — session turn count still advances, but asset/
        # objective memory is untouched (nothing new was bound).
        _persist_session_turn(session_id, frame)
        stream = ResponseAssembler.assemble_stream(
            run_id=run_id,
            route="SIMPLE",
            text=meta_answer.text,
            llm_available=meta_answer.llm_available,
        )
        return StreamingResponse(
            _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
        )

    # 5. NEW Query Execution Flow
    run_id = f"R-{uuid4().hex[:8]}"
    initial_run = RunState(
        run_id=run_id,
        session_id=session_id,
        status="RUNNING",
    )
    save_run(initial_run)

    # 5.1 Early Context Clarify Guard (e.g. empty or unroutable input)
    if frame.needs_clarify:
        clarify_frame = raise_clarify(
            run_id=run_id,
            session_id=session_id,
            reason="CLARIFY",
            slot=None,
            options=["Check well status", "Why did it trip?", "Glossary inquiry"],
            resume_at="CONTEXT",
            custom_question="Please provide an operational question or select an asset to inspect.",
        )
        record_audit("clarification_raised", run_id=run_id, session_id=session_id, payload={"reason": "EMPTY_MESSAGE"})
        _persist_session_turn(session_id, frame)
        stream = ResponseAssembler.assemble_stream(
            run_id=run_id,
            route="SIMPLE",
            clarification=clarify_frame,
        )
        return StreamingResponse(
            _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
        )

    # Capability Retrieval
    cand_obj, cand_tools, cand_list = retrieve_candidates(raw_msg)

    # Router Input (filtered copy without internal flags)
    r_in = RouterInput(
        raw_message=raw_msg,
        asset_id=frame.asset.id,
        asset_source=frame.asset.source,
        turn_count=frame.session_snapshot.turn_count + 1,
        candidate_objectives=cand_obj,
        candidate_tools=cand_tools,
    )

    _t0 = time.perf_counter()
    route_result = await route_query_full(r_in)
    decision = route_result.decision
    log_stage(
        "router",
        (time.perf_counter() - _t0) * 1000,
        "FALLBACK" if route_result.fallback_used else ("CLARIFY" if decision.clarification_needed else decision.route),
        run_id=run_id,
        session_id=session_id,
        llm_available=route_result.llm_available,
    )

    # Inject the resolved time window into the plan args. The Context
    # Resolver parses phrases like "last 30 mins" deterministically (no
    # LLM); this carries that window through to the Tool Gateway's
    # time-scoped calls (get_events, get_historian_window) as ISO-8601
    # start/end. Only set when the message actually specified a window —
    # otherwise the gateway applies its own now-relative default. Explicit
    # start/end already present in args (e.g. from a resumed run) are not
    # overwritten.
    if frame.time and frame.time.window_start and frame.time.window_end:
        if isinstance(decision.args, dict):
            decision.args.setdefault(
                "start", frame.time.window_start.isoformat().replace("+00:00", "Z")
            )
            decision.args.setdefault(
                "end", frame.time.window_end.isoformat().replace("+00:00", "Z")
            )
    if frame.query_params and isinstance(decision.args, dict):
        for _k, _v in frame.query_params.items():
            if _v is not None:
                decision.args.setdefault(_k, _v)

    if not route_result.llm_available:
        record_audit("query_llm_down", run_id=run_id, session_id=session_id, payload={"stage": "router"})

    # If Router flags clarification needed (e.g. missing asset_id for fault diagnosis)
    if decision.clarification_needed:
        clarify_frame = raise_clarify(
            run_id=run_id,
            session_id=session_id,
            reason=decision.clarify_reason or "CLARIFY",
            slot=decision.clarify_slot,
            options=decision.clarify_options,
            resume_at="PLAN_BUILD",
            objective_id=decision.objective_id,
            args=decision.args,
        )
        record_audit(
            "clarification_raised",
            run_id=run_id,
            session_id=session_id,
            payload={"slot": decision.clarify_slot, "options": decision.clarify_options},
        )
        # Persist the router's confidence too, so a later resume can reuse it.
        run = get_run(run_id)
        if run:
            run.confidence = decision.confidence
            save_run(run)
        # A CLARIFY here still bound an objective (e.g. OP03) even though
        # the asset itself is still missing — remember the objective, but
        # not an asset that was never actually resolved.
        _persist_session_turn(session_id, frame, objective_id=decision.objective_id)
        stream = ResponseAssembler.assemble_stream(
            run_id=run_id,
            route=decision.route,
            clarification=clarify_frame,
            llm_available=route_result.llm_available,
        )
        return StreamingResponse(
            _timed_stream(stream, run_id, decision.route), media_type="application/x-ndjson"
        )

    # If route is SIMPLE
    if decision.route == "SIMPLE":
        if decision.objective_id in ("OP06", "OP06_KNOWLEDGE_LOOKUP"):
            # Procedural / approved KB lookup workflow
            _t0 = time.perf_counter()
            kb_args = dict(decision.args) if isinstance(decision.args, dict) else {}
            if "query" not in kb_args or not kb_args["query"]:
                kb_args["query"] = raw_msg

            workflow_result = await run_workflow(
                run_id=run_id,
                session_id=session_id,
                objective_id="OP06_KNOWLEDGE_LOOKUP",
                args=kb_args,
                confidence=decision.confidence,
            )
            log_stage(
                "workflow_runner",
                (time.perf_counter() - _t0) * 1000,
                "OK" if workflow_result.ok else "ERROR",
                run_id=run_id,
                session_id=session_id,
                objective_id="OP06_KNOWLEDGE_LOOKUP",
                via="simple_kb",
            )
            run = get_run(run_id)
            if run:
                if workflow_result.insufficient_evidence:
                    run.status = "INSUFFICIENT"
                elif workflow_result.ok:
                    run.status = "DONE"
                else:
                    run.status = "FAILED"
                run.objective_id = "OP06_KNOWLEDGE_LOOKUP"
                run.args = kb_args
                save_run(run)
            record_audit(
                "query_completed",
                run_id=run_id,
                session_id=session_id,
                payload={"route": "SIMPLE", "objective_id": "OP06_KNOWLEDGE_LOOKUP", "ok": workflow_result.ok, "status": run.status if run else "UNKNOWN"},
            )
            _persist_session_turn(session_id, frame, objective_id="OP06_KNOWLEDGE_LOOKUP", asset_id=None, analysis_id=run_id if workflow_result.ok else None)

            if workflow_result.insufficient_evidence:
                err = ErrorFrame(
                    run_id=run_id,
                    code="INSUFFICIENT_EVIDENCE",
                    message=workflow_result.text or "No approved knowledge base coverage found.",
                )
                stream = ResponseAssembler.assemble_stream(
                    run_id=run_id,
                    route="SIMPLE",
                    error=err,
                    done_status="INSUFFICIENT",
                    llm_available=route_result.llm_available,
                )
                return StreamingResponse(
                    _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
                )

            if not workflow_result.ok:
                err = ErrorFrame(
                    run_id=run_id,
                    code="WORKFLOW_FAILED",
                    message=workflow_result.text,
                )
                stream = ResponseAssembler.assemble_stream(
                    run_id=run_id,
                    route="SIMPLE",
                    error=err,
                    done_status="FAILED",
                    llm_available=route_result.llm_available,
                )
                return StreamingResponse(
                    _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
                )

            stream = ResponseAssembler.assemble_stream(
                run_id=run_id,
                route="SIMPLE",
                text=workflow_result.text,
                advisory=workflow_result.advisory,
                visualization=workflow_result.visualization,
                llm_available=route_result.llm_available,
            )
            return StreamingResponse(
                _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
            )

        answer = await handle_direct_query(raw_msg)
        run = get_run(run_id)
        if run:
            run.status = "DONE"
            save_run(run)
        record_audit("query_completed", run_id=run_id, session_id=session_id, payload={"route": "SIMPLE"})
        # SIMPLE/glossary answers don't touch an asset or objective — only
        # the turn count advances, so a later pronoun still resolves
        # against whatever asset was last touched by a WORKFLOW turn.
        _persist_session_turn(session_id, frame)
        stream = ResponseAssembler.assemble_stream(
            run_id=run_id,
            route="SIMPLE",
            text=answer.text,
            llm_available=route_result.llm_available and answer.llm_available,
        )
        return StreamingResponse(
            _timed_stream(stream, run_id, "SIMPLE"), media_type="application/x-ndjson"
        )

    # Workflow route — actually run it (Plan Builder -> Policy Gate -> Tool Gateway).
    _t0 = time.perf_counter()
    workflow_result = await run_workflow(
        run_id=run_id,
        session_id=session_id,
        objective_id=decision.objective_id,
        args=decision.args,
        confidence=decision.confidence,
    )
    log_stage(
        "workflow_runner",
        (time.perf_counter() - _t0) * 1000,
        "OK" if workflow_result.ok else "ERROR",
        run_id=run_id,
        session_id=session_id,
        objective_id=decision.objective_id,
        via="new_query",
    )
    run = get_run(run_id)
    if run:
        if workflow_result.insufficient_evidence:
            run.status = "INSUFFICIENT"
        elif workflow_result.ok:
            run.status = "DONE"
        else:
            run.status = "FAILED"
        run.objective_id = decision.objective_id
        run.args = decision.args
        save_run(run)
    record_audit(
        "query_completed",
        run_id=run_id,
        session_id=session_id,
        payload={"route": "WORKFLOW", "ok": workflow_result.ok, "status": run.status if run else "UNKNOWN"},
    )
    # This is the write-side that makes a later pronoun turn ("why did it
    # trip again?") resolve against THIS run's asset via session memory.
    raw_aid = decision.args.get("asset_id") if isinstance(decision.args, dict) else None
    persisted_asset_id = frame.asset.id or (normalize_well_id(raw_aid) if raw_aid else None) or raw_aid
    _persist_session_turn(
        session_id,
        frame,
        objective_id=decision.objective_id,
        asset_id=persisted_asset_id,
        analysis_id=run_id if workflow_result.ok else None,
    )
    # If evidence is insufficient:
    if workflow_result.insufficient_evidence:
        if getattr(req, "clarify_on_insufficient", False):
            missing_str = ", ".join(workflow_result.missing_required)
            clarify_frame = raise_clarify(
                run_id=run_id,
                session_id=session_id,
                reason="INSUFFICIENT",
                slot="missing_evidence",
                options=["Proceed with partial evidence", "Retry data acquisition", "Select another well"],
                resume_at="PLAN_BUILD",
                objective_id=decision.objective_id,
                args=decision.args,
                custom_question=f"Diagnostic run for {persisted_asset_id or 'the well'} could not be completed: required evidence missing ({missing_str}). How would you like to proceed?",
            )
            record_audit(
                "clarification_raised",
                run_id=run_id,
                session_id=session_id,
                payload={"reason": "INSUFFICIENT", "missing_required": workflow_result.missing_required},
            )
            run = get_run(run_id)
            if run:
                run.status = "PAUSED"
                run.objective_id = decision.objective_id
                run.args = decision.args
                save_run(run)
            stream = ResponseAssembler.assemble_stream(
                run_id=run_id,
                route=decision.route,
                clarification=clarify_frame,
                llm_available=route_result.llm_available,
            )
            return StreamingResponse(
                _timed_stream(stream, run_id, decision.route), media_type="application/x-ndjson"
            )
        else:
            # Bug C & Bug E: Emit ErrorFrame and DoneFrame(status="INSUFFICIENT"), omit Visual and TextDelta
            err = ErrorFrame(
                run_id=run_id,
                code="INSUFFICIENT_EVIDENCE",
                message=workflow_result.text,
            )
            stream = ResponseAssembler.assemble_stream(
                run_id=run_id,
                route=decision.route,
                error=err,
                done_status="INSUFFICIENT",
                llm_available=route_result.llm_available,
            )
            return StreamingResponse(
                _timed_stream(stream, run_id, decision.route), media_type="application/x-ndjson"
            )

    if not workflow_result.ok:
        err = ErrorFrame(
            run_id=run_id,
            code="WORKFLOW_FAILED",
            message=workflow_result.text,
        )
        stream = ResponseAssembler.assemble_stream(
            run_id=run_id,
            route=decision.route,
            error=err,
            done_status="FAILED",
            llm_available=route_result.llm_available,
        )
        return StreamingResponse(
            _timed_stream(stream, run_id, decision.route), media_type="application/x-ndjson"
        )

    stream = ResponseAssembler.assemble_stream(
        run_id=run_id,
        route=decision.route,
        text=workflow_result.text,
        advisory=workflow_result.advisory,
        visualization=workflow_result.visualization,
        llm_available=route_result.llm_available,
    )
    return StreamingResponse(
        _timed_stream(stream, run_id, decision.route), media_type="application/x-ndjson"
    )
