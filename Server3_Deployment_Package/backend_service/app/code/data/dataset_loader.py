"""
Dataset Loader for Machine Learning Pipelines.
Provides leak-free temporal and group-aware train/validation/test splits
for Fault Classification, Risk Prediction, RUL, and Anomaly Detection.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_FILE = BASE_DIR / "data" / "processed" / "canonical_esp_site_telemetry.parquet"


class ESPDatasetLoader:
    def __init__(self, data_path: Path = PROCESSED_FILE):
        self.data_path = data_path
        self._df: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """Load the processed canonical dataset."""
        if self._df is None:
            if not self.data_path.exists():
                from scripts.download_datasets import extract_site_dataset
                self._df = extract_site_dataset()
            else:
                self._df = pd.read_parquet(self.data_path)
            
            # Ensure proper datetime parsing
            self._df["datetime"] = pd.to_datetime(self._df["timestamp"], errors="coerce")
            self._df = self._df.sort_values(by=["datetime"]).reset_index(drop=True)
            
        return self._df

    def get_temporal_split(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Chronological Walk-Forward Train/Val/Test split with ZERO shuffling
        to strictly prevent time-series data leakage.
        """
        df = self.load_data()
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        return train_df, val_df, test_df

    def get_group_well_split(
        self,
        test_wells: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Group-aware split partitioning by distinct Well IDs for cross-well generalization.
        """
        df = self.load_data()
        all_wells = df["well_id"].unique().tolist()
        
        if not test_wells:
            # Pick roughly 20% of wells for holdout testing
            n_test = max(1, int(len(all_wells) * 0.2))
            test_wells = all_wells[-n_test:]

        train_df = df[~df["well_id"].isin(test_wells)].copy().reset_index(drop=True)
        test_df = df[df["well_id"].isin(test_wells)].copy().reset_index(drop=True)

        return train_df, test_df

    def get_healthy_baseline_data(self) -> pd.DataFrame:
        """Returns exclusively verified healthy operating sequences for anomaly model training."""
        df = self.load_data()
        healthy_df = df[
            (df["fault_class"] == "HEALTHY") & 
            (df["operating_state"] == "running") &
            (df["status"] == "NORMAL")
        ].copy().reset_index(drop=True)
        return healthy_df
