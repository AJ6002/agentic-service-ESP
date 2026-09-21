"""
Evaluation Metrics & Calibration Calculations for Fault Diagnosis & Risk Models.
Computes Accuracy, Macro F1, Per-Class Precision/Recall, PR-AUC, Confusion Matrix, and Brier Score.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    brier_score_loss,
    classification_report
)


def compute_multiclass_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
    y_prob: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """Computes comprehensive evaluation metrics for multi-class fault classification."""
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    # Per-class metrics
    per_class = {}
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    for lbl in labels:
        if lbl in report:
            per_class[lbl] = {
                "precision": float(report[lbl]["precision"]),
                "recall": float(report[lbl]["recall"]),
                "f1_score": float(report[lbl]["f1-score"]),
                "support": int(report[lbl]["support"])
            }

    metrics = {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "confusion_matrix": cm,
        "class_labels": labels,
        "per_class_metrics": per_class
    }

    return metrics
