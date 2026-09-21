import os
import glob
from typing import List, Dict, Any, Optional


_GLOBAL_EMBEDDING_MODEL = None


class RAGAdapter:
    """Universal Documentation Retrieval (RAG) Adapter supporting pgvector hybrid search and local file fallback."""

    def __init__(self, docs_dir: Optional[str] = None):
        if not docs_dir or not os.path.exists(docs_dir):
            from pathlib import Path
            repo_root = Path(__file__).resolve().parents[3]
            candidate = repo_root / "knowledge" / "processed" / "text"
            if candidate.exists():
                docs_dir = str(candidate)

        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, Any]] = []
        if docs_dir and os.path.exists(docs_dir):
            self.index_documents(docs_dir)

    def _get_embedding_model(self):
        """Lazy load and cache global sentence-transformer embedding model"""
        global _GLOBAL_EMBEDDING_MODEL
        if _GLOBAL_EMBEDDING_MODEL is None:
            try:
                from sentence_transformers import SentenceTransformer
                _GLOBAL_EMBEDDING_MODEL = SentenceTransformer("all-mpnet-base-v2")
            except Exception:
                _GLOBAL_EMBEDDING_MODEL = None
        return _GLOBAL_EMBEDDING_MODEL

    def index_documents(self, docs_dir: str):
        """Reads text, markdown, and PDF files, splits them into logical chunks, and indexes them for retrieval."""
        self.docs_dir = docs_dir
        self.chunks = []
        doc_files = glob.glob(os.path.join(docs_dir, "*.*"))

        for file_path in doc_files:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()

            doc_type = "manual"
            if "troubleshoot" in file_name.lower():
                doc_type = "troubleshooting"
            elif "sop" in file_name.lower() or "maint" in file_name.lower() or "safety" in file_name.lower():
                doc_type = "maintenance_sop"

            content = ""
            if file_ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
                    content = "\n\n".join(pages_text)
                except Exception:
                    continue
            else:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

            if not content.strip():
                continue

            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 20]
            for idx, p in enumerate(paragraphs):
                self.chunks.append({
                    "id": f"{file_name}_{idx}",
                    "file_name": file_name,
                    "doc_type": doc_type,
                    "text": p,
                })

    def search_pgvector(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query PostgreSQL pgvector database for semantic similarity matches"""
        try:
            import psycopg2
            model = self._get_embedding_model()
            if model is None:
                return []
                
            query_embedding = model.encode(query).tolist()
            
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "esp_agent"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                connect_timeout=1
            )
            cur = conn.cursor()
            
            cur.execute("""
                SELECT ki.text_content, d.title, ki.canonical_category,
                       1 - (ke.embedding <=> %s::vector) AS similarity
                FROM knowledge_embeddings ke
                JOIN knowledge_items ki ON ke.knowledge_id = ki.knowledge_id
                JOIN documents d ON ki.document_id = d.document_id
                ORDER BY ke.embedding <=> %s::vector ASC
                LIMIT %s;
            """, (query_embedding, query_embedding, top_k))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            results = []
            for text, source, doc_type, sim in rows:
                results.append({
                    "text": text,
                    "source": source,
                    "doc_type": doc_type or "manual",
                    "score": round(float(sim), 4)
                })
            return results
        except Exception:
            return []

    def search(self, query: str, top_k: int = 3, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches document chunks using local indexed chunks or pgvector semantic search."""
        # If local chunks were explicitly indexed, search local chunks first for unit test compatibility
        if self.chunks:
            query_terms = [t.lower() for t in query.replace(",", " ").replace(">", " ").replace("<", " ").split() if len(t) > 2]
            scored_results = []

            for chunk in self.chunks:
                if doc_type and chunk["doc_type"] != doc_type:
                    continue

                text_lower = chunk["text"].lower()

                if "references" in text_lower or "doi.org" in text_lower or "creative commons" in text_lower or "academic editors" in text_lower:
                    continue

                score = 0.0
                for term in query_terms:
                    if term in text_lower:
                        score += 1.0

                if score > 0:
                    if chunk["doc_type"] == "troubleshooting":
                        score *= 1.5
                    scored_results.append((score, chunk))

            scored_results.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, chunk in scored_results[:top_k]:
                results.append({
                    "text": chunk["text"],
                    "source": chunk["file_name"],
                    "doc_type": chunk["doc_type"],
                    "score": round(score, 2)
                })

            if results:
                return results

        # Try pgvector search
        pg_results = self.search_pgvector(query, top_k=top_k)
        if pg_results:
            return pg_results

        # Fallback if both local and pgvector return empty
        if self.chunks:
            return [{
                "text": chunk["text"],
                "source": chunk["file_name"],
                "doc_type": chunk["doc_type"],
                "score": 0.5
            } for chunk in self.chunks[:top_k]]

        return []

