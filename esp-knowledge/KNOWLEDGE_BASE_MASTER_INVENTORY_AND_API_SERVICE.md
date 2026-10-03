# ESP APM Knowledge Base — Master Inventory, Architecture & API Service Specification

> **Document Version**: 2.0.0  
> **Status**: Production Grounded Architecture  
> **Location**: `x:\TAS\v2_ESP\esp-knowledge\`  
> **Target Consumer**: Agent Jane V2 / V3 (REST API Gateway Interconnect)  

---

## Part 1: Complete Inventory of `esp-knowledge`

The `esp-knowledge/` directory contains an industrial-grade, multi-tiered knowledge repository specifically curated for Electric Submersible Pump (ESP) operations across the 27 wells in Farha South.

```
esp-knowledge/
├── KB-2/                                # 39 Supplementary Engineering PDFs & Guides
├── sources/raw/                         # 24 Primary Authoritative Foundation Standards
├── deterministic/                       # Deterministic Ground-Truth YAML Registries
│   ├── alerts/seed_alerts.yaml          # Alarm definitions, thresholds, priorities
│   ├── faults/seed_faults.yaml          # 13 primary ESP failure modes & root causes
│   ├── glossary/seed_glossary.yaml      # Oilfield & ESP acronyms (PIP, PDP, TDH, BEP)
│   ├── model_semantics/                # Feature mappings & model boundaries
│   ├── objectives/seed_objectives.yaml  # OP00 through OP14 operational contracts
│   ├── policies/                        # SOT hierarchy & safety scope matrices
│   └── units/canonical_units.yaml       # Oilfield units (psi, bpd, Hz, A, °C, mD)
├── processed/                           # 100% Parsed & Chunked Machine-Readable Assets
│   ├── docling_md/                      # Markdown conversions of KB-1 foundation docs
│   ├── kb2_docling_md/                  # Markdown conversions of KB-2 supplementary docs
│   ├── kb2_tables/                      # Extracted structured engineering tables
│   └── docling_parse_summary.json       # Ingestion audit log & SHA-256 hashes
├── manifests/                           # Reconciliation & Deduplication Manifests
│   └── reconciliation_inventory.json    # Full 63-document taxonomy and trust scoring
└── evaluation/                          # Integrity benchmarks and retrieval test cases
```

---

### 1.1 Document Breakdown & Trust Tiers

Every document in the knowledge base is categorized into an **Authority Hierarchy** so the Agent never cites unverified opinions over approved industry standards:

```
                  LEVEL A: International Standards (API, IEC)
                                      ▲
                                      │
                  LEVEL B: OEM Engineering Bulletins (SLB, Baker, Weatherford)
                                      ▲
                                      │
                  LEVEL C: Academic & SPE Research Papers (SPE-199091, OTC)
                                      ▲
                                      │
                  LEVEL D: Client Field Case Studies & Historical Incidents
