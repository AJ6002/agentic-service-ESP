import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LABELLED_DB_PATH = str(DATA_DIR / "labelled.db")
UNLABELLED_DB_PATH = str(DATA_DIR / "unlabelled.db")
NORMALIZED_DB_PATH = str(DATA_DIR / "normalized.db")
HISTORIAN_DB_PATH = str(DATA_DIR / "historian" / "unlabelled_recovered.db")
DB_PATH = UNLABELLED_DB_PATH

# Valid Authorized Broker IDs for ML Telemetry Polling API
VALID_BROKER_IDS = {
    "BROKER-DEMO-001",
    "CCED-ML-TEST-01",
    "OPG-SECURE-01",
    "DEFAULT_DEMO_BROKER",
    "MQTT-SECURE-BROKER-01",
    "OPG-BROKER-PROD",
}

class MQTTConfig(BaseModel):
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "192.168.1.155")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    username: Optional[str] = os.getenv("MQTT_USERNAME", None)
    password: Optional[str] = os.getenv("MQTT_PASSWORD", None)
    client_id_prefix: str = "opg_collector_"
    topics: List[str] = ["esp/v1/+/telemetry", "esp/#", "wells/#", "opg/#"]
    keepalive: int = 60
    reconnect_delay_min: int = 1
    reconnect_delay_max: int = 30

class IngestionState(BaseModel):
    is_running: bool = True               # Master switch (Play/Pause)
    buffer_on_pause: bool = True          # If True, incoming data is buffered during pause; if False, dropped
    storage_category_mode: str = "BOTH"   # "BOTH" (Labelled + Unlabelled), "LABELLED_ONLY", "UNLABELLED_ONLY"
    filter_mode: str = "ALL"              # "ALL", "WHITELIST", "BLACKLIST"
    allowed_asset_ids: List[str] = []
    blocked_asset_ids: List[str] = []
    allowed_wells: List[str] = []
    allowed_scenarios: List[str] = []     # e.g. ["gas_interference_to_lock", "undervoltage"]
    allowed_operating_states: List[str] = [] # e.g. ["running", "tripped"]
    allowed_trip_causes: List[str] = []   # e.g. ["GAS_LOCK_UNDERLOAD", "UNDER_VOLTAGE"]
    allowed_pump_families: List[str] = [] # e.g. ["B400", "TD650", "PMSND"]
    min_pressure_psi: Optional[float] = None
    max_pressure_psi: Optional[float] = None
    min_intake_pressure_psi: Optional[float] = None
    max_temperature_c: Optional[float] = None

# Default instances
DEFAULT_MQTT_CONFIG = MQTTConfig()
DEFAULT_INGESTION_STATE = IngestionState()
