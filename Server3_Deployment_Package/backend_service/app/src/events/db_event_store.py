"""
Durable PostgreSQL Event Store & Permanent Audit Repository
Grounded in Phase 6 Event-Driven Architecture Spec §4, §16
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3

from shared.schemas.event import ESPEvent, SeverityLevel

logger = logging.getLogger(__name__)


class DatabaseEventStore:
    """
    Durable Event Store persisting every published & processed event to PostgreSQL / DB.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("EVENT_DB_PATH", "esp_events.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_version TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_service TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    causation_id TEXT,
                    idempotency_key TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_asset_id ON events(asset_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_correlation_id ON events(correlation_id)")
            conn.commit()

    def save_event(self, event: ESPEvent, status: str = "PROCESSED") -> bool:
        """Persist ESPEvent into durable database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO events (
                        event_id, event_type, event_version, asset_id, tenant_id,
                        timestamp, source_service, source_version, severity, payload,
                        correlation_id, causation_id, idempotency_key, processed_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type,
                    event.event_version,
                    event.asset_id,
                    event.tenant_id,
                    event.timestamp,
                    event.source_service,
                    event.source_version,
                    event.severity.value if isinstance(event.severity, SeverityLevel) else str(event.severity),
                    json.dumps(event.payload),
                    event.correlation_id,
                    event.causation_id,
                    event.idempotency_key,
                    datetime.utcnow().isoformat() + "Z",
                    status
                ))
                conn.commit()
            return True
        except Exception as ex:
            logger.error(f"Failed to save event '{event.event_id}' to DatabaseEventStore: {ex}")
            return False

    def get_event(self, event_id: str) -> Optional[ESPEvent]:
        """Fetch single event by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, event_type, event_version, asset_id, tenant_id, timestamp, source_service, source_version, severity, payload, correlation_id, causation_id, idempotency_key FROM events WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ESPEvent(
                event_id=row[0],
                event_type=row[1],
                event_version=row[2],
                asset_id=row[3],
                tenant_id=row[4],
                timestamp=row[5],
                source_service=row[6],
                source_version=row[7],
                severity=SeverityLevel(row[8]),
                payload=json.loads(row[9]),
                correlation_id=row[10],
                causation_id=row[11],
                idempotency_key=row[12]
            )

    def list_events_by_asset(self, asset_id: str, limit: int = 50) -> List[ESPEvent]:
        """Query event history for a specific asset."""
        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, event_type, event_version, asset_id, tenant_id, timestamp, source_service, source_version, severity, payload, correlation_id, causation_id, idempotency_key FROM events WHERE asset_id = ? ORDER BY timestamp DESC LIMIT ?", (asset_id, limit))
            rows = cursor.fetchall()
            for r in rows:
                events.append(ESPEvent(
                    event_id=r[0], event_type=r[1], event_version=r[2], asset_id=r[3],
                    tenant_id=r[4], timestamp=r[5], source_service=r[6], source_version=r[7],
                    severity=SeverityLevel(r[8]), payload=json.loads(r[9]), correlation_id=r[10],
                    causation_id=r[11], idempotency_key=r[12]
                ))
        return events
