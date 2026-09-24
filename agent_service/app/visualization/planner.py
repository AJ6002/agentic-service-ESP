"""
Visualization Planner — Step 3.1.
Consumes: objective_id + sealed EvidencePack.
Produces: VisualizationSpec (card_ids, evidence_ids).
Selection Rule (Rule C — filter, not ranker):
For each card_id in the objective manifest allowed_visuals,
include it iff the pack contains its required signals/data.
Reference: SLICE_2_PLAN.md §3.1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set
import yaml

from app.contracts.evidence import EvidencePack
from app.contracts.visualization import VisualizationSpec
from app.evidence.formatter import format_pack, FormattedEvidence
from app.routing.objective_registry import get_objective

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_CARDS_REGISTRY_PATH = _CONFIG_DIR / "cards_registry.yaml"

_CARDS_REGISTRY: dict = {}


def _load_cards_registry() -> dict:
    global _CARDS_REGISTRY
    if not _CARDS_REGISTRY and _CARDS_REGISTRY_PATH.exists():
        with open(_CARDS_REGISTRY_PATH, "r", encoding="utf-8") as f:
            _CARDS_REGISTRY = yaml.safe_load(f).get("cards", {})
    return _CARDS_REGISTRY


def plan_visualization(
    objective_id: str,
    pack: EvidencePack,
    formatted_evidence: Optional[FormattedEvidence] = None,
) -> VisualizationSpec:
    """
    Selects qualifying cards from the objective's allowed_visuals.
    A card qualifies iff the pack is sealed and all its required signals are present in the pack.
    """
    if not pack.sealed:
        return VisualizationSpec(widget_id="cards", card_ids=[], evidence_ids=[])

    manifest = get_objective(objective_id)
    if not manifest or not manifest.allowed_visuals:
        return VisualizationSpec(widget_id="cards", card_ids=[], evidence_ids=[])

    if formatted_evidence is None:
        formatted_evidence = format_pack(pack)

    available_signals: Set[str] = {fv.signal for fv in formatted_evidence.values}

    registry = _load_cards_registry()

    selected_cards: list[str] = []
    cited_evidence_ids: Set[str] = set()

    for card_id in manifest.allowed_visuals:
        card_cfg = registry.get(card_id)
        if not card_cfg:
            continue

        req_signals = card_cfg.get("required_signals", [])
        # If card requires specific signals, verify they are all present
        if req_signals:
            if all(sig in available_signals for sig in req_signals):
                selected_cards.append(card_id)
                for fv in formatted_evidence.values:
                    if fv.signal in req_signals:
                        cited_evidence_ids.add(fv.evidence_id)
        else:
            # Cards with empty required_signals (e.g. fleet-health or system-ingestion)
            # qualify if any item is in the pack
            if pack.items:
                selected_cards.append(card_id)
                for item in pack.items:
                    cited_evidence_ids.add(item.evidence_id)

    return VisualizationSpec(
        widget_id="cards",
        card_ids=selected_cards,
        evidence_ids=sorted(list(cited_evidence_ids)),
        data={"cards": selected_cards},
    )
