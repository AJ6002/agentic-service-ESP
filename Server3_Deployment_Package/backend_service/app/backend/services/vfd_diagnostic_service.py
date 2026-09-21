"""
VFD Diagnostic Service — ESP_APM_models Live Bridge
====================================================
Wraps a lazily-loaded WellDiagnosticEngine singleton and turns each incoming
MQTT telemetry payload into a structured diagnostic record:

    raw MQTT payload
        -> extract_vfd_signals()            (backend/transformer.py)
        -> WellDiagnosticEngine.evaluate_live_telemetry()   (ESP_APM_models)
        -> JSONL log line (append-only, one record per evaluation)
        -> pretty console "Operator Diagnostic Intelligence Card" (demo visual)

The JSONL log is the durable hand-off surface: esp_agent (or any other reader)
can tail/parse cced_esp/data/logs/vfd_diagnostics.jsonl without needing a live
socket connection into this process.

This module is purely additive — it does not touch opg_well_telemetry writes,
transform_mqtt_payload(), or the old 5-model unified_pipeline.py. If
ESP_APM_models fails to import, every method degrades to a safe no-op so the
MQTT batch-writer loop is never blocked or crashed by this service.
"""

import os
import sys
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("opg.vfd_diagnostic_service")

# -- Make ML models importable (located in code/models) ---
_WORKSPACE_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
_CODE_DIR = os.path.join(_WORKSPACE_ROOT, "code")
for p in [_CODE_DIR, _WORKSPACE_ROOT]:
    if p not in sys.path:
        sys.path.append(p)

try:
    try:
        from models.diagnostic_engine import WellDiagnosticEngine
    except ImportError:
        from code.models.diagnostic_engine import WellDiagnosticEngine
    _ENGINE_IMPORTABLE = True
except Exception as e:  # pragma: no cover — defensive, never block the MQTT pipeline
    logger.warning(f"[vfd_diagnostic_service] ML models not importable: {e}")
    WellDiagnosticEngine = None  # type: ignore
    _ENGINE_IMPORTABLE = False

from backend.transformer import extract_vfd_signals

_LOG_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "data" / "logs"
_LOG_FILE = _LOG_DIR / "vfd_diagnostics.jsonl"


