"""
Live Paho-MQTT Telemetry Collector & Broker Listener
Subscribes to live ESP well telemetry, processes incoming packets through the full pipeline:
MQTT Input Stream -> labelled.db -> unlabelled.db -> normalized.db -> ML-Model-Layers
"""

import json
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
import paho.mqtt.client as mqtt
from pydantic import ValidationError

from src.contracts.mqtt_payloads import (
    TelemetryPayload,
    VFMPayload,
    AssetPayload,
    SimulatorStatus,
    EventPayload,
)
from src.services.well_data_cache import WellDataCacheService
from src.pipeline.pipeline_orchestrator import get_orchestrator

logger = logging.getLogger("mqtt_collector")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [MQTT] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

def _expand_well_keys(well_id: str) -> List[str]:
    """Generates all canonical casing and zero-padding key variants for robust well lookup."""
    if not well_id:
        return []
    clean = str(well_id).strip().upper()
    keys = {clean}
    if "-00" in clean:
        keys.add(clean.replace("-00", "-"))
    if "-0" in clean:
        keys.add(clean.replace("-0", "-"))
    parts = clean.split("-")
    if len(parts) == 2 and parts[1].isdigit():
        if len(parts[1]) == 1:
            keys.add(f"{parts[0]}-0{parts[1]}")
            keys.add(f"{parts[0]}-00{parts[1]}")
        elif len(parts[1]) == 2:
            keys.add(f"{parts[0]}-0{parts[1]}")
    return list(keys)

