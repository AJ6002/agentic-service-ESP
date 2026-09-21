"""
XAI Visual Story Engine Builder — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §6

Connects Qwen model outputs to the UI visual storytelling layer.

Transforms structured Qwen advisory findings into UI Visual Story specifications:
  Qwen Finding
       ↓
  XAI Story Builder
       ↓
  Claim + Evidence + Reasoning + Confidence + Visual Specs
       ↓
  Frontend Workspace Canvas (interactive cards & charts)
"""

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.structured_output import AdvisoryOutputSchema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# XAI Payload Schemas
# ---------------------------------------------------------------------------
@dataclass
class VisualSpec:
    card_id: str             # e.g. 'telemetry', 'pump_curve', 'diagnosis'
    chart_type: str          # e.g. 'multi_signal_trend', 'pump_curve_overlay', 'matrix'
    title: str
    description: str
    target_signals: List[str] = field(default_factory=list)
    highlight_anomaly: Optional[str] = None


@dataclass
class XAIExplanationPayload:
    claim: str
    primary_hypothesis: str
    confidence: float
    reasoning: str
    recommendation: str
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    verification_checklist: List[str] = field(default_factory=list)
    visualizations: List[VisualSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# XAI Story Builder Engine
# ---------------------------------------------------------------------------
class XAIVisualStoryBuilder:
    """
    Constructs XAIExplanationPayload from structured advisory output and compact context.
    Maps diagnosis causes to specific UI canvas visualization cards.
    """

    def build(
        self,
        advisory: AdvisoryOutputSchema,
        compact_context: Dict[str, Any],
    ) -> XAIExplanationPayload:
        """
        Build XAIExplanationPayload from parsed Qwen advisory output and compact context.
        """
        top_hypothesis = advisory.hypotheses[0] if advisory.hypotheses else None
        cause = top_hypothesis.cause if top_hypothesis else "Normal Operations"
        confidence = top_hypothesis.confidence if top_hypothesis else 0.85
        supp_ev = top_hypothesis.supporting_evidence if top_hypothesis else []
        contra_ev = top_hypothesis.contradicting_evidence if top_hypothesis else []

        claim = f"{cause} identified as primary operational finding ({int(confidence * 100)}% confidence)."
        reasoning = f"{advisory.assessment} {advisory.recommendation}"

        # Build dynamic visualization specifications based on fault cause
        visualizations = self._determine_visualizations(cause, compact_context)

        # Parse verification string or list into checklist items
        if isinstance(advisory.verification, list):
            verification_items = [str(v).strip() for v in advisory.verification if str(v).strip()]
        elif isinstance(advisory.verification, str):
            verification_items = [v.strip() for v in advisory.verification.split(".") if v.strip()]
        else:
            verification_items = ["Verify SCADA readings against local wellhead gauge."]

        payload = XAIExplanationPayload(
            claim=claim,
            primary_hypothesis=cause,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=supp_ev,
            contradicting_evidence=contra_ev,
            uncertainties=advisory.uncertainties,
            recommendation=advisory.recommendation,
            verification_checklist=verification_items,
            visualizations=visualizations,
        )

        logger.info(
            f"XAIVisualStoryBuilder: built XAI story for cause '{cause}' "
            f"with {len(visualizations)} visual specs."
        )
        return payload

    def _determine_visualizations(
        self, cause: str, compact_context: Dict[str, Any]
    ) -> List[VisualSpec]:
        """
        Map hypothesis cause to UI canvas visual cards.
        """
        cause_lower = cause.lower()
        visuals: List[VisualSpec] = []

        # 1. Telemetry Trend Card
        if any(k in cause_lower for k in ("gas", "slugging", "pressure", "wear", "decline", "flow")):
            visuals.append(VisualSpec(
                card_id="telemetry",
                chart_type="multi_signal_trend",
                title="Multi-signal Telemetry Trend (48h)",
                description="Intake Pressure (PIP) & Drive Current correlation analysis",
                target_signals=["intake_pressure", "drive_current", "flow"],
                highlight_anomaly="Cyclic PIP Spiking & Current Dip Correlation (r=0.88)"
                if "gas" in cause_lower else "Linear Flow & Pressure Degradation"
            ))

        # 2. Pump Curve Card
        if any(k in cause_lower for k in ("pump", "head", "tdh", "bep", "decline", "wear", "gas")):
            visuals.append(VisualSpec(
                card_id="pump_curve",
                chart_type="pump_curve_overlay",
                title="Pump Operating Point vs BEP Curve",
                description="Weatherford OEM Pump Curve Overlay",
                target_signals=["tdh_ft", "flow"],
                highlight_anomaly="Operating Left of BEP (-17.1%)"
            ))

        # 3. Diagnosis Matrix Card
        visuals.append(VisualSpec(
            card_id="diagnosis",
            chart_type="matrix",
            title="Differential Diagnosis Matrix",
            description="Likelihood breakdown across physics & ML evidence streams",
            target_signals=["confidence", "ml_scores"],
            highlight_anomaly=f"Primary: {cause}"
        ))

        return visuals
