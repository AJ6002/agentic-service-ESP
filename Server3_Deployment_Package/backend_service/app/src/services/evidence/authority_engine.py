"""
Authority Precedence Engine for Evidence Packaging
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §9 & Guidelines.pdf §3.1
"""

from typing import List, Dict, Any, Optional
from src.schemas.evidence import EvidenceItem, AuthorityLevel

# Priority rank mapping: lower integer = higher authority
AUTHORITY_RANK: Dict[AuthorityLevel, int] = {
    AuthorityLevel.LEVEL_A_INSTALLED_APPROVED: 1,
    AuthorityLevel.LEVEL_B_OEM: 2,
    AuthorityLevel.LEVEL_C_CUSTOMER_ENG: 3,
    AuthorityLevel.LEVEL_D_SITE_HISTORY: 4,
    AuthorityLevel.LEVEL_E_INDUSTRY: 5,
    AuthorityLevel.LEVEL_F_LLM_PRIOR: 6,
}


class AuthorityEngine:
    """
    Enforces §3.1 Authority Level Precedence.
    Guarantees that lower-level sources (e.g. Level F LLM prior or general industry guidance)
    never override higher-level installed asset specs or OEM limits.
    """

    @staticmethod
    def get_rank(level: AuthorityLevel) -> int:
        return AUTHORITY_RANK.get(level, 99)

    @classmethod
    def compare(cls, item_a: EvidenceItem, item_b: EvidenceItem) -> int:
        """
        Compare authority of two items.
        Returns negative if item_a has higher authority than item_b,
        positive if item_b has higher authority, or 0 if equal.
        """
        rank_a = cls.get_rank(item_a.authority_level)
        rank_b = cls.get_rank(item_b.authority_level)
        return rank_a - rank_b

    @classmethod
    def resolve_precedence(cls, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """
        Sort evidence items strictly by authority level (Level A first).
        """
        return sorted(items, key=lambda item: (cls.get_rank(item.authority_level), -item.confidence))
