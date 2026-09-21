"""
Evidence Freeze Manager Service
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §19
"""

import hashlib
import json
import time
from typing import Dict, Any
from src.schemas.evidence import EvidencePack


class EvidenceFreezeManager:
    """
    Manages immutability freezing and SHA-256 checksum verification for EvidencePack snapshots.
    Grounded in Phase 8 Design §19.
    """

    @classmethod
    def compute_checksum(cls, pack: EvidencePack) -> str:
        """
        Compute deterministic SHA-256 hash across canonical evidence items, request ID, asset ID, and objective ID.
        """
        hash_payload = {
            "request_id": pack.request_id,
            "asset_id": pack.asset_id,
            "objective_id": pack.objective_id,
            "created_at": pack.created_at,
            "item_ids": sorted([item.evidence_id for item in pack.items]),
            "statements": [item.statement for item in pack.items]
        }
        serialized = json.dumps(hash_payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def freeze_pack(cls, pack: EvidencePack) -> EvidencePack:
        """
        Freeze an EvidencePack instance and compute cryptographic checksum.
        """
        pack.frozen = True
        pack.checksum = cls.compute_checksum(pack)
        return pack

    @classmethod
    def verify_integrity(cls, pack: EvidencePack) -> bool:
        """
        Verify that a frozen pack matches its recorded cryptographic checksum.
        """
        if not pack.frozen or not pack.checksum:
            return False
        expected_checksum = cls.compute_checksum(pack)
        return pack.checksum == expected_checksum
