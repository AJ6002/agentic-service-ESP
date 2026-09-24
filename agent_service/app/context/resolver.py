import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

import yaml

from app.contracts.api import UIContext
from app.contracts.context import (
    AssetBinding,
    ContextFrame,
    Mentions,
    SessionSnapshot,
    TimeBinding,
)
from app.contracts.enums import AssetSource, MatchMethod, Resolution
from app.contracts.hitl import PendingInterrupt
from app.context.well_ids import normalize_well_id
from app.stores.session_store import get_pending, get_session

WELL_ID_REGEX = re.compile(r"\b(FSWS-\d+-[A-Za-z0-9]+|FNW-\d+|FWS-\d+|ULFA-\d+|FS-\d+)\b", re.IGNORECASE)
PRONOUN_REGEX = re.compile(r"\b(it|this well|the well|that well|the pump)\b", re.IGNORECASE)
CONTINUATION_REGEX = re.compile(r"\b(recheck|rerun|re-check|re-run|re-evaluate|check again)\b", re.IGNORECASE)
META_QUESTION_REGEX = re.compile(
    r"\b(why.*(ask|need|want)|what.*(choice|option|mean by)|which.*(choice|option))\b",
    re.IGNORECASE,
)
# Markers that indicate the message is asking a NEW question, not just
# supplying the slot value the pending clarification asked for. Used to
# stop a well-id mention inside an unrelated question ("what's the
# pressure at FS-091?") from being mistaken for a direct slot answer.
NEW_QUESTION_MARKERS_REGEX = re.compile(
    r"\b(what|why|how|when|show|check|explain|tell me|status|pressure|reading|"
    r"vibration|temperature|amps?|frequency|hz|history|compare|instead)\b",
    re.IGNORECASE,
)
# A direct slot answer is short — a bare id, or a short confirming phrase
# ("it's FS-017", "FS-017 please"). Anything longer is more likely a
# fresh sentence that happens to mention an asset.
DIRECT_ANSWER_MAX_WORDS = 4

# ---------------------------------------------------------------------------
# Asset alias table (deterministic, no LLM) — config/asset_aliases.yaml
# ---------------------------------------------------------------------------

_ALIAS_TABLE: dict[str, list[str]] | None = None


def _load_alias_table() -> dict[str, list[str]]:
    """
    Loads config/asset_aliases.yaml once and caches it.
    Shape: {asset_id: [alias, alias, ...]}, all aliases lowercased for lookup.
    """
    global _ALIAS_TABLE
    if _ALIAS_TABLE is not None:
        return _ALIAS_TABLE

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "config" / "asset_aliases.yaml"
    table: dict[str, list[str]] = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for asset_id, entry in data.items():
            aliases = (entry or {}).get("aliases", [])
            table[asset_id] = [a.lower().strip() for a in aliases]
    _ALIAS_TABLE = table
    return table


def match_alias(message: str) -> Optional[str]:
    """
    Deterministic substring match against the alias table.
    Returns the canonical asset_id on a hit, or None.
    Longest-alias-first so "flowstation 17" doesn't get shadowed by a
    shorter unrelated alias substring.
    """
    table = _load_alias_table()
    text = message.lower()
    best: tuple[int, str] | None = None  # (alias_len, asset_id)
    for asset_id, aliases in table.items():
        for alias in aliases:
            if alias and alias in text:
                if best is None or len(alias) > best[0]:
                    best = (len(alias), asset_id)
    return best[1] if best else None


def extract_mentions(message: str) -> Mentions:
    assets = []
    for m in WELL_ID_REGEX.findall(message):
        norm = normalize_well_id(m)
        assets.append(norm if norm else m.upper())
    pronouns = [p.lower() for p in PRONOUN_REGEX.findall(message)]
    times = []
    tb = parse_time_window(message)
    if tb and tb.label:
        times.append(tb.label)
    return Mentions(assets=assets, pronouns=pronouns, times=times)


