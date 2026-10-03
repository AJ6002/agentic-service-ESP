"""
Unified PostgreSQL Knowledge Base Ingestion Script.
Ingests all authoritative standards, manuals, deterministic faults, alerts, and causal graphs
from esp-knowledge/ into esp_apm_db (PostgreSQL 16 + pgvector).
"""

import os
import re
import sys
import glob
import yaml
import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from fastembed import TextEmbedding

DB_URL = os.getenv("DATABASE_URL", "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db")
KNOWLEDGE_ROOT = Path("A:/TAS-AI/ESP/esp-knowledge")
TAXONOMY_MAP = Path("A:/TAS-AI/ESP/agent_service/config/fault_taxonomy_mapping.yaml")

# Garbage section patterns to filter out of vector search:
GARBAGE_PATTERNS = [
    re.compile(r"(?i)^\s*x?\s*contents?\s*$"),
    re.compile(r"(?i)^table\s+of\s+contents"),
    re.compile(r"(?i)^preface"),
    re.compile(r"(?i)^(index|glossary)\s*$"),
    re.compile(r"(?i)Final\s+Revision\s+\d+\s+\d{1,2}\w*\s+\w+\s+\d{4}"),
    re.compile(r"(?i)<!-- Page 1 -->"),
]

def is_garbage(text: str, title: str) -> bool:
    if len(text.strip()) < 40:
        return True
    for p in GARBAGE_PATTERNS:
        if p.search(title) or p.search(text[:150]):
            return True
    return False