```

#### Tier 1: Foundation Standards (`sources/raw/`) — 24 Documents
* **API Standards (American Petroleum Institute)**:
  - `API RP 11S`: Recommended Practice for Operation, Maintenance, and Troubleshooting of ESPs.
  - `API RP 11S1`: Teardown Report & Dismantle Failure Analysis (Root Cause Analysis procedures).
  - `API RP 11S3`: Electric Submersible Pump Installations.
  - `API RP 11S4`: Sizing and Selection of Electric Submersible Pump Systems.
  - `API RP 11S6`: Testing of Electric Submersible Pump Cables.
  - `API RP 11S8`: Recommended Practice for Vibration of ESP Units.
* **IEC Electrical Standards**:
  - `IEC 60034-14 (1998 & 2018)`: Mechanical Vibration of Rotating Electrical Machines.
  - `IEC TS 60034-25`: Guidance for converter-supplied AC cage induction motors.
* **Textbooks & Engineering Models**:
  - `Takacs_ESP_Manual_2nd_Ed.pdf`: Gabor Takacs' authoritative textbook on ESP hydraulics and electrical design.
  - `Takacs_TDH_Calculation_Models_2020.pdf`: Analytical pressure gradient & total dynamic head equations.
* **OEM Bulletins & Guidelines**:
  - `Baker_Hughes_FusionPro_Manual.pdf`: Baker Hughes Centrilift drive and sensor thresholds.
  - `Weatherford_ESP_Application_Guide.pdf`: Weatherford ESP handling & sizing guidelines.
  - `SLB_Defining_ESP.pdf`: Schlumberger technical ESP terminology.
  - `BP_ESP_Troubleshooting_Guidelines.pdf`: BP operational troubleshooting flows.

#### Tier 2: Operational & Troubleshooting Repository (`KB-2/`) — 39 Documents
* **Ampchart Signature Analysis**:
  - `269941060-ESP-Training-4-Ampchart-Analysis-Troubleshooting-11-Pgs.pdf`: Cyclic hunting, gas lock, underload curves.
* **Field Incident Case Studies & SPE Papers**:
  - `725133886-SPE-199091-MS`: Electric Submersible Pump Troubleshooting Guide (System performance & failure prevention).
  - `728680985-24-Well-Troubleshooting-Cases.pdf`: 24 real-world field case studies detailing symptom $\rightarrow$ intervention.
  - `802296155-Electric-Submersible-Pump-Vibration-Anal.pdf`: Downhole vibration signatures and bearing failure patterns.
  - `449589170-Risk-Analysis-in-ESP-Failure-1-0.pdf`: Run-life risk analysis and mean-time-between-failure (MTBF).
* **Pump Sizing & Total Dynamic Head (TDH)**:
  - `442719745-ESP-design-Step-4-Total-Dynamic-Head.pdf`: Step-by-step TDH math models.
  - `684188721-ESP-Standard-Sizing.pdf`: Engineering sizing manual.
* **Quarantine & Deduplication**:
  - 2 duplicates merged with KB-1 foundation (`BP Guidelines` and `Defining ESP`).
  - 1 off-topic file quarantined (`Automatic Bulk Weighing System.pdf` — dry bulk weighing, not downhole ESP).

#### Tier 3: Deterministic Ground-Truth (`deterministic/`)
Structured YAML files that provide 100% deterministic rules (zero LLM hallucination):
* `faults/seed_faults.yaml`: 13 primary ESP failure modes (Gas Locking, Fluid Pound, Sand Abrasion, Broken Shaft, Asphaltene Deposition, Electrical Insulation Breakdown, Overload, Underload, Gas Interference, Scale Deposition, High Backpressure, Mechanical Seal Failure, Power Cable Failure).
* `objectives/seed_objectives.yaml`: Strict tool-calling schema for OP00 through OP14.
* `units/canonical_units.yaml`: Conversion factors between field units (psi, bar, kPa, bpd, m3/d, Hz, RPM).

---

## Part 2: Autonomous Knowledge Base Microservice (`esp-kb-service`)

### 2.1 Dedicated Port & Gateway Architecture
* **Host**: Server 3 (`192.168.1.184`)
* **Port**: **`8085`** (Dedicated service isolated from SCADA `:8090`)
* **Design Rule**: The Agent **never** builds URLs. It calls tools through the **Tool Gateway `kb` adapter**.

```text
┌──────────────────────────────────────────────────┐
│           ESP Agent Service (191)                │
│            └ Tool Gateway                        │
│               └ kb adapter                       │
└────────────────────┬─────────────────────────────┘
                     │ HTTP via adapter
                     ▼
┌──────────────────────────────────────────────────┐
│           ESP KB Service (184, :8085)            │
│                                                  │
│  POST /api/kb/search       (semantic)            │
│  POST /api/kb/graph/trace  (cause-effect path)   │
│  GET  /api/kb/faults/{id}  (taxonomy)            │
│  GET  /api/kb/standards/{id} (API/IEC clause)    │
│  GET  /health              (liveness)            │
└────────┬───────────────────────────┬─────────────┘
         ▼                           ▼
  [ Qdrant ]                    [ Neo4j ]
  vectors                        graph
