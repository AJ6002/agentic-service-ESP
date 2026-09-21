"""
Universal Graph Adapter for ESP Asset Topology & Failure Modes
Supports live Neo4j queries via Cypher (bolt://localhost:7687) with local JSON fallback.
Grounded in ESP APM Phase 3 Knowledge Base & Phase 8 Evidence architecture.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schemas.canonical import ComponentNode

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_KG_PATH = ROOT_DIR / "knowledge_bases" / "esp" / "graph" / "esp_graph.json"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class GraphAdapter:
    """
    Universal Graph Adapter:
    - Primary: Queries live Neo4j database using Cypher.
    - Fallback: In-memory traversal of local esp_graph.json file.
    """

    def __init__(self, graph_json_path: Optional[str] = None, neo4j_uri: Optional[str] = None):
        self.graph_json_path = graph_json_path or str(DEFAULT_KG_PATH)
        self.neo4j_uri = neo4j_uri or NEO4J_URI
        self._graph_data: Dict[str, Any] = {}
        self._neo4j_available: Optional[bool] = None

        if os.path.exists(self.graph_json_path):
            try:
                with open(self.graph_json_path, "r", encoding="utf-8") as f:
                    self._graph_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load KG JSON: {e}")

    @classmethod
    def from_file(cls, graph_json_path: str) -> "GraphAdapter":
        return cls(graph_json_path=graph_json_path)

    def is_neo4j_live(self) -> bool:
        """Check if Neo4j driver connects successfully."""
        if self._neo4j_available is not None:
            return self._neo4j_available
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(self.neo4j_uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as s:
                s.run("RETURN 1;").single()
            driver.close()
            self._neo4j_available = True
        except Exception:
            self._neo4j_available = False
        return self._neo4j_available

    def get_components(self, asset_id: str) -> List[ComponentNode]:
        """Returns component nodes belonging to the asset from Neo4j or JSON fallback."""
        if self.is_neo4j_live():
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver(self.neo4j_uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
                nodes: List[ComponentNode] = []
                with driver.session() as session:
                    res = session.run("MATCH (c:Component)-[:PART_OF]->(s:Subsystem) RETURN c.name as comp, s.name as sub;")
                    for r in res:
                        nodes.append(ComponentNode(
                            component_name=r["comp"],
                            parent_component=r["sub"],
                            monitored_metrics=[]
                        ))
                driver.close()
                if nodes:
                    return nodes
            except Exception as e:
                logger.warning(f"Neo4j get_components failed: {e}")

        # JSON fallback
        if not self._graph_data:
            return []

        nodes: List[ComponentNode] = []
        raw_components = self._graph_data.get("components", [])
        for comp in raw_components:
            comp_name = comp if isinstance(comp, str) else comp.get("name")
            parent = comp.get("subsystem") if isinstance(comp, dict) else "Motor Section"
            metrics = comp.get("metrics", []) if isinstance(comp, dict) else []
            nodes.append(ComponentNode(
                component_name=comp_name,
                parent_component=parent,
                monitored_metrics=metrics
            ))
        return nodes

    def get_failure_modes(self, target: str) -> List[Dict[str, Any]]:
        """Returns failure modes associated with target from Neo4j or JSON fallback."""
        if self.is_neo4j_live():
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver(self.neo4j_uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
                results = []
                with driver.session() as session:
                    query = """
                        MATCH (a)-[r]->(b)
                        WHERE toLower(a.name) CONTAINS toLower($target)
                           OR toLower(b.name) CONTAINS toLower($target)
                        RETURN elementId(a) as src_id, a.name as src, type(r) as rel, elementId(b) as tgt_id, b.name as tgt;
                    """
                    res = session.run(query, target=target)
                    for r in res:
                        results.append({
                            "source": r["src"],
                            "type": r["rel"],
                            "target": r["tgt"],
                            "neo4j_src_id": r["src_id"],
                            "neo4j_tgt_id": r["tgt_id"],
                            "deep_link": f"{self.neo4j_uri}?node_id={r['tgt_id']}&name={r['tgt']}"
                        })
                driver.close()
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}")

        # JSON fallback
        if not self._graph_data:
            return []

        raw_fm = self._graph_data.get("failure_modes", [])
        relationships = self._graph_data.get("relationships", [])
        results = []
        target_lower = target.lower()

        for rel in relationships:
            source = rel.get("source", "").lower()
            target_node = rel.get("target", "").lower()
            if target_lower in source or target_lower in target_node:
                results.append(rel)

        if not results and raw_fm:
            for fm in raw_fm:
                fm_name = fm if isinstance(fm, str) else fm.get("name")
                results.append({
                    "source": target,
                    "type": "can_fail_with",
                    "target": fm_name
                })
        return results

    def trace_cause_effect(self, symptom_or_metric: str) -> List[Dict[str, Any]]:
        """Traces symptoms back to failure modes using Neo4j Cypher or JSON fallback."""
        if self.is_neo4j_live():
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver(self.neo4j_uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
                traces = []
                with driver.session() as session:
                    query = """
                        MATCH (a)-[r]->(b)
                        WHERE toLower(a.name) CONTAINS toLower($key)
                           OR toLower(b.name) CONTAINS toLower($key)
                        RETURN elementId(a) as src_id, a.name as src, type(r) as rel, elementId(b) as tgt_id, b.name as tgt;
                    """
                    res = session.run(query, key=symptom_or_metric)
                    for r in res:
                        connected = r["tgt"] if symptom_or_metric.lower() in r["src"].lower() else r["src"]
                        node_id = r["tgt_id"] if symptom_or_metric.lower() in r["src"].lower() else r["src_id"]
                        traces.append({
                            "symptom_or_metric": symptom_or_metric,
                            "relationship": r["rel"],
                            "connected_node": connected,
                            "full_rule": f"{r['src']} -> {r['rel']} -> {r['tgt']}",
                            "neo4j_node_id": node_id,
                            "deep_link": f"{self.neo4j_uri}?node_id={node_id}&name={connected}"
                        })
                driver.close()
                if traces:
                    return traces
            except Exception as e:
                logger.warning(f"Neo4j trace failed: {e}")

        # JSON fallback
        if not self._graph_data:
            return []

        relationships = self._graph_data.get("relationships", [])
        matched_traces = []
        key_lower = symptom_or_metric.lower()

        for rel in relationships:
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            rel_type = rel.get("type", "")
            if key_lower in src.lower() or key_lower in tgt.lower():
                conn = tgt if key_lower in src.lower() else src
                matched_traces.append({
                    "symptom_or_metric": symptom_or_metric,
                    "relationship": rel_type,
                    "connected_node": conn,
                    "full_rule": f"{src} -> {rel_type} -> {tgt}",
                    "chunk_ids": self.get_node_chunk_ids(conn)
                })
        return matched_traces

    def get_node_chunk_ids(self, node_name: str) -> List[str]:
        """Cognee Pattern: Resolve graph node directly to grounded vector chunk IDs."""
        mapping = self._graph_data.get("node_chunk_mappings", {})
        for k, v in mapping.items():
            if k.lower() in node_name.lower() or node_name.lower() in k.lower():
                return v
        return []