def create_kb_tables(cur):
    print("--- 1. Creating Knowledge Base Tables in PostgreSQL ---")
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS kb_documents (
            doc_id VARCHAR(100) PRIMARY KEY,
            title TEXT NOT NULL,
            tier VARCHAR(30),
            source_path TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS kb_chunks (
            chunk_id VARCHAR(120) PRIMARY KEY,
            doc_id VARCHAR(100) REFERENCES kb_documents(doc_id) ON DELETE CASCADE,
            doc_title TEXT,
            section_title TEXT,
            content TEXT NOT NULL,
            token_count INT,
            embedding vector(384),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_kb_chunks_doc ON kb_chunks(doc_id);
        
        CREATE TABLE IF NOT EXISTS kb_fault_taxonomy (
            fault_id VARCHAR(60) PRIMARY KEY,
            fault_class VARCHAR(60) NOT NULL,
            category VARCHAR(30),
            preferred_name TEXT NOT NULL,
            synonyms JSONB,
            canonical_metric TEXT,
            symptoms JSONB,
            contributing_factors JSONB,
            evidence_required JSONB,
            severity_range VARCHAR(50),
            escalation TEXT,
            troubleshooting_steps JSONB,
            source TEXT
        );

        CREATE TABLE IF NOT EXISTS kb_causal_edges (
            from_node VARCHAR(100),
            to_node VARCHAR(100),
            relationship VARCHAR(40),
            confidence REAL DEFAULT 1.0,
            PRIMARY KEY (from_node, to_node)
        );

        CREATE TABLE IF NOT EXISTS kb_glossary (
            term VARCHAR(60) PRIMARY KEY,
            category VARCHAR(40),
            preferred_label TEXT,
            definition TEXT,
            acronym_for TEXT,
            typical_range TEXT
        );

        CREATE TABLE IF NOT EXISTS kb_alerts (
            alert_id VARCHAR(60) PRIMARY KEY,
            parameter TEXT,
            severity VARCHAR(20),
            condition TEXT,
            threshold_display TEXT,
            potential_causes JSONB,
            recommended_action TEXT
        );
    """)
    print("KB tables created successfully.")

def ingest_deterministic_registries(conn, cur):
    print("\n--- 2. Ingesting Deterministic Registries ---")
    
    # 2.1 Faults from seed_faults.yaml
    faults_yaml = KNOWLEDGE_ROOT / "deterministic" / "faults" / "seed_faults.yaml"
    if faults_yaml.exists():
        with open(faults_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            fault_list = data.get("faults", [])
            for f_item in fault_list:
                fid = f_item.get("fault_id")
                fclass = fid.replace("-", "_").upper()
                cur.execute("""
                    INSERT INTO kb_fault_taxonomy (
                        fault_id, fault_class, category, preferred_name, synonyms,
                        canonical_metric, symptoms, contributing_factors, evidence_required,
                        severity_range, escalation, source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fault_id) DO UPDATE SET
                        fault_class = EXCLUDED.fault_class,
                        preferred_name = EXCLUDED.preferred_name,
                        symptoms = EXCLUDED.symptoms,
                        contributing_factors = EXCLUDED.contributing_factors;
                """, (
                    fid, fclass, f_item.get("category"), f_item.get("preferred_name"),
                    json.dumps(f_item.get("synonyms", [])), f_item.get("canonical_metric"),
                    json.dumps(f_item.get("symptoms", [])), json.dumps(f_item.get("contributing_factors", [])),
                    json.dumps(f_item.get("evidence_required", [])), f_item.get("severity_range"),
                    f_item.get("escalation"), f_item.get("source")
                ))

                # Build Causal Edges (Symptom -> Fault)
                for symp in f_item.get("symptoms", []):
                    cur.execute("""
                        INSERT INTO kb_causal_edges (from_node, to_node, relationship, confidence)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (from_node, to_node) DO NOTHING;
                    """, (symp, fid, "INDICATES", 0.95))

            print(f"Ingested {len(fault_list)} deterministic fault definitions & causal edges.")

    # 2.1b Taxonomy Mappings from fault_taxonomy_mapping.yaml
    if TAXONOMY_MAP.exists():
        with open(TAXONOMY_MAP, "r", encoding="utf-8") as f:
            tdata = yaml.safe_load(f) or {}
            mappings = tdata.get("mappings", {})
            for m_cls, m_val in mappings.items():
                primary_id = m_val.get("primary_fault_id", m_cls)
                symptoms = m_val.get("symptoms", [])
                for s in symptoms:
                    cur.execute("""
                        INSERT INTO kb_causal_edges (from_node, to_node, relationship, confidence)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (from_node, to_node) DO NOTHING;
                    """, (s, primary_id, "INDICATES", 0.90))
            print(f"Ingested {len(mappings)} taxonomy mapping relationships into causal DAG.")

    # 2.2 Alerts
    alerts_yaml = KNOWLEDGE_ROOT / "deterministic" / "alerts" / "seed_alerts.yaml"
    if alerts_yaml.exists():
        with open(alerts_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            alerts_list = data.get("alerts", [])
            for a_item in alerts_list:
                cur.execute("""
                    INSERT INTO kb_alerts (
                        alert_id, parameter, severity, condition, threshold_display,
                        potential_causes, recommended_action
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (alert_id) DO UPDATE SET
                        severity = EXCLUDED.severity,
                        recommended_action = EXCLUDED.recommended_action;
                """, (
                    a_item.get("alert_id"), a_item.get("parameter"), a_item.get("severity"),
                    a_item.get("condition"), a_item.get("threshold_display"),
                    json.dumps(a_item.get("potential_causes", [])), a_item.get("recommended_action")
                ))
            print(f"Ingested {len(alerts_list)} deterministic alerts.")

    # 2.3 Glossary
    glossary_yaml = KNOWLEDGE_ROOT / "deterministic" / "glossary" / "seed_glossary.yaml"
    if glossary_yaml.exists():
        with open(glossary_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            terms = data.get("terms", [])
            for t_item in terms:
                term_name = t_item.get("term_id") or t_item.get("term")
                if not term_name:
                    continue
                cur.execute("""
                    INSERT INTO kb_glossary (
                        term, category, preferred_label, definition, acronym_for, typical_range
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (term) DO UPDATE SET
                        definition = EXCLUDED.definition;
                """, (
                    term_name, t_item.get("domain") or t_item.get("category"),
                    t_item.get("preferred_name") or t_item.get("preferred_label"),
                    t_item.get("definition"),
                    t_item.get("acronym_for") or (", ".join(t_item.get("synonyms", []))),
                    t_item.get("unit") or t_item.get("typical_range")
                ))
            print(f"Ingested {len(terms)} glossary acronyms & definitions.")

    conn.commit()

def chunk_markdown_file(file_path: Path, max_chars: int = 800) -> list[tuple[str, str]]:
    """Splits markdown file by headers and size into (section_title, text_chunk)."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines()
    chunks = []
    current_section = file_path.stem.replace("_", " ")
    buffer = []

    for line in lines:
        if line.startswith("#"):
            if buffer:
                chunk_text = "\n".join(buffer).strip()
                if not is_garbage(chunk_text, current_section):
                    chunks.append((current_section, chunk_text))
                buffer = []
            current_section = line.lstrip("#").strip()
        else:
            buffer.append(line)
            if sum(len(l) for l in buffer) >= max_chars:
                chunk_text = "\n".join(buffer).strip()
                if not is_garbage(chunk_text, current_section):
                    chunks.append((current_section, chunk_text))
                buffer = buffer[-2:] # 2-line overlap

    if buffer:
        chunk_text = "\n".join(buffer).strip()
        if not is_garbage(chunk_text, current_section):
            chunks.append((current_section, chunk_text))

    return chunks

def ingest_vector_documents(conn, cur):
    print("\n--- 3. Ingesting & Embedding Authoritative Markdown Documents ---")
    embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    md_dirs = [
        KNOWLEDGE_ROOT / "processed" / "docling_md",
        KNOWLEDGE_ROOT / "processed" / "kb2_docling_md"
    ]
    
    all_files = []
    for d in md_dirs:
        if d.exists():
            all_files.extend(list(d.glob("*.md")))
            
    print(f"Found {len(all_files)} markdown document files.")
    
    total_chunks = 0
    for doc_idx, file_path in enumerate(all_files, 1):
        doc_id = f"DOC-{file_path.stem[:40]}"
        doc_title = file_path.stem.replace("_", " ")
        tier = "TIER_1_STANDARD" if "docling_md" in str(file_path) else "TIER_2_OEM_GUIDE"
        
        # Insert Doc
        cur.execute("""
            INSERT INTO kb_documents (doc_id, title, tier, source_path)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (doc_id) DO UPDATE SET title = EXCLUDED.title;
        """, (doc_id, doc_title, tier, str(file_path.name)))
        
        chunks = chunk_markdown_file(file_path)
        if not chunks:
            continue
            
        texts_to_embed = [c[1] for c in chunks]
        embeddings = list(embed_model.embed(texts_to_embed))
        
        records = []
        for i, ((sec_title, chunk_content), emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}-C{i:04d}"
            emb_list = [float(x) for x in emb]
            records.append((
                chunk_id, doc_id, doc_title, sec_title, chunk_content,
                len(chunk_content.split()), emb_list
            ))
            
        execute_values(cur, """
            INSERT INTO kb_chunks (
                chunk_id, doc_id, doc_title, section_title, content, token_count, embedding
            ) VALUES %s
            ON CONFLICT (chunk_id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding;
        """, records, template="(%s, %s, %s, %s, %s, %s, %s::vector)")
        
        total_chunks += len(records)
        conn.commit()
        print(f"[{doc_idx}/{len(all_files)}] Ingested {doc_id}: {len(records)} chunks")

    print(f"\nTotal Chunks Ingested and Embedded: {total_chunks}")
    print("Building HNSW vector cosine index in PostgreSQL...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_kb_chunks_vector ON kb_chunks USING hnsw (embedding vector_cosine_ops);")
    conn.commit()
    print("HNSW Index Created Successfully.")

def main():
    print(f"Connecting to PostgreSQL at {DB_URL} ...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    create_kb_tables(cur)
    ingest_deterministic_registries(conn, cur)
    ingest_vector_documents(conn, cur)
    
    conn.close()
    print("\n=== KNOWLEDGE BASE INGESTION TO POSTGRESQL COMPLETE ===")

if __name__ == "__main__":
    main()
