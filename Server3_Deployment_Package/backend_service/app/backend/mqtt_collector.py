import asyncio
import json
import logging
import time
from collections import deque
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Optional, Callable
import paho.mqtt.client as mqtt
from backend.config import MQTTConfig, IngestionState
from backend.database import db, labelled_db, unlabelled_db
from backend.database_normalized import normalized_db
from backend.transformer import transform_mqtt_payload
from backend.services.vfd_diagnostic_service import vfd_diagnostic_service


logger = logging.getLogger("opg.mqtt")

class MQTTCollector:
    def __init__(self, config: MQTTConfig, state: IngestionState):
        self.config = config
        self.state = state
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.last_error: Optional[str] = None
        self.connection_status_text = "Disconnected"
        
        # Ingestion metrics
        self.total_received = 0
        self.total_saved = 0
        self.total_filtered = 0
        self.total_buffered = 0
        self.start_time = time.time()
        self.recent_msg_timestamps: List[float] = []
        
        # Memory buffer for pause mode and thread-safe ingestion queue
        self.pause_buffer: List[Dict[str, Any]] = []
        # Rolling raw MQTT packets buffer for UI debugging modal
        self.recent_packets: deque = deque(maxlen=100)
        self._packets_lock = threading.Lock()
        import queue
        self.raw_thread_queue = queue.Queue(maxsize=10000)
        self.last_broadcast_time = 0.0

        # Strong references to fire-and-forget VFD diagnostic background tasks —
        # asyncio.create_task() results MUST be retained or the task can be
        # garbage-collected mid-execution. Self-removes via done_callback.
        self._vfd_bg_tasks: Set[asyncio.Task] = set()
        
        # Callbacks for WebSocket broadcasting
        self.broadcast_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        self.status_change_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        
        # In-memory live telemetry registry by asset_id and well_id
        self.live_telemetry_registry: Dict[str, Dict[str, Any]] = {}

        # Worker tasks
        self._batch_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_broadcast_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.broadcast_callback = callback

    def set_status_change_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.status_change_callback = callback

    async def start(self):
        """Start the collector worker loop."""
        self._loop = asyncio.get_running_loop()
        self._batch_task = asyncio.create_task(self._batch_writer_loop())
        self.connect()

    def connect(self, host: Optional[str] = None, port: Optional[int] = None, topic: Optional[str] = None):
        """Initialize or reconnect Paho MQTT client using threaded connect with timeout."""
        if host and str(host).strip():
            self.config.broker_host = str(host).strip()
        if port:
            try:
                self.config.broker_port = int(port)
            except (ValueError, TypeError):
                pass
        if topic and str(topic).strip():
            t_clean = str(topic).strip()
            if t_clean not in self.config.topics:
                self.config.topics.insert(0, t_clean)

        if not self.config.broker_host or not self.config.broker_host.strip():
            self.disconnect()
            self.connection_status_text = "Disconnected (Broker Host Not Configured)"
            self.last_error = None
            self._notify_status()
            return

        try:
            self.disconnect()

            client_id = f"{self.config.client_id_prefix}{int(time.time())}"
            try:
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
            except AttributeError:
                self.client = mqtt.Client(client_id=client_id)

            if self.config.username and self.config.password:
                self.client.username_pw_set(self.config.username, self.config.password)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            self.connection_status_text = f"Connecting to {self.config.broker_host}:{self.config.broker_port}..."
            logger.info(f"Connecting to MQTT Broker {self.config.broker_host}:{self.config.broker_port}...")

            import threading
            # Run synchronous connect in a background thread with a 6-second socket timeout
            # so TCP failures are immediately detected instead of hanging indefinitely.
            def _do_connect():
                try:
                    self.client.connect(
                        self.config.broker_host,
                        self.config.broker_port,
                        keepalive=self.config.keepalive
                    )
                    self.client.loop_start()
                except Exception as e:
                    self.is_connected = False
                    self.last_error = str(e)
                    self.connection_status_text = f"Connection failed: {e}"
                    logger.error(f"MQTT connect failed: {e}")
                    self._notify_status()

            t = threading.Thread(target=_do_connect, daemon=True)
            t.start()
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            self.connection_status_text = f"Connection error: {e}"
            logger.error(f"Failed to initiate MQTT connection: {e}")
            self._notify_status()

    def disconnect(self):
        """Disconnect and stop MQTT client loop."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            self.client = None
        self.is_connected = False
        self.connection_status_text = "Disconnected"

    def _notify_status(self):
        if self.status_change_callback and self._loop and self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.status_change_callback(self.get_status()), self._loop
                )
            except Exception:
                pass

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.is_connected = True
            self.last_error = None
            self.connection_status_text = f"Connected to {self.config.broker_host}:{self.config.broker_port}"
            logger.info(f"Connected successfully to MQTT Broker {self.config.broker_host}:{self.config.broker_port}")
            # Ensure topic subscriptions
            topics_to_sub = self.config.topics if self.config.topics else ["esp/#", "opg/#", "wells/#"]
            for topic in topics_to_sub:
                client.subscribe(topic.strip())
                logger.info(f"Subscribed to topic: {topic.strip()}")
        else:
            self.is_connected = False
            error_lookup = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            err_msg = error_lookup.get(rc, f"Connection refused (code {rc})")
            self.last_error = err_msg
            self.connection_status_text = err_msg
            logger.warning(f"MQTT connection refused: {err_msg}")

        self._notify_status()

    def _on_disconnect(self, client, userdata, flags_or_rc, rc_or_props=None, properties=None):
        self.is_connected = False
        self.connection_status_text = "Disconnected from broker"
        logger.warning("Disconnected from MQTT Broker.")
        self._notify_status()

    def _on_message(self, client, userdata, msg):
        """Ultra-fast thread-safe enqueue."""
        now = time.time()
        self.total_received += 1
        self.recent_msg_timestamps.append(now)
        if len(self.recent_msg_timestamps) > 100:
            self.recent_msg_timestamps = self.recent_msg_timestamps[-50:]

        # Buffer recent packet for UI packet viewer modal
        try:
            try:
                parsed_payload = json.loads(msg.payload.decode("utf-8", errors="replace"))
            except Exception:
                parsed_payload = msg.payload.decode("utf-8", errors="replace")[:300]
            with self._packets_lock:
                self.recent_packets.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "topic": msg.topic,
                    "payload": parsed_payload,
                    "size_bytes": len(msg.payload)
                })
        except Exception:
            pass

        try:
            self.raw_thread_queue.put_nowait((msg.topic, msg.payload))
        except Exception:
            pass

    async def _run_and_broadcast_vfd_diagnostic(self, payload_data: Dict[str, Any], well_id_hint: Optional[str]):
        """
        Runs vfd_diagnostic_service.process() off the event loop thread (CPU-bound model
        inference), then — if a diagnosis was produced — broadcasts it live over the same
        WebSocket channel used for LIVE_TELEMETRY, tagged with a distinct message type
        (VFD_DIAGNOSTIC) so the frontend can distinguish it without touching its existing
        LIVE_TELEMETRY / ESP_ASSESSMENT / STATUS_UPDATE handling.

        vfd_diagnostic_service.process() already writes the JSONL durability log itself
        and never raises (errors are logged and swallowed internally) — this wrapper only
        adds the broadcast step on top, and swallows its own errors too so a WebSocket
        hiccup can never affect telemetry DB writes or the raw LIVE_TELEMETRY broadcast.
        """
        try:
            result = await asyncio.to_thread(vfd_diagnostic_service.process, payload_data, well_id_hint)
        except Exception as e:
            logger.debug(f"[MQTTCollector] VFD diagnostic evaluation failed: {e}")
            return

        if not result or not self.broadcast_callback:
            return

        try:
            await self.broadcast_callback({
                "type": "VFD_DIAGNOSTIC",
                "well_id": result.get("well_id"),
                "family": result.get("family"),
                "timestamp": result.get("timestamp"),
                "diagnostic": result.get("diagnostic"),
                "dynamics": result.get("dynamics"),
                "ml_anomaly": result.get("ml_anomaly"),
                "raw_measurements": result.get("raw_measurements"),
            })
        except Exception as e:
            logger.debug(f"[MQTTCollector] VFD diagnostic broadcast failed: {e}")

    def _normalize_records(self, data: Dict[str, Any], topic: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Pass incoming MQTT payload through dedicated transformer.
        Outputs both LABELLED and stripped UNLABELLED records.
        """
        return transform_mqtt_payload(data, topic)

    def _matches_filters(self, record: Dict[str, Any]) -> bool:
        """Evaluate dynamic filters against record."""
        # Whitelist / Blacklist Asset/Well
        if self.state.filter_mode == "WHITELIST" and self.state.allowed_asset_ids:
            if record["asset_id"] not in self.state.allowed_asset_ids and record["well_id"] not in self.state.allowed_asset_ids:
                return False

        if self.state.filter_mode == "BLACKLIST" and self.state.blocked_asset_ids:
            if record["asset_id"] in self.state.blocked_asset_ids or record["well_id"] in self.state.blocked_asset_ids:
                return False

        if self.state.allowed_wells and record["well_id"] not in self.state.allowed_wells:
            return False

        # Scenario / Fault Filter
        if self.state.allowed_scenarios and record.get("scenario"):
            rec_scen = str(record["scenario"]).lower().replace("-", "_").replace(" ", "_")
            allowed_norm = [s.lower().replace("-", "_").replace(" ", "_") for s in self.state.allowed_scenarios]
            if rec_scen not in allowed_norm and record["scenario"] not in self.state.allowed_scenarios:
                return False

        # Operating State Filter
        if self.state.allowed_operating_states:
            state_val = str(record.get("operating_state", "")).lower()
            allowed = [s.lower() for s in self.state.allowed_operating_states]
            if state_val not in allowed:
                return False

        # Trip Cause Filter
        if self.state.allowed_trip_causes:
            trip_val = record.get("trip_cause", "")
            if trip_val not in self.state.allowed_trip_causes:
                return False

        # Pump Family Filter
        if self.state.allowed_pump_families:
            asset_str = record.get("asset_id", "")
            if not any(family in asset_str for family in self.state.allowed_pump_families):
                return False

        # Pressure and Temperature Physical Limits
        if self.state.min_pressure_psi is not None and record["pressure_psi"] < self.state.min_pressure_psi:
            return False
        if self.state.max_pressure_psi is not None and record["pressure_psi"] > self.state.max_pressure_psi:
            return False
        if self.state.min_intake_pressure_psi is not None and record.get("intake_pressure_psi", 0.0) < self.state.min_intake_pressure_psi:
            return False
        if self.state.max_temperature_c is not None and record.get("temperature_c", 0.0) > self.state.max_temperature_c:
            return False

        return True

    async def _batch_writer_loop(self):
        """High-performance batch processor and SQLite writer."""
        import queue
        while True:
            try:
                raw_items = []
                while len(raw_items) < 200:
                    try:
                        raw_items.append(self.raw_thread_queue.get_nowait())
                    except queue.Empty:
                        break

                if not raw_items:
                    await asyncio.sleep(0.05)
                    continue

                labelled_batch = []
                unlabelled_batch = []
                latest_labelled = None
                latest_unlabelled = None

                for topic, payload_bytes in raw_items:
                    try:
                        payload_str = payload_bytes.decode("utf-8", errors="ignore")
                        try:
                            payload_data = json.loads(payload_str)
                        except Exception:
                            payload_data = {"raw_text": payload_str}

                        labelled, unlabelled = self._normalize_records(payload_data, topic)

                        if not self.state.is_running:
                            if self.state.buffer_on_pause:
                                if len(self.pause_buffer) < 2000:
                                    self.pause_buffer.append(labelled)
                                    self.total_buffered = len(self.pause_buffer)
                            else:
                                self.total_filtered += 1
                            continue

                        if not self._matches_filters(labelled):
                            self.total_filtered += 1
                            continue

                        labelled_batch.append(labelled)
                        unlabelled_batch.append(unlabelled)
                        self.total_saved += 1

                        aid = unlabelled.get("asset_id") or labelled.get("asset_id")
                        wid = unlabelled.get("well_id") or labelled.get("well_id")
                        if aid:
                            self.live_telemetry_registry[aid] = unlabelled
                        if wid:
                            self.live_telemetry_registry[wid] = unlabelled

                        latest_labelled = labelled
                        latest_unlabelled = unlabelled

                        # Additive VFD diagnostic bridge: feeds the SAME raw payload_data
                        # (not the DB-shaped labelled/unlabelled records) through
                        # ESP_APM_models.WellDiagnosticEngine, appends a JSONL log record
                        # for the agent to read, AND broadcasts the result live over the
                        # same WebSocket used for LIVE_TELEMETRY (type: VFD_DIAGNOSTIC) so
                        # the frontend / any live consumer gets it in real time too.
                        # Off-loaded to a worker thread so CPU-bound model inference never
                        # blocks the asyncio event loop. Never allowed to affect DB
                        # writes/broadcast of telemetry — errors are logged and swallowed.
                        try:
                            task = asyncio.create_task(
                                self._run_and_broadcast_vfd_diagnostic(payload_data, wid or aid)
                            )
                            self._vfd_bg_tasks.add(task)
                            task.add_done_callback(self._vfd_bg_tasks.discard)
                        except Exception as e:
                            logger.debug(f"[MQTTCollector] VFD diagnostic dispatch skipped: {e}")
                    except Exception as e:
                        logger.error(f"Error processing item from queue: {e}")

                if labelled_batch:
                    await labelled_db.insert_telemetry_batch(labelled_batch)
                if unlabelled_batch:
                    await unlabelled_db.insert_telemetry_batch(unlabelled_batch)
                    await normalized_db.insert_batch(unlabelled_batch)

                # Rate-limited WebSocket broadcast using unlabelled data as ground truth
                now = time.time()
                if latest_unlabelled and self.broadcast_callback and (now - self.last_broadcast_time > 0.05):
                    self.last_broadcast_time = now
                    try:
                        await self.broadcast_callback({
                            "type": "LIVE_TELEMETRY",
                            "data": latest_unlabelled,
                            "labelled_data": latest_labelled
                        })
                    except Exception:
                        pass

                await asyncio.sleep(0.02)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch loop: {e}")
                await asyncio.sleep(0.2)

    async def resume_and_flush_buffer(self):
        """Flush buffered items from pause state into the active processing queue."""
        if self.pause_buffer:
            logger.info(f"Flushing {len(self.pause_buffer)} buffered records to processing queue...")
            flushed = 0
            for rec in self.pause_buffer:
                if self._matches_filters(rec):
                    try:
                        # Re-encode to bytes so the batch loop can process normally
                        payload_bytes = json.dumps(rec).encode("utf-8")
                        self.raw_thread_queue.put_nowait((rec.get("topic", "buffer/flush"), payload_bytes))
                        flushed += 1
                    except Exception:
                        pass
                else:
                    self.total_filtered += 1
            self.pause_buffer.clear()
            self.total_buffered = 0
            logger.info(f"Flushed {flushed} records from pause buffer.")

    def get_msg_rate(self) -> float:
        now = time.time()
        recent = [t for t in self.recent_msg_timestamps if now - t <= 5.0]
        if not recent:
            return 0.0
        return round(len(recent) / 5.0, 1)

    def get_recent_packets(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Returns the most recent incoming raw MQTT packets."""
        with self._packets_lock:
            pkts = list(self.recent_packets)
            pkts.reverse()
            return pkts[:limit]

    def get_status(self) -> Dict[str, Any]:
        curr_topic = self.config.topics[0] if self.config.topics else "esp/v1/+/telemetry"
        return {
            "broker_host": self.config.broker_host,
            "broker_port": self.config.broker_port,
            "username": self.config.username,
            "topics": self.config.topics,
            "current_topic": curr_topic,
            "is_connected": self.is_connected,
            "last_error": self.last_error,
            "connection_status_text": self.connection_status_text,
            "is_running": self.state.is_running,
            "buffer_on_pause": self.state.buffer_on_pause,
            "storage_category_mode": self.state.storage_category_mode,
            "filter_mode": self.state.filter_mode,
            "allowed_asset_ids": self.state.allowed_asset_ids,
            "blocked_asset_ids": self.state.blocked_asset_ids,
            "allowed_wells": self.state.allowed_wells,
            "min_pressure_psi": self.state.min_pressure_psi,
            "max_pressure_psi": self.state.max_pressure_psi,
            "total_received": self.total_received,
            "total_saved": self.total_saved,
            "total_filtered": self.total_filtered,
            "total_buffered": len(self.pause_buffer),
            "msg_rate_per_sec": self.get_msg_rate(),
            "uptime_seconds": int(time.time() - self.start_time)
        }

    def update_config(self, new_config: MQTTConfig):
        old_host = self.config.broker_host
        old_port = self.config.broker_port
        reconnect_needed = False

        # Preserve existing values if new config has empty or default fields
        if new_config.broker_host and str(new_config.broker_host).strip():
            new_h = str(new_config.broker_host).strip()
            if new_h != old_host:
                self.config.broker_host = new_h
                reconnect_needed = True
        if new_config.broker_port:
            if new_config.broker_port != old_port:
                self.config.broker_port = new_config.broker_port
                reconnect_needed = True
        if new_config.username is not None and new_config.username != self.config.username:
            self.config.username = new_config.username
            reconnect_needed = True
        if new_config.password is not None and new_config.password != self.config.password:
            self.config.password = new_config.password
            reconnect_needed = True
        if new_config.topics:
            self.config.topics = new_config.topics
            if self.is_connected and self.client and not reconnect_needed:
                for t in self.config.topics:
                    try:
                        self.client.subscribe(t.strip())
                    except Exception:
                        pass

        if reconnect_needed or not self.is_connected:
            if self.config.broker_host and self.config.broker_host.strip():
                self.connect()
            else:
                self.disconnect()
                self.connection_status_text = "Disconnected (Broker Host Not Configured)"
                self._notify_status()

    def update_state(self, new_state: IngestionState):
        was_paused = not self.state.is_running
        self.state = new_state
        if was_paused and self.state.is_running and self._loop:
            asyncio.run_coroutine_threadsafe(self.resume_and_flush_buffer(), self._loop)

    def stop(self):
        self.disconnect()
        if self._batch_task:
            self._batch_task.cancel()
