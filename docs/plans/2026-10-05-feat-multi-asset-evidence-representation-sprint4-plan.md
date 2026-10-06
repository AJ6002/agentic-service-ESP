# Sprint 4 Plan: Multi-Asset Evidence Representation

```yaml
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
docs_root: docs
created_at: 2026-10-05
updated_at: 2026-10-05
```

---

## 1. Goal Capsule

Extend the Evidence representation, QoD engine, and Evidence Formatter to natively support both single-asset and multi-asset/fleet evidence:
1. **`EvidenceItem.asset_id`**: Add optional `asset_id: Optional[str] = None` field to the `EvidenceItem` contract. Single-asset tools set `asset_id`; fleet/multi-asset tools leave `asset_id = None` and carry per-well arrays in payload.
2. **Multi-Asset Formatter**: Extend `FormattedValue` with `well_id: Optional[str] = None`. Add `by_well_and_signal(well_id, signal)` to `FormattedEvidence` using bidirectional well ID normalization (`get_well_id_variants`), while retaining `by_signal(signal)` for 100% backward compatibility.
3. **Multi-Well Extraction**: Update `_extract_from_item` to extract per-well metrics from `payload["wells"]` arrays (e.g. from `get_fleet_health` and future multi-well endpoints).
4. **QoD Gate Validation**: Ensure multi-well payloads pass QoD without `MISSING_ASSET_ID` rejections and populate `EvidenceItem.asset_id` appropriately.
5. **Sealing & Storage**: Verify multi-asset evidence packs seal cleanly into `EvidencePack` with zero new storage keys required.

---

## 2. Technical Context & Exact File References

