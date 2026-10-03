"""
Knowledge Base Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Uses pgvector on kb_chunks for semantic similarity and direct relational queries
for kb_fault_taxonomy, kb_causal_edges, kb_glossary, and kb_documents.
Zero HTTP dependency on :8085.
"""

from __future__ import annotations

import os
import re
import asyncio
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError

_MIN_HIT_SCORE: float = 0.55

_GARBAGE_SECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)^\s*x?\s*contents?\s*$"),
    re.compile(r"(?i)^table\s+of\s+contents"),
    re.compile(r"(?i)^preface"),
    re.compile(r"(?i)^(index|glossary)\s*$"),
    re.compile(r"(?i)minimum\s+tag\s+universe"),
]

_GARBAGE_SNIPPET_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)Final\s+Revision\s+\d+\s+\d{1,2}\w*\s+\w+\s+\d{4}"),
    re.compile(r"(?i)Prepared\s+by:.*Reviewed\s+by:"),
    re.compile(r"(?i)<!-- Page 1 -->"),
]

_EMBED_MODEL = None


def _get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        try:
            from fastembed import TextEmbedding
            _EMBED_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception:
            _EMBED_MODEL = False
    return _EMBED_MODEL


def _is_garbage_hit(hit: dict) -> bool:
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

    non_whitespace = snippet_head.replace(" ", "").replace("\n", "")
    if len(non_whitespace) > 10:
        pipe_density = non_whitespace.count("|") / len(non_whitespace)
        if pipe_density > 0.15:
            return True

    return False


async def check_kb_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Microservice health check directly against PostgreSQL."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT count(*) FROM kb_chunks;")
            chunk_cnt = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM kb_documents;")
            doc_cnt = cur.fetchone()[0]
            return {
                "status": "HEALTHY",
                "source": "POSTGRESQL",
                "chunks": chunk_cnt,
                "documents": doc_cnt,
            }
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL"}


