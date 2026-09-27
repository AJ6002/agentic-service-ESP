"""
Knowledge Base Domain Adapter (esp_kb_service).
Reference: ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md v2.1.0.

Separate microservice from Server 184's other domains -- different host/port
(:8085, not :8090), and its two primary endpoints are POST with a JSON body,
not GET with query params. Everything else follows the same adapter
contract as historian/live/events/ml/kpi/cards: one call per function,
errors raised as AdapterError via handle_adapter_response, zero fabricated
data on failure.
"""

import os
import re
from typing import Any, Optional

import httpx

from .common import DEFAULT_TIMEOUT_SEC, handle_adapter_response

# Minimum relevance score for a hit to be passed to the formatter.
# Hits below this threshold are structurally off-topic noise.
_MIN_HIT_SCORE: float = 0.65

# Section name patterns that indicate a ToC, cover page, or document header
# chunk. These chunks score high because they contain all domain vocabulary
# in their table rows or title lines, but carry no substantive content.
_GARBAGE_SECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)^\s*x?\s*contents?\s*$"),          # "Contents", "x Contents"
    re.compile(r"(?i)^table\s+of\s+contents"),            # "Table of contents"
    re.compile(r"(?i)^preface"),                          # "Preface to the First Edition"
    re.compile(r"(?i)^(index|glossary)\s*$"),             # standalone index/glossary pages
    re.compile(r"(?i)minimum\s+tag\s+universe"),          # ADVAIT PMM monitoring tag list chunk
]

# Snippet patterns that indicate a document cover page or pure-navigation chunk.
# Match on the first 200 chars of the snippet.
_GARBAGE_SNIPPET_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)Final\s+Revision\s+\d+\s+\d{1,2}\w*\s+\w+\s+\d{4}"),  # cover date lines
    re.compile(r"(?i)Prepared\s+by:.*Reviewed\s+by:"),                        # cover attribution
    re.compile(r"(?i)<!-- Page 1 -->"),                                         # document cover marker
]


def _is_garbage_hit(hit: dict) -> bool:
    """
    Returns True when a KB hit is a ToC, cover-page, or document-header chunk
    that contains domain vocabulary but no substantive definitional content.

    Two checks:
    1. Score below the minimum threshold.
    2. Section name or snippet matches a known garbage pattern.
    """
    score = float(hit.get("score", 0.0) or 0.0)
    if score < _MIN_HIT_SCORE:
        return True

    section = str(hit.get("section", "") or "")
    for pat in _GARBAGE_SECTION_PATTERNS:
        if pat.search(section):
            return True

    snippet = str(hit.get("snippet", "") or "")
    snippet_head = snippet[:250]
    for pat in _GARBAGE_SNIPPET_PATTERNS:
        if pat.search(snippet_head):
            return True

    # Drop chunks whose snippet is predominantly pipe-delimited table rows
    # (these are ToC or specification table entries, not prose content).
    non_whitespace = snippet_head.replace(" ", "").replace("\n", "")
    if len(non_whitespace) > 10:
        pipe_density = non_whitespace.count("|") / len(non_whitespace)
        if pipe_density > 0.15:
            return True

    return False


def get_kb_base_url() -> str:
    return os.getenv("KB_SERVICE_BASE_URL", "http://192.168.1.184:8085").rstrip("/")


async def check_kb_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    url = f"{get_kb_base_url()}/health"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/health")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/health")


async def search_kb(
    query: str,
    top_k: int = 5,
    min_authority: Optional[str] = None,
    category: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """
    POST /api/kb/search -- primary semantic/hybrid search. Returns hits with
    the strict Evidence Pack contract (doc_id, section, revision, authority,
    applicability, page, snippet, score) per spec section 3.

    Fetches top_k * 2 hits (capped at 20) to compensate for garbage-hit
    filtering applied after the response. Garbage hits are ToC/cover/header
    chunks that the Qdrant index scores highly because they contain all domain
    vocabulary in their table rows, but carry no substantive content.
    After filtering, returns the top top_k clean hits.
    """
    url = f"{get_kb_base_url()}/api/kb/search"
    effective_query = query
    q_lower = query.lower()
    if "stand for" in q_lower or "mean" in q_lower or any(w.isupper() and 2 <= len(w) <= 5 for w in query.split()):
        effective_query = f"{query} abbreviation acronym definition"

    body: dict[str, Any] = {"query": effective_query, "top_k": top_k}
    if min_authority:
        body["min_authority"] = min_authority
    if category:
        body["category"] = category

    if client:
        resp = await client.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        raw = handle_adapter_response(resp, "kb", "/api/kb/search")
    else:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
            raw = handle_adapter_response(resp, "kb", "/api/kb/search")

    hits = raw.get("hits")
    if isinstance(hits, list):
        clean = [h for h in hits if not _is_garbage_hit(h)]
        stop_words = {"what", "is", "the", "for", "and", "about", "does", "that", "this", "how", "do", "i", "to", "explain", "stand"}
        terms = [t.lower() for t in re.findall(r"\w+", query) if t.lower() not in stop_words and len(t) > 2]
        if terms:
            def term_score(h: dict) -> tuple[int, float]:
                text = (str(h.get("snippet", "")) + " " + str(h.get("section", ""))).lower()
                matches = sum(1 for t in terms if t in text)
                score = float(h.get("score", 0.0) or 0.0)
                return (matches, score)
            clean.sort(key=term_score, reverse=True)
        raw["hits"] = clean[:top_k]

    return raw


async def trace_kb_graph(
    symptom_ids: list[str],
    observed_parameters: Optional[dict[str, float]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """
    POST /api/kb/graph/trace -- symptom-to-root-cause causal chain + SOP.
    Not used by search_knowledge; kept for a later, dedicated diagnostic tool.
    """
    url = f"{get_kb_base_url()}/api/kb/graph/trace"
    body: dict[str, Any] = {"symptom_ids": symptom_ids}
    if observed_parameters:
        body["observed_parameters"] = observed_parameters

    if client:
        resp = await client.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/graph/trace")
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, json=body, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", "/api/kb/graph/trace")


async def get_kb_fault(fault_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """GET /api/kb/faults/{fault_id} -- single deterministic fault profile."""
    url = f"{get_kb_base_url()}/api/kb/faults/{fault_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/faults/{fault_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/faults/{fault_id}")


async def get_kb_standard(standard_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """GET /api/kb/standards/{standard_id} -- certified standard clause lookup."""
    url = f"{get_kb_base_url()}/api/kb/standards/{standard_id}"
    if client:
        resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/standards/{standard_id}")
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
        return handle_adapter_response(resp, "kb", f"/api/kb/standards/{standard_id}")
