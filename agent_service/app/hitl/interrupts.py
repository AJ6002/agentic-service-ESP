import inspect
from datetime import datetime
from typing import Callable, Optional
from app.contracts.enums import InterruptType, ResumeAt
from app.contracts.events import ClarificationFrame
from app.contracts.hitl import PendingInterrupt, RunState
from app.stores.run_store import get_run, save_run
from app.stores.session_store import save_pending

class HardError(Exception):
    pass

def generate_clarification_question(reason: InterruptType, slot: Optional[str]) -> str:
    if slot == "asset_id":
        return "Which well would you like me to analyze?"
    if slot == "trip_ts":
        return "Multiple trips detected. Which timestamp should I inspect?"
    return "Could you please clarify your request?"

def raise_clarify(
    run_id: str,
    session_id: str,
    reason: InterruptType,
    slot: Optional[str],
    options: list[str],
    resume_at: ResumeAt,
    custom_question: Optional[str] = None,
    objective_id: Optional[str] = None,
    args: Optional[dict] = None,
) -> ClarificationFrame:
    pending = PendingInterrupt(
        run_id=run_id,
        reason=reason,
        resume_at=resume_at,
        slot=slot,
        options=options,
        raised_at=datetime.utcnow(),
    )
    save_pending(session_id, pending)

    run = get_run(run_id)
    if not run:
        run = RunState(run_id=run_id, session_id=session_id)
    run.status = "PAUSED"
    run.resume_at = resume_at
    # Persist what the resumed run needs to actually continue the workflow —
    # this is what makes resume() a real continuation instead of a fresh,
    # context-free question to the LLM.
    if objective_id is not None:
        run.objective_id = objective_id
    if args is not None:
        run.args = {**run.args, **args}
    save_run(run)

    question = custom_question or generate_clarification_question(reason, slot)
    return ClarificationFrame(
        run_id=run_id,
        question=question,
        options=options,
        slot=slot,
        pending_ref=f"esp:session:{session_id}:pending",
    )

# Resume Handlers Registry (Lookup table, never an if/elif chain)
RESUME_TABLE: dict[str, Callable[[RunState, any], any]] = {}

def register_resume_handler(phase: ResumeAt, handler: Callable[[RunState, any], any]):
    RESUME_TABLE[phase] = handler

async def resume(run_id: str, bound_value: any) -> any:
    run = get_run(run_id)
    if not run:
        raise HardError(f"Cannot resume run {run_id}: not found in run store")

    phase = run.resume_at
    if not phase:
        raise HardError(f"Cannot resume run {run_id}: resume_at phase is null")

    handler = RESUME_TABLE.get(phase)
    if not handler:
        raise HardError(f"No resume handler registered for phase {phase}")

    # Mark running and clear resume_at
    run.status = "RUNNING"
    run.resume_at = None
    save_run(run)

    result = handler(run, bound_value)
    if inspect.isawaitable(result):
        result = await result
    return result
