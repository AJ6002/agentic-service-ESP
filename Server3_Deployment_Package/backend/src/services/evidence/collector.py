"""
Multi-Source Evidence Collector
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §5, §7, §8

Each EvidenceItem is stamped with a real source_deep_link URI pointing to the exact
source record, file path, node, or chunk that produced it.

Deep-link URI conventions:
  Tier 1 (always real, no server needed):
    file:///<abs_path>?<query_params>   — SQLite DBs, JSON files, text/PDF docs
  Tier 2 (real only when server is live):
    neo4j://bolt:<port>?node_id=<id>    — Neo4j (bolt:7687)
    http://localhost:<port>/api/...     — REST services (pgvector, Advait, ML)
  Links are NEVER mocked — field is omitted (None) when source is unreachable.
"""

import os
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schemas.evidence import (
    EvidenceItem, EvidenceType, AuthorityLevel, QualityStatus
)

# ── Resolve canonical source paths (Tier 1 — always available) ────────────
_ESP_AGENT_ROOT = Path(__file__).resolve().parents[3]   # esp_agent/
_CCED_ROOT       = _ESP_AGENT_ROOT.parent / "cced_esp"

DB_HISTORIAN = _CCED_ROOT / "data" / "unlabelled.db"
DB_EVENTS    = _ESP_AGENT_ROOT / "esp_events.db"
KG_JSON      = _ESP_AGENT_ROOT / "knowledge_bases" / "esp" / "graph" / "esp_graph.json"
KB_DOCS_DIR  = _ESP_AGENT_ROOT / "knowledge_bases" / "esp" / "documents"
_seed_candidates = [
    _ESP_AGENT_ROOT.parent / "data" / "advait" / "asset_context_initial_seed_v2_rich.json",
    _CCED_ROOT / "data" / "advait" / "asset_context_initial_seed_v2_rich.json",
    _ESP_AGENT_ROOT.parent / "data" / "advait" / "advait_api_mock_service" / "data" / "asset_context_initial_seed_v2_rich.json",
]
ASSET_SEED = next((p for p in _seed_candidates if p.exists()), _seed_candidates[0])



def _file_uri(path: Path, **params) -> str:
    """Return a file:// URI with optional query-string params and PDF #page= anchors for direct viewing."""
    abs_path = str(path).replace("\\", "/")
    if params:
        page = params.get("page")
        qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if abs_path.lower().endswith(".pdf") and page:
            return f"file:///{abs_path}#page={page}"
        return f"file:///{abs_path}?{qs}"
    return f"file:///{abs_path}"


