"""
Knowledge Domain Specialist Subgraph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class KnowledgeState(TypedDict):
    input: Dict[str, Any]
    citations: List[Dict[str, Any]]
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_knowledge_graph():
    """Build and compile the Knowledge domain specialist subgraph."""
    retrieval_service = RetrievalService()

    builder = StateGraph(KnowledgeState)

    def formulate_queries_node(state: KnowledgeState) -> Dict[str, Any]:
        inp = state["input"]
        query_text = inp.get("task", "ESP production decline intake pressure drawdown procedure")
        return {"findings": [f"Knowledge search initiated for query: '{query_text[:50]}'"]}

    def search_kb_node(state: KnowledgeState) -> Dict[str, Any]:
        inp = state["input"]
        query_text = inp.get("task", "ESP intake pressure drawdown procedure")

        # 1. Deterministic Procedure Knowledge (Authority Rank 1, <1ms)
        try:
            from src.services.procedure_knowledge import procedure_knowledge_service
            adv_info = procedure_knowledge_service.format_advisory_text(query_text, inp.get("asset_id", ""))
            if adv_info.get("citations"):
                citations = [
                    {
                        "doc_id": c["document_id"],
                        "title": c.get("section", "Operating Limits"),
                        "authority_rank": 1 if c.get("authority_level") == "A" else 2,
                        "text": adv_info["assessment"][:200]
                    }
                    for c in adv_info["citations"]
                ]
                evidence = [f"esp:kb:{c['document_id']}" for c in adv_info["citations"]]
                return {"citations": citations, "evidence_refs": evidence}
        except Exception:
            pass

        try:
            res_dict = retrieval_service.hybrid_retrieve(query=query_text, top_k=3)
            raw_citations = res_dict.get("vector_results", []) or res_dict.get("fault_matches", [])
        except Exception as ex:
            logger.warning(f"Hybrid retrieval failed: {ex}")
            raw_citations = []

        citations = []
        evidence = []

        for item in raw_citations:
            c_dict = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            citations.append(c_dict)
            doc_id = c_dict.get("document_id") or c_dict.get("doc_id") or "KB"
            page_num = c_dict.get("page", 1)
            evidence.append(f"esp:kb:{doc_id}:p{page_num}")

        return {"citations": citations, "evidence_refs": evidence}

    def apply_authority_filter_node(state: KnowledgeState) -> Dict[str, Any]:
        citations = state["citations"]
        sorted_citations = sorted(citations, key=lambda x: x.get("authority_rank", 99))

        findings = []
        for c in sorted_citations[:2]:
            findings.append(f"KB Citation [{c.get('doc_id', 'SOP')}] (Rank {c.get('authority_rank', 1)}): {c.get('text', '')[:120]}")

        output = SpecialistOutput(
            specialist_id="knowledge",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=[],
            next_verification=["Verify citation against field SOP document version"],
            completion_reason="Grounded knowledge retrieval completed"
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("formulate_queries", formulate_queries_node)
    builder.add_node("search_kb", search_kb_node)
    builder.add_node("apply_authority_filter", apply_authority_filter_node)

    builder.add_edge(START, "formulate_queries")
    builder.add_edge("formulate_queries", "search_kb")
    builder.add_edge("search_kb", "apply_authority_filter")
    builder.add_edge("apply_authority_filter", END)

    return builder.compile()


knowledge_graph = create_knowledge_graph()
