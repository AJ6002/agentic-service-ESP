from typing import List
from pydantic import BaseModel, Field


class KnowledgeBaseManifest(BaseModel):
    domain_name: str = Field(..., description="Domain name (e.g. Electric Submersible Pump)")
    domain_version: str = Field(..., description="Version of domain ontology")
    knowledge_base_version: str = Field(..., description="Version of knowledge base")
    assets: List[str] = Field(..., description="List of supported asset IDs")
    supports_telemetry: bool = Field(True, description="Whether telemetry loading is supported")
    supports_graph: bool = Field(True, description="Whether graph topology queries are supported")
    supports_rag: bool = Field(True, description="Whether documentation RAG is supported")
    supports_rules: bool = Field(True, description="Whether deterministic rules evaluation is supported")
    supports_operational_actions: bool = Field(False, description="Whether operational actions are permitted")
    system_prompt_overlay: str = Field(..., description="Domain specific context prompt overlay for LLM")
    required_canonical_concepts: List[str] = Field(
        default=["Asset", "TelemetryMetric", "ComponentNode", "DiagnosticResult"],
        description="Required canonical concepts"
    )
