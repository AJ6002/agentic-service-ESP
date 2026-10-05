---
title: "feat: Ingest UI Map YAML into Postgres KB with distinct source_domain (Sprint 4)"
type: feat
status: draft
date: 2026-10-05
repo: agent_service
branch_base: feat/ui-route-context
---

# Sprint 4 — Agent Ingestion Path Plan

## 1. Executive Summary & Objective

The goal of **Sprint 4** is to establish the agent's ingestion and indexing path for the static platform self-model (`ui_map.yaml`). 
We will:
1. Establish the agent working-copy location in `agent_service/config/ui_map/ui_map.yaml`.
2. Ensure PostgreSQL `kb_chunks` supports `source_domain` (tagging UI map chunks as `ui_map` vs default `esp_knowledge`) and `metadata` (JSONB).
3. Implement an idempotent Python ingestion script `agent_service/scripts/ingest_ui_map_to_postgres.py` that validates entries via `UiMapEntry`, computes 384-d embeddings using `FastEmbed (BAAI/bge-small-en-v1.5)`, and upserts entries into PostgreSQL.
4. Ingest the 3 sample entries (`route.working-status`, `component.subsystem-equalizer`, `concept.tdh`).
5. Empirically verify distinct tagging, retrievability via vector search, and strict domain isolation (zero cross-contamination with the 7,752 ESP domain chunks).

> [!NOTE]
> **Out of Scope for Sprint 4**:
> - Does **not** add the OP15 objective (Sprint 6).
> - Does **not** add the `ui_map` tool adapter (Sprint 5).
> - Does **not** modify the router (Sprint 7).
> - Does **not** implement automated cross-repo sync (Sprint 9).

---

## 2. Architectural Analysis & Schema Grounding

### 2.1 Current PostgreSQL Schema (`esp_apm_db`)
In PostgreSQL on Server 184:
- `kb_documents`: `(doc_id PK, title, tier, source_path, created_at)`
- `kb_chunks`: `(chunk_id PK, doc_id FK -> kb_documents, doc_title, section_title, content, token_count, embedding vector(384), created_at)`
  * *Foreign Key constraint*: `doc_id` references `kb_documents(doc_id) ON DELETE CASCADE`.

### 2.2 Schema Additions for Multi-Domain KB
To support distinct tagging without disrupting existing queries:
```sql
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS source_domain VARCHAR(50) DEFAULT 'esp_knowledge';
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_kb_chunks_source_domain ON kb_chunks(source_domain);
```
- Existing 7,752 chunks are tagged `esp_knowledge`.
- Ingested UI map chunks will be tagged `source_domain = 'ui_map'`.
- A root document record `DOC-UI-MAP` will be ensured in `kb_documents` (`tier='PLATFORM_METADATA'`) to satisfy foreign key integrity.

---

## 3. Implementation Plan & Tasks

### Task 4.1 — Create the Working-Copy Location
- **Path**: `agent_service/config/ui_map/ui_map.yaml`
- **Action**: Create directory `agent_service/config/ui_map/` and populate `ui_map.yaml` with the 3 canonical sample entries:
  1. `route.working-status` (type: route, workspace: operations, path: `/working-status`)
  2. `component.subsystem-equalizer` (type: component, workspace: operations)
  3. `concept.tdh` (type: concept, workspace: platform)

