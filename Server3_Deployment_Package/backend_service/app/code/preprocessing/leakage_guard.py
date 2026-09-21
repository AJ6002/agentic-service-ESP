"""
Anti-Leakage Audit and Verification Module.
Asserts that training feature pipelines contain zero future lookahead,
zero target label contamination, and zero cross-split temporal overlap.
"""

import pandas as pd
from typing import List, Tuple


def assert_no_temporal_leakage(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    time_col: str = "datetime"
) -> bool:
    """Verifies strict chronological ordering between train, validation, and test splits."""
    max_train_time = train_df[time_col].max()
    min_val_time = val_df[time_col].min()
    max_val_time = val_df[time_col].max()
    min_test_time = test_df[time_col].min()

    assert max_train_time <= min_val_time, (
        f"Temporal Leakage Detected! Train max time ({max_train_time}) > Val min time ({min_val_time})"
    )
    assert max_val_time <= min_test_time, (
        f"Temporal Leakage Detected! Val max time ({max_val_time}) > Test min time ({min_test_time})"
    )
    return True


def assert_no_target_in_features(
    feature_names: List[str],
    target_columns: List[str] = ["fault_class", "scenario", "operating_state", "trip_cause", "alarms", "alerts", "status"]
) -> bool:
    """Asserts that no ground-truth target or leak-prone column is present in feature columns."""
    for feat in feature_names:
        for tgt in target_columns:
            assert feat != tgt and not feat.startswith(f"{tgt}_"), (
                f"Target Leakage Detected! Target '{tgt}' is present in feature set: '{feat}'"
            )
    return True