# ---------------------------------------------------------------------------
# Time-window parsing (deterministic, no LLM) — Slice 2
# ---------------------------------------------------------------------------
# Turns a free-text time phrase in the user's message ("last 30 mins",
# "past 2 hours", "last 7 days", "yesterday") into a concrete
# [window_start, window_end] pair anchored at "now". This is what lets a
# query like "status of FS-17 in the last 30 mins" actually fetch the
# 30-minute window the user asked for, instead of a fixed hardcoded range.
#
# Unit → seconds. Kept small and explicit (Rule C): a lookup table, not a
# natural-language date library.
_TIME_UNIT_SECONDS: dict[str, int] = {
    "sec": 1,
    "secs": 1,
    "second": 1,
    "seconds": 1,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "hr": 3600,
    "hrs": 3600,
    "hour": 3600,
    "hours": 3600,
    "day": 86400,
    "days": 86400,
    "week": 604800,
    "weeks": 604800,
    "month": 2592000,   # 30-day month, sanity approximation
    "months": 2592000,
}

# "last 30 mins", "past 2 hours", "previous 7 days", "last 24 hrs"
_REL_WINDOW_REGEX = re.compile(
    r"\b(?:last|past|previous|recent)\s+(\d+)\s*"
    r"(secs?|seconds?|mins?|minutes?|hrs?|hours?|days?|weeks?|months?)\b",
    re.IGNORECASE,
)
# "last hour", "past day", "last week" (implicit N=1)
_REL_SINGLE_REGEX = re.compile(
    r"\b(?:last|past|previous)\s+"
    r"(sec|second|min|minute|hr|hour|day|week|month)\b",
    re.IGNORECASE,
)


_DATE_RANGE_REGEX = re.compile(
    r"\b(?:from|between)\s+(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?Z?)?)\s+(?:to|and|-)\s+(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?Z?)?)\b",
    re.IGNORECASE,
)


def parse_time_window(message: str, now: Optional[datetime] = None) -> Optional[TimeBinding]:
    """
    Parses a relative time phrase from the message into a TimeBinding with
    concrete window_start/window_end. Returns None if no phrase is found —
    the caller then falls back to UI context or a default window.

    Deterministic and timezone-aware (UTC). Not a full NL date parser:
    handles the "last/past N <unit>" and "last <unit>" shapes plus
    "yesterday"/"today", which cover the operational questions this agent
    actually receives.
    """
    text = message.lower()
    _now = now or datetime.now(timezone.utc)

    # Check explicit date ranges (e.g. from 2026-09-18 to 2026-09-19)
    m_range = _DATE_RANGE_REGEX.search(message)
    if m_range:
        s_str = m_range.group(1).strip().replace(" ", "T")
        e_str = m_range.group(2).strip().replace(" ", "T")
        try:
            if "T" not in s_str:
                s_str += "T00:00:00Z"
            elif not s_str.endswith("Z"):
                s_str += "Z"
            if "T" not in e_str:
                e_str += "T00:00:00Z"
            elif not e_str.endswith("Z"):
                e_str += "Z"
            s_dt = datetime.fromisoformat(s_str.replace("Z", "+00:00"))
            e_dt = datetime.fromisoformat(e_str.replace("Z", "+00:00"))
            return TimeBinding(
                window_start=s_dt,
                window_end=e_dt,
                source="EXPLICIT",
                label=f"{m_range.group(1)} to {m_range.group(2)}",
                confidence=1.0,
            )
        except Exception:
            pass

    seconds: Optional[int] = None
    label: Optional[str] = None

    m = _REL_WINDOW_REGEX.search(text)
    if m:
        qty = int(m.group(1))
        unit = m.group(2)
        unit_sec = _TIME_UNIT_SECONDS.get(unit)
        if unit_sec and qty > 0:
            seconds = qty * unit_sec
            label = f"last {qty} {unit}"
    if seconds is None:
        ms = _REL_SINGLE_REGEX.search(text)
        if ms:
            unit = ms.group(1)
            unit_sec = _TIME_UNIT_SECONDS.get(unit)
            if unit_sec:
                seconds = unit_sec
                label = f"last {unit}"
    if seconds is None:
        if re.search(r"\byesterday\b", text):
            seconds = 86400
            label = "yesterday"
        elif re.search(r"\btoday\b", text):
            seconds = 86400
            label = "today"

    if seconds is None:
        return None

    window_start = _now - timedelta(seconds=seconds)
    return TimeBinding(
        window_start=window_start,
        window_end=_now,
        source="EXPLICIT",
        label=label,
        confidence=1.0,
    )


