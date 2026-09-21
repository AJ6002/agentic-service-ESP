"""
Evidence Ranker Service
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §11
"""

from typing import List
from src.schemas.evidence import EvidenceItem, QualityStatus
from src.services.evidence.authority_engine import AuthorityEngine


class EvidenceRanker:
    """
    Ranks evidence items according to objective relevance, authority precedence, and quality status.
    """

    @classmethod
    def calculate_score(cls, item: EvidenceItem) -> float:
        """
        Compute composite rank score for an EvidenceItem.
        Higher score = prioritized for ContextView.
        """
        # Authority base weight: Level A = 1.0, Level B = 0.9, Level C = 0.8, Level D = 0.7, Level E = 0.6, Level F = 0.5
        auth_rank = AuthorityEngine.get_rank(item.authority_level)
        auth_weight = max(0.2, 1.1 - (auth_rank * 0.1))

        # Quality penalty
        q_weight = 1.0
        if item.quality_status == QualityStatus.DEGRADED:
            q_weight = 0.8
        elif item.quality_status == QualityStatus.STALE:
            q_weight = 0.5
        elif item.quality_status in (QualityStatus.INVALID, QualityStatus.MISSING):
            q_weight = 0.0

        # Composite score
        return item.relevance_score * auth_weight * q_weight * item.confidence

    @classmethod
    def rank_items(cls, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """
        Sort items in descending order of composite rank score.
        """
        return sorted(items, key=lambda item: cls.calculate_score(item), reverse=True)
