"""
Quality of Data (QoD) & Freshness Validator Service
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §10 & Guidelines.pdf §7
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from src.schemas.evidence import EvidenceItem, QualityStatus


class QoDValidator:
    """
    Validates Quality of Data (QoD) and freshness thresholds per objective requirement.
    """

    # Objective-specific telemetry freshness max age in seconds
    FRESHNESS_THRESHOLDS: Dict[str, float] = {
        "OP01_CURRENT_STATUS": 300.0,       # 5 mins
        "OP02_PRODUCTION_DECLINE_RCA": 3600.0, # 1 hour
        "OP03_FAULT_DIAGNOSIS": 1800.0,       # 30 mins
        "OP04_HEALTH_ASSESSMENT": 86400.0,    # 24 hours
        "OP05_EARLY_WARNING": 3600.0,         # 1 hour
        "OP06_PROCEDURE_LOOKUP": 604800.0,    # 7 days
    }

    @classmethod
    def evaluate_item_qod(
        cls,
        item: EvidenceItem,
        objective_id: str,
        current_time_epoch: Optional[float] = None
    ) -> QualityStatus:
        """
        Evaluate freshness and quality status of an EvidenceItem.
        """
        if item.quality_status in (QualityStatus.INVALID, QualityStatus.MISSING):
            return item.quality_status

        # Check telemetry / model freshness if timestamp is available
        max_age = cls.FRESHNESS_THRESHOLDS.get(objective_id, 3600.0)
        now = current_time_epoch or time.time()

        try:
            # Parse ISO timestamp (e.g. 2026-08-26T12:00:00Z)
            import datetime
            dt = datetime.datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
            age_seconds = now - dt.timestamp()
            if age_seconds > max_age:
                return QualityStatus.STALE
        except Exception:
            pass

        return item.quality_status

    @classmethod
    def audit_quality_summary(cls, items: List[EvidenceItem]) -> Tuple[str, List[str]]:
        """
        Generates overall data quality summary status (COMPLETE, PARTIAL, STALE) and lists missing items.
        """
        missing = [item.source_id for item in items if item.quality_status == QualityStatus.MISSING]
        stale = [item.source_id for item in items if item.quality_status == QualityStatus.STALE]

        if missing or stale:
            summary = "PARTIAL" if len(items) > len(missing) + len(stale) else "STALE"
        else:
            summary = "COMPLETE"

        return summary, missing
