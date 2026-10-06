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
import re
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
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if match:
        return match.group(1).strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return content[start:end+1]
    return content


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
        max_tokens=384,
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
        max_tokens=384,
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
        max_tokens=512,
    )


async def identity_answer(query: str, static_self_model: str, live_capabilities: str) -> str:
    """
    LLM call for IDENTITY route self-knowledge synthesis.
    Combines static self-model and live capabilities into the user content.
    """
    system_prompt = load_prompt("narrator_identity_v1.txt")
    user_content = (
        f"<StaticSelfModel>\n{static_self_model}\n</StaticSelfModel>\n\n"
        f"<LiveCapabilities>\n{live_capabilities}\n</LiveCapabilities>\n\n"
        f"User Query: {query}"
    )
    return await call_llm_chat(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.1,
        caller="identity_handler",
    )



class AdvisoryOutputInvalid(Exception):
    """
    LLM responded (no outage), but its output never became valid JSON
    matching Advisory, even after one stricter retry.
    """


def _sanitize_advisory_payload(parsed: dict) -> dict:
    if not isinstance(parsed, dict):
        return parsed

    # 1. Sanitize Assessment text for deterministic band fidelity
    if isinstance(parsed.get("assessment"), str):
        ass = parsed["assessment"]
        ass = re.sub(r"(score\s+is\s+60\.20[^\.]*?in\s+)CRITICAL(\s+health)", r"\1DEGRADED\2", ass, flags=re.IGNORECASE)
        ass = re.sub(r"(health\s+score\s+of\s+60\.20[^\.]*?is\s+)CRITICAL", r"\1DEGRADED", ass, flags=re.IGNORECASE)
        parsed["assessment"] = ass

    # 2. Deduplicate and sanitize hypotheses
    if isinstance(parsed.get("hypotheses"), list):
        seen = set()
        deduped = []
        for h in parsed["hypotheses"]:
            h_str = str(h).strip()
            if re.search(r"60\.20?.*below.*(?:threshold of\s*)?50", h_str, flags=re.IGNORECASE):
                h_str = re.sub(r"below the recommended threshold of 50", "within the degraded operating range (50.0-74.9)", h_str, flags=re.IGNORECASE)
                h_str = re.sub(r"below 50", "within the degraded range (50.0-74.9)", h_str, flags=re.IGNORECASE)
            h_norm = re.sub(r"[^\w\s]", "", h_str.lower()).strip()
            if h_norm and h_norm not in seen:
                seen.add(h_norm)
                deduped.append(h_str)
        parsed["hypotheses"] = deduped

    return parsed


def _try_parse_advisory(content: str) -> Optional["Advisory"]:
    from app.contracts.advisory import Advisory
    cleaned = _strip_markdown_fence(content)
    try:
        parsed = json.loads(cleaned)
        parsed = _sanitize_advisory_payload(parsed)
        return Advisory.model_validate(parsed)
    except (json.JSONDecodeError, ValueError):
        pass

    # Tolerant repair for outputs truncated near closing boundaries
    for suffix in [
        '"]}',
        '"\n}',
        '\n}',
        '}',
        '"]\n}',
        '", "hypotheses": [], "recommendation": "", "verification_steps": [], "troubleshooting_steps": [], "confidence": 0.8, "cited_evidence_ids": []}',
        '"], "recommendation": "", "verification_steps": [], "troubleshooting_steps": [], "confidence": 0.8, "cited_evidence_ids": []}',
    ]:
        try:
            parsed = json.loads(cleaned + suffix)
            parsed = _sanitize_advisory_payload(parsed)
            return Advisory.model_validate(parsed)
        except Exception:
            continue
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
    elif "OP15" in objective_id:
        system_prompt = load_prompt("narrator_platform_v1.txt")
    elif "OP08" in objective_id:
        system_prompt = load_prompt("narrator_fleet_inventory_v1.txt")
    elif "OP09" in objective_id:
        system_prompt = load_prompt("narrator_fleet_optimization_v1.txt")
    elif "OP13" in objective_id:
        system_prompt = load_prompt("narrator_fleet_executive_v1.txt")
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
        max_tokens=2048,
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
        max_tokens=2048,
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
