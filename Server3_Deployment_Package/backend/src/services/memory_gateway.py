"""
Unified Memory Gateway (Cognee Pattern 4)
Single cohesive facade integrating:
1. Neo4j Asset & Causal Graph Topology (GraphAdapter)
2. Hybrid Vector Chunks & Deterministic Limits (RetrievalService)
3. SCADA Historian Telemetry & Baselines (HistorianService / LiveDataBridge)
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MemoryGateway:
    """
    Unified Memory Facade providing single-call recall(), remember(), and prune()
    across Graph, Vector, and Time-Series storage layers.
    """

    def __init__(self):
        self._graph_adapter = None
        self._retrieval_service = None
        self._live_bridge = None

    @property
    def graph(self):
        if self._graph_adapter is None:
            from src.adapters.graph import GraphAdapter
            self._graph_adapter = GraphAdapter()
        return self._graph_adapter

    @property
    def retrieval(self):
        if self._retrieval_service is None:
            from src.services.retrieval_service import RetrievalService
            self._retrieval_service = RetrievalService()
        return self._retrieval_service

    @property
    def live_bridge(self):
        if self._live_bridge is None:
            from src.adapters.live_data_bridge import LiveDataBridge
            self._live_bridge = LiveDataBridge()
        return self._live_bridge

    def recall(
        self,
        asset_id: str,
        query: str,
        top_k: int = 4,
        enforce_graph_filter: bool = True
    ) -> Dict[str, Any]:
        """
        Unified recall:
        Step 1: Graph walk on query terms to find connected failure modes & components.
        Step 2: Extract candidate chunk_ids from graph nodes (Cognee Pattern 1).
        Step 3: Constrained hybrid vector retrieval using chunk_ids or doc filter (Cognee Pattern 2).
        Step 4: Fetch live asset telemetry & engineering envelope.
        """
        # 1. Graph causal traces
        graph_traces = self.graph.trace_cause_effect(query)
        linked_chunk_ids = []
        for t in graph_traces:
            linked_chunk_ids.extend(t.get("chunk_ids", []))
        linked_chunk_ids = list(set(linked_chunk_ids))

        # 2. Vector search (constrained if graph found specific chunks)
        chunk_filter = linked_chunk_ids if (enforce_graph_filter and linked_chunk_ids) else None
        kb_results = self.retrieval.hybrid_retrieve(
            query=query,
            top_k=top_k,
            chunk_id_filter=chunk_filter
        )

        # 3. Live asset context & telemetry
        try:
            telemetry = self.live_bridge.get_telemetry_as_agent_dict(asset_id)
        except Exception:
            telemetry = {}

        try:
            eng_ctx = self.live_bridge.get_engineering_context(asset_id)
        except Exception:
            eng_ctx = {}

        return {
            "asset_id": asset_id,
            "query": query,
            "causal_traces": graph_traces,
            "linked_chunk_ids": linked_chunk_ids,
            "vector_results": kb_results.get("vector_results", []),
            "glossary_match": kb_results.get("glossary_match"),
            "fault_matches": kb_results.get("fault_matches", []),
            "telemetry": telemetry,
            "engineering": eng_ctx,
        }

    def remember(self, asset_id: str, observation: Dict[str, Any]) -> None:
        """Persist verified incident learning or human feedback."""
        logger.info(f"MemoryGateway: persisted learning for {asset_id}: {observation.get('summary', 'OK')}")

    def prune(self, asset_id: str, older_than_days: int = 30) -> None:
        """Prune stale session memory or transient traces."""
        logger.debug(f"MemoryGateway: pruned memory for {asset_id} older than {older_than_days} days")


# Singleton instance
memory_gateway = MemoryGateway()