### Task 4.2 — Implement Ingestion Script
- **Path**: `agent_service/scripts/ingest_ui_map_to_postgres.py`
- **Logic**:
  1. Connect to PostgreSQL using `app.stores.postgres_client.get_db_cursor()`.
  2. Ensure migration columns (`source_domain`, `metadata`) and indices exist.
  3. Upsert parent document in `kb_documents` with `doc_id = 'DOC-UI-MAP'`, `title = 'ESP Insight Suite Platform UI Map'`, `tier = 'PLATFORM_METADATA'`.
  4. Load YAML from `agent_service/config/ui_map/ui_map.yaml`.
  5. Validate each record using `app.contracts.ui_map.UiMapEntry`.
  6. Compute 384-d vector embeddings using `FastEmbed (BAAI/bge-small-en-v1.5)` over combined text:
     ```python
     embed_text = f"{entry.title}\n{entry.summary}\n{entry.description}\nAliases: {', '.join(entry.aliases)}"
     ```
  7. Construct payload:
     - `chunk_id`: `f"ui_map:{entry.id}"`
     - `doc_id`: `"DOC-UI-MAP"`
     - `doc_title`: `f"UI Map - {entry.title}"`
     - `section_title`: `f"{entry.type.upper()}: {entry.title}"`
     - `content`: `entry.description`
     - `token_count`: rough word/token estimate
     - `embedding`: 384-d vector
     - `source_domain`: `'ui_map'`
     - `metadata`: `{ "id": entry.id, "type": entry.type, "workspace": entry.workspace, "path": entry.path, "summary": entry.summary, "related": entry.related, "aliases": entry.aliases }`
  8. Execute idempotent upsert:
     ```sql
     INSERT INTO kb_chunks (chunk_id, doc_id, doc_title, section_title, content, token_count, embedding, source_domain, metadata)
     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
     ON CONFLICT (chunk_id) DO UPDATE SET
         doc_title = EXCLUDED.doc_title,
         section_title = EXCLUDED.section_title,
         content = EXCLUDED.content,
         token_count = EXCLUDED.token_count,
         embedding = EXCLUDED.embedding,
         source_domain = EXCLUDED.source_domain,
         metadata = EXCLUDED.metadata;
     ```

### Task 4.3 — Run Ingestion & Verify Database Rows
- Execute: `python agent_service/scripts/ingest_ui_map_to_postgres.py`
- Direct SQL query:
  ```sql
  SELECT chunk_id, source_domain, LEFT(content, 60)
  FROM kb_chunks
  WHERE source_domain = 'ui_map';
  ```
- **Expectation**: Exactly 3 rows returned with `source_domain = 'ui_map'`.

### Task 4.4 — Verify Semantic Retrievability & Domain Isolation
- Create verification test/script `agent_service/scripts/verify_ui_map_retrieval.py` and unit test `agent_service/tests/test_ui_map_retrieval.py`.
- **Query 1**: `"subsystem equalizer"` -> `component.subsystem-equalizer` appears as top hit.
- **Query 2**: `"gas lock"` -> returns ESP domain chunks (`source_domain = 'esp_knowledge'`), does **not** return `ui_map` entries.
- **Query 3**: `"total dynamic head"` -> matches `concept.tdh`.

### Task 4.5 — Tag Discreteness & Idempotency Check
- Run count checks:
  ```sql
  SELECT COUNT(*) FROM kb_chunks WHERE source_domain = 'ui_map';     -- Expect 3
  SELECT COUNT(*) FROM kb_chunks WHERE source_domain != 'ui_map';    -- Expect 7,752
  ```
- Re-run `ingest_ui_map_to_postgres.py`:
  - Verify count remains exactly 3 (no duplication, 0 growth).

---

## 4. Acceptance & Exit Criteria

| # | Criterion | Verification Method | Expected Outcome |
|---|---|---|---|
| 1 | Working-copy location | `Test-Path agent_service/config/ui_map/ui_map.yaml` | YAML file exists with 3 valid entries |
| 2 | Ingestion script execution | Run `ingest_ui_map_to_postgres.py` | Exits with code 0 without exceptions |
| 3 | Database tag check | `SELECT COUNT(*) FROM kb_chunks WHERE source_domain = 'ui_map'` | Exactly 3 rows |
| 4 | Semantic search | Vector search for "subsystem equalizer" | Top hit is `component.subsystem-equalizer` |
| 5 | Domain separation | Vector search for "gas lock" | Zero UI map chunks in top results |
| 6 | Idempotency | Re-run ingestion script | `ui_map` row count remains 3 |

---

## 5. Artifacts to Create / Touch

- [ui_map.yaml](file:///a:/TAS-AI/ESP/agent_service/config/ui_map/ui_map.yaml) (new working copy)
- [ingest_ui_map_to_postgres.py](file:///a:/TAS-AI/ESP/agent_service/scripts/ingest_ui_map_to_postgres.py) (new ingestion script)
- [test_ui_map_ingestion.py](file:///a:/TAS-AI/ESP/agent_service/tests/test_ui_map_ingestion.py) (automated regression tests)
- [verify_ui_map_retrieval.py](file:///a:/TAS-AI/ESP/agent_service/scripts/verify_ui_map_retrieval.py) (standalone verification runner)
- `reports/SPRINT_4_UI_MAP_INGESTION_VERIFICATION_REPORT.txt` (full raw output report)