def resolve_asset(
    message_mentions: list[str],
    raw_message: str,
    has_pronoun: bool,
    resolved_from_pending: Optional[str],
    session_snapshot: Optional[SessionSnapshot],
    ui_context: Optional[UIContext],
) -> AssetBinding:
    """
    Asset priority:
    EXPLICIT (typed in this message, exact id or alias)
      > RESOLVED (just answered via a clarification reply)
      > SESSION (remembered earlier in the conversation, incl. pronoun reference)
      > UI (currently selected on screen)
      > UNRESOLVED
    """
    # RESOLVED — a clarification reply just bound this asset.
    if resolved_from_pending:
        norm_resolved = normalize_well_id(resolved_from_pending) or resolved_from_pending
        return AssetBinding(
            id=norm_resolved,
            source="RESOLVED",
            confidence=1.0,
            match_method="EXACT_ID",
        )

    # EXPLICIT — exact well-id mentioned in this message.
    if message_mentions:
        norm_mention = normalize_well_id(message_mentions[0]) or message_mentions[0]
        return AssetBinding(
            id=norm_mention,
            source="EXPLICIT",
            confidence=1.0,
            match_method="EXACT_ID",
        )

    # EXPLICIT (alias) — layman term / nickname resolved via the alias table.
    alias_hit = match_alias(raw_message)
    if alias_hit:
        return AssetBinding(
            id=alias_hit,
            source="EXPLICIT",
            confidence=0.8,
            match_method="ALIAS",
        )

    # SESSION — pronoun reference ("it", "that well") or continuation query ("recheck")
    # resolved against the last asset touched in this session.
    if (has_pronoun or CONTINUATION_REGEX.search(raw_message)) and session_snapshot:
        session_asset = session_snapshot.last_asset_id
        if session_asset:
            return AssetBinding(
                id=session_asset,
                source="SESSION",
                confidence=0.7,
                match_method="PRONOUN",
            )

    # UI — currently selected on screen (ranked below EXPLICIT/SESSION on purpose,
    # see the old-repo bug this order prevents).
    if ui_context and ui_context.selected_asset:
        norm_ui = normalize_well_id(ui_context.selected_asset) or ui_context.selected_asset
        return AssetBinding(
            id=norm_ui,
            source="UI",
            confidence=0.8,
            match_method="EXACT_ID",
        )

    return AssetBinding(
        id=None,
        source="UNRESOLVED",
        confidence=0.0,
        match_method="NONE",
    )


def _looks_like_direct_slot_answer(text: str) -> bool:
    """
    Shape check for a slot-type match (e.g. asset_id): a real answer to
    "which well?" is short and doesn't carry its own question — "FS-017",
    "it's FS-017", "FS-017 please". A fresh, unrelated question that
    happens to mention an asset ("what's the pressure at FS-091?") is
    longer and/or contains its own question markers, and must fall
    through to SUPERSEDE instead of being auto-bound.
    """
    word_count = len(text.split())
    if word_count > DIRECT_ANSWER_MAX_WORDS:
        return False
    if NEW_QUESTION_MARKERS_REGEX.search(text):
        return False
    return True


def classify_resolution(message: str, pending: Optional[PendingInterrupt]) -> Tuple[Resolution, Optional[str]]:
    """
    Classifies whether incoming message binds to pending, supersedes it, or is meta.
    Returns (Resolution, bound_value_if_bind).
    """
    if not pending:
        return "NEW", None

    text = message.strip()

    # 1. Direct option match — exact match always wins (unambiguous), but
    # a SUBSTRING match only counts if the message also looks like a
    # direct answer. Otherwise "what's the pressure at FS-091?" would
    # false-BIND just because FS-091 happens to be one of the offered
    # options, even though the user asked something else entirely.
    for opt in pending.options:
        if text.lower() == opt.lower():
            return "BIND", opt
    if _looks_like_direct_slot_answer(text):
        for opt in pending.options:
            if opt.lower() in text.lower():
                return "BIND", opt

    # 2. Slot type match — but only if the message actually LOOKS like a
    # direct answer to the slot, not a fresh, unrelated question that
    # happens to mention an asset. Without this shape check, "what's the
    # pressure at FS-091?" (a different question) would be silently
    # treated as "the answer to which well tripped is FS-091" and run the
    # WRONG diagnosis instead of the question actually asked.
    if pending.slot == "asset_id" and _looks_like_direct_slot_answer(text):
        matches = WELL_ID_REGEX.findall(text)
        if matches:
            norm_match = normalize_well_id(matches[0]) or matches[0].upper()
            return "BIND", norm_match
        alias_hit = match_alias(text)
        if alias_hit:
            return "BIND", alias_hit

    # 3. Meta question about the pending clarification
    if META_QUESTION_REGEX.search(text) or (text.endswith("?") and "why are you asking" in text.lower()):
        return "META", None

    # 4. Otherwise user asked something else -> SUPERSEDE
    return "SUPERSEDE", None



