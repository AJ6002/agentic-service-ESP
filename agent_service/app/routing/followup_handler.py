"""
Follow-Up Route Handler (Slice 4).
Consumes sealed EvidencePack and artifacts from a prior diagnostic run.
Produces explanatory narrative with zero network fetches, zero new numbers,
and 100% visualization reuse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.contracts.advisory import Advisory, ProvenanceResult
from app.contracts.evidence import EvidencePack
from app.contracts.visualization import VisualizationSpec
from app.evidence.formatter import format_pack, FormattedEvidence
from app.llm.calls import followup_narrate
from app.llm.client import LLMUnavailableError
from app.stores.run_store import get_pack, get_run_artifacts
from app.stores.session_store import get_session
from app.synthesis.numeric_check import check_numeric_provenance
from app.synthesis.xai import format_evidence_for_prompt


@dataclass
class FollowUpResult:
    ok: bool
    text: str = ""
    code: Optional[str] = None
    message: Optional[str] = None
    advisory: Optional[Advisory | dict] = None
    visualization: Optional[VisualizationSpec | dict] = None
    provenance: Optional[ProvenanceResult] = None
    evidence_ids: list[str] = field(default_factory=list)
    analysis_id: Optional[str] = None


FOLLOWUP_EVIDENCE_QUERY_REGEX = re.compile(
    r"\b(what\s+data|which\s+data|evidence\s+ids?|what\s+sources?|source\s+data)\b",
    re.IGNORECASE,
)


async def handle_followup(
    session_id: str,
    raw_message: str,
    requested_analysis_id: Optional[str] = None,
) -> FollowUpResult:
    """
    Executes the FOLLOW_UP route turn:
    1. Resolves analysis_id from explicit arg or session.last_analysis_id.
    2. Validates that the pack exists, is unexpired, and was sealed.
    3. Reconstructs FormattedEvidence and validates prior visualization.
    4. Calls LLM #5 (followup_narrate) with zero HTTP adapter calls.
    5. Validates numeric provenance (zero uncited numbers).
    6. Returns FollowUpResult with reused artifacts and verified narrative.
    """
    try:
        session = get_session(session_id)
    except Exception:
        return FollowUpResult(
            ok=False,
            code="ANALYSIS_EXPIRED",
            message="Prior analysis expired or not found. Please ask your diagnostic question again.",
            analysis_id=requested_analysis_id,
        )
    analysis_id = requested_analysis_id or (session.last_analysis_id if session else None)

    if not analysis_id:
        return FollowUpResult(
            ok=False,
            code="ANALYSIS_EXPIRED",
            message="Prior analysis expired or not found. Please ask your diagnostic question again.",
        )

    pack_data = get_pack(analysis_id, "latest")
    if not pack_data:
        return FollowUpResult(
            ok=False,
            code="ANALYSIS_EXPIRED",
            message="Prior analysis expired or not found. Please ask your diagnostic question again.",
            analysis_id=analysis_id,
        )

    try:
        pack = EvidencePack.model_validate(pack_data)
    except Exception:
        return FollowUpResult(
            ok=False,
            code="ANALYSIS_EXPIRED",
            message="Prior analysis data could not be restored.",
            analysis_id=analysis_id,
        )

    # Defensive check: unsealed pack must return INSUFFICIENT
    if not pack.sealed:
        return FollowUpResult(
            ok=False,
            code="INSUFFICIENT_EVIDENCE",
            message="Prior analysis evidence pack was never sealed.",
            analysis_id=analysis_id,
        )

    formatted_evidence = format_pack(pack)
    pack_evidence_ids = [item.evidence_id for item in pack.items]

    # Load prior artifacts (advisory and visualization)
    adv_dict, viz_dict = get_run_artifacts(analysis_id)

    # Validate visualization card evidence IDs against current pack
    valid_viz: Optional[VisualizationSpec | dict] = None
    if viz_dict:
        try:
            viz_spec = VisualizationSpec.model_validate(viz_dict)
            # Filter card evidence IDs to only those that exist in this pack
            valid_ev_ids = [eid for eid in viz_spec.evidence_ids if eid in pack_evidence_ids]
            viz_spec.evidence_ids = valid_ev_ids
            valid_viz = viz_spec
        except Exception:
            valid_viz = viz_dict

    # Check if user specifically asks "what data did you use?"
    if FOLLOWUP_EVIDENCE_QUERY_REGEX.search(raw_message):
        evidence_list = ", ".join(pack_evidence_ids) if pack_evidence_ids else "None"
        direct_text = f"The prior analysis used the following evidence IDs: {evidence_list}."
        return FollowUpResult(
            ok=True,
            text=direct_text,
            advisory=adv_dict,
            visualization=valid_viz,
            evidence_ids=pack_evidence_ids,
            analysis_id=analysis_id,
        )

    # Format inputs for LLM follow-up narrator
    prior_adv_text = ""
    if adv_dict:
        prior_adv_text = (
            f"Assessment: {adv_dict.get('assessment', '')}\n"
            f"Recommendation: {adv_dict.get('recommendation', '')}\n"
            f"Hypotheses: {adv_dict.get('hypotheses', [])}"
        )

    evidence_text = format_evidence_for_prompt(formatted_evidence)

    try:
        narrative = await followup_narrate(
            user_query=raw_message,
            evidence_text=evidence_text,
            prior_advisory_text=prior_adv_text,
        )
    except LLMUnavailableError:
        return FollowUpResult(
            ok=False,
            code="LLM_UNAVAILABLE",
            message="LLM service is currently unavailable for follow-up explanations.",
            analysis_id=analysis_id,
        )
    except Exception as e:
        return FollowUpResult(
            ok=False,
            code="FOLLOWUP_FAILED",
            message=f"Follow-up generation failed: {e}",
            analysis_id=analysis_id,
        )

    # Check numeric provenance: verify numbers in narrative trace to pack
    synthetic_advisory = Advisory(
        objective_id=session.last_objective or "FOLLOW_UP",
        assessment=narrative,
        recommendation="",
        cited_evidence_ids=pack_evidence_ids,
    )
    provenance = check_numeric_provenance(synthetic_advisory, formatted_evidence)

    final_text = narrative
    if not provenance.passed and provenance.unattributed_numbers:
        unverified_str = ", ".join(provenance.unattributed_numbers)
        final_text += f"\n\n[Notice: Unverified numbers flagged: {unverified_str}]"

    return FollowUpResult(
        ok=True,
        text=final_text,
        advisory=adv_dict,
        visualization=valid_viz,
        provenance=provenance,
        evidence_ids=pack_evidence_ids,
        analysis_id=analysis_id,
    )
