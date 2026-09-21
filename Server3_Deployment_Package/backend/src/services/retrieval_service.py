"""
Retrieval Service for ESP Knowledge Base
Coordinates multi-tier retrieval across deterministic YAML files, PostgreSQL structured tables,
and pgvector semantic vector search with cross-source conflict detection.
"""

import os
import json
import yaml
import psycopg2
from typing import List, Dict, Any, Optional

from pathlib import Path

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "esp_agent"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "connect_timeout": 1
}

ROOT_DIR = os.getenv("ESP_APM_ROOT_DIR") or str(Path(__file__).resolve().parents[3])
DETERMINISTIC_DIR = os.path.join(ROOT_DIR, "knowledge", "deterministic")
if not os.path.exists(DETERMINISTIC_DIR):
    DETERMINISTIC_DIR = os.path.join(ROOT_DIR, "esp-knowledge", "deterministic")
PROCESSED_TEXT_DIR = os.path.join(ROOT_DIR, "knowledge", "processed", "text")

class RetrievalService:
    """
    Multi-tier Knowledge Retrieval Service:
    Tier 1: Deterministic YAML Exact Lookups (Glossary, Faults, Alerts, Units)
    Tier 2: PostgreSQL Structured Table Lookups (fault_patterns, pump_curves, glossary_terms)
    Tier 3: Local RAG Chunks / pgvector Cosine Similarity Semantic Vector Search
    """

    def __init__(self):
        self._embedding_model = None
        self._rag_adapter = None
        self._use_postgres = os.getenv("USE_POSTGRES", "1") == "1"

    def _get_rag_adapter(self):
        if self._rag_adapter is None:
            for mod_path in ("src.adapters.rag", "backend.src.adapters.rag", "esp_agent.src.adapters.rag"):
                try:
                    import importlib
                    mod = importlib.import_module(mod_path)
                    self._rag_adapter = mod.RAGAdapter(docs_dir=PROCESSED_TEXT_DIR)
                    break
                except Exception:
                    continue
        return self._rag_adapter

    def _get_embedding_model(self):
        if not self._use_postgres:
            return None
        if self._embedding_model is not None:
            return self._embedding_model

        model = None
        for mod_path in ("src.adapters.rag", "backend.src.adapters.rag", "esp_agent.src.adapters.rag"):
            try:
                import importlib
                mod = importlib.import_module(mod_path)
                model = getattr(mod, "_GLOBAL_EMBEDDING_MODEL", None)
                if model is not None:
                    break
            except Exception:
                continue

        if model is None:
            try:
                adapter = self._get_rag_adapter()
                if adapter:
                    model = adapter._get_embedding_model()
            except Exception:
                pass

        if model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer("all-mpnet-base-v2")
            except Exception:
                model = None

        self._embedding_model = model
        return self._embedding_model

    def search_glossary(self, term: str) -> Optional[Dict[str, Any]]:
        """Exact lookup for business & engineering terms in deterministic YAML & Postgres"""
        import re
        term_clean = term.strip().upper()
        term_lower = term.strip().lower()
        yaml_file = os.path.join(DETERMINISTIC_DIR, "glossary", "seed_glossary.yaml")
        
        if os.path.exists(yaml_file):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                terms_list = data.get("terms", [])
                # Pass 1: exact match
                for item in terms_list:
                    if item["term_id"] == term_clean or term_clean in [s.upper() for s in item.get("synonyms", [])]:
                        return {
                            "term_id": item["term_id"],
                            "preferred_name": item["preferred_name"],
                            "definition": item["definition"],
                            "domain": item.get("domain", "ESP"),
                            "unit": item.get("unit"),
                            "source": "deterministic_yaml"
                        }
                # Pass 2: word boundary match within conversational sentence (e.g. "What is the TDS and all?")
                for item in terms_list:
                    tid = item["term_id"]
                    if re.search(r'\b' + re.escape(tid) + r'\b', term_clean):
                        return {
                            "term_id": item["term_id"],
                            "preferred_name": item["preferred_name"],
                            "definition": item["definition"],
                            "domain": item.get("domain", "ESP"),
                            "unit": item.get("unit"),
                            "source": "deterministic_yaml"
                        }
                    for s in item.get("synonyms", []):
                        if re.search(r'\b' + re.escape(s.lower()) + r'\b', term_lower):
                            return {
                                "term_id": item["term_id"],
                                "preferred_name": item["preferred_name"],
                                "definition": item["definition"],
                                "domain": item.get("domain", "ESP"),
                                "unit": item.get("unit"),
                                "source": "deterministic_yaml"
                            }

        # PostgreSQL fallback
        if self._use_postgres:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
                cur.execute("""
                    SELECT term_id, preferred_term, definition, domain, unit
                    FROM glossary_terms
                    WHERE UPPER(term_id) = %s OR UPPER(preferred_term) = %s;
                """, (term_clean, term_clean))
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    return {
                        "term_id": row[0],
                        "preferred_name": row[1],
                        "definition": row[2],
                        "domain": row[3],
                        "unit": row[4],
                        "source": "postgres_glossary_terms"
                    }
            except Exception:
                pass

        return None

    def search_fault_taxonomy(self, fault_query: str) -> List[Dict[str, Any]]:
        """Lookup fault patterns by symptom or category in deterministic YAML & Postgres"""
        query_clean = fault_query.strip().upper()
        results = []

        yaml_file = os.path.join(DETERMINISTIC_DIR, "faults", "seed_faults.yaml")
        if os.path.exists(yaml_file):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for fault in data.get("faults", []):
                    if query_clean in fault["fault_id"] or query_clean in fault["preferred_name"].upper() or query_clean == fault["category"]:
                        results.append({
                            "fault_id": fault["fault_id"],
                            "category": fault["category"],
                            "preferred_name": fault["preferred_name"],
                            "canonical_metric": fault.get("canonical_metric"),
                            "symptoms": fault.get("symptoms", []),
                            "contributing_factors": fault.get("contributing_factors", []),
                            "severity_range": fault.get("severity_range"),
                            "source": "deterministic_yaml"
                        })

        if results:
            return results

        # Postgres fallback
        if self._use_postgres:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
                cur.execute("""
                    SELECT fault_id, category, preferred_name, canonical_metric,
                           symptoms, contributing_factors, severity_range
                    FROM fault_patterns
                    WHERE UPPER(fault_id) LIKE %s OR UPPER(preferred_name) LIKE %s OR UPPER(category) = %s;
                """, (f"%{query_clean}%", f"%{query_clean}%", query_clean))
                rows = cur.fetchall()
                cur.close()
                conn.close()
                for r in rows:
                    results.append({
                        "fault_id": r[0],
                        "category": r[1],
                        "preferred_name": r[2],
                        "canonical_metric": r[3],
                        "symptoms": r[4],
                        "contributing_factors": r[5],
                        "severity_range": r[6],
                        "source": "postgres_fault_patterns"
                    })
            except Exception:
                pass

        return results

    def vector_search(
        self,
        query: str,
        top_k: int = 4,
        category_filter: Optional[str] = None,
        document_filter: Optional[List[str]] = None,
        chunk_id_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute semantic search over knowledge base (local RAG chunks or pgvector)."""
        if self._use_postgres:
            model = self._get_embedding_model()
            if model is not None:
                try:
                    query_embedding = model.encode(query).tolist()
                    query_embedding_str = str(query_embedding)

                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()

                    sql = """
                        SELECT ki.knowledge_id, ki.text_content, d.title, ki.canonical_category,
                               ki.page, ki.section, ki.heading_path, d.document_id, d.sha256_checksum,
                               1 - (ke.embedding <=> %s::vector) AS similarity,
                               COALESCE(ki.authority_level, d.authority_level, 'E') AS authority_level
                        FROM knowledge_embeddings ke
                        JOIN knowledge_items ki ON ke.knowledge_id = ki.knowledge_id
                        JOIN documents d ON ki.document_id = d.document_id
                    """
                    params = [query_embedding_str]
                    where_clauses = []

                    if category_filter:
                        where_clauses.append("ki.canonical_category = %s")
                        params.append(category_filter)
                    if document_filter:
                        where_clauses.append("d.document_id = ANY(%s)")
                        params.append(document_filter)
                    if chunk_id_filter:
                        where_clauses.append("ki.knowledge_id = ANY(%s)")
                        params.append(chunk_id_filter)

                    if where_clauses:
                        sql += " WHERE " + " AND ".join(where_clauses)

                    sql += " ORDER BY ke.embedding <=> %s::vector ASC LIMIT %s;"
                    params.extend([query_embedding_str, top_k])

                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    cur.close()
                    conn.close()

                    results = []
                    for r in rows:
                        results.append({
                            "knowledge_id": r[0],
                            "text": r[1],
                            "text_content": r[1],
                            "source_title": r[2],
                            "category": r[3],
                            "page": r[4],
                            "section": r[5],
                            "heading_path": r[6],
                            "document_id": r[7],
                            "checksum": r[8],
                            "similarity": round(float(r[9]), 4),
                            "authority_level": r[10] if len(r) > 10 else "E"
                        })
                    if results:
                        return results
                except Exception:
                    pass

        # Fallback to local RAG adapter over processed text
        rag = self._get_rag_adapter()
        if rag:
            rag_matches = rag.search(query, top_k=top_k)
            results = []
            for idx, m in enumerate(rag_matches):
                results.append({
                    "knowledge_id": f"LOCAL_{m['source']}_{idx}",
                    "text": m["text"],
                    "source_title": m["source"],
                    "category": m.get("doc_type", "standard"),
                    "page": 1,
                    "section": "Standard Guidance",
                    "heading_path": m["source"],
                    "document_id": m["source"],
                    "checksum": "",
                    "similarity": min(0.98, max(0.60, round(float(m.get("score", 1.0)) * 0.25, 4))),
                    "authority_level": "A" if "11S" in m["source"] else ("B" if "IEC" in m["source"] else "C")
                })
            return results
        return []

    def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 5,
        authority_filter: str = None,
        document_filter: Optional[List[str]] = None,
        chunk_id_filter: Optional[List[str]] = None,
        max_chunks_per_doc: int = 2,
     ) -> Dict[str, Any]:
        """
        Phase 3 Hybrid Retrieval:
        1. Exact glossary match (deterministic)
        2. Structured fault taxonomy match
        3. BM25 sparse lexical search over knowledge_items
        4. pgvector dense semantic search (with optional Cognee subgraph constraint)
        5. Candidate fusion (deduplicate by knowledge_id)
        6. Authority-level sort (A > B > C > D > E > F)
        7. MMR Document Diversity Gating (prevents large manuals from crowding out specialized docs)
        8. Conflict detection
        """
        glossary_match = self.search_glossary(query)
        fault_matches = self.search_fault_taxonomy(query)
        bm25_results = self.bm25_search(query, top_k=max(top_k * 5, 30))
        vector_results = self.vector_search(
            query,
            top_k=max(top_k * 5, 30),
            document_filter=document_filter,
            chunk_id_filter=chunk_id_filter
        )

        # Fuse and deduplicate by knowledge_id
        seen = {}
        for r in bm25_results:
            seen[r["knowledge_id"]] = dict(r, retrieval_source="bm25")
        for r in vector_results:
            kid = r["knowledge_id"]
            if kid not in seen:
                seen[kid] = dict(r, retrieval_source="vector")
            else:
                # Already in BM25 — upgrade similarity to whichever is higher
                existing = seen[kid]
                existing["retrieval_source"] = "hybrid"
                existing["similarity"] = max(existing.get("similarity", 0), r.get("similarity", 0))

        fused = list(seen.values())

        # Composite Authority Fusion: balances dense semantic similarity with authority level precedence
        AUTH_BONUS = {"A": 0.12, "B": 0.08, "C": 0.04, "D": 0.00, "E": -0.05, "F": -0.10}
        AUTHORITY_RANK = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
        if authority_filter:
            max_rank = AUTHORITY_RANK.get(authority_filter.upper(), 5)
            fused = [r for r in fused if AUTHORITY_RANK.get(r.get("authority_level", "E"), 4) <= max_rank]

        for r in fused:
            sim = r.get("similarity", 0.0)
            if r.get("retrieval_source") == "bm25":
                sim *= 0.70  # Normalize pure lexical match against dense cosine similarity
            bonus = AUTH_BONUS.get(r.get("authority_level", "E"), -0.05)
            r["composite_score"] = round(sim + bonus, 4)

        fused.sort(key=lambda r: -r.get("composite_score", 0.0))

        # Document Diversity Gating (MMR approximation to prevent single-document starvation)
        if max_chunks_per_doc and max_chunks_per_doc > 0 and (not document_filter or len(document_filter) > 1):
            doc_counts: Dict[str, int] = {}
            ranked = []
            leftover = []
            for r in fused:
                doc = r.get("document_id") or r.get("source_pdf") or r.get("knowledge_id", "").split("#")[0]
                if doc_counts.get(doc, 0) < max_chunks_per_doc:
                    ranked.append(r)
                    doc_counts[doc] = doc_counts.get(doc, 0) + 1
                else:
                    leftover.append(r)
                if len(ranked) >= top_k:
                    break
            # If diversity pool didn't fill top_k, backfill from leftovers
            if len(ranked) < top_k:
                for r in leftover:
                    ranked.append(r)
                    if len(ranked) >= top_k:
                        break
        else:
            ranked = fused[:top_k]

        conflicts = self._detect_conflicts(ranked)

        return {
            "query": query,
            "glossary_match": glossary_match,
            "fault_matches": fault_matches,
            "vector_results": ranked,
            "conflicts": conflicts,
            "retrieval_status": "SUCCESS" if (ranked or glossary_match or fault_matches) else "EMPTY"
        }

    def _detect_conflicts(self, vector_results: List[Dict[str, Any]]) -> List[str]:
        """Detect conflicts between retrieved sources; flag Authority-level disagreements."""
        conflicts = []
        import re
        temps_found = set()
        for res in vector_results:
            text = res.get("text", "").lower()
            if "temperature" in text and "°c" in text:
                for m in re.findall(r"(\d{2,3})\s*°c", text):
                    temps_found.add(int(m))

        if len(temps_found) > 1 and max(temps_found) - min(temps_found) > 20:
            conflicts.append(
                f"KNOWLEDGE_CONFLICT: Thermal threshold discrepancy {sorted(list(temps_found))}°C. "
                "Installed asset limits (Level A) take precedence. Engineering review required."
            )
        return conflicts

    def bm25_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """BM25 sparse lexical search over all knowledge_items text content."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            return []  # graceful degradation if not installed

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT ki.knowledge_id, ki.text_content, d.title, ki.canonical_category,
                       ki.page, ki.section, ki.heading_path, d.document_id,
                       COALESCE(ki.authority_level, 'E') as authority_level
                FROM knowledge_items ki
                JOIN documents d ON ki.document_id = d.document_id
                WHERE ki.status = 'PUBLISHED';
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception:
            return []

        if not rows:
            return []

        corpus = [r[1].lower().split() for r in rows]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query.lower().split())

        top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        results = []
        for i in top_indices:
            if scores[i] > 0:
                r = rows[i]
                results.append({
                    "knowledge_id": r[0],
                    "text": r[1],
                    "source_title": r[2],
                    "category": r[3],
                    "page": r[4],
                    "section": r[5],
                    "heading_path": r[6],
                    "document_id": r[7],
                    "authority_level": r[8],
                    "similarity": round(float(scores[i]) / (max(scores) + 1e-6), 4)  # normalised
                })
        return results

    def search_similar_cases(self, symptom_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search historical case library by symptom text similarity (keyword match).
        Splits query into individual keywords and OR-matches against symptom_summary and confirmed_cause.
        """
        keywords = [w.strip() for w in symptom_query.upper().split() if len(w.strip()) > 2]
        if not keywords:
            return []
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            # Build dynamic OR clause for each keyword
            conditions = " OR ".join(
                ["(UPPER(symptom_summary) LIKE %s OR UPPER(confirmed_cause) LIKE %s)"] * len(keywords)
            )
            params = []
            for kw in keywords:
                params.extend([f"%{kw}%", f"%{kw}%"])
            params.append(top_k)
            cur.execute(f"""
                SELECT case_id, asset_id, equipment_model, confirmed_cause,
                       symptom_summary, operator_action, action_outcome, approval_status
                FROM historical_cases
                WHERE approval_status = 'APPROVED' AND ({conditions})
                LIMIT %s;
            """, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [{
                "case_id": r[0], "asset_id": r[1], "equipment_model": r[2],
                "confirmed_cause": r[3], "symptom_summary": r[4],
                "operator_action": r[5], "action_outcome": r[6], "approval_status": r[7]
            } for r in rows]
        except Exception:
            return []


    def get_pump_curve(self, pump_model: str) -> Optional[Dict[str, Any]]:
        """Exact lookup for pump curve data by model name (Authority Level B)."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT curve_id, pump_model, manufacturer, stage_count, frequency_hz,
                       ror_min_bpd, ror_max_bpd, bep_bpd, curve_points, authority_level
                FROM pump_curves
                WHERE LOWER(pump_model) = LOWER(%s)
                LIMIT 1;
            """, (pump_model,))
            r = cur.fetchone()
            cur.close()
            conn.close()
            if r:
                return {
                    "curve_id": r[0], "pump_model": r[1], "manufacturer": r[2],
                    "stage_count": r[3], "frequency_hz": r[4],
                    "ror_min_bpd": r[5], "ror_max_bpd": r[6], "bep_bpd": r[7],
                    "curve_points": r[8], "authority_level": r[9]
                }
        except Exception:
            pass
        return None