async def search_kb(
    query: str,
    top_k: int = 5,
    min_authority: Optional[str] = None,
    category: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """
    Semantic & keyword search across 7,752 chunks in PostgreSQL kb_chunks.
    Returns EvidencePack compliant format.
    """
    def _search():
        effective_query = query.strip()
        embedder = _get_embed_model()
        vec = None
        if embedder:
            try:
                vec = list(embedder.embed([effective_query]))[0].tolist()
            except Exception:
                vec = None

        with get_db_cursor() as cur:
            if vec is not None:
                cur.execute("""
                    SELECT c.chunk_id, c.doc_id, c.doc_title, c.section_title, c.content,
                           d.tier, (1 - (c.embedding <=> %s::vector)) AS score
                    FROM kb_chunks c
                    LEFT JOIN kb_documents d ON c.doc_id = d.doc_id
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s;
                """, (vec, vec, top_k * 3))
            else:
                terms = [f"%{t}%" for t in re.findall(r"\w+", effective_query) if len(t) > 2]
                if terms:
                    cur.execute("""
                        SELECT c.chunk_id, c.doc_id, c.doc_title, c.section_title, c.content,
                               d.tier, 0.75 AS score
                        FROM kb_chunks c
                        LEFT JOIN kb_documents d ON c.doc_id = d.doc_id
                        WHERE c.content ILIKE ANY(%s) OR c.section_title ILIKE ANY(%s)
                        LIMIT %s;
                    """, (terms, terms, top_k * 3))
                else:
                    cur.execute("""
                        SELECT c.chunk_id, c.doc_id, c.doc_title, c.section_title, c.content,
                               d.tier, 0.70 AS score
                        FROM kb_chunks c
                        LEFT JOIN kb_documents d ON c.doc_id = d.doc_id
                        LIMIT %s;
                    """, (top_k * 3,))

            rows = cur.fetchall()

        raw_hits = []
        for r in rows:
            chunk_id, doc_id, doc_title, sec_title, content, tier, score = r
            raw_hits.append({
                "doc_id": doc_id or "DOC-ESP-MANUAL",
                "doc_title": doc_title or doc_id,
                "section": sec_title or "General Overview",
                "revision": "2026.1",
                "authority": tier or "AUTHORITATIVE",
                "applicability": "ALL",
                "page": 1,
                "snippet": content,
                "score": float(score or 0.0),
                "chunk_id": chunk_id,
            })

        clean = [h for h in raw_hits if not _is_garbage_hit(h)]
        stop_words = {"what", "is", "the", "for", "and", "about", "does", "that", "this", "how", "do", "i", "to", "explain", "stand"}
        terms = [t.lower() for t in re.findall(r"\w+", query) if t.lower() not in stop_words and len(t) > 2]
        if terms:
            def term_score(h: dict) -> tuple[int, float]:
                text = (str(h.get("snippet", "")) + " " + str(h.get("section", ""))).lower()
                matches = sum(1 for t in terms if t in text)
                score = float(h.get("score", 0.0) or 0.0)
                return (matches, score)
            clean.sort(key=term_score, reverse=True)

        selected_hits = clean[:top_k]
        return {
            "query": query,
            "total_hits": len(selected_hits),
            "hits": selected_hits,
            "source": "POSTGRESQL",
        }

    try:
        return await asyncio.to_thread(_search)
    except Exception as e:
        raise AdapterError(f"PostgreSQL search_kb failed: {e}", status_code=500, code="KB_SEARCH_FAILED")


async def get_kb_fault(fault_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Lookup deterministic fault profile from kb_fault_taxonomy."""
    def _query():
        clean_id = fault_id.strip().upper().replace(" ", "_")
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT fault_id, fault_class, category, preferred_name, synonyms, canonical_metric,
                       symptoms, contributing_factors, evidence_required, severity_range, escalation,
                       troubleshooting_steps, source
                FROM kb_fault_taxonomy
                WHERE fault_id = %s OR fault_class = %s OR preferred_name ILIKE %s;
            """, (clean_id, clean_id, f"%{fault_id}%"))
            r = cur.fetchone()
            if not r:
                return {"status": "NOT_FOUND", "fault_id": fault_id}
            return {
                "fault_id": r[0],
                "fault_class": r[1],
                "category": r[2],
                "preferred_name": r[3],
                "synonyms": r[4] or [],
                "canonical_metric": r[5],
                "symptoms": r[6] or [],
                "contributing_factors": r[7] or [],
                "evidence_required": r[8] or [],
                "severity_range": r[9],
                "escalation": r[10],
                "troubleshooting_steps": r[11] or [],
                "source": r[12] or "POSTGRESQL",
            }
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL get_kb_fault failed: {e}", status_code=500, code="KB_FAULT_FAILED")


async def trace_kb_graph(
    symptom_ids: list[str],
    observed_parameters: Optional[dict[str, float]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Causal DAG graph traversal from kb_causal_edges in PostgreSQL."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT from_node, to_node, relationship, confidence FROM kb_causal_edges;")
            rows = cur.fetchall()

        paths = []
        root_causes = set()
        symptom_lower = {s.lower() for s in symptom_ids}

        for from_n, to_n, rel, conf in rows:
            for sym in symptom_ids:
                if sym.lower() in from_n.lower() or from_n.lower() in sym.lower():
                    paths.append({
                        "from": from_n,
                        "to": to_n,
                        "relationship": rel,
                        "confidence": float(conf or 0.95),
                    })
                    root_causes.add(to_n)

        return {
            "symptoms": symptom_ids,
            "paths": paths,
            "root_causes": list(root_causes),
            "source": "POSTGRESQL",
        }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL trace_kb_graph failed: {e}", status_code=500, code="KB_GRAPH_FAILED")


async def get_kb_standard(standard_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch standard metadata from kb_documents."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT doc_id, title, tier, source_path, created_at
                FROM kb_documents
                WHERE doc_id ILIKE %s OR title ILIKE %s;
            """, (f"%{standard_id}%", f"%{standard_id}%"))
            r = cur.fetchone()
            if not r:
                return {"status": "NOT_FOUND", "standard_id": standard_id}
            return {
                "doc_id": r[0],
                "title": r[1],
                "tier": r[2],
                "source_path": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
                "source": "POSTGRESQL",
            }
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL get_kb_standard failed: {e}", status_code=500, code="KB_STANDARD_FAILED")