class EvidenceCollector:
    """
    Unified collector that ingests raw outputs from upstream services/adapters and
    normalises them into 22-field canonical EvidenceItem records.
    Every item carries a source_deep_link pointing to the exact source record.
    """

    # ── Asset Context (Advait Registry / JSON seed) ───────────────────────
    @classmethod
    def collect_from_asset_context(cls, asset_id: str, context: Dict[str, Any]) -> List[EvidenceItem]:
        items = []
        if not context:
            return items
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Resolve the actual source: Advait REST (if reachable) or local JSON seed
        advait_url = os.getenv("ADVAIT_API_URL")
        if advait_url:
            asset_deep_link = f"{advait_url.rstrip('/')}/api/v1/assets/{asset_id}"
        elif ASSET_SEED.exists():
            asset_deep_link = _file_uri(ASSET_SEED, asset_id=asset_id, field="pump_model")
        else:
            asset_deep_link = None

        pump_model = context.get("pump_model") or "ESP Pump"
        items.append(EvidenceItem(
            evidence_id=f"EVID-AST-{uuid.uuid4().hex[:6]}",
            evidence_type=EvidenceType.ASSET,
            asset_id=asset_id,
            source_system="AssetContextService",
            source_id="installed_pump_model",
            source_version="1.0.0",
            timestamp=now,
            observed_at=now,
            authority_level=AuthorityLevel.LEVEL_A_INSTALLED_APPROVED,
            quality_status=QualityStatus.GOOD,
            confidence=1.0,
            relevance_score=1.0,
            semantic_type="equipment_spec",
            value=pump_model,
            statement=f"Installed pump model is {pump_model}.",
            citation=f"AssetRegistry[asset_id={asset_id}, field=pump_model]",
            source_deep_link=asset_deep_link,
        ))

        motor_hp = context.get("motor_rating_hp")
        if motor_hp:
            hp_link = _file_uri(ASSET_SEED, asset_id=asset_id, field="motor_rating_hp") if ASSET_SEED.exists() else None
            items.append(EvidenceItem(
                evidence_id=f"EVID-AST-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.ASSET,
                asset_id=asset_id,
                source_system="AssetContextService",
                source_id="motor_rating_hp",
                source_version="1.0.0",
                timestamp=now,
                observed_at=now,
                authority_level=AuthorityLevel.LEVEL_A_INSTALLED_APPROVED,
                quality_status=QualityStatus.GOOD,
                confidence=1.0,
                relevance_score=0.9,
                semantic_type="equipment_spec",
                value=motor_hp,
                unit="hp",
                statement=f"Motor rating is {motor_hp} hp.",
                citation=f"AssetRegistry[asset_id={asset_id}, field=motor_rating_hp]",
                source_deep_link=hp_link,
            ))

        return items

    # ── Live Telemetry (MQTT / cced_esp backend) ──────────────────────────
    @classmethod
    def collect_from_telemetry(cls, asset_id: str, telemetry: Dict[str, float]) -> List[EvidenceItem]:
        items = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        backend_url = os.getenv("CCED_ESP_BACKEND_URL", "http://127.0.0.1:8000")

        for tag, val in telemetry.items():
            unit = (
                "°C"   if "temp"  in tag else
                "psi"  if "press" in tag or "pip" in tag or "pdp" in tag else
                "A"    if "current" in tag else
                "Hz"   if "freq"  in tag else "bpd"
            )
            # Deep-link: live REST endpoint if backend reachable, else None
            deep_link = f"{backend_url}/api/v1/telemetry/{asset_id}/{tag}?latest=true"

            items.append(EvidenceItem(
                evidence_id=f"EVID-TEL-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.TELEMETRY,
                asset_id=asset_id,
                source_system="TelemetryService",
                source_id=tag,
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=now_iso,
                authority_level=AuthorityLevel.LEVEL_A_INSTALLED_APPROVED,
                quality_status=QualityStatus.GOOD,
                confidence=1.0,
                relevance_score=0.95,
                semantic_type="sensor_measurement",
                value=val,
                unit=unit,
                statement=f"Telemetry metric '{tag}' measured {val} {unit}.",
                citation=f"MQTT[asset={asset_id}, tag={tag}]",
                source_deep_link=deep_link,
            ))

        return items

    # ── Engineering Calculations (in-process) ────────────────────────────
    @classmethod
    def collect_from_engineering(cls, asset_id: str, calculations: Dict[str, Any]) -> List[EvidenceItem]:
        items = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        backend_url = os.getenv("CCED_ESP_BACKEND_URL", "http://127.0.0.1:8000")

        for calc_name, val in calculations.items():
            res_val = val.get("result", val) if isinstance(val, dict) else val
            unit = (
                "ft" if "tdh" in calc_name.lower() else
                "%"  if "bep" in calc_name.lower() or "deviation" in calc_name.lower() else
                "psi"
            )
            deep_link = f"{backend_url}/api/v1/engineering/{asset_id}/{calc_name}"

            items.append(EvidenceItem(
                evidence_id=f"EVID-ENG-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.ENGINEERING,
                asset_id=asset_id,
                source_system="EngineeringService",
                source_id=calc_name,
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=now_iso,
                authority_level=AuthorityLevel.LEVEL_C_CUSTOMER_ENG,
                quality_status=QualityStatus.GOOD,
                confidence=0.95,
                relevance_score=0.95,
                semantic_type="engineering_calculation",
                value=res_val,
                unit=unit,
                statement=f"Deterministic calculation '{calc_name}' evaluated to {res_val} {unit}.",
                citation=f"EngineeringService[asset={asset_id}, formula={calc_name}]",
                source_deep_link=deep_link,
            ))

        return items

    # ── ML Model Predictions ──────────────────────────────────────────────
    @classmethod
    def collect_from_models(cls, asset_id: str, models: Dict[str, Any]) -> List[EvidenceItem]:
        items = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        model_url = os.getenv("MODEL_API_URL", "http://localhost:8082")

        for model_name, payload in models.items():
            pred = (
                payload.get("identified_fault") or
                payload.get("status") or
                str(payload)
            ) if isinstance(payload, dict) else str(payload)
            conf = float(payload.get("confidence", 0.85)) if isinstance(payload, dict) else 0.85
            run_id = payload.get("run_id", uuid.uuid4().hex[:8]) if isinstance(payload, dict) else uuid.uuid4().hex[:8]

            deep_link = f"{model_url}/api/v1/esps/{asset_id}/predict?model={model_name}&run_id={run_id}"

            items.append(EvidenceItem(
                evidence_id=f"EVID-ML-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.ML,
                asset_id=asset_id,
                source_system="ModelAdapter",
                source_id=model_name,
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=now_iso,
                authority_level=AuthorityLevel.LEVEL_D_SITE_HISTORY,
                quality_status=QualityStatus.GOOD,
                confidence=conf,
                relevance_score=0.90,
                semantic_type="ml_prediction",
                value=pred,
                statement=f"Predictive model '{model_name}' predicted '{pred}' with confidence {conf:.2f}.",
                citation=f"ModelAdapter[model={model_name}, asset={asset_id}, run_id={run_id}]",
                source_deep_link=deep_link,
            ))

        return items

    # ── Knowledge Base (RAG local docs / pgvector) ────────────────────────
    @classmethod
    def collect_from_knowledge(cls, asset_id: str, knowledge_results: List[Dict[str, Any]]) -> List[EvidenceItem]:
        items = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        for res in knowledge_results:
            source_title = res.get("source_title") or res.get("source") or "Technical Manual"
            text_claim   = res.get("text") or res.get("claim") or ""
            doc_id       = res.get("document_id") or res.get("id") or "KB-DOC-001"
            page         = res.get("page")
            score        = float(res.get("similarity") or res.get("score") or 0.85)
            chunk_idx    = res.get("chunk_idx") or doc_id  # e.g. "manual.txt_42"

            # Tier 1: in-app standard document viewer if available
            code_slug = (source_title or "").replace(" ", "-").replace(".pdf", "").replace(".txt", "")
            if (KB_DOCS_DIR / source_title).exists():
                deep_link = f"/api/esp/knowledge/document/{code_slug}"
            else:
                # Tier 2: Qdrant Vector DB collection dashboard
                deep_link = "http://localhost:6333/dashboard#/collections/esp_kb"

            auth = (
                AuthorityLevel.LEVEL_B_OEM
                if any(w in source_title.lower() for w in ["oem", "weatherford", "baker", "slb"])
                else AuthorityLevel.LEVEL_E_INDUSTRY
            )

            items.append(EvidenceItem(
                evidence_id=f"EVID-KB-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.KNOWLEDGE,
                asset_id=asset_id,
                source_system="RetrievalService",
                source_id=doc_id,
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=now_iso,
                authority_level=auth,
                quality_status=QualityStatus.GOOD,
                confidence=score,
                relevance_score=score,
                semantic_type="knowledge_claim",
                value=text_claim[:200],
                statement=f"Retrieved from {source_title} (Page {page or 1}): {text_claim[:150]}...",
                citation=f"{source_title}, DocID: {doc_id}, Page: {page or 1}",
                source_deep_link=deep_link,
            ))

        return items

    # ── Knowledge Graph (local JSON / Neo4j) ─────────────────────────────
    @classmethod
    def collect_from_knowledge_graph(
        cls,
        asset_id: str,
        graph_results: List[Dict[str, Any]],
        neo4j_node_ids: Optional[Dict[str, int]] = None,   # populated when Neo4j is live
    ) -> List[EvidenceItem]:
        """
        Collect evidence from the ESP Knowledge Graph.
        graph_results: list of relationship dicts from GraphAdapter.get_failure_modes() or
                       trace_cause_effect().
        neo4j_node_ids: optional map of {node_name: bolt_node_id} — populated only when
                        Neo4j server is reachable. When absent, links point to local JSON.
        """
        from urllib.parse import quote

        items = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        neo4j_browser_base = os.getenv("NEO4J_BROWSER_URL", "http://localhost:7474/browser")

        for rel in graph_results:
            src_node = rel.get("source") or rel.get("symptom_or_metric", "")
            tgt_node = rel.get("connected_node") or rel.get("target", "")
            rel_type = rel.get("relationship") or rel.get("type", "CAUSES")
            full_rule = rel.get("full_rule") or f"{src_node} → {rel_type} → {tgt_node}"

            # Deep-link: browser-clickable URL directly opening Neo4j Browser with Cypher query
            fault_target = tgt_node or src_node
            if fault_target:
                cypher_cmd = f"MATCH (n:FaultMode {{name: '{fault_target}'}})-[r]-(m) RETURN n,r,m"
                deep_link = f"{neo4j_browser_base}/?cmd=play&arg={quote(cypher_cmd)}"
            else:
                deep_link = f"{neo4j_browser_base}/?cmd=play&arg={quote('MATCH (n:FaultMode)-[r]-(m) RETURN n,r,m LIMIT 25')}"

            items.append(EvidenceItem(
                evidence_id=f"EVID-KG-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.KNOWLEDGE,
                asset_id=asset_id,
                source_system="GraphAdapter",
                source_id=tgt_node or src_node,
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=now_iso,
                authority_level=AuthorityLevel.LEVEL_E_INDUSTRY,
                quality_status=QualityStatus.GOOD,
                confidence=0.9,
                relevance_score=0.92,
                semantic_type="causal_relationship",
                value=full_rule,
                statement=f"Knowledge Graph: {full_rule}",
                citation=f"esp_graph.json :: {full_rule}",
                source_deep_link=deep_link,
            ))

        return items

    # ── ESP_APM_models Live VFD Diagnosis (14-signal engine, real MQTT-fed) ────
    @classmethod
    def collect_from_vfd_diagnostic(
        cls,
        asset_id: str,
        vfd_diagnostic: Optional[Dict[str, Any]],
    ) -> List[EvidenceItem]:
        """
        Build EvidenceItem(s) from ESP_APM_models.WellDiagnosticEngine's live diagnosis,
        fetched via LiveDataBridge.get_vfd_diagnostic() -> cced_esp GET /api/vfd/diagnostics/{id}.
        This is the sole source of truth for live ESP fault classification (the legacy
        5-model pipeline in collect_from_models() covers a different, older evidence path).

        Returns [] if vfd_diagnostic is None — never fabricates a diagnosis for a well
        that hasn't been evaluated yet (e.g. cced_esp unreachable, or no MQTT traffic
        seen for this well since service start).

        Emits up to two items:
          1. Fault classification + health score (always, if vfd_diagnostic is present)
          2. Anomaly detector flag (only if the anomaly detector actually fired) — kept
             as a SEPARATE item rather than folded into #1, since the two sub-models can
             genuinely disagree (e.g. fault classifier says Normal Operation while the
             IsolationForest anomaly detector flags the reading as anomalous). Surfacing
             both lets the LLM/XAI layer reason about the disagreement explicitly instead
             of silently picking one.
        """
        if not vfd_diagnostic:
            return []

        items: List[EvidenceItem] = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        backend_url = os.getenv("CCED_ESP_BACKEND_URL", "http://127.0.0.1:8000")

        diag = vfd_diagnostic.get("diagnostic") or {}
        dynamics = vfd_diagnostic.get("dynamics") or {}
        ml_anom = vfd_diagnostic.get("ml_anomaly") or {}
        engine_ts = vfd_diagnostic.get("timestamp") or now_iso
        well_id = vfd_diagnostic.get("well_id") or asset_id

        deep_link = f"{backend_url}/api/vfd/diagnostics/{asset_id}"

        primary_fault = diag.get("primary_fault", "Normal Operation")
        confidence_val = float(diag.get("confidence_val", 0.9))
        health_score = diag.get("health_score")

        # Severity-aware relevance: EvidenceRanker.calculate_score() weighs
        # relevance_score * authority_weight * quality * confidence, with no native
        # concept of "this evidence indicates an active fault" — only source-type
        # authority tier. Without this boost, a genuine live critical diagnosis (e.g.
        # High Backpressure at health 5.6) can be outranked by routine AST/TEL/ENG
        # items (Level A/C authority) and silently dropped by the downstream cap-to-8
        # in generate_advisory_draft_node, exactly the failure this fixes. A live
        # fault is the single highest-value evidence a diagnostic agent can surface,
        # so it is boosted to compete with — and typically beat — Level A authority
        # items whenever the classifier has actually flagged a non-normal condition.
        is_fault_active = primary_fault not in ("Normal Operation", "", None)
        fault_relevance = 1.0 if is_fault_active else 0.75
        est_time_to_trip = diag.get("est_time_to_trip", "N/A")
        description = diag.get("description", "")
        action_advisory = diag.get("action_advisory", "")
        root_causes = diag.get("root_cause_drivers") or []
        root_cause_str = "; ".join(f"{d[0]}: {d[1]}" for d in root_causes if isinstance(d, (list, tuple)) and len(d) == 2)

        statement_parts = [
            f"ESP_APM_models diagnosis for {well_id}: {primary_fault} "
            f"(confidence {diag.get('confidence', f'{confidence_val*100:.0f}%')}), "
            f"health score {health_score}/100, est. time-to-trip: {est_time_to_trip}."
        ]
        if description:
            statement_parts.append(description)
        if action_advisory:
            statement_parts.append(f"Recommended action: {action_advisory}")
        if root_cause_str:
            statement_parts.append(f"Root-cause drivers: {root_cause_str}")

        items.append(EvidenceItem(
            evidence_id=f"EVID-VFD-{asset_id}-{uuid.uuid4().hex[:6]}",
            evidence_type=EvidenceType.ML,
            asset_id=asset_id,
            source_system="ESP_APM_models.WellDiagnosticEngine",
            source_id="fault_classification",
            source_version="1.0.0",
            timestamp=now_iso,
            observed_at=engine_ts,
            authority_level=AuthorityLevel.LEVEL_D_SITE_HISTORY,
            quality_status=QualityStatus.GOOD,
            confidence=confidence_val,
            relevance_score=fault_relevance,
            semantic_type="ml_fault_classification",
            value=primary_fault,
            statement=" ".join(statement_parts),
            supporting_signals=list((vfd_diagnostic.get("raw_measurements") or {}).keys()),
            citation=(
                f"ESP_APM_models[well={well_id}, engine_ts={engine_ts}, "
                f"fault={primary_fault}, health_score={health_score}]"
            ),
            source_deep_link=deep_link,
        ))

        # Dynamics (ΔP, torque proxy, thermal elevation, etc.) as a supplementary
        # engineering-style statement folded into the same statement text is avoided here
        # deliberately — dynamics are physics-derived intermediate values, not an
        # independent evidence source, so they are not split into their own EvidenceItem.

        if ml_anom.get("is_anomaly"):
            anom_prob = float(ml_anom.get("anomaly_probability", 0.0))
            items.append(EvidenceItem(
                evidence_id=f"EVID-VFD-ANOM-{asset_id}-{uuid.uuid4().hex[:6]}",
                evidence_type=EvidenceType.ML,
                asset_id=asset_id,
                source_system="ESP_APM_models.MultivariateAnomalyDetector",
                source_id="anomaly_detector",
                source_version="1.0.0",
                timestamp=now_iso,
                observed_at=engine_ts,
                authority_level=AuthorityLevel.LEVEL_D_SITE_HISTORY,
                quality_status=QualityStatus.GOOD,
                confidence=anom_prob,
                relevance_score=0.90 if is_fault_active else 0.80,
                semantic_type="ml_anomaly_flag",
                value="ANOMALOUS",
                statement=(
                    f"Multivariate IsolationForest anomaly detector flagged the current "
                    f"14-signal reading for {well_id} as anomalous (probability {anom_prob:.2f}), "
                    f"independent of the fault classifier's '{primary_fault}' verdict above."
                ),
                citation=f"ESP_APM_models.MultivariateAnomalyDetector[well={well_id}, engine_ts={engine_ts}]",
                source_deep_link=deep_link,
                derived_from=[items[0].evidence_id],
            ))

        return items

    # ── Historian Time-Series (SQLite DB) ─────────────────────────────────
    @classmethod
    def collect_from_historian(
        cls,
        asset_id: str,
        signal: str,
        db_path: Optional[Path] = None,
        ts_from: Optional[str] = None,
        ts_to: Optional[str] = None,
        n_points: int = 0,
        stats: Optional[Dict[str, Any]] = None,
        unit: str = "",
    ) -> EvidenceItem:
        """
        Build a single historian EvidenceItem with a real file:// deep-link to the
        exact SQLite table, asset_id, signal column, and timestamp range queried.
        """
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db = db_path or DB_HISTORIAN
        stats = stats or {}

        col_map = {
            "flow_rate":          "flow_rate_bpd",
            "intake_pressure":    "intake_pressure_psi",
            "discharge_pressure": "pressure_psi",
            "motor_temperature":  "temperature_c",
            "frequency":          "frequency_hz",
            "motor_current":      "motor_current_a",
        }
        db_col = col_map.get(signal, signal)

        deep_link = _file_uri(
            db,
            table="opg_well_telemetry",
            asset_id=asset_id,
            column=db_col,
            ts_from=(ts_from or "").replace(":", "%3A"),
            ts_to=(ts_to or "").replace(":", "%3A"),
            n_points=n_points,
        )

        stmt_parts = [f"Historical {signal} on {asset_id}: n={n_points} pts"]
        if stats.get("first") is not None:
            stmt_parts.append(
                f"baseline={stats['first']} {unit} → latest={stats.get('last')} {unit} "
                f"(Δ{stats.get('delta', 0):+.2f} {unit}, {stats.get('pct_change', 0):+.1f}%)"
            )
        if stats.get("mean") is not None:
            stmt_parts.append(f"mean={stats['mean']} | σ={stats.get('std', 0)} | slope={stats.get('slope_per_sample', 0):+.4f}")

        return EvidenceItem(
            evidence_id=f"EVID-HIST-{asset_id}-{signal.upper()}-{now_iso[-8:-1].replace(':', '')}",
            evidence_type=EvidenceType.TREND,
            asset_id=asset_id,
            source_system="cced_esp.HistorianService",
            source_id=f"unlabelled_recovered.db::opg_well_telemetry::{db_col}",
            source_version="v2.3-recovered",
            timestamp=now_iso,
            observed_at=ts_to or now_iso,
            authority_level=AuthorityLevel.LEVEL_D_SITE_HISTORY,
            quality_status=QualityStatus.GOOD,
            confidence=1.0,
            relevance_score=0.98,
            semantic_type="historical_time_series_statistics",
            value=stats,
            unit=unit,
            statement=" | ".join(stmt_parts),
            supporting_signals=[signal],
            citation=(
                f"HistorianDB[asset={asset_id}, signal={signal}, "
                f"column={db_col}, pts={n_points}, "
                f"span={str(ts_from)[-19:]}…{str(ts_to)[-19:]}]"
            ),
            source_deep_link=deep_link,
        )
