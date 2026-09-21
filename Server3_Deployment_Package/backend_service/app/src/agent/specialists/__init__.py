"""
Domain Specialist Subgraphs Package
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

from src.agent.specialists.well_performance import create_well_performance_graph, well_performance_graph
from src.agent.specialists.reliability import create_reliability_graph, reliability_graph
from src.agent.specialists.knowledge import create_knowledge_graph, knowledge_graph
from src.agent.specialists.digital_twin import create_digital_twin_graph, digital_twin_graph
from src.agent.specialists.maintenance import create_maintenance_graph, maintenance_graph

__all__ = [
    "create_well_performance_graph", "well_performance_graph",
    "create_reliability_graph", "reliability_graph",
    "create_knowledge_graph", "knowledge_graph",
    "create_digital_twin_graph", "digital_twin_graph",
    "create_maintenance_graph", "maintenance_graph"
]