class VFDDiagnosticService:
    """
    Live bridge from raw MQTT telemetry payloads to ESP_APM_models.WellDiagnosticEngine,
    persisting every evaluation as a JSONL record for downstream (agent) consumption.
    """

    def __init__(self, log_file: Optional[Path] = None, console_card: bool = True):
        self.log_file = log_file or _LOG_FILE
        self.console_card = console_card
        self._engine: Optional["WellDiagnosticEngine"] = None
        self._engine_ready = False
        self._prev_by_well: Dict[str, Dict[str, float]] = {}
        # In-memory "latest diagnosis per well" cache — the primary read path for
        # esp_agent's LiveDataBridge (via a small REST endpoint), avoiding cross-process
        # JSONL tailing/partial-line races entirely. The JSONL log remains the durable
        # audit trail; this cache is just the fast, always-current snapshot.
        self._latest_by_well: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()  # guards _prev_by_well/_latest_by_well + file append

        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        if _ENGINE_IMPORTABLE:
            try:
                self._engine = WellDiagnosticEngine()
                self._engine_ready = True
                logger.info("[vfd_diagnostic_service] WellDiagnosticEngine loaded successfully.")
                # Pre-warm cache for all known wells in background thread
                threading.Thread(target=self.prewarm_cache_from_db, daemon=True).start()
            except Exception as e:
                logger.error(f"[vfd_diagnostic_service] Failed to initialise WellDiagnosticEngine: {e}")

    @property
    def is_ready(self) -> bool:
        return self._engine_ready

    def evaluate_single_well_from_db(self, well_id: str) -> Optional[Dict[str, Any]]:
        """Evaluates a single well on-demand using its latest row in normalized.db."""
        if not self._engine_ready or self._engine is None:
            return None
        import sqlite3
        norm_db_path = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "data" / "normalized.db"
        if not norm_db_path.exists():
            return None
        try:
            with sqlite3.connect(str(norm_db_path)) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute(
                    "SELECT * FROM opg_normalized_telemetry WHERE Wells = ? ORDER BY id DESC LIMIT 1",
                    (well_id,)
                )
                row = c.fetchone()
                if not row:
                    return None
                raw_dict = {
                    "Report_DateTime": row["timestamp"],
                    "Inp bar/psi": row["Inp bar/psi"],
                    "Int temp °C": row["Int temp °C"],
                    "Motor temp °C": row["Motor temp °C"],
                    "Disch pr. Bar/psi": row["Disch pr. Bar/psi"],
                    "Vibration G's-Vx": row["Vibration G's-Vx"],
                    "Leak Current Ct": row["Leak Current Ct"],
                    "Volt": row["Volt"],
                    "VSD Amps/Load": row["VSD Amps/Load"],
                    "Frequency": row["Frequency"],
                    "DHG Current": row["DHG Current"],
                    "WHP (PSI)": row["WHP (PSI)"],
                    "FLP (PSI)": row["FLP (PSI)"],
                    "AP (PSI)": row["AP (PSI)"],
                    "VFD STS": row["VFD STS"],
                }
                return self._engine.evaluate_live_telemetry(well_id, raw_dict, verbose=False)
        except Exception as e:
            logger.debug(f"[vfd_diagnostic_service] On-demand evaluation failed for {well_id}: {e}")
            return None

    def prewarm_cache_from_db(self, max_wells: int = 50):
        """Pre-warms in-memory cache for all wells from normalized.db on startup."""
        if not self._engine_ready or self._engine is None:
            return
        import sqlite3
        norm_db_path = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "data" / "normalized.db"
        if not norm_db_path.exists():
            return
        try:
            with sqlite3.connect(str(norm_db_path)) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT DISTINCT Wells FROM opg_normalized_telemetry ORDER BY Wells")
                wells = [r[0] for r in c.fetchall()]
                count = 0
                for w in wells[:max_wells]:
                    res = self.evaluate_single_well_from_db(w)
                    if res:
                        with self._lock:
                            self._latest_by_well[str(w).upper()] = res
                        count += 1
                logger.info(f"[vfd_diagnostic_service] Pre-warmed model diagnostics cache for {count} wells from normalized.db.")
        except Exception as e:
            logger.warning(f"[vfd_diagnostic_service] Pre-warming cache from normalized.db failed: {e}")

    def get_latest(self, well_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent diagnosis for a well. Evaluates on-demand from DB if not yet cached."""
        key = str(well_id).upper()
        with self._lock:
            cached = self._latest_by_well.get(key)
        if cached is not None:
            return cached

        # Fallback: on-demand instant evaluation from normalized.db
        res = self.evaluate_single_well_from_db(well_id)
        if res:
            with self._lock:
                self._latest_by_well[key] = res
            return res
        return None

    def get_all_latest(self) -> Dict[str, Dict[str, Any]]:
        """Return the latest diagnosis for every well seen so far, keyed by well_id."""
        with self._lock:
            return dict(self._latest_by_well)

    def process(self, payload: Dict[str, Any], well_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluate one raw MQTT telemetry payload through WellDiagnosticEngine.

        Args:
            payload: raw MQTT payload dict (same shape passed to transform_mqtt_payload).
            well_id: explicit well ID override; falls back to payload's own well_id fields.

        Returns:
            The full result dict from evaluate_live_telemetry(), or None if the engine
            is unavailable or no VFD-mappable signals could be resolved from the payload.
        """
        if not self._engine_ready or self._engine is None:
            return None

        resolved_id = str(
            well_id
            or payload.get("well_id") or payload.get("wellId") or payload.get("WellID")
            or payload.get("well") or "UNKNOWN"
        ).upper()

        raw_vfd = extract_vfd_signals(payload)
        if not raw_vfd:
            # Nothing mappable in this payload — skip rather than feed the engine an
            # all-defaults vector that would misrepresent a genuine reading.
            return None

        with self._lock:
            prev_vfd = self._prev_by_well.get(resolved_id)

            try:
                result = self._engine.evaluate_live_telemetry(
                    well_id=resolved_id,
                    raw_telemetry=raw_vfd,
                    prev_telemetry=prev_vfd,
                    verbose=False,
                )
            except Exception as e:
                logger.error(f"[vfd_diagnostic_service] Engine evaluation failed for well '{resolved_id}': {e}")
                return None

            self._prev_by_well[resolved_id] = raw_vfd
            self._latest_by_well[resolved_id] = result

        self._append_jsonl(resolved_id, result)

        if self.console_card:
            try:
                self._engine.print_diagnostic_card(result)
            except Exception as e:  # pragma: no cover — cosmetic only, never fatal
                logger.debug(f"[vfd_diagnostic_service] Console card print failed: {e}")

        return result

    def _append_jsonl(self, well_id: str, result: Dict[str, Any]) -> None:
        """Append one structured diagnostic record. Thread-safe via the same lock as process()."""
        record = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "well_id": well_id,
            "family": result.get("family"),
            "engine_timestamp": result.get("timestamp"),
            "diagnostic": result.get("diagnostic"),
            "dynamics": result.get("dynamics"),
            "ml_anomaly": result.get("ml_anomaly"),
            "raw_measurements": result.get("raw_measurements"),
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except Exception as e:  # pragma: no cover — never let a disk/IO issue crash ingestion
            logger.error(f"[vfd_diagnostic_service] Failed to append JSONL record: {e}")


# Module-level singleton — mirrors the health_index_predictor.py pattern used elsewhere
# in cced_esp, so main.py / mqtt_collector.py can just `from backend.services.vfd_diagnostic_service
# import vfd_diagnostic_service` and call `.process(payload)`.
vfd_diagnostic_service = VFDDiagnosticService()
