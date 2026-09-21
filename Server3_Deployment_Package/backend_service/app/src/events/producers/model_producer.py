"""
Model Event Producer
Grounded in Phase 6 Event-Driven Architecture Spec §7.2, §18
"""

import uuid
import logging
from typing import Dict, Any, Optional
from shared.schemas.event import ESPEvent, SeverityLevel
from src.events.publisher import EventPublisher, RedisStreamPublisher

logger = logging.getLogger(__name__)


class ModelEventProducer:
    """
    Producer emitting events based on ML / rule-based model outputs.
    """

    def __init__(self, publisher: Optional[EventPublisher] = None):
        self.publisher = publisher or RedisStreamPublisher()

    def emit_failure_risk_increased(self, asset_id: str, risk_7d: float, previous_risk_7d: float, correlation_id: str = "") -> str:
        """Emit FAILURE_RISK_INCREASED event."""
        evt = ESPEvent(
            event_id=f"EVT-MODEL-{uuid.uuid4().hex[:8]}",
            event_type="FAILURE_RISK_INCREASED",
            asset_id=asset_id,
            source_service="failure-risk-model",
            source_version="3.2",
            severity=SeverityLevel.HIGH,
            payload={
                "risk_7d": risk_7d,
                "previous_risk_7d": previous_risk_7d
            },
            correlation_id=correlation_id or f"RUN-{uuid.uuid4().hex[:6]}",
            idempotency_key=f"IDEMP-RISK-{asset_id}-{int(risk_7d*100)}"
        )
        return self.publisher.publish(evt, category="model")

    def emit_anomaly_detected(self, asset_id: str, anomaly_score: float, signal_tag: str, observed_value: float) -> str:
        """Emit ANOMALY_DETECTED event."""
        evt = ESPEvent(
            event_id=f"EVT-ANOM-{uuid.uuid4().hex[:8]}",
            event_type="ANOMALY_DETECTED",
            asset_id=asset_id,
            source_service="anomaly-detector",
            source_version="1.1",
            severity=SeverityLevel.MEDIUM,
            payload={
                "anomaly_score": anomaly_score,
                "signal_tag": signal_tag,
                "observed_value": observed_value
            },
            idempotency_key=f"IDEMP-ANOM-{asset_id}-{signal_tag}"
        )
        return self.publisher.publish(evt, category="model")