- **Evidence Contract**: [`agent_service/app/contracts/evidence.py`](file:///a:/TAS-AI/ESP/agent_service/app/contracts/evidence.py#L19-L28)
  - `EvidenceItem`: add `asset_id: Optional[str] = None`.
- **Evidence Formatter**: [`agent_service/app/evidence/formatter.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/formatter.py)
  - `FormattedValue`: add `well_id: Optional[str] = None`.
  - `FormattedEvidence`: add `by_well_and_signal(well_id: str, signal: str) -> Optional[FormattedValue]`, `all_by_signal(signal: str) -> list[FormattedValue]`, `events_by_well(well_id: str) -> list[FormattedEventRecord]`.
  - `_extract_from_item`: populate `well_id` on single-well items and iterate over `payload.get("wells")` for multi-well items.
- **QoD Engine**: [`agent_service/app/evidence/qod.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/qod.py#L207-L220)
  - Extract `asset_id` from payload (`well_id` or `asset_id`) when instantiating `EvidenceItem`.
  - Range sanity for `fleet_health_score` and `total_production_bpd`.
- **Well ID Normalizer**: [`agent_service/app/gateway/adapters/common.py:18-49`](file:///a:/TAS-AI/ESP/agent_service/app/gateway/adapters/common.py#L18-L49)
  - `get_well_id_variants(well_id)` for bidirectional matching (e.g. `FS-17` <-> `FS-017`).
- **Existing Test Suites**:
  - [`agent_service/tests/test_fleet_tools.py`](file:///a:/TAS-AI/ESP/agent_service/tests/test_fleet_tools.py)
  - [`agent_service/tests/test_phase1_evidence.py`](file:///a:/TAS-AI/ESP/agent_service/tests/test_phase1_evidence.py)

---

## 3. Implementation Units

### U1: Extend `EvidenceItem` Contract with `asset_id`
- **File**: [`agent_service/app/contracts/evidence.py`](file:///a:/TAS-AI/ESP/agent_service/app/contracts/evidence.py#L19-L28)
- **Change**:
  ```python
  class EvidenceItem(BaseModel):
      evidence_id: str
      tool: str
      source_domain: str
      asset_id: Optional[str] = None
      fetched_at: datetime
      freshness_sec: float | None = None
      status: Literal["OK", "STALE", "PARTIAL"] = "OK"
      payload: dict[str, Any] = Field(default_factory=dict)
      unit_map: dict[str, str] = Field(default_factory=dict)
  ```
- **Verification**: `EvidenceItem` parses with or without `asset_id` (defaults to `None`).

---

### U2: Update QoD Validation to Populate `asset_id`
- **File**: [`agent_service/app/evidence/qod.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/qod.py#L207-L220)
- **Change**:
  ```python
  raw_asset = payload.get("well_id") or payload.get("asset_id")
  asset_id = str(raw_asset).strip() if raw_asset else None

  item = EvidenceItem(
      evidence_id=evidence_id,
      tool=tool,
      source_domain=source_domain,
      asset_id=asset_id,
      fetched_at=fetched_at,
      status=freshness_status,
      payload=payload,
      unit_map=unit_map,
  )
  ```
  And add fleet range checks in `_TOPLEVEL_RANGE_FIELDS`:
  ```python
  "fleet_health_score": (None, (0.0, 100.0)),
  "total_production_bpd": (None, (0.0, 1000000.0)),
  ```
- **Verification**: Single-well payloads yield `item.asset_id == "FS-17"`; fleet payloads yield `item.asset_id is None`.

---

### U3: Extend Formatter with `well_id` & `by_well_and_signal`
- **File**: [`agent_service/app/evidence/formatter.py`](file:///a:/TAS-AI/ESP/agent_service/app/evidence/formatter.py)
- **Changes**:
  1. Add `well_id: Optional[str] = None` to `FormattedValue`.
  2. Implement `by_well_and_signal(self, well_id: str, signal: str) -> Optional[FormattedValue]`:
     - Match `v.signal == signal` and `v.well_id` against `get_well_id_variants(well_id)`.
  3. Implement `all_by_signal(self, signal: str) -> list[FormattedValue]`.
  4. Implement `events_by_well(self, well_id: str) -> list[FormattedEventRecord]`.
  5. In `_extract_from_item`:
     - Assign `well_id = item.asset_id or payload.get("well_id")` for all standard extracted values.
     - Extract `payload.get("wells")` array if present (e.g. from `get_fleet_health`):
       - For each well item: extract `health_score` and `health_band` tagged with `w["well_id"]`.
- **Verification**: Formatter can query both global `by_signal("fleet_health_score")` and per-well `by_well_and_signal("FS-17", "health_score")`.

---

### U4: Unit & Integration Tests for Multi-Asset Evidence
- **File**: `agent_service/tests/test_multi_asset_evidence.py`
- **Test Scenarios**:
  1. `test_evidence_item_asset_id_optional`: Single-asset has `asset_id`, fleet has `asset_id=None`.
  2. `test_qod_validates_multi_well_payloads`: `get_fleet_kpi`, `get_fleet_health`, `get_fleet_events` pass QoD and seal into `EvidencePack`.
  3. `test_formatter_by_signal_and_by_well_and_signal`:
     - `fmt.by_signal("total_production_bpd")` returns fleet total.
     - `fmt.by_well_and_signal("FS-17", "health_score")` returns FS-17's specific score.
     - `fmt.by_well_and_signal("FS-017", "health_score")` returns FS-17's score via unpadded/padded variant matching.
  4. `test_formatter_events_by_well`:
     - Filter fleet events by specific well ID.

---

## 4. Verification Contract & Definition of Done

1. **Contract Check**:
   ```python
   from app.contracts.evidence import EvidenceItem
   item_single = EvidenceItem(evidence_id="EV-1", tool="get_kpi", source_domain="kpi", asset_id="FS-17", fetched_at=datetime.now())
   assert item_single.asset_id == "FS-17"
   item_fleet = EvidenceItem(evidence_id="EV-2", tool="get_fleet_kpi", source_domain="kpi", fetched_at=datetime.now())
   assert item_fleet.asset_id is None
   ```
2. **Formatter Lookup**:
   ```python
   fmt = format_pack(pack)
   assert fmt.by_signal("fleet_health_score") is not None
   assert fmt.by_well_and_signal("FS-17", "health_score") is not None
   assert fmt.by_well_and_signal("FS-017", "health_score") is not None
   ```
3. **Automated Suite**:
   ```bash
   py -m pytest agent_service/tests/test_multi_asset_evidence.py agent_service/tests/test_fleet_tools.py agent_service/tests/objectives/test_manifests.py -v
   ```
   **Pass Criteria**: 100% green tests.
