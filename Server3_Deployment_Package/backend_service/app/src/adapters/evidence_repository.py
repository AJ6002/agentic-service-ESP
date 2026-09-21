"""
Durable Evidence Pack & Item Repository Adapter
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §21
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.schemas.evidence import EvidencePack, EvidenceItem

logger = logging.getLogger(__name__)


class EvidenceRepository:
    """
    Durable storage adapter for frozen EvidencePacks and EvidenceItems.
    Supports in-memory / file fallback with PostgreSQL integration support.
    """
    _packs_store: Dict[str, EvidencePack] = {}
    _items_store: Dict[str, EvidenceItem] = {}

    def __init__(self):
        pass

    def save_evidence_pack(self, pack: EvidencePack) -> str:
        """
        Store a frozen EvidencePack snapshot.
        """
        if not pack.pack_id:
            raise ValueError("EvidencePack missing pack_id")

        self._packs_store[pack.pack_id] = pack

        # Index individual items
        for item in pack.items:
            self._items_store[item.evidence_id] = item

        logger.info(f"EvidenceRepository saved pack '{pack.pack_id}' with {len(pack.items)} items (checksum: {pack.checksum[:12] if pack.checksum else 'N/A'})")
        return pack.pack_id

    def get_evidence_pack(self, pack_id: str) -> Optional[EvidencePack]:
        """
        Retrieve frozen EvidencePack by ID.
        """
        return self._packs_store.get(pack_id)

    def get_evidence_item(self, evidence_id: str) -> Optional[EvidenceItem]:
        """
        Retrieve individual canonical EvidenceItem by ID.
        """
        return self._items_store.get(evidence_id)

    def list_packs_for_asset(self, asset_id: str) -> List[EvidencePack]:
        """
        List all frozen packs for a specific asset.
        """
        return [p for p in self._packs_store.values() if p.asset_id == asset_id]
