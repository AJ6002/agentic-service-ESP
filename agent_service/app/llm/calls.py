"""
One typed function per LLM call type used by agent_service.

This is the layer that was missing between app/llm/client.py (raw HTTP to
llama-server) and the callers (router.py, direct_handler.py, and in
Slice 2: xai.py, gapfill.py). Before this module existed, each caller
held its own prompt text, its own JSON-parsing/strip-markdown-fence
logic, and its own idea of what "malformed output" meant — exactly the
duplication that was flagged before Slice 2 adds narrate() and gapfill()
on top of the same pattern.

Rules for every function here:
  - loads its prompt from app/llm/prompts/*.txt, never an inline string
  - validates the LLM's JSON against the call's Pydantic schema
  - retries ONCE with a stricter prompt on malformed JSON, per
    IMPLEMENTATION_SEQUENCE.md Stage 5 ("retry once with a stricter
    system prompt, then fall back") — this retry was specified but never
    actually implemented before this module
  - raises LLMUnavailableError (unchanged, from client.py) on a real
    outage; raises RouterOutputInvalid (new, distinct) if the LLM
    responded but never produced valid JSON even after the retry —
    callers decide their own fallback for each of those two, separately
  - never returns a partially-validated or best-guess object silently
"""

import json
from typing import Optional

from app.contracts.routing import RouteDecision
from app.llm.client import LLMUnavailableError
import app.llm.client as _client

async def call_llm_chat(*args, **kwargs):
    return await _client.call_llm_chat(*args, **kwargs)

from app.llm.prompt_loader import load_prompt


class RouterOutputInvalid(Exception):
    """
    LLM responded (no outage), but its output never became valid JSON
    matching RouteDecision, even after one stricter retry. Distinct from
    LLMUnavailableError — this is a router/prompt defect, not a downed
    gateway, and callers should treat/log/fallback for it differently.
    """


def _strip_markdown_fence(content: str) -> str:
    content = content.strip()
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


async def route(raw_message: str, context_block: str) -> RouteDecision:
    """
    LLM #1 — Query Router. `context_block` is the pre-formatted string of
    resolved asset/candidates/etc. that goes under the raw message in the
    user turn (built by the caller from RouterInput, kept out of this
    module so this module owns prompting/parsing only, not context shape).

    Raises LLMUnavailableError if the gateway itself is down (caller's
    job to fall back to the keyword heuristic).
    Raises RouterOutputInvalid if the LLM answered but never produced
    valid JSON, even after one stricter retry (caller's job to decide —
    currently also falls back to the keyword heuristic, but logged and
    counted separately from an outage).
    """
    system_prompt = load_prompt("router_v2.txt")
    user_content = f"User message: {raw_message}\n{context_block}"

    content = await call_llm_chat(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.0,
        caller="router",
    )
    decision = _try_parse_route_decision(content)
    if decision is not None:
        return decision

    # First attempt wasn't valid JSON — retry once with a stricter prompt,
    # per the design spec. Still counts as "LLM available", just needed a
    # second try.
    strict_prompt = load_prompt("router_v1_strict_retry.txt")
    retry_content = await call_llm_chat(
        system_prompt=strict_prompt,
        user_content=user_content,
        temperature=0.0,
        caller="router_retry",
    )
    decision = _try_parse_route_decision(retry_content)
    if decision is not None:
        return decision

    raise RouterOutputInvalid(
        f"LLM output was not valid RouteDecision JSON after retry: {retry_content[:200]!r}"
    )


def _try_parse_route_decision(content: str) -> Optional[RouteDecision]:
    try:
        cleaned = _strip_markdown_fence(content)
        parsed = json.loads(cleaned)
        return RouteDecision.model_validate(parsed)
    except (json.JSONDecodeError, ValueError):
        return None


async def direct_answer(query: str) -> str:
    """
    LLM #2 — Direct Handler (SIMPLE route). Plain text, no schema to
    validate — the caller's job to decide what counts as an acceptable
    answer (e.g. non-empty).
    """
    system_prompt = load_prompt("direct_handler_v1.txt")
    return await call_llm_chat(
        system_prompt=system_prompt,
        user_content=query,
        temperature=0.2,
        caller="direct_handler",
    )


