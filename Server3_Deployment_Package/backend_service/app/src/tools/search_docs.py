from typing import List, Dict, Any, Optional
from src.adapters.rag import RAGAdapter


def search_docs_tool(rag_adapter: RAGAdapter, query: str, top_k: int = 3, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tool function to search documentation passages for troubleshooting guidance."""
    return rag_adapter.search(query=query, top_k=top_k, doc_type=doc_type)
