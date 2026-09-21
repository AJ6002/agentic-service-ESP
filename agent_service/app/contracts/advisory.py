"""
Advisory Contracts — Phase 2 Data Models.
Reference: SLICE_2_PLAN.md SS2.1 and SS2.2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Re-export canonical FormattedValue & FormattedEvidence from app.evidence.formatter
# to prevent duplicate type definitions while preserving contracts/__init__.py exports.
from app.evidence.formatter import FormattedValue, FormattedEvidence


class Advisory(BaseModel):
    """
    Synthesised XAI diagnostic output produced by LLM #3 (narrate).
    Strictly grounded in verified EvidencePack data.
    """
    objective_id: str
    assessment: str
    hypotheses: list[str] = Field(default_factory=list)
    recommendation: str
    verification_steps: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    cited_evidence_ids: list[str] = Field(default_factory=list)


class ProvenanceResult(BaseModel):
    """
    Outcome of numeric provenance check (Step 2.2).
    Lists any unattributed numeric tokens found in Advisory prose.
    """
    passed: bool
    unattributed_numbers: list[str] = Field(default_factory=list)