class AdvisoryOutputInvalid(Exception):
    """
    LLM responded (no outage), but its output never became valid JSON
    matching Advisory, even after one stricter retry.
    """


def _try_parse_advisory(content: str) -> Optional["Advisory"]:
    from app.contracts.advisory import Advisory
    try:
        cleaned = _strip_markdown_fence(content)
        parsed = json.loads(cleaned)
        return Advisory.model_validate(parsed)
    except (json.JSONDecodeError, ValueError):
        return None


async def narrate(objective_id: str, formatted_evidence_text: str, user_query: str = "") -> "Advisory":
    """
    LLM #3 — XAI Synthesizer.
    Generates an Advisory strictly based on formatted evidence.
    Raises LLMUnavailableError on gateway outage.
    Raises AdvisoryOutputInvalid on malformed JSON after strict retry.
    """
    if "OP04" in objective_id:
        system_prompt = load_prompt("narrator_health_v1.txt")
    elif "OP05" in objective_id:
        system_prompt = load_prompt("narrator_early_warning_v1.txt")
    elif "OP14" in objective_id:
        system_prompt = load_prompt("narrator_history_v1.txt")
    elif "OP02" in objective_id:
        system_prompt = load_prompt("narrator_decline_rca_v1.txt")
    elif "OP06" in objective_id:
        system_prompt = load_prompt("narrator_procedure_v1.txt")
    else:
        system_prompt = load_prompt("narrator_v1.txt")
    user_content = (
        f"Objective: {objective_id}\n"
        f"User Query: {user_query}\n\n"
        f"Verified Evidence:\n{formatted_evidence_text}"
    )

    content = await call_llm_chat(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.0,
        caller="xai_narrator",
    )
    advisory = _try_parse_advisory(content)
    if advisory is not None:
        return advisory

    strict_prompt = load_prompt("narrator_v1_strict_retry.txt")
    retry_content = await call_llm_chat(
        system_prompt=strict_prompt,
        user_content=user_content,
        temperature=0.0,
        caller="xai_narrator_retry",
    )
    advisory = _try_parse_advisory(retry_content)
    if advisory is not None:
        return advisory

    raise AdvisoryOutputInvalid(
        f"LLM output was not valid Advisory JSON after retry: {retry_content[:200]!r}"
    )



class GapFillOutputInvalid(Exception):
    """
    LLM responded but its output never became a valid tool list JSON,
    even after one stricter retry. Distinct from LLMUnavailableError.
    """


async def gapfill(missing_tools: list[str], candidate_tools: list[str]) -> list[str]:
    """
    LLM #4 (optional) — Gap-Fill Tool Selector.

    Given the tools that returned no usable data (missing_tools) and the
    full set of required tools (candidate_tools), returns the subset that
    should be re-dispatched for a single gap-fill retry round.

    Slice 2.5: implementation is a deterministic passthrough — we return
    missing_tools directly (filtered to candidate_tools for safety).
    The LLM-driven path is scaffolded here for future prioritization when
    there are many missing tools and we want to rank/select a subset.

    Raises LLMUnavailableError on gateway outage.
    Raises GapFillOutputInvalid if LLM-driven path fails (unused in 2.5).
    """
    # Deterministic: retry exactly the missing required tools, nothing extra.
    # Filter defensively to only tools actually in the candidate set.
    candidate_set = set(candidate_tools)
    return [t for t in missing_tools if t in candidate_set]


async def followup_narrate(user_query: str, evidence_text: str, prior_advisory_text: str) -> str:
    """
    LLM #5 — Follow-Up Re-Narrator.
    Explains a prior diagnostic outcome using only the existing sealed evidence.
    Forbids introducing new facts or numbers not in evidence_text.
    """
    system_prompt = load_prompt("followup_narrator_v1.txt")
    user_content = (
        f"User Question: {user_query}\n\n"
        f"Prior Diagnostic Findings:\n{prior_advisory_text}\n\n"
        f"Available Evidence Pack:\n{evidence_text}"
    )
    content = await call_llm_chat(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.0,
        caller="followup_narrator",
    )
    return content.strip()
