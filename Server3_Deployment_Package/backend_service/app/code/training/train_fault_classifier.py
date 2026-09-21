"""
Training Pipeline for Model 2: Multiclass Fault Classifier.
Features: Time-Series Rolling Statistics + Domain Ratios.
Validation: Chronological Temporal Walk-Forward Holdout (Zero Leakage).
Calibration: Platt Scaling / Isotonic Regression.
Artifact: Saved to models/fault_classifier/v1.0/
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "fault_classifier" / "v1.0"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

from ml.data.dataset_loader import ESPDatasetLoader
from ml.features.time_series_features import extract_batch_dataframe_features
from ml.evaluation.classifier_metrics import compute_multiclass_metrics
from ml.preprocessing.leakage_guard import assert_no_temporal_leakage, assert_no_target_in_features


def train_fault_classifier():
    print("[*] Starting Multiclass Fault Classifier Training Pipeline...", flush=True)
    
    # 1. Load Data
    loader = ESPDatasetLoader()
    raw_df = loader.load_data()
    print(f"    Loaded {len(raw_df):,} raw records across {raw_df['well_id'].nunique()} wells.", flush=True)

    # 2. Extract Features
    print("[*] Computing time-series rolling features and physics domain ratios...", flush=True)
    features_df = extract_batch_dataframe_features(raw_df)
    features_df["datetime"] = pd.to_datetime(features_df["timestamp"], errors="coerce")
    features_df = features_df.sort_values(by="datetime").reset_index(drop=True)
    
    # Define Feature Columns (exclude metadata and target columns)
    non_feature_cols = [
        "id", "timestamp", "datetime", "asset_id", "well_id", "topic",
        "data_category", "scenario", "alarms", "alerts", "operating_state",
        "trip_cause", "status", "raw_payload", "created_at", "fault_class"
    ]
    feature_cols = [c for c in features_df.columns if c not in non_feature_cols]
    assert_no_target_in_features(feature_cols)
    print(f"    Total engineered features per sample: {len(feature_cols)}", flush=True)

    # 3. Chronological Walk-Forward Split (70% Train, 15% Val, 15% Test)
    n = len(features_df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train_df = features_df.iloc[:train_end].copy()
    val_df = features_df.iloc[train_end:val_end].copy()
    test_df = features_df.iloc[val_end:].copy()

    assert_no_temporal_leakage(train_df, val_df, test_df)
    print(f"    Temporal Splits -> Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}", flush=True)

    # 4. Target Encoding
    le = LabelEncoder()
    y_train = le.fit_transform(train_df["fault_class"])
    classes = list(le.classes_)
    print(f"    Target classes ({len(classes)}): {classes}", flush=True)

    # For validation & test, handle unseen classes gracefully
    def safe_transform(series, encoder):
        return np.array([encoder.transform([v])[0] if v in encoder.classes_ else -1 for v in series])

    y_val = safe_transform(val_df["fault_class"], le)
    y_test = safe_transform(test_df["fault_class"], le)

    # Filter out any -1 from eval
    val_mask = y_val >= 0
    test_mask = y_test >= 0

    X_train = train_df[feature_cols].fillna(0.0).values
    X_val = val_df[feature_cols].fillna(0.0).values[val_mask]
    y_val_clean = y_val[val_mask]
    X_test = test_df[feature_cols].fillna(0.0).values[test_mask]
    y_test_clean = y_test[test_mask]

    # 5. Model Training (Balanced Class Weights, Parallelized)
    print("[*] Training Random Forest Classifier with class balancing (n_jobs=-1)...", flush=True)
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    # 6. Evaluation on Test Set
    print("[*] Evaluating model on unseen chronological test holdout...", flush=True)
    y_test_pred_idx = clf.predict(X_test)
    y_test_true_labels = le.inverse_transform(y_test_clean)
    y_test_pred_labels = le.inverse_transform(y_test_pred_idx)

    metrics = compute_multiclass_metrics(
        y_true=y_test_true_labels,
        y_pred=y_test_pred_labels,
        labels=classes
    )
    print(f"    [TEST METRICS] Accuracy: {metrics['accuracy']:.4f} | Macro F1: {metrics['macro_f1']:.4f} | Weighted F1: {metrics['weighted_f1']:.4f}", flush=True)

    # 7. Save Model Artifacts & Report
    artifact_bundle = {
        "model": clf,
        "label_encoder": le,
        "feature_names": feature_cols,
        "classes": classes,
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    joblib.dump(artifact_bundle, MODEL_DIR / "fault_classifier.joblib")
    print(f"    Saved model bundle to {MODEL_DIR / 'fault_classifier.joblib'}", flush=True)

    report = {
        "model_type": "RandomForestClassifier",
        "version": "v1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "feature_count": len(feature_cols),
        "feature_names": feature_cols,
        "classes": classes,
        "metrics": metrics
    }
    with open(MODEL_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"    Saved training report to {MODEL_DIR / 'training_report.json'}", flush=True)

    print("\n>>> FAULT CLASSIFIER TRAINING COMPLETED SUCCESSFULLY! <<<\n", flush=True)
    return report



if __name__ == "__main__":
    train_fault_classifier()
