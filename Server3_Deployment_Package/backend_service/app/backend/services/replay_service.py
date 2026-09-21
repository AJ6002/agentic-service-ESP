"""
Historical Scenario Replay Engine.
Replays actual recorded/public historical fault sequences chronologically
through the live inference pipeline at configurable speeds (1x, 5x, 10x).
Strictly operates on genuine recorded data — zero fake values.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from ml.data.dataset_loader import ESPDatasetLoader
from backend.adapters.telemetry_adapter import record_to_canonical
from backend.services.unified_pipeline import esp_pipeline

logger = logging.getLogger("esp.replay_service")


class ESPReplayService:
    def __init__(self):
        self.is_playing = False
        self.playback_speed = 1.0  # 1.0x, 5.0x, 10.0x
        self.current_index = 0
        self.selected_well = "ALL"
        self.selected_fault = "ALL"
        self.replay_data: Optional[pd.DataFrame] = None
        self._replay_task: Optional[asyncio.Task] = None
        self.broadcast_callback = None

    def set_broadcast_callback(self, callback):
        self.broadcast_callback = callback

    def load_replay_dataset(
        self,
        well_id: Optional[str] = None,
        fault_class: Optional[str] = None
    ) -> int:
        """Loads and filters genuine historical records for replay."""
        loader = ESPDatasetLoader()
        df = loader.load_data()

        if well_id and well_id != "ALL":
            df = df[df["well_id"] == well_id]
        if fault_class and fault_class != "ALL":
            df = df[df["fault_class"] == fault_class]

        df = df.sort_values(by="datetime").reset_index(drop=True)
        self.replay_data = df
        self.current_index = 0
        return len(df)

    async def start_replay(self, speed: float = 1.0):
        """Starts asynchronous chronological replay loop."""
        if self.replay_data is None or len(self.replay_data) == 0:
            self.load_replay_dataset()

        self.playback_speed = speed
        self.is_playing = True

        if self._replay_task is None or self._replay_task.done():
            self._replay_task = asyncio.create_task(self._replay_loop())

    def pause_replay(self):
        self.is_playing = False

    def seek(self, index: int):
        if self.replay_data is not None:
            self.current_index = max(0, min(len(self.replay_data) - 1, index))

    async def _replay_loop(self):
        logger.info(f"Replay loop started at {self.playback_speed}x speed.")
        base_delay = 1.0  # 1 second between normal samples

        while self.is_playing and self.replay_data is not None:
            if self.current_index >= len(self.replay_data):
                self.is_playing = False
                logger.info("Replay sequence completed.")
                break

            row = self.replay_data.iloc[self.current_index].to_dict()
            canonical = record_to_canonical(row)

            # Process through genuine inference pipeline
            assessment = await esp_pipeline.process_telemetry(canonical, persist_db=True)

            # Broadcast over WebSocket if wired up
            if self.broadcast_callback:
                try:
                    await self.broadcast_callback({
                        "type": "ESP_REPLAY_UPDATE",
                        "index": self.current_index,
                        "total": len(self.replay_data),
                        "assessment": assessment.model_dump()
                    })
                except Exception as e:
                    logger.error(f"Replay broadcast error: {e}")

            self.current_index += 1
            delay = max(0.05, base_delay / max(0.1, self.playback_speed))
            await asyncio.sleep(delay)


replay_service = ESPReplayService()
