# ESP APM Knowledge Base Architecture & Technology Guide

> **Target Directory**: `x:\TAS\v2_ESP\esp-knowledge\KB-2` (39 Engineering PDFs, Sizing Manuals, SPE Papers, Troubleshooting Guides)  
> **Audience**: Engineering Team & Operators  
> **Goal**: Explain in simple, plain English how to turn raw technical PDFs into an intelligent, instant question-answering system.

---

## 1. The Core Problem We Are Solving

In the `KB-2` folder, you have 39 high-value technical documents:
* Ampchart analysis & troubleshooting guides
* SPE research papers (e.g. SPE-199091 on ESP failure reduction)
* Total Dynamic Head (TDH) and pump sizing manuals
* Vibration analysis standards and manufacturer bulletins

When an engineer asks:
> *"Why is well FS-031 fluctuating in current with high motor temperature at 52 Hz, and what does the troubleshooting guide recommend?"*

A generic LLM **cannot answer accurately** because:
1. It has never seen your private engineering manuals.
2. If it guesses, it will **hallucinate** wrong pressure values or safety thresholds.
3. It cannot cite the exact document name, page number, and procedure chart.

To solve this, we build a **Retrieval-Augmented Generation (RAG) Knowledge Base**.

---

## 2. The 3 Core Technologies & What Each One Does

Building a smart knowledge base requires three distinct technologies working together like a team:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           1. THE READER (Docas / Docling)               │
│  Converts complex PDFs with tables and columns into clean text         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
┌─────────────────────────────────┐   ┌───────────────────────────────────┐
│ 2. THE SEARCHER (Vector DB)     │   │ 3. THE CONNECTOR (Neo4j Graph)    │
│ Finds matching paragraphs       │   │ Maps cause-and-effect             │
│ by meaning (e.g. "heat" = "temp")│   │ (Symptom -> Cause -> Action)      │
└────────────────┬────────────────┘   └───────────────────┬───────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          4. THE EXPLAINER (Local LLM)                   │
│  Reads the retrieved facts and writes a clear answer with citations     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Technology 1: Document Parsing (Docling / Docas / PyMuPDF)
* **What it is**: The **"Eyes & Reader"** of the system.
* **Why normal text extractors fail**: Engineering PDFs are messy. They have multi-column text, equipment photos, diagrams, and complex tables (e.g., pump head vs. flow rate). A naive reader will scramble columns and ruin tables into unreadable garbage.
* **What Docas / Docling does**:
  - Understands the visual layout of the PDF.
  - Keeps tables intact as clean structured Markdown rows.
  - Recognizes headings (`# Step 4: Total Dynamic Head`).
  - Pulls out captions from charts and pump curves.

---

### Technology 2: Vector Database (Qdrant / Chroma / FAISS)
* **What it is**: The **"Semantic Search Engine"** (Matches by Meaning).
* **How it works**:
  1. We split the clean text from PDFs into small paragraphs (called **Chunks**, usually ~300–500 words).
  2. An **Embedding Model** (a small neural net) converts every chunk into a list of ~384 numbers called a **Vector**.
  3. Vectors that mean similar things are placed close to each other in math space.
* **Why it matters**:
  - If a manual says: *"Motor thermal overload due to low fluid velocity across housing"*.
  - And the operator asks: *"Why is my pump overheating in low flow?"*
  - A traditional keyword search (like `Ctrl + F`) **fails** because "thermal overload" $\neq$ "overheating".
  - A **Vector Database matches them instantly** because it searches by **concept and meaning**, not just exact spelling. It finds the answer in less than 5 milliseconds.

---

### Technology 3: Knowledge Graph (Neo4j / GraphRAG)
* **What it is**: The **"Mind Map of Relationships"** (Cause $\rightarrow$ Effect).
* **Why Vector Search alone is not enough**:
  A vector database finds paragraphs, but it cannot connect dots across 3 different documents.
* **What Neo4j does**:
  It stores knowledge as **Nodes** (things) connected by **Edges** (relationships):
  ```text
  (Gas Interference) ──[causes]──> (Fluctuating Current / Hunting)
  (Fluctuating Current) ──[identified_by]──> (Ampchart Type 3)
  (Gas Interference) ──[mitigated_by]──> (Increase Intake Pressure / Install Gas Separator)
  (API RP 11S) ──[mandates]──> (Maximum allowable backspin protection)
  ```
* **The Magic of combining Vector + Neo4j**:
  - Vector search finds the exact text snippet from the manual.
  - Neo4j traverses the relationship graph to say: *"This symptom is linked to gas locking, which links to pump head drop, which requires procedure SOP-04 from the BP guide."*

---

## 4. Step-by-Step Implementation Pipeline

Here is how we take the 39 PDFs in `esp-knowledge/KB-2` and make them queryable:

### Step 1: Ingestion (Offline Processing — Done Once)
1. **Extract**: Run Docling/Docas on all 39 PDFs in `KB-2`.
2. **Chunk**: Break documents into logical sections (preserving table boundaries).
3. **Embed**: Generate vectors using an embedding model (e.g. `bge-small-en-v1.5` or `all-MiniLM-L6-v2`).
4. **Index**: Store vectors in Qdrant / Chroma along with metadata:
   - `file_name`: e.g. `269941060-ESP-Training-4-Ampchart-Analysis-Troubleshooting-11-Pgs.pdf`
   - `page_number`: e.g. `Page 7`
   - `section_title`: e.g. `Gas Locking vs. Fluid Pound`
5. **Graph Extraction**: Extract equipment components, failure modes, and symptoms into Neo4j nodes and relationships.

---

### Step 2: Live Querying (When User Asks a Question)
1. **User asks**: *"What are the signs of gas locking on an amp chart?"*
2. **Hybrid Retrieval**:
   - Vector DB searches for paragraphs matching "gas locking amp chart signs".
   - Neo4j checks what symptoms connect to `(Gas Locking)`.
3. **Evidence Pack Assembly**: The top 3 most relevant paragraphs + tables are gathered into a clean context pack.
4. **LLM Synthesis**: The local LLM (Qwen2.5 on Server 2) reads the evidence and answers:
   > *"According to **ESP Training 4: Ampchart Analysis (Page 5)**, gas locking exhibits rapid cyclical current swings between underload and normal load as gas pockets pass through the pump stages. Mitigation steps include..."*

---

## 5. Summary Table

| Technology | What it Represents | Plain-English Role | Example in ESP Operations |
| :--- | :--- | :--- | :--- |
| **Docas / Docling** | The Reader | Parses PDFs, preserving tables & headers | Converts a multi-column SPE paper into clean Markdown |
| **Vector DB (Qdrant/Chroma)** | The Searcher | Finds text by meaning in < 5ms | Matches *"pump getting too hot"* to *"thermal trip threshold"* |
| **Neo4j Graph** | The Connector | Maps cause-and-effect relationships | Connects `Low PIP` $\rightarrow$ `Gas Breakout` $\rightarrow$ `Amp Hunting` |
| **Local LLM (Qwen2.5)** | The Explainer | Synthesizes verified text into plain advice | Formats the final answer with page citations |
