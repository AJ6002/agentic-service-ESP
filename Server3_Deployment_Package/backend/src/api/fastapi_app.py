import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.api.rest.bff_routes import router as bff_router

app = FastAPI(
    title="Knowledge-Base-Agnostic Diagnostic Agent API",
    description="REST API for domain-agnostic industrial equipment diagnostic agent",
    version="1.0.0",
)

# Enable CORS for Next.js web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount BFF UI router for agent dock, workspace, and evidence stream
app.include_router(bff_router)

# In-memory store for registered knowledge bases and execution runs
REGISTERED_KNOWLEDGE_BASES: Dict[str, str] = {
    "esp": "knowledge_bases/esp"
}
DIAGNOSTIC_RUNS: Dict[str, Dict[str, Any]] = {}


class RegisterKBRequest(BaseModel):
    kb_id: str = Field(..., description="Unique ID for the knowledge base")
    kb_path: str = Field(..., description="Local path to knowledge base directory")


class DiagnoseRequest(BaseModel):
    user_query: str = Field(..., description="Diagnostic query or symptom description")
    asset_id: str = Field(..., description="ID of the target asset")
    kb_id: str = Field("esp", description="Knowledge base ID to use")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "registered_kbs_count": len(REGISTERED_KNOWLEDGE_BASES),
        "total_runs_count": len(DIAGNOSTIC_RUNS),
    }


@app.get("/knowledge-bases")
def list_knowledge_bases():
    return {"registered_knowledge_bases": REGISTERED_KNOWLEDGE_BASES}


@app.post("/knowledge-bases/register")
def register_knowledge_base(req: RegisterKBRequest):
    REGISTERED_KNOWLEDGE_BASES[req.kb_id] = req.kb_path
    return {"status": "success", "kb_id": req.kb_id, "kb_path": req.kb_path}


from src.agent.supervisor.user_entry import UserEntryAdapter
from src.schemas.advisory import StandardAdvisoryPayload

@app.post("/diagnose")
def run_diagnosis(req: DiagnoseRequest):
    try:
        adapter = UserEntryAdapter()
        adv = adapter.run(
            user_query=req.user_query,
            asset_id=req.asset_id
        )
        run_id = str(uuid.uuid4())
        run_record = {
            "run_id": run_id,
            "user_query": req.user_query,
            "asset_id": req.asset_id,
            "kb_id": req.kb_id,
            "result": adv.model_dump() if hasattr(adv, "model_dump") else dict(adv),
        }
        DIAGNOSTIC_RUNS[run_id] = run_record
        return run_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/advisory", response_model=StandardAdvisoryPayload)
def generate_advisory(req: DiagnoseRequest):
    """
    Generate Standard Advisory Response complying with Guidelines.pdf Appendix C.
    Executes through UserEntryAdapter and LangGraph supervisor.
    """
    try:
        adapter = UserEntryAdapter()
        return adapter.run(
            user_query=req.user_query,
            asset_id=req.asset_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diagnose/{run_id}")
def get_diagnosis_result(run_id: str):
    if run_id not in DIAGNOSTIC_RUNS:
        raise HTTPException(status_code=404, detail=f"Run ID '{run_id}' not found.")
    return DIAGNOSTIC_RUNS[run_id]


# ── Phase 3 Knowledge Service Routes ──────────────────────────────────────────

from src.services.retrieval_service import RetrievalService
_retrieval = RetrievalService()


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language or keyword query")
    top_k: int = Field(5, ge=1, le=20)
    authority_filter: Optional[str] = Field(None, description="Max authority level to include: A B C D E F")


@app.post("/knowledge/search")
def knowledge_search(req: KnowledgeSearchRequest):
    """Hybrid KB search: BM25 + pgvector + authority sort (Sprint 3.9)"""
    result = _retrieval.hybrid_retrieve(req.query, top_k=req.top_k, authority_filter=req.authority_filter)
    return result


@app.post("/knowledge/search-faults")
def knowledge_search_faults(req: KnowledgeSearchRequest):
    """Structured fault object lookup (Sprint 3.6)"""
    faults = _retrieval.search_fault_taxonomy(req.query)
    return {"query": req.query, "fault_matches": faults, "count": len(faults)}


class CaseSearchRequest(BaseModel):
    symptom_query: str
    top_k: int = Field(3, ge=1, le=10)


@app.post("/cases/search-similar")
def cases_search_similar(req: CaseSearchRequest):
    """Historical case similarity search (Sprint 3.7)"""
    cases = _retrieval.search_similar_cases(req.symptom_query, top_k=req.top_k)
    return {"symptom_query": req.symptom_query, "similar_cases": cases, "count": len(cases)}


@app.get("/knowledge/pump-curve/{pump_model:path}")
def knowledge_get_pump_curve(pump_model: str):
    """Exact pump curve lookup by model name (Sprint 3.8)"""
    curve = _retrieval.get_pump_curve(pump_model)
    if not curve:
        raise HTTPException(status_code=404, detail=f"No pump curve found for model: {pump_model}")
    return curve
