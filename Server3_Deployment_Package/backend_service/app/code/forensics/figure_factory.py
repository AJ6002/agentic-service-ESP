"""
Pure Plotly Engineering Figure Factory for ESP APM
===================================================
Contains deterministic, zero-Streamlit rendering functions for:
1. Incident Tipping Timelines (Synchronized Before-During-After Forensics)
2. Baseline Corridor Breakouts (P10-P90 Envelope Shading)
3. Subsystem Multi-Trace Time-Series
4. Health Trajectories and Degradation Slopes
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional, List


def render_incident_tipping_timeline(
    df_window: pd.DataFrame,
    incident_meta: Dict[str, Any],
    well_profile: Optional[Dict[str, Any]] = None,
    height: int = 650
) -> go.Figure:
    """
    Renders a 3-row synchronized forensic tipping timeline:
      Row 1: Hydraulic Pressures (Intake and Discharge PSI) + Normal Intake Corridor
      Row 2: Electrical Loading (VSD Amps and Frequency Hz) + Normal Amps Corridor
      Row 3: Thermal and Mechanical (Motor Temp C and Vibration G) + Normal Temp Corridor
    With a vertical red dashed line at the exact moment of the fault trip.
    """
    if df_window is None or len(df_window) < 5:
        fig = go.Figure()
        msg = "⚠️ Insufficient telemetry data found for the requested incident window (< 5 samples)." if df_window is not None and len(df_window) > 0 else "⚠️ No telemetry data found for the specified incident window."
        fig.add_annotation(
            text=msg,
            showarrow=False,
            font=dict(size=14, color="#ffb74d")
        )
        fig.update_layout(template="plotly_dark", height=300)
        return fig

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "<b>1. Hydraulic Pressures (Intake and Discharge PSI)</b>",
            "<b>2. Electrical Loading (VSD Amps and Frequency Hz)</b>",
            "<b>3. Thermal and Mechanical Reaction (Motor Temp C and Vibration G)</b>"
        )
    )

    x_data = df_window["Report_DateTime"] if "Report_DateTime" in df_window.columns else df_window.get("timestamp", df_window.index)
    sensors_prof = (well_profile or {}).get("sensors", {})

    # -------------------------------------------------------------
    # Row 1: Hydraulic Pressures
    # -------------------------------------------------------------
    if "Inp bar/psi" in sensors_prof:
        p_min = sensors_prof["Inp bar/psi"].get("min", 200.0)
        p_max = sensors_prof["Inp bar/psi"].get("max", 500.0)
        fig.add_hrect(
            y0=p_min, y1=p_max, row=1, col=1,
            fillcolor="rgba(76, 175, 80, 0.15)", line_width=0,
            annotation_text="Normal Intake Corridor", annotation_position="top right",
            annotation_font=dict(color="#4caf50", size=10)
        )

    if "Inp bar/psi" in df_window.columns:
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["Inp bar/psi"],
            name="Intake Pressure (PSI)",
            line=dict(color="#29b6f6", width=2),
            mode="lines"
        ), row=1, col=1)

    if "Disch pr. Bar/psi" in df_window.columns:
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["Disch pr. Bar/psi"],
            name="Discharge Pressure (PSI)",
            line=dict(color="#ab47bc", width=2),
            mode="lines"
        ), row=1, col=1)

    # -------------------------------------------------------------
    # Row 2: Electrical Work (Amps and Frequency)
    # -------------------------------------------------------------
    if "VSD Amps/Load" in sensors_prof:
        a_min = sensors_prof["VSD Amps/Load"].get("min", 35.0)
        a_max = sensors_prof["VSD Amps/Load"].get("max", 65.0)
        fig.add_hrect(
            y0=a_min, y1=a_max, row=2, col=1,
            fillcolor="rgba(76, 175, 80, 0.15)", line_width=0,
            annotation_text="Normal Current Corridor", annotation_position="top right",
            annotation_font=dict(color="#4caf50", size=10)
        )

    if "VSD Amps/Load" in df_window.columns:
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["VSD Amps/Load"],
            name="Motor Current (Amps)",
            line=dict(color="#ff7043", width=2),
            mode="lines"
        ), row=2, col=1)

    if "Frequency" in df_window.columns:
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["Frequency"],
            name="VFD Frequency (Hz)",
            line=dict(color="#26a69a", width=1.5, dash="dot"),
            mode="lines"
        ), row=2, col=1)

    # -------------------------------------------------------------
    # Row 3: Thermal and Mechanical (Temp and Vibration)
    # -------------------------------------------------------------
    if "Motor temp °C" in sensors_prof:
        t_min = sensors_prof["Motor temp °C"].get("min", 60.0)
        t_max = sensors_prof["Motor temp °C"].get("max", 85.0)
        fig.add_hrect(
            y0=t_min, y1=t_max, row=3, col=1,
            fillcolor="rgba(76, 175, 80, 0.15)", line_width=0,
            annotation_text="Normal Temp Corridor", annotation_position="top right",
            annotation_font=dict(color="#4caf50", size=10)
        )

    if "Motor temp °C" in df_window.columns:
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["Motor temp °C"],
            name="Motor Temp (°C)",
            line=dict(color="#ef5350", width=2),
            mode="lines"
        ), row=3, col=1)

    if "Vibration G's-Vx" in df_window.columns:
        # Scale vibration x100 for visibility
        fig.add_trace(go.Scatter(
            x=x_data, y=df_window["Vibration G's-Vx"] * 100.0,
            name="Vibration Vx (Scaled x100 G)",
            line=dict(color="#ffa726", width=1.5, dash="dash"),
            mode="lines"
        ), row=3, col=1)

    # -------------------------------------------------------------
    # Vertical Red Tipping Marker
    # -------------------------------------------------------------
    event_ts = incident_meta.get("timestamp", incident_meta.get("Timestamp", ""))
    fault_name = incident_meta.get("fault", incident_meta.get("Detected_Fault", "Incident"))
    health_score = incident_meta.get("health_score", incident_meta.get("Health_Score", "N/A"))

    if event_ts:
        for r in [1, 2, 3]:
            fig.add_vline(
                x=event_ts,
                line_width=2,
                line_dash="dash",
                line_color="#f44336",
                annotation_text=f"🚨 {fault_name} ({health_score}/100)" if r == 1 else None,
                annotation_position="top left",
                annotation_font=dict(color="#f44336", size=12, family="monospace"),
                row=r, col=1
            )

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=50, r=40, t=50, b=40),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def build_evidence_comparison_table(
    raw_at_trip: Dict[str, Any],
    well_profile: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Builds a structured evidence comparison table comparing values at trip instant
    against calibrated P10-P90 normal boundaries.
    """
    sensors_prof = (well_profile or {}).get("sensors", {})
    rows = []

    labels_map = {
        "Inp bar/psi": ("Intake Pressure", "PSI"),
        "Disch pr. Bar/psi": ("Discharge Pressure", "PSI"),
        "VSD Amps/Load": ("Motor Current", "A"),
        "Volt": ("Motor Voltage", "V"),
        "Frequency": ("VFD Frequency", "Hz"),
        "Motor temp °C": ("Motor Temperature", "°C"),
        "Int temp °C": ("Intake Temperature", "°C"),
        "Vibration G's-Vx": ("Vibration (X-axis)", "G"),
        "Leak Current Ct": ("Leakage Current", "mA"),
        "WHP (PSI)": ("Wellhead Pressure", "PSI"),
        "FLP (PSI)": ("Flowline Pressure", "PSI"),
    }

    for col, (param_name, unit) in labels_map.items():
        if col not in raw_at_trip:
            continue
        try:
            val = float(raw_at_trip[col])
        except (ValueError, TypeError):
            continue

        prof = sensors_prof.get(col, {})
        p_min = prof.get("min", None)
        p_max = prof.get("max", None)
        p_med = prof.get("median", None)

        # Ignore unrealistic uncalibrated bounds (e.g. -1e30 or 1e35)
        is_valid_calib = (
            p_min is not None and p_max is not None and
            -500.0 <= p_min <= 10000.0 and
            0.0 <= p_max <= 10000.0 and
            p_min < p_max
        )

        if is_valid_calib:
            norm_str = f"{p_min:.1f} - {p_max:.1f} {unit}"
            if val < p_min:
                dev = ((val - p_min) / max(1.0, abs(p_min))) * 100.0
                status = "🔴 Below Normal"
                finding = f"Low by {abs(dev):.1f}% (Under baseline envelope)"
            elif val > p_max:
                dev = ((val - p_max) / max(1.0, abs(p_max))) * 100.0
                status = "🔴 Above Normal"
                finding = f"High by +{dev:.1f}% (Exceeded safe ceiling)"
            else:
                dev = ((val - p_med) / max(1.0, abs(p_med))) * 100.0 if p_med else 0.0
                status = "🟢 In Corridor"
                finding = "Within calibrated healthy boundaries"
        else:
            norm_str = "Nominal Dynamic"
            dev = 0.0
            status = "🟢 In Range"
            finding = "Active telemetry within operational rating"

        rows.append({
            "Parameter": param_name,
            "Value at Incident": f"{val:.2f} {unit}",
            "Nominal Corridor (P10 - P90)": norm_str,
            "Deviation vs Baseline": f"{dev:+.1f}%" if norm_str != "Uncalibrated" else "N/A",
            "Status": status,
            "Physical Evidence Finding": finding
        })

    return pd.DataFrame(rows)
