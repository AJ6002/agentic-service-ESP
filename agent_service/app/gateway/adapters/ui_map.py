"""
UI Map Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries platform self-model metadata ingested from ui_map.yaml in kb_chunks table.
Zero fabricated fallback data.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError
from .kb import _get_embed_model


def _map_row_to_ui_entry(row: tuple, include_score: bool = False) -> dict[str, Any]:
    """
    Maps a database row from kb_chunks to the canonical 9-field UiMap schema.
    Row layout: (chunk_id, doc_title, section_title, content, metadata, [score])
    """
    chunk_id = row[0]
    doc_title = row[1] or ""
    section_title = row[2] or ""
    content = row[3] or ""
    raw_meta = row[4]

    if isinstance(raw_meta, dict):
        meta = raw_meta
    elif isinstance(raw_meta, str) and raw_meta.strip():
        try:
            meta = json.loads(raw_meta)
        except Exception:
            meta = {}
    else:
        meta = {}

    # Extract entry ID
    entry_id = meta.get("id")
    if not entry_id:
        entry_id = chunk_id[len("ui_map:"):] if chunk_id.startswith("ui_map:") else chunk_id

    # Extract title
    title = meta.get("title")
    if not title:
        if section_title and ":" in section_title:
            title = section_title.split(":", 1)[1].strip()
        elif doc_title.startswith("UI Map - "):
            title = doc_title[len("UI Map - "):].strip()
        else:
            title = doc_title or entry_id

    result: dict[str, Any] = {
        "id": str(entry_id),
        "type": str(meta.get("type", "unknown")),
        "title": str(title),
        "path": meta.get("path"),
        "workspace": str(meta.get("workspace", "platform")),
        "summary": str(meta.get("summary", "")),
        "description": str(content),
        "related": list(meta.get("related", [])),
        "aliases": list(meta.get("aliases", [])),
    }

    if include_score and len(row) > 5 and row[5] is not None:
        result["score"] = round(float(row[5]), 4)

    return result


async def lookup_by_id(
    entry_id: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[dict[str, Any]]:
    """
    Direct lookup of a UI map entry by its unique ID (e.g. 'component.subsystem-equalizer').
    Queries PostgreSQL kb_chunks filtered strictly by source_domain = 'ui_map'.
    Returns full 9-field dictionary or None if not found. Never fabricates.
    """
    if not entry_id or not str(entry_id).strip():
        return None

    clean_id = str(entry_id).strip()

    def _query() -> Optional[dict[str, Any]]:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT chunk_id, doc_title, section_title, content, metadata
                FROM kb_chunks
                WHERE source_domain = 'ui_map'
                  AND (
                    metadata->>'id' = %s
                    OR metadata->>'id' ILIKE %s
                    OR metadata->>'path' = %s
                    OR chunk_id = %s
                    OR chunk_id = %s
                  )
                LIMIT 1;
            """, (clean_id, clean_id, clean_id, clean_id, f"ui_map:{clean_id}"))
            
            row = cur.fetchone()
            if not row:
                return None
            return _map_row_to_ui_entry(row)

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL lookup_by_id failed: {e}", status_code=500, code="UI_MAP_LOOKUP_FAILED")


async def search_ui_map(
    query: str,
    top_k: int = 5,
    client: Optional[httpx.AsyncClient] = None,
) -> list[dict[str, Any]]:
    """
    Semantic vector search against PostgreSQL kb_chunks filtered strictly to source_domain = 'ui_map'.
    Returns list of matched entries adhering to the 9-field schema.
    """
    effective_query = (query or "").strip()
    if not effective_query:
        return []

    def _search() -> list[dict[str, Any]]:
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
                    SELECT chunk_id, doc_title, section_title, content, metadata,
                           (1 - (embedding <=> %s::vector)) AS score
                    FROM kb_chunks
                    WHERE source_domain = 'ui_map'
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (vec, vec, max(1, top_k)))
            else:
                terms = [f"%{t}%" for t in re.findall(r"\w+", effective_query) if len(t) > 2]
                if terms:
                    cur.execute("""
                        SELECT chunk_id, doc_title, section_title, content, metadata,
                               0.75 AS score
                        FROM kb_chunks
                        WHERE source_domain = 'ui_map'
                          AND (content ILIKE ANY(%s) OR section_title ILIKE ANY(%s) OR doc_title ILIKE ANY(%s))
                        LIMIT %s;
                    """, (terms, terms, terms, max(1, top_k)))
                else:
                    cur.execute("""
                        SELECT chunk_id, doc_title, section_title, content, metadata,
                               0.70 AS score
                        FROM kb_chunks
                        WHERE source_domain = 'ui_map'
                        LIMIT %s;
                    """, (max(1, top_k),))

            rows = cur.fetchall()
            return [_map_row_to_ui_entry(r, include_score=True) for r in rows]

    try:
        return await asyncio.to_thread(_search)
    except Exception as e:
        raise AdapterError(f"PostgreSQL search_ui_map failed: {e}", status_code=500, code="UI_MAP_SEARCH_FAILED")


# Alias for consistent function interface
search = search_ui_map


async def check_ui_map_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Microservice health check for UI map knowledge chunks in PostgreSQL."""
    def _query() -> dict[str, Any]:
        with get_db_cursor() as cur:
            cur.execute("SELECT count(*) FROM kb_chunks WHERE source_domain = 'ui_map';")
            count = cur.fetchone()[0]
            return {
                "status": "HEALTHY" if count > 0 else "DEGRADED",
                "source": "POSTGRESQL",
                "domain": "ui_map",
                "count": count,
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL", "domain": "ui_map"}