ANOMALY_REGEX = re.compile(r"\b(anomal(?:y|ies|ous)|abnormal|outlier)\b", re.IGNORECASE)

LIMIT_PREFIX_REGEX = re.compile(r"\b(?:top|limit|last|recent|show|first|fetch)\s+(\d{1,4})\b", re.IGNORECASE)
LIMIT_SUFFIX_REGEX = re.compile(r"\b(\d{1,4})\s+(?:records|rows|anomalies|events|results|items|samples)\b", re.IGNORECASE)

def parse_query_limit(message: str) -> Optional[int]:
    # 1. Try prefix: e.g. "top 50", "limit 100", "show 25"
    m = LIMIT_PREFIX_REGEX.search(message)
    if m:
        end_idx = m.end()
        after_str = message[end_idx:].strip().lower()
        is_time = any(after_str.startswith(unit) for unit in ["min", "minute", "hr", "hour", "day", "week", "month", "sec", "second"])
        if not is_time:
            try:
                val = int(m.group(1))
                if val > 0:
                    return val
            except ValueError:
                pass

    # 2. Try suffix: e.g. "25 records", "50 anomalies"
    m2 = LIMIT_SUFFIX_REGEX.search(message)
    if m2:
        try:
            val = int(m2.group(1))
            if val > 0:
                return val
        except ValueError:
            pass

    return None

def parse_anomaly_filter(message: str) -> Optional[bool]:
    if ANOMALY_REGEX.search(message):
        return True
    return None

def resolve_context(
    session_id: str,
    message: str,
    ui_context: Optional[UIContext] = None,
) -> ContextFrame:
    session = get_session(session_id) or SessionSnapshot()
    pending = get_pending(session_id)

    resolution, bound_val = classify_resolution(message, pending)
    mentions = extract_mentions(message)
    has_pronoun = len(mentions.pronouns) > 0

    asset = resolve_asset(
        message_mentions=mentions.assets,
        raw_message=message,
        has_pronoun=has_pronoun,
        resolved_from_pending=bound_val if resolution == "BIND" and pending and pending.slot == "asset_id" else None,
        session_snapshot=session,
        ui_context=ui_context,
    )

    # Time priority: an explicit phrase in the message ("last 30 mins")
    # wins over a UI dropdown selection, which wins over the default.
    parsed_time = parse_time_window(message)
    if parsed_time is not None:
        time_b = parsed_time
    else:
        time_b = TimeBinding(
            source="UI" if (ui_context and ui_context.selected_time_range) else "DEFAULT",
            label=ui_context.selected_time_range if ui_context else None,
            confidence=1.0,
        )

    is_empty = not message.strip()

    query_params: dict[str, Any] = {}
    _extracted_limit = parse_query_limit(message)
    if _extracted_limit is not None:
        query_params["limit"] = _extracted_limit
    _extracted_anom = parse_anomaly_filter(message)
    if _extracted_anom is not None:
        query_params["anomalous_only"] = _extracted_anom

    return ContextFrame(
        session_id=session_id,
        query_params=query_params,
        raw_message=message,
        mentions=mentions,
        asset=asset,
        time=time_b,
        resolution=resolution,
        pending_ref=f"esp:session:{session_id}:pending" if pending else None,
        prior_analysis_ref=session.last_analysis_id,
        needs_clarify=is_empty,
        # CLARIFY is the interrupt TYPE (matches InterruptType); the specific
        # cause ("message was empty") lives in the clarification question text,
        # not in this field — this field is not a free-text reason code.
        clarify_reason="CLARIFY" if is_empty else None,
        session_snapshot=session,
    )
