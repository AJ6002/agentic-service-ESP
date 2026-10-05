"""
Ingests the static UI Map YAML into PostgreSQL kb_chunks table (Server 184).
Tags records distinctly with source_domain='ui_map' and attaches JSONB metadata.
Idempotent — uses ON CONFLICT (chunk_id) DO UPDATE.
"""

import os
import sys
import json
import yaml
from pathlib import Path

# Add agent_service to path
sys.path.insert(0, os.path.abspath("agent_service"))

from app.stores.postgres_client import get_db_cursor
from app.contracts.ui_map import UiMapEntry

def ingest_ui_map(yaml_path: str = None) -> int:
    if yaml_path is None:
        default_p = Path(__file__).resolve().parent.parent / "config" / "ui_map" / "ui_map.yaml"
        yaml_path = os.environ.get("UI_MAP_PATH", str(default_p))
    
    path_obj = Path(yaml_path)
    if not path_obj.is_file():
        raise FileNotFoundError(f"UI map YAML file not found at: {yaml_path}")
    
    print(f"Reading UI map source from: {path_obj}")
    with open(path_obj, "r", encoding="utf-8") as f:
        raw_items = yaml.safe_load(f)
    
    if not isinstance(raw_items, list):
        raise ValueError("ui_map.yaml root must be a list of entries")
    
    entries = [UiMapEntry.model_validate(item) for item in raw_items]
    print(f"Validated {len(entries)} UiMapEntry items.")

    # 1. Initialize FastEmbed embedder
    from fastembed import TextEmbedding
    print("Initializing FastEmbed (BAAI/bge-small-en-v1.5)...")
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    embed_texts = [
        f"{e.title}\n{e.summary}\n{e.description}\nAliases: {', '.join(e.aliases)}"
        for e in entries
    ]
    embeddings = [emb.tolist() for emb in embedder.embed(embed_texts)]

    # 2. Database connection & schema setup
    with get_db_cursor() as cur:
        # Ensure migration columns and index
        print("Ensuring source_domain and metadata columns on kb_chunks...")
        cur.execute("""
            ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS source_domain VARCHAR(50) DEFAULT 'esp_knowledge';
            ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
            CREATE INDEX IF NOT EXISTS idx_kb_chunks_source_domain ON kb_chunks(source_domain);
        """)

        # Ensure parent document record in kb_documents
        cur.execute("""
            INSERT INTO kb_documents (doc_id, title, tier, source_path)
            VALUES ('DOC-UI-MAP', 'ESP Insight Suite Platform UI Map', 'PLATFORM_METADATA', 'config/ui_map/ui_map.yaml')
            ON CONFLICT (doc_id) DO UPDATE SET
                title = EXCLUDED.title,
                tier = EXCLUDED.tier,
                source_path = EXCLUDED.source_path;
        """)

        # 3. Upsert chunks
        upsert_query = """
            INSERT INTO kb_chunks (
                chunk_id, doc_id, doc_title, section_title, content, token_count, embedding, source_domain, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s::vector, %s, %s::jsonb
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                doc_title = EXCLUDED.doc_title,
                section_title = EXCLUDED.section_title,
                content = EXCLUDED.content,
                token_count = EXCLUDED.token_count,
                embedding = EXCLUDED.embedding,
                source_domain = EXCLUDED.source_domain,
                metadata = EXCLUDED.metadata;
        """

        for entry, emb in zip(entries, embeddings):
            chunk_id = f"ui_map:{entry.id}"
            doc_id = "DOC-UI-MAP"
            doc_title = f"UI Map - {entry.title}"
            section_title = f"{entry.type.upper()}: {entry.title}"
            content = entry.description
            token_count = len(entry.description.split())
            source_domain = "ui_map"
            tier = entry.id.split(".")[0]
            meta_json = json.dumps({
                "id": entry.id,
                "type": tier,
                "contract_type": entry.type,
                "tier": tier,
                "workspace": entry.workspace,
                "path": entry.path,
                "summary": entry.summary,
                "related": entry.related,
                "aliases": entry.aliases,
            })

            cur.execute(
                upsert_query,
                (
                    chunk_id,
                    doc_id,
                    doc_title,
                    section_title,
                    content,
                    token_count,
                    emb,
                    source_domain,
                    meta_json,
                )
            )
            print(f"  [UPSERT] {chunk_id} (type={entry.type}, workspace={entry.workspace})")

    print(f"\nSuccessfully ingested {len(entries)} UI map chunks into PostgreSQL.")
    return len(entries)

if __name__ == "__main__":
    count = ingest_ui_map()
    print(f"Done. Ingested {count} items.")
