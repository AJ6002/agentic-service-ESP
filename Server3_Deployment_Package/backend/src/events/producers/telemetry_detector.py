"""
Telemetry Event Detector Producer
Grounded in Phase 6 Event-Driven Architecture Spec §7.1, §9, §18
"""

import uuid
import logging
from typing import Dict, Any, Optional
from shared.schemas.event import ESPEvent, SeverityLevel
from src.events.publisher import EventPublisher, RedisStreamPublisher

logger = logging.getLogger(__name__)


class TelemetryEventDetector:
    """
    Evaluates telemetry against operating envelope boundaries and emits operational events.
    Enforces Rule: Raw telemetry stays in Historian; only meaningful events enter Event Bus.
    """

    def __init__(self, publisher: Optional[EventPublisher] = None):
        self.publisher = publisher or RedisStreamPublisher()

    def evaluate_telemetry(self, asset_id: str, metrics: Dict[str, float]) -> Optional[str]:
        """
        Evaluate telemetry snapshot and emit event if threshold exceeded.
        """
        flow_rate = metrics.get("flow_rate", 1450.0)
        motor_temp = metrics.get("motor_temperature", 90.0)

        # Check production drop (> 15% drop from baseline 1720 BPD)
        if flow_rate < 1350.0:
            evt = ESPEvent(
                event_id=f"EVT-PROD-{uuid.uuid4().hex[:8]}",
                event_type="PRODUCTION_DECLINE_DETECTED",
                asset_id=asset_id,
                source_service="telemetry-detector",
                severity=SeverityLevel.MEDIUM,
                payload={
                    "current_flow_bpd": flow_rate,
                    "baseline_bpd": 1720.0,
                    "drop_pct": round((1720.0 - flow_rate) / 1720.0 * 100.0, 1)
                },
                idempotency_key=f"IDEMP-DECLINE-{asset_id}-{int(flow_rate)}"
            )
            return self.publisher.publish(evt, category="operational")

        # Check high motor temperature thermal warning
        if motor_temp > 130.0:
            evt = ESPEvent(
                event_id=f"EVT-THERM-{uuid.uuid4().hex[:8]}",
                event_type="THERMAL_RISK_INCREASED",
                asset_id=asset_id,
                source_service="telemetry-detector",
                severity=SeverityLevel.HIGH,
                payload={
                    "motor_temperature": motor_temp,
                    "limit_c": 130.0
                },
                idempotency_key=f"IDEMP-THERM-{asset_id}-{int(motor_temp)}"
            )
            return self.publisher.publish(evt, category="operational")

        return None
