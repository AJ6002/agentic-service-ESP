"""
Signal name vocabulary normalization.
Translates between live SCADA uppercase keys (e.g. STD_INT_PRS_PSI)
and canonical lowercase snake_case database keys (e.g. int_prs_psi).
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 §3.
"""

from typing import Any, Optional

# Mapping of SCADA / upper signal names to canonical lowercase names
SCADA_TO_CANONICAL: dict[str, str] = {
    "STD_INT_PRS_PSI": "int_prs_psi",
    "STD_DISCH_PRS_PSI": "disch_prs_psi",
    "STD_INT_TEMP_C": "int_temp_c",
    "STD_MOTOR_TEMP_C": "motor_temp_c",
    "STD_VIBRATION_G": "vibration_g",
    "STD_VOLT_V": "volt_v",
    "STD_AMP_A": "amp_a",
    "STD_FREQ_HZ": "freq_hz",
    "STD_LEAK_CURRENT_CT": "leak_current_ct",
    "STD_DHG_CURRENT_MA": "dhg_current_ma",
    "STD_WHP_PSI": "whp_psi",
    "STD_FLP_PSI": "flp_psi",
    "STD_AP_PSI": "ap_psi",
    "STD_VFD_STS": "vfd_sts",
    "STD_LIQUID_RATE_BPD": "liquid_rate_bpd",
    "STD_OIL_RATE_BOPD": "oil_rate_bopd",
    "STD_WATER_CUT_PCT": "water_cut_pct",
    "STD_GAS_RATE_MSCFD": "gas_rate_mscfd",
}

CANONICAL_TO_SCADA: dict[str, str] = {v: k for k, v in SCADA_TO_CANONICAL.items()}

CANONICAL_SIGNALS: set[str] = {
    "int_prs_psi",
    "disch_prs_psi",
    "int_temp_c",
    "motor_temp_c",
    "vibration_g",
    "volt_v",
    "amp_a",
    "freq_hz",
    "leak_current_ct",
    "dhg_current_ma",
    "whp_psi",
    "flp_psi",
    "ap_psi",
    "vfd_sts",
    "liquid_rate_bpd",
    "oil_rate_bopd",
    "water_cut_pct",
    "gas_rate_mscfd",
    "health_score",
    "anomaly_score",
    "score",
    "rate_per_day",
    "projected_days_to_threshold",
}


def to_canonical_signal_name(name: str) -> str:
    """
    Normalizes a signal name to canonical lowercase snake_case.
    e.g. 'STD_INT_PRS_PSI' -> 'int_prs_psi'
         'int_prs_psi' -> 'int_prs_psi'
         'SCORE' -> 'score'
    """
    if not name:
        return name
    clean = name.strip()
    upper = clean.upper()
    if upper in SCADA_TO_CANONICAL:
        return SCADA_TO_CANONICAL[upper]
    return clean.lower()


def to_scada_signal_name(name: str) -> Optional[str]:
    """
    Converts canonical lowercase signal name to SCADA STD_* name if available.
    """
    canon = to_canonical_signal_name(name)
    return CANONICAL_TO_SCADA.get(canon)


def is_known_signal(name: str) -> bool:
    canon = to_canonical_signal_name(name)
    return canon in CANONICAL_SIGNALS


def normalize_measurements_dict(measurements: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizes all keys in a measurements dictionary to canonical lowercase names.
    Preserves values.
    """
    if not measurements:
        return {}
    normalized = {}
    for k, v in measurements.items():
        canon_k = to_canonical_signal_name(k)
        normalized[canon_k] = v
    return normalized
