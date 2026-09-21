"""
Unit tests for app.synthesis.kpi_alarm_check.

Import note: app.contracts must be imported FIRST to break the pre-existing
circular import cycle between app.contracts.advisory and app.evidence.formatter.
This matches the pattern used by test_phase2_synthesis.py.

Tests:
  - Dead well evidence (Q07 data) fires CRITICAL alarms
  - Healthy evidence produces clean result
  - Anomaly score threshold boundaries (0.84, 0.85, 0.95)
  - Per-signal highest-severity rule (only one alarm per signal)
  - alarm_summary() output format
  - Empty evidence
"""
import pytest

# Import contracts first to break circular import cycle (pre-existing issue)
import app.contracts  # noqa: F401

from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.synthesis.kpi_alarm_check import check_kpi_alarms, KpiAlarmResult


def _make_evidence(**signals) -> FormattedEvidence:
    """Build a minimal FormattedEvidence with only the given signals."""
    fe = FormattedEvidence(run_id="test-run", pack_version=1)
    for i, (signal, raw) in enumerate(signals.items()):
        fe.values.append(
            FormattedValue(
                value_str=f"{raw:.4g}",
                unit="",
                evidence_id=f"EV-test-{i:04d}",
                signal=signal,
                raw=float(raw),
            )
        )
    return fe


# -- Dead-well scenario (Q07 reproduction) --

def test_dead_well_fires_critical():
    """
    Q07 exact data: 0 oil/liquid/gas/motor + 0.95 anomaly + 78.2 water cut.
    Must produce CRITICAL alarms -- never a clean result.
    """
    ev = _make_evidence(
        oil_rate_bopd=0.00,
        liquid_rate_bpd=0.00,
        gas_rate_mscfd=0.00,
        motor_load_pct=0.00,
        water_cut_pct=78.20,
        anomaly_score=0.95,
        health_score=92.00,
    )
    result = check_kpi_alarms(ev)

    assert result.has_critical, "Expected CRITICAL alarms on dead well data"
    assert not result.is_clean

    critical_signals = {a.signal for a in result.alarms if a.severity == "CRITICAL"}
    assert "oil_rate_bopd" in critical_signals
    assert "liquid_rate_bpd" in critical_signals
    assert "motor_load_pct" in critical_signals
    assert "anomaly_score" in critical_signals


def test_dead_well_alarm_summary_contains_constraint():
    """alarm_summary() for dead well must contain the ASSESSMENT CONSTRAINT block."""
    ev = _make_evidence(
        oil_rate_bopd=0.00,
        liquid_rate_bpd=0.00,
        motor_load_pct=0.00,
        anomaly_score=0.95,
    )
    result = check_kpi_alarms(ev)
    summary = result.alarm_summary()
    assert "ASSESSMENT CONSTRAINT" in summary
    assert "functioning as expected" in summary
    assert "KPI ALARM PRE-CHECK" in summary


# -- Healthy well: no alarms --

def test_healthy_well_is_clean():
    """Normal production values must produce no alarms."""
    ev = _make_evidence(
        oil_rate_bopd=320.5,
        liquid_rate_bpd=412.0,
        gas_rate_mscfd=1.8,
        motor_load_pct=72.3,
        water_cut_pct=22.0,
        anomaly_score=0.12,
        health_score=91.0,
    )
    result = check_kpi_alarms(ev)
    assert result.is_clean
    assert not result.has_critical
    assert not result.has_high
    assert result.alarm_summary() == ""


# -- Anomaly score boundary tests --

def test_anomaly_score_below_threshold_no_alarm():
    ev = _make_evidence(anomaly_score=0.84)
    result = check_kpi_alarms(ev)
    alarm_signals = {a.signal for a in result.alarms}
    assert "anomaly_score" not in alarm_signals


def test_anomaly_score_at_high_threshold():
    ev = _make_evidence(anomaly_score=0.85)
    result = check_kpi_alarms(ev)
    anomaly_alarms = [a for a in result.alarms if a.signal == "anomaly_score"]
    assert len(anomaly_alarms) == 1
    assert anomaly_alarms[0].severity == "HIGH"


def test_anomaly_score_at_critical_threshold():
    ev = _make_evidence(anomaly_score=0.95)
    result = check_kpi_alarms(ev)
    anomaly_alarms = [a for a in result.alarms if a.signal == "anomaly_score"]
    assert len(anomaly_alarms) == 1, "Must be exactly one alarm per signal"
    assert anomaly_alarms[0].severity == "CRITICAL"


def test_anomaly_score_0_99_is_critical():
    ev = _make_evidence(anomaly_score=0.99)
    result = check_kpi_alarms(ev)
    critical = [a for a in result.alarms if a.signal == "anomaly_score" and a.severity == "CRITICAL"]
    assert critical


# -- Per-signal single-alarm rule --

def test_single_alarm_per_signal():
    """
    anomaly_score=0.95 matches both the HIGH (>=0.85) and CRITICAL (>=0.95) rule.
    Only the CRITICAL alarm must appear -- not both.
    """
    ev = _make_evidence(anomaly_score=0.95)
    result = check_kpi_alarms(ev)
    anomaly_alarms = [a for a in result.alarms if a.signal == "anomaly_score"]
    assert len(anomaly_alarms) == 1


# -- Water cut --

def test_water_cut_at_95_fires_high():
    ev = _make_evidence(water_cut_pct=95.0)
    result = check_kpi_alarms(ev)
    wc_alarms = [a for a in result.alarms if a.signal == "water_cut_pct"]
    assert wc_alarms
    assert wc_alarms[0].severity == "HIGH"


def test_water_cut_78_no_alarm():
    """78.2% water cut is high but below the 95% threshold -- no alarm."""
    ev = _make_evidence(water_cut_pct=78.2)
    result = check_kpi_alarms(ev)
    wc_alarms = [a for a in result.alarms if a.signal == "water_cut_pct"]
    assert not wc_alarms


# -- Edge: empty evidence --

def test_empty_evidence_is_clean():
    ev = FormattedEvidence(run_id="test-run", pack_version=1)
    result = check_kpi_alarms(ev)
    assert result.is_clean
    assert result.alarm_summary() == ""


# -- has_high includes CRITICAL --

def test_has_high_includes_critical():
    """has_high must be True when only CRITICAL alarms are present."""
    ev = _make_evidence(oil_rate_bopd=0.0)
    result = check_kpi_alarms(ev)
    assert result.has_critical
    assert result.has_high