```

### 2.2 Tool Gateway Configuration
```yaml
# config/tools.yaml
search_knowledge:
  adapter: kb
  method: POST
  url: "http://192.168.1.184:8085/api/kb/search"
  args:
    query: { type: string, required: true }
    top_k: { type: int, required: false, default: 5 }
  returns:
    hits: list
```

### 2.3 Evidence Pack Strict Response Contract
Every KB response provides the exact metadata the Evidence Pack and XAI layer require:

```json
{
  "hits": [
    {
      "doc_id": "OEM-Borets-B400-400",
      "section": "3.2.1",
      "revision": "2019-04",
      "authority": "OEM",
      "applicability": ["B400-400", "B400-500"],
      "page": 42,
      "snippet": "Underload protection trips when motor load falls below...",
      "score": 0.87
    }
  ]
}
```
* **`authority`**: Distinguishes international standards (`LEVEL_A`), OEM manuals (`LEVEL_B`), and research papers (`LEVEL_C`).
* **`revision` & `page`**: Provides auditability for XAI citations.
* **`applicability`**: Ensures the pump model on the well matches the cited equipment manual.

---

#### 2. Knowledge Graph Relationship Traversal Endpoint
* **Method**: `POST /api/kb/graph/trace`
* **Purpose**: Navigates cause-and-effect paths through Neo4j to find verified SOPs.
* **Request Body**:
```json
{
  "symptom_ids": ["high_motor_temperature", "fluctuating_current"],
  "observed_parameters": {
    "frequency_hz": 52.0,
    "pip_psi": 142.0
  }
}
```
* **Response Body**:
```json
{
  "possible_faults": [
    {
      "fault_id": "FAULT_001_GAS_LOCKING",
      "fault_name": "Gas Interference / Gas Locking",
      "confidence": 0.88,
      "chain": [
        "Low Intake Pressure (142 psi < Bubble Point 280 psi)",
        "Gas Breakout at Pump Intake",
        "Fluid Density Fluctuations inside Impellers",
        "Cyclic Motor Underload / Hunting"
      ],
      "recommended_sop": {
        "sop_id": "SOP_ESP_04_GAS_MITIGATION",
        "standard_ref": "API RP 11S Section 5.4",
        "action": "Increase casing backpressure or reduce frequency by 2-3 Hz to prevent motor overheating"
      }
    }
  ]
}
```

---

#### 3. Deterministic Fault Taxonomy Endpoint
* **Method**: `GET /api/kb/faults/{fault_id}`
* **Purpose**: Fetches the mathematically verified physical limits and indicators without using an LLM.
* **Response Body**:
```json
{
  "fault_id": "FAULT_003_UNDERLOAD_PUMP_OFF",
  "name": "Underload / Fluid Pound",
  "symptoms": ["Current drop > 25% below nominal", "Zero liquid production", "Rapid motor temperature rise"],
  "criticality": "HIGH",
  "auto_trip_delay_sec": 30,
  "applicable_manual": "API RP 11S1 Section 4"
}
```

---

## Part 3: Step-by-Step Deployment Roadmap

### Phase 1: Ingestion & Vector Indexing
1. Run pre-processing script on `esp-knowledge/KB-2/` and `sources/raw/`.
2. Convert all PDFs to structured JSON and Markdown using Docling.
3. Compute dense vector embeddings using `sentence-transformers/all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5`.
4. Store in local Qdrant vector database on Server 2 (`192.168.1.191:6333`).

### Phase 2: Knowledge Graph Population in Neo4j
1. Load `deterministic/faults/seed_faults.yaml` and `seed_alerts.yaml` into Neo4j nodes.
2. Link documents to faults: `(:Document)-[:DIAGNOSES]->(:Fault)-[:REQUIRES]->(:SOP)`.

### Phase 3: Launch FastAPI Microservice
1. Deploy `esp-kb-service` on port `8085` under systemd.
2. In Agent Jane's `.env`, configure:
   `KB_SERVICE_URL=http://192.168.1.191:8085`
3. Agent Jane simply calls `POST /api/kb/search` whenever the user asks technical, procedure, or diagnostic questions.
