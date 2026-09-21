"""
Context Builder Service for Bounded ContextView Assembly & Context Budgeting
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §15, §16, §17
"""

import time
import uuid
from typing import List, Dict, Any, Optional

from src.schemas.evidence import (
    EvidencePack, EvidenceItem, EvidenceConflict, EvidenceType, QualityStatus, AuthorityLevel,
    KnowledgeEvidence, TelemetryEvidence, ModelEvidence, CalculationEvidence
)
from src.schemas.context_view import ContextView
from src.services.evidence.collector import EvidenceCollector
from src.services.evidence.qod_validator import QoDValidator
from src.services.evidence.authority_engine import AuthorityEngine
from src.services.evidence.conflict_engine import ConflictEngine
from src.services.evidence.ranker import EvidenceRanker
from src.services.evidence.freeze_manager import EvidenceFreezeManager
from src.services.retrieval_service import RetrievalService


class ContextBuilder:
    """
    Assembles normalized EvidencePack envelopes and bounded ContextView working contexts.
    Enforces objective-specific context budgeting (max top-k, character limits).
    """

    def __init__(self):
        self.retrieval_service = RetrievalService()

    def build_evidence_pack(
        self,
        request_id: str,
        asset_id: str,
        objective_id: str,
        user_query: str = "",
        asset_context: Optional[Dict[str, Any]] = None,
        telemetry_data: Optional[Dict[str, float]] = None,
        model_outputs: Optional[Dict[str, Any]] = None,
        calculations: Optional[Dict[str, Any]] = None,
        knowledge_results: Optional[List[Dict[str, Any]]] = None,
        specialist_results: Optional[List[Dict[str, Any]]] = None,
        vfd_diagnostic: Optional[Dict[str, Any]] = None
    ) -> EvidencePack:
        """
        Builds, validates, ranks, deduplicates, and freezes an EvidencePack.
        """
        all_items: List[EvidenceItem] = []

        # 1. Collect from Asset Context
        if asset_context:
            all_items.extend(EvidenceCollector.collect_from_asset_context(asset_id, asset_context))

        # 2. Collect from Telemetry
        if telemetry_data:
            all_items.extend(EvidenceCollector.collect_from_telemetry(asset_id, telemetry_data))

        # 3. Collect from Engineering Calculations
        if calculations:
            all_items.extend(EvidenceCollector.collect_from_engineering(asset_id, calculations))

        # 4. Collect from Predictive Models (legacy health-index path)
        if model_outputs:
            all_items.extend(EvidenceCollector.collect_from_models(asset_id, model_outputs))

        # 4b. Collect from ESP_APM_models live VFD diagnosis (sole source of truth for
        # live ESP fault classification — see collect_from_vfd_diagnostic() docstring).
        # No-ops (returns []) if vfd_diagnostic is None, e.g. cced_esp unreachable or
        # this well has no MQTT-fed diagnosis yet.
        if vfd_diagnostic:
            all_items.extend(EvidenceCollector.collect_from_vfd_diagnostic(asset_id, vfd_diagnostic))

        # 5. Collect from Knowledge RAG
        if knowledge_results is None and user_query:
            try:
                ret_res = self.retrieval_service.hybrid_retrieve(user_query, top_k=4)
                knowledge_results = ret_res.get("vector_results", [])
            except Exception:
                knowledge_results = []
        
        if knowledge_results:
            all_items.extend(EvidenceCollector.collect_from_knowledge(asset_id, knowledge_results))

        # 6. Apply QoD Evaluation & Freshness Validation
        for item in all_items:
            item.quality_status = QoDValidator.evaluate_item_qod(item, objective_id)

        dq_summary, missing_tags = QoDValidator.audit_quality_summary(all_items)

        # 7. Detect Evidence Conflicts (ML vs Physics / Telemetry Discrepancies)
        conflicts: List[EvidenceConflict] = ConflictEngine.detect_conflicts(all_items)

        # 8. Apply Authority & Relevance Ranking
        ranked_items = EvidenceRanker.rank_items(all_items)

        # Build backward-compatible sub-collections
        know_ev = [
            KnowledgeEvidence(
                claim=i.statement,
                source=i.citation or "KB Doc",
                document_id=i.source_id,
                page=1,
                knowledge_id=i.evidence_id,
                score=i.confidence
            ) for i in ranked_items if i.evidence_type == EvidenceType.KNOWLEDGE
        ]

        tel_ev = [
            TelemetryEvidence(
                tag=i.source_id,
                value=float(i.value) if isinstance(i.value, (int, float)) else 0.0,
                unit=i.unit or "",
                timestamp=i.timestamp,
                source=i.source_system,
                data_quality=i.quality_status.value
            ) for i in ranked_items if i.evidence_type == EvidenceType.TELEMETRY
        ]

        mod_ev = [
            ModelEvidence(
                model_name=i.source_id,
                prediction=str(i.value),
                confidence=i.confidence,
                timestamp=i.timestamp,
                model_version=i.source_version,
                data_quality=i.quality_status.value
            ) for i in ranked_items if i.evidence_type == EvidenceType.ML
        ]

        calc_ev = [
            CalculationEvidence(
                calculation_name=i.source_id,
                inputs={"asset_id": asset_id},
                result=float(i.value) if isinstance(i.value, (int, float)) else 0.0,
                unit=i.unit or "",
                assumption="Standard conditions",
                calculation_version=i.source_version
            ) for i in ranked_items if i.evidence_type == EvidenceType.ENGINEERING
        ]

        constraints = [
            "Do NOT recommend automatic speed increases without engineering review.",
            "Do NOT suppress safety alarms or trip interlocks.",
            "Always state confidence score and source citations explicitly.",
            "If data quality is STALE or PARTIAL, disclose missing sensor inputs."
        ]

        for c in conflicts:
            constraints.append(f"CONFLICT [{c.conflict_type}]: {c.authority_comparison}")

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        pack = EvidencePack(
            pack_id=f"PACK-{uuid.uuid4().hex[:8]}",
            request_id=request_id,
            asset_id=asset_id,
            objective_id=objective_id,
            created_at=now_iso,
            frozen=False,
            items=ranked_items,
            conflicts=conflicts,
            missing_data=missing_tags,
            asset_context=asset_context or {},
            knowledge_evidence=know_ev,
            telemetry_evidence=tel_ev,
            model_evidence=mod_ev,
            calculation_evidence=calc_ev,
            data_quality_summary=dq_summary,
            constraints=constraints,
            provenance=[
                "AssetContextService", "TelemetryService", "EngineeringService", "ModelAdapter",
                "RetrievalService"
            ] + (["ESP_APM_models.WellDiagnosticEngine"] if vfd_diagnostic else [])
        )

        # Cryptographically Freeze Pack
        return EvidenceFreezeManager.freeze_pack(pack)

    def build_context_view(self, pack: EvidencePack, run_id: str) -> ContextView:
        """
        Builds a bounded ContextView from a frozen EvidencePack.
        Enforces token/context budgeting limits.
        """
        # Context Budgeting Limits
        MAX_KB_ITEMS = 3
        MAX_ENGINEERING_ITEMS = 5
        MAX_MODEL_ITEMS = 3

        kb_items = [i.model_dump() for i in pack.items if i.evidence_type == EvidenceType.KNOWLEDGE][:MAX_KB_ITEMS]
        eng_items = [i.model_dump() for i in pack.items if i.evidence_type == EvidenceType.ENGINEERING][:MAX_ENGINEERING_ITEMS]
        mod_items = [i.model_dump() for i in pack.items if i.evidence_type == EvidenceType.ML][:MAX_MODEL_ITEMS]
        tel_dict = {i.source_id: i.value for i in pack.items if i.evidence_type == EvidenceType.TELEMETRY}

        return ContextView(
            run_id=run_id,
            objective_id=pack.objective_id,
            evidence_pack_id=pack.pack_id,
            asset_context=pack.asset_context or {},
            current_state=tel_dict,
            engineering=eng_items,
            model_outputs=mod_items,
            knowledge=kb_items,
            conflicts=[c.model_dump() for c in pack.conflicts],
            missing_data=pack.missing_data,
            safety_constraints=pack.constraints
        )

    def format_llm_prompt_overlay(self, pack: EvidencePack) -> str:
        """
        Format compact, structured zero-hallucination prompt overlay block for the LLM.
        """
        lines = []
        lines.append(f"=== EVIDENCE PACK (Asset: {pack.asset_id} | Objective: {pack.objective_id} | Pack ID: {pack.pack_id}) ===")
        lines.append(f"Data Quality: {pack.data_quality_summary} | Frozen: {pack.frozen} | Checksum: {pack.checksum[:16] if pack.checksum else 'N/A'}")
        lines.append("")

        if pack.items:
            lines.append("--- CANONICAL EVIDENCE ITEMS (RANKED BY AUTHORITY §3.1) ---")
            for item in pack.items[:8]:
                lines.append(f"  • [{item.evidence_id}] ({item.authority_level.value}) {item.source_system} / {item.source_id}: {item.statement}")
            lines.append("")

        if pack.conflicts:
            lines.append("--- DETECTED EVIDENCE CONFLICTS ---")
            for c in pack.conflicts:
                lines.append(f"  [!] Conflict {c.conflict_id} ({c.conflict_type}): {c.authority_comparison}")
            lines.append("")

        if pack.constraints:
            lines.append("--- MANDATORY SAFETY CONSTRAINTS ---")
            for c in pack.constraints:
                lines.append(f"  [!] {c}")
            lines.append("")

        lines.append("=================================================================")
        return "\n".join(lines)
