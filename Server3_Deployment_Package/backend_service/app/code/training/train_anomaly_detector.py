"""
Training Pipeline for Model 5: Healthy-State Anomaly Detector.
Trained EXCLUSIVELY on verified healthy operating telemetry to establish
the baseline normal manifold and detect novel/unseen anomalies.
Artifact: Saved to models/anomaly_detector/v1.0/
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "anomaly_detector" / "v1.0"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

from ml.data.dataset_loader import ESPDatasetLoader
from ml.features.time_series_features import extract_batch_dataframe_features
from ml.preprocessing.leakage_guard import assert_no_target_in_features


def train_anomaly_detector():
    print("[*] Starting Healthy-State Anomaly Detector Training Pipeline...", flush=True)
    
    loader = ESPDatasetLoader()
    raw_df = loader.load_data()

    # Extract Healthy Subset
    healthy_raw = raw_df[raw_df["fault_class"] == "HEALTHY"].copy()
    print(f"    Extracted {len(healthy_raw):,} verified healthy baseline samples.", flush=True)

    features_df = extract_batch_dataframe_features(healthy_raw)
    
    non_feature_cols = [
        "id", "timestamp", "datetime", "asset_id", "well_id", "topic",
        "data_category", "scenario", "alarms", "alerts", "operating_state",
        "trip_cause", "status", "raw_payload", "created_at", "fault_class"
    ]
    feature_cols = [c for c in features_df.columns if c not in non_feature_cols]
    assert_no_target_in_features(feature_cols)

    X_healthy = features_df[feature_cols].fillna(0.0).values

    # 1. Fit Standard Scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_healthy)

    # 2. Fit Isolation Forest
    print("[*] Training Isolation Forest on healthy manifold...", flush=True)
    iso_forest = IsolationForest(
        n_estimators=120,
        contamination=0.03,  # 3% expected noise in healthy data
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_scaled)

    # 3. Fit PCA Reconstruction Baseline
    pca = PCA(n_components=0.95, random_state=42)
    pca.fit(X_scaled)

    # Compute calibrated anomaly scores using decision_function
    # decision_function > 0 for normal inliers, < 0 for anomalous outliers
    decision_scores = iso_forest.decision_function(X_scaled)
    # Anomaly probability mapping: higher = more anomalous
    norm_scores = 1.0 / (1.0 + np.exp(decision_scores * 4.0))
    threshold = 0.55

    print(f"    [ANOMALY CALIBRATION] Decision Threshold: {threshold:.4f} (Mean normal score: {np.mean(norm_scores):.4f})", flush=True)

    bundle = {
        "scaler": scaler,
        "isolation_forest": iso_forest,
        "pca": pca,
        "feature_names": feature_cols,
        "threshold": threshold,
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    joblib.dump(bundle, MODEL_DIR / "anomaly_detector.joblib")
    print(f"    Saved anomaly detector bundle to {MODEL_DIR / 'anomaly_detector.joblib'}", flush=True)

    report = {
        "model_type": "IsolationForest_Plus_PCA",
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "healthy_training_samples": len(X_healthy),
        "features_used": len(feature_cols),
        "calibrated_threshold": threshold
    }

    with open(MODEL_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n>>> ANOMALY DETECTOR TRAINING COMPLETED! <<<\n", flush=True)


if __name__ == "__main__":
    train_anomaly_detector()
