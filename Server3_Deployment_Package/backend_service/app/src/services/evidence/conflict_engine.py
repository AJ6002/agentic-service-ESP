"""
Conflict Engine for Multi-Source Evidence
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §13
"""

import uuid
from typing import List, Dict, Any, Optional
from src.schemas.evidence import EvidenceItem, EvidenceConflict, EvidenceType, AuthorityLevel


class ConflictEngine:
    """
    Detects and constructs explicit EvidenceConflict records when contradictory sources disagree.
    """

    @classmethod
    def detect_conflicts(cls, items: List[EvidenceItem]) -> List[EvidenceConflict]:
        """
        Scans evidence items for ML vs. Physics engineering or multi-sensor discrepancies.
        """
        conflicts: List[EvidenceConflict] = []

        # 1. Check ML Models vs. Engineering Physics Calculations
        ml_items = [i for i in items if i.evidence_type == EvidenceType.ML]
        eng_items = [i for i in items if i.evidence_type == EvidenceType.ENGINEERING]

        for ml in ml_items:
            for eng in eng_items:
                # Example: ML claims Gas Interference but Engineering TDH shows Normal Hydraulic head
                ml_val = str(ml.value).lower()
                eng_val = str(eng.value).lower()
                if ("gas" in ml_val and "normal" in eng_val) or ("anomalous" in ml_val and "stable" in eng_val):
                    conflicts.append(EvidenceConflict(
                        conflict_id=f"CONF-ML-ENG-{uuid.uuid4().hex[:6]}",
                        evidence_refs=[ml.evidence_id, eng.evidence_id],
                        conflict_type="ML_VS_PHYSICS",
                        values={ml.source_id: ml.value, eng.source_id: eng.value},
                        authority_comparison=f"Deterministic Calculation ({eng.authority_level.value}) > ML Model ({ml.authority_level.value})",
                        impact="HIGH",
                        resolution_status="SURFACED",
                        resolution_method="Deterministic engineering physics calculation maintained as authoritative baseline; ML prediction retained as secondary anomaly flag.",
                        next_verification=["1. Inspect wellhead physical pressure gauge.", "2. Perform acoustic fluid level measurement."]
                    ))

        # 2. Check Telemetry Discrepancies (e.g. PIP vs Intake Pressure)
        tel_items = [i for i in items if i.evidence_type == EvidenceType.TELEMETRY]
        pip_readings = [i for i in tel_items if "intake_pressure" in i.source_id or "pip" in i.source_id]
        if len(pip_readings) >= 2:
            val1, val2 = float(pip_readings[0].value or 0), float(pip_readings[1].value or 0)
            if abs(val1 - val2) > 50.0:  # >50 psi discrepancy
                conflicts.append(EvidenceConflict(
                    conflict_id=f"CONF-TEL-{uuid.uuid4().hex[:6]}",
                    evidence_refs=[pip_readings[0].evidence_id, pip_readings[1].evidence_id],
                    conflict_type="TELEMETRY_DISCREPANCY",
                    values={pip_readings[0].source_id: val1, pip_readings[1].source_id: val2},
                    authority_comparison="Sensor tag telemetry comparison",
                    impact="MEDIUM",
                    resolution_status="SURFACED",
                    resolution_method="Flag sensor variance exceeding 50 psi threshold.",
                    next_verification=["1. Verify transmitter calibration.", "2. Check telemetry wiring."]
                ))

        # 3. Check Cross-Source Knowledge Base Discrepancies (e.g. Takacs Manual 140°C vs API RP 11S 150°C)
        kb_items = [i for i in items if i.evidence_type == EvidenceType.KNOWLEDGE]
        AUTHORITY_ORDER = {
            AuthorityLevel.LEVEL_A_INSTALLED_APPROVED: 0,
            AuthorityLevel.LEVEL_B_OEM: 1,
            AuthorityLevel.LEVEL_C_CUSTOMER_ENG: 2,
            AuthorityLevel.LEVEL_D_SITE_HISTORY: 3,
            AuthorityLevel.LEVEL_E_INDUSTRY: 4,
            AuthorityLevel.LEVEL_F_LLM_PRIOR: 5,
        }

        for i in range(len(kb_items)):
            for j in range(i + 1, len(kb_items)):
                item1 = kb_items[i]
                item2 = kb_items[j]

                # If same semantic topic or parameter but differing numeric values or limits
                if (item1.semantic_type == item2.semantic_type or (item1.unit and item1.unit == item2.unit)) and item1.value != item2.value:
                    rank1 = AUTHORITY_ORDER.get(item1.authority_level, 4)
                    rank2 = AUTHORITY_ORDER.get(item2.authority_level, 4)

                    higher_item = item1 if rank1 < rank2 else item2
                    lower_item = item2 if rank1 < rank2 else item1

                    conflicts.append(EvidenceConflict(
                        conflict_id=f"CONF-KB-DISCREPANCY-{uuid.uuid4().hex[:6]}",
                        evidence_refs=[item1.evidence_id, item2.evidence_id],
                        conflict_type="KB_LIMIT_DISCREPANCY",
                        values={item1.source_id: item1.value, item2.source_id: item2.value},
                        authority_comparison=f"Authority Precedence (§3.1): {higher_item.authority_level.value} ({higher_item.source_id}) > {lower_item.authority_level.value} ({lower_item.source_id})",
                        impact="HIGH",
                        resolution_status="RESOLVED",
                        resolution_method=f"Enforced Authority Precedence (§3.1): Level {higher_item.authority_level.value} ({higher_item.source_id}) overrides Level {lower_item.authority_level.value} ({lower_item.source_id}).",
                        next_verification=[f"Verify {higher_item.source_id} governing standard documentation."]
                    ))

        return conflicts