class MqttCollectorService:
    """Thread-safe background MQTT Collector service using Paho MQTT Client."""

    def __init__(self):
        self._lock = threading.Lock()
        self.broker_host: str = os.getenv("MQTT_BROKER_HOST", "192.168.1.155")
        self.broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        # Broker is confirmed anonymous (verified via mosquitto_sub with zero credentials).
        # Do NOT read MQTT_USERNAME/MQTT_PASSWORD from env here — a stale config.env, shell
        # variable, or git checkpoint has repeatedly reintroduced a broken "scada_operator"
        # credential that gets rejected by this anonymous broker (Return Code 5 / not authorized).
        # Connection is permanently anonymous; username_pw_set() is never called.
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.current_topic: str = "esp/#"
        self.topics: List[str] = ["esp/v1/+/telemetry", "esp/#", "opg/#"]
        
        self.is_connected: bool = False
        self.total_received: int = 0
        self.last_packet_time: Optional[str] = None
        self._recent_packets: deque = deque(maxlen=60)
        
        # Multi-topic storage for Digital Twin Simulator
        self.well_assets: Dict[str, Dict[str, Any]] = {}
        self.well_vfm: Dict[str, Dict[str, Any]] = {}
        self.well_alarms: Dict[str, List[Dict[str, Any]]] = {}
        self.simulator_status: Dict[str, Any] = {"online": True}

        # Rate tracking
        self._rate_window: deque = deque(maxlen=20)
        self.msg_rate_per_sec: float = 0.0

        self.client: Optional[mqtt.Client] = None
        self._running: bool = False
        self._broadcast_callbacks: List[Any] = []

    def register_broadcast_callback(self, cb: Any):
        """Registers a listener called synchronously or asynchronously on every live packet ingestion."""
        with self._lock:
            if cb not in self._broadcast_callbacks:
                self._broadcast_callbacks.append(cb)

    def unregister_broadcast_callback(self, cb: Any):
        """Unregisters a broadcast callback listener."""
        with self._lock:
            self._broadcast_callbacks = [c for c in self._broadcast_callbacks if c != cb]

    def get_status(self) -> Dict[str, Any]:
        """Returns the real-time status of the MQTT collector."""
        with self._lock:
            # Refresh rate calculation
            now = time.time()
            # Clean old entries older than 3 seconds
            while self._rate_window and (now - self._rate_window[0]) > 3.0:
                self._rate_window.popleft()
            rate = len(self._rate_window) / 3.0 if self.is_connected else 0.0

            return {
                "is_connected": self.is_connected,
                "is_running": self._running,
                "broker_host": self.broker_host,
                "broker_port": self.broker_port,
                "current_topic": self.current_topic,
                "topics": self.topics,
                "username": self.username,
                "total_received": self.total_received,
                "msg_rate_per_sec": round(rate, 2),
                "last_packet_time": self.last_packet_time,
                "simulator_status": self.simulator_status,
                "active_wells_count": len(self.well_assets)
            }

    def get_well_asset(self, well_id: str) -> Optional[Dict[str, Any]]:
        """Returns cached asset specifications and pump curve coefficients for a well."""
        with self._lock:
            for k in _expand_well_keys(well_id):
                if k in self.well_assets:
                    return self.well_assets[k]
            return None

    def get_well_vfm(self, well_id: str) -> Optional[Dict[str, Any]]:
        """Returns cached virtual flow metering (VFM) rates for a well."""
        with self._lock:
            for k in _expand_well_keys(well_id):
                if k in self.well_vfm:
                    return self.well_vfm[k]
            return None

    def get_well_alarms(self, well_id: str) -> List[Dict[str, Any]]:
        """Returns recent simulator alarm events for a well."""
        with self._lock:
            for k in _expand_well_keys(well_id):
                if k in self.well_alarms:
                    return list(self.well_alarms[k])
            return []

    def get_all_active_alarms(self) -> List[Dict[str, Any]]:
        """Returns fleet-wide recent simulator alarm events."""
        with self._lock:
            alarms = []
            for wid, al_list in self.well_alarms.items():
                for a in al_list[-3:]:
                    alarms.append({"well_id": wid, **a})
            alarms.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return alarms[:25]

    def get_recent_packets(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Returns the most recent incoming MQTT packets buffer."""
        with self._lock:
            pkts = list(self._recent_packets)
            pkts.reverse()
            return pkts[:limit]

    def connect(self, host: Optional[str] = None, port: Optional[int] = None, topic: Optional[str] = None) -> bool:
        """Connects the Paho client to the configured broker.

        Network teardown/setup (loop_stop/disconnect/connect_async) runs OUTSIDE self._lock.
        Previously the entire body ran under the lock, so any reconnect attempt (e.g. a
        broker drop leaving the socket in CLOSE_WAIT) froze every other collector method —
        including get_status(), which every /api/* status endpoint calls — for as long as
        the blocking Paho teardown took. Only pure state mutations are now lock-protected.
        """
        with self._lock:
            if host:
                self.broker_host = host
            if port:
                self.broker_port = int(port)
            if topic:
                self.current_topic = topic
            old_client = self.client
            self.client = None
            self.is_connected = False
            self._running = False

        self._teardown_client(old_client)

        logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port} (Topic: {self.current_topic})...")

        try:
            if hasattr(mqtt, "CallbackAPIVersion"):
                new_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"esp_apm_collector_{int(time.time())}")
            else:
                new_client = mqtt.Client(client_id=f"esp_apm_collector_{int(time.time())}")

            new_client.on_connect = self._on_connect
            new_client.on_disconnect = self._on_disconnect
            new_client.on_message = self._on_message

            new_client.connect_async(self.broker_host, int(self.broker_port), keepalive=60)
            new_client.loop_start()

            with self._lock:
                self.client = new_client
                self._running = True
            return True
        except Exception as e:
            logger.error(f"Failed to initiate connection to broker: {e}")
            with self._lock:
                self.is_connected = False
                self._running = False
            return False

    def start_simulation(self):
        """Simulation is permanently disabled. The system operates strictly on live field MQTT telemetry."""
        logger.warning("[MQTT] Simulation mode is permanently disabled. Operating strictly on real field MQTT broker streams.")
        return False

    def disconnect(self):
        """Disconnects the Paho client and stops the background loop."""
        with self._lock:
            old_client = self.client
            self.client = None
            self.is_connected = False
            self._running = False
        self._teardown_client(old_client)
        logger.info("Disconnected from MQTT broker.")

    @staticmethod
    def _teardown_client(client: "Optional[mqtt.Client]"):
        """Stops and disconnects a Paho client instance. Must be called OUTSIDE self._lock —
        loop_stop()/disconnect() perform blocking network I/O and can take seconds when the
        connection is already half-dead (e.g. a socket stuck in CLOSE_WAIT)."""
        if client:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass

    def update_config(self, host: Optional[str] = None, port: Optional[int] = None, topic: Optional[str] = None) -> Dict[str, Any]:
        """Dynamically re-subscribes to topic or reconnects to new broker host/port without dropping wildcard streams."""
        client_to_resubscribe = None
        with self._lock:
            reconnect_needed = False
            if host and host != self.broker_host:
                self.broker_host = host
                reconnect_needed = True
            if port and int(port) != self.broker_port:
                self.broker_port = int(port)
                reconnect_needed = True

            if topic:
                self.current_topic = topic
                if self.is_connected and self.client and not reconnect_needed:
                    client_to_resubscribe = self.client

        # Subscribe is network I/O — kept outside the lock so a slow/dead socket can't
        # block get_status() or any other collector method while this runs.
        if client_to_resubscribe:
            try:
                client_to_resubscribe.subscribe(self.current_topic, qos=1)
                for wildcard in self.topics:
                    client_to_resubscribe.subscribe(wildcard, qos=1)
                logger.info(f"Subscribed to topic: '{self.current_topic}' (Wildcard streams active)")
            except Exception as e:
                logger.warning(f"Error updating topic subscription: {e}")

        if reconnect_needed:
            self.connect()

        return self.get_status()

    # ── Internal Callbacks ───────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc_or_reason=None, properties=None, *args, **kwargs):
        rc_code = getattr(rc_or_reason, "value", rc_or_reason)
        if rc_code == 0 or rc_code is None:
            with self._lock:
                self.is_connected = True
            logger.info(f"Successfully connected to broker at {self.broker_host}:{self.broker_port}")
            for sub_top in set([self.current_topic] + self.topics):
                try:
                    client.subscribe(sub_top, qos=1)
                    logger.info(f"Subscribed to topic: {sub_top}")
                except Exception as e:
                    logger.error(f"Failed to subscribe to topic {sub_top}: {e}")
        else:
            with self._lock:
                self.is_connected = False
            logger.warning(f"Connection refused with code: {rc_code}")

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        with self._lock:
            self.is_connected = False
        logger.info("Broker disconnected.")

    def _on_message(self, client, userdata, msg):
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_clock = datetime.now().strftime("%H:%M:%S")
        raw_payload = msg.payload.decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw_payload)
            if not isinstance(payload, dict):
                payload = {"raw_value": payload}
        except Exception:
            payload = {"raw_text": raw_payload}

        # Topic structure inspection:
        # esp/v1/simulator/status
        # esp/v1/<well_id>/asset
        # esp/v1/<well_id>/telemetry
        # esp/v1/<well_id>/vfm
        # esp/v1/<well_id>/events
        parts = [p for p in msg.topic.strip("/").split("/") if p]
        topic_suffix = parts[-1].lower() if parts else "telemetry"

        well_id = payload.get("well_id") or payload.get("asset_id") or payload.get("WELL") or payload.get("asset")
        if not well_id:
            if len(parts) >= 3 and parts[2] not in ("+", "#", "simulator"):
                well_id = parts[2]
            else:
                import re
                m = re.search(r"\b(FSWS-[A-Za-z0-9\-]+|FS-\d+[A-Za-z0-9\-]*|FNW-[A-Za-z0-9\-]+|FWS-[A-Za-z0-9\-]+|ULFA-[A-Za-z0-9\-]+)\b", msg.topic, re.I)
                well_id = m.group(1).upper() if m else "FIELD_FLEET"

        # Phase 2 Deliverable 3.1: Validate against Phase 0 contract by topic type
        validated_telemetry: Optional[TelemetryPayload] = None
        validated_vfm: Optional[VFMPayload] = None
        validated_asset: Optional[AssetPayload] = None
        validated_status: Optional[SimulatorStatus] = None
        validated_event: Optional[EventPayload] = None

        try:
            if "status" in msg.topic.lower():
                validated_status = SimulatorStatus.model_validate(payload)
            elif topic_suffix == "telemetry":
                validated_telemetry = TelemetryPayload.model_validate(payload)
            elif topic_suffix == "vfm":
                validated_vfm = VFMPayload.model_validate(payload)
            elif topic_suffix == "asset":
                validated_asset = AssetPayload.model_validate(payload)
            elif topic_suffix == "events":
                # Edge-triggered well state-change notification (operating_state,
                # scenario, phase, trip_cause, alarms). NOT the same concept as the
                # agent-to-browser SSE AgentStreamEvent -- see mqtt_payloads.py §5.
                validated_event = EventPayload.model_validate(payload)
        except ValidationError as val_err:
            logger.warning(
                f"[MQTT] Validation failed for well '{well_id}' on topic '{msg.topic}': {val_err}"
            )
            return

        # Phase 2 Deliverable 3.2: Update process-singleton WellDataCacheService
        cache_service = WellDataCacheService.get_instance()
        if validated_telemetry is not None:
            cache_service.update_telemetry(well_id, validated_telemetry)
        elif validated_vfm is not None:
            cache_service.update_vfm(well_id, validated_vfm)
        elif validated_asset is not None:
            cache_service.update_asset(well_id, validated_asset)
        elif validated_event is not None:
            cache_service.record_event(well_id, validated_event)

        # 1. Handle Simulator Heartbeat Status
        if "status" in msg.topic.lower():
            status_dict = validated_status.model_dump() if validated_status else payload
            with self._lock:
                self.simulator_status = status_dict
                self.total_received += 1
                self.last_packet_time = now_ts
                self._rate_window.append(time.time())
                self._recent_packets.append({
                    "id": self.total_received,
                    "timestamp": time_clock,
                    "topic": msg.topic,
                    "well_id": "SIMULATOR",
                    "preview": status_dict,
                    "raw_json": raw_payload[:300]
                })
            status_msg = {"type": "SIMULATOR_STATUS", "data": status_dict, "status": status_dict}
            for cb in list(self._broadcast_callbacks):
                try: cb(status_msg)
                except Exception: pass
            return

        # 2. Handle Asset Specifications & Curve Coefficients
        if topic_suffix == "asset":
            asset_dict = validated_asset.model_dump() if validated_asset else payload
            keys = _expand_well_keys(well_id)
            with self._lock:
                for k in keys:
                    self.well_assets[k] = asset_dict
                self.total_received += 1
                self.last_packet_time = now_ts
                self._rate_window.append(time.time())
                self._recent_packets.append({
                    "id": self.total_received,
                    "timestamp": time_clock,
                    "topic": msg.topic,
                    "well_id": well_id,
                    "preview": {k: asset_dict[k] for k in list(asset_dict.keys())[:6]},
                    "raw_json": raw_payload[:300]
                })
            asset_msg = {"type": "ASSET_SPEC_UPDATE", "well_id": well_id, "data": asset_dict, "asset_spec": asset_dict}
            for cb in list(self._broadcast_callbacks):
                try: cb(asset_msg)
                except Exception: pass
            return

        # 3. Handle Virtual Flow Metering (VFM)
        if topic_suffix == "vfm":
            vfm_dict = validated_vfm.model_dump() if validated_vfm else payload
            keys = _expand_well_keys(well_id)
            with self._lock:
                for k in keys:
                    self.well_vfm[k] = vfm_dict
                self.total_received += 1
                self.last_packet_time = now_ts
                self._rate_window.append(time.time())
                self._recent_packets.append({
                    "id": self.total_received,
                    "timestamp": time_clock,
                    "topic": msg.topic,
                    "well_id": well_id,
                    "preview": {k: vfm_dict[k] for k in list(vfm_dict.keys())[:6]},
                    "raw_json": raw_payload[:300]
                })
            vfm_msg = {"type": "VFM_UPDATE", "well_id": well_id, "data": vfm_dict, "vfm": vfm_dict}
            for cb in list(self._broadcast_callbacks):
                try: cb(vfm_msg)
                except Exception: pass
            return

        # 4. Handle Event & Trip Alarms
        if topic_suffix == "events":
            keys = _expand_well_keys(well_id)
            event_name = payload.get("event") or payload.get("trip_cause") or payload.get("message") or "ALARM"
            event_entry = {
                "timestamp": payload.get("timestamp", now_ts),
                "well_id": well_id,
                "event": event_name,
                "message": payload.get("message") or event_name,
                "severity": payload.get("severity", "CRITICAL" if "trip" in str(payload).lower() else "WARNING"),
                "details": payload,
                "received_at": time.time()
            }
            with self._lock:
                for k in keys:
                    if k not in self.well_alarms:
                        self.well_alarms[k] = []
                    # If reset or normal event received, clear alarms for this well
                    if "clear" in str(event_name).lower() or "normal" in str(event_name).lower() or "reset" in str(event_name).lower():
                        self.well_alarms[k] = []
                    else:
                        self.well_alarms[k].append(event_entry)
                self.total_received += 1
                self.last_packet_time = now_ts
                self._rate_window.append(time.time())
                self._recent_packets.append({
                    "id": self.total_received,
                    "timestamp": time_clock,
                    "topic": msg.topic,
                    "well_id": well_id,
                    "preview": event_entry,
                    "raw_json": raw_payload[:300]
                })
            event_msg = {"type": "SIMULATOR_EVENT", "well_id": well_id, "data": event_entry, "event": event_entry}
            for cb in list(self._broadcast_callbacks):
                try: cb(event_msg)
                except Exception: pass
            return

        # 5. Telemetry stream: augment with cached asset and vfm data, then run pipeline
        telemetry_dict = validated_telemetry.model_dump() if validated_telemetry else payload
        with self._lock:
            self.total_received += 1
            self.last_packet_time = now_ts
            self._rate_window.append(time.time())
            preview_items = {}
            for k, v in list(telemetry_dict.get("measurements", {}).items())[:6]:
                if isinstance(v, float):
                    preview_items[k] = round(v, 2)
                elif isinstance(v, (int, str, bool)):
                    preview_items[k] = v

            self._recent_packets.append({
                "id": self.total_received,
                "timestamp": time_clock,
                "topic": msg.topic,
                "well_id": well_id,
                "preview": preview_items,
                "raw_json": raw_payload[:300]
            })

        cached_asset = None
        cached_vfm = None
        cached_alarms = []
        now_epoch = time.time()
        with self._lock:
            for k in _expand_well_keys(well_id):
                if not cached_asset and k in self.well_assets:
                    cached_asset = self.well_assets[k]
                if not cached_vfm and k in self.well_vfm:
                    cached_vfm = self.well_vfm[k]
                if k in self.well_alarms:
                    # Prune alarms older than 25-second TTL
                    self.well_alarms[k] = [
                        alm for alm in self.well_alarms[k]
                        if (now_epoch - alm.get("received_at", now_epoch)) < 25.0
                    ]
                    if not cached_alarms and self.well_alarms[k]:
                        cached_alarms = self.well_alarms[k]

        pipeline_payload = dict(telemetry_dict)
        pipeline_payload["well_id"] = well_id
        pipeline_payload["asset_id"] = well_id
        if "timestamp" not in pipeline_payload:
            pipeline_payload["timestamp"] = now_ts
        if cached_asset:
            pipeline_payload["asset_specs"] = cached_asset
        if cached_vfm:
            pipeline_payload["vfm"] = cached_vfm
        if cached_alarms:
            pipeline_payload["simulator_alarms"] = cached_alarms[-5:]
        else:
            pipeline_payload["simulator_alarms"] = []

        # Process through sequential pipeline:
        # MQTT Stream -> labelled.db -> unlabelled.db -> normalized.db -> ML-Model-Layers
        try:
            orch = get_orchestrator()
            res = orch.ingest_mqtt_telemetry(msg.topic, pipeline_payload)

            # Instantly dispatch to registered live WebSocket broadcasters
            for cb in list(self._broadcast_callbacks):
                try:
                    cb(res)
                except Exception as cb_err:
                    logger.debug(f"Broadcast callback error: {cb_err}")
        except Exception as e:
            logger.error(f"Error in pipeline orchestration: {e}")


# Singleton Collector Instance
_MQTT_COLLECTOR: Optional[MqttCollectorService] = None
_COLLECTOR_LOCK = threading.Lock()

def get_mqtt_collector() -> MqttCollectorService:
    global _MQTT_COLLECTOR
    with _COLLECTOR_LOCK:
        if _MQTT_COLLECTOR is None:
            _MQTT_COLLECTOR = MqttCollectorService()
        return _MQTT_COLLECTOR
