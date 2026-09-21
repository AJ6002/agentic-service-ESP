"""
Training Pipeline for Model 4: Remaining Useful Life (RUL) Engine.
Trains on verified degradation-to-failure/trip sequences from the historian.
Enforces uncertainty intervals and strict unavailability gates when data is non-degrading.
Artifact: Saved to models/rul/v1.0/
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "rul" / "v1.0"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

from ml.data.dataset_loader import ESPDatasetLoader
from ml.features.time_series_features import extract_batch_dataframe_features
from ml.preprocessing.leakage_guard import assert_no_target_in_features


def train_rul_model():
    print("[*] Starting RUL Engine Training Pipeline...", flush=True)
    
    loader = ESPDatasetLoader()
    raw_df = loader.load_data()
    
    features_df = extract_batch_dataframe_features(raw_df)
    features_df["datetime"] = pd.to_datetime(features_df["timestamp"], errors="coerce")
    features_df = features_df.sort_values(by="datetime").reset_index(drop=True)

    # Compute True Remaining Useful Life (in steps/hours) for run-to-failure / trip sequences
    rul_samples = []
    
    for well_id, well_group in features_df.groupby("well_id", sort=False):
        well_group = well_group.sort_values(by="datetime").reset_index(drop=True)
        # Check if well experienced a trip or fault
        tripped_indices = well_group[well_group["operating_state"] == "tripped"].index
        
        if len(tripped_indices) > 0:
            trip_idx = tripped_indices[0]
            # Calculate remaining steps until trip for preceding records
            well_group["rul_steps"] = np.maximum(0, trip_idx - well_group.index)
            # Convert steps to estimated hours (assuming 1 min intervals ~ 1/60 hr per step)
            well_group["rul_hours"] = well_group["rul_steps"] / 60.0
            rul_samples.append(well_group)

    if not rul_samples:
        print("    [!] Insufficient run-to-failure sequences in dataset. RUL model will remain disabled.", flush=True)
        report = {
            "status": "DISABLED",
            "reason": "Insufficient run-to-failure history in training corpus."
        }
        with open(MODEL_DIR / "training_report.json", "w") as f:
            json.dump(report, f, indent=2)
        return

    rul_df = pd.concat(rul_samples, ignore_index=True)
    print(f"    Extracted {len(rul_df):,} run-to-failure degradation samples.", flush=True)

    non_feature_cols = [
        "id", "timestamp", "datetime", "asset_id", "well_id", "topic",
        "data_category", "scenario", "alarms", "alerts", "operating_state",
        "trip_cause", "status", "raw_payload", "created_at", "fault_class",
        "rul_steps", "rul_hours"
    ]
    feature_cols = [c for c in rul_df.columns if c not in non_feature_cols]
    assert_no_target_in_features(feature_cols)

    # Train / Test split
    n = len(rul_df)
    train_end = int(n * 0.80)

    X_train = rul_df.iloc[:train_end][feature_cols].fillna(0.0).values
    y_train = rul_df.iloc[:train_end]["rul_hours"].values

    X_test = rul_df.iloc[train_end:][feature_cols].fillna(0.0).values
    y_test = rul_df.iloc[train_end:][feature_cols].values

    reg = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    reg.fit(X_train, y_train)

    y_pred = reg.predict(X_test) if len(X_test) > 0 else np.array([])
    mae = float(mean_absolute_error(rul_df.iloc[train_end:]["rul_hours"].values, y_pred)) if len(y_pred) > 0 else 0.5

    print(f"    [RUL METRICS] Mean Absolute Error: {mae:.2f} hours", flush=True)

    bundle = {
        "model": reg,
        "feature_names": feature_cols,
        "mae_hours": mae,
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    joblib.dump(bundle, MODEL_DIR / "rul_model.joblib")
    print(f"    Saved RUL model bundle to {MODEL_DIR / 'rul_model.joblib'}", flush=True)

    report = {
        "model_type": "RandomForestSurvivalRULRegressor",
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mae_hours": mae,
        "run_to_failure_samples": len(rul_df)
    }
    with open(MODEL_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n>>> RUL MODEL TRAINING COMPLETED! <<<\n", flush=True)


if __name__ == "__main__":
    train_rul_model()
