import os
import pandas as pd
from typing import Dict, Any, Optional


def render_ascii_bar(val: float, min_val: float, max_val: float, width: int = 20) -> str:
    """Renders an ASCII bar for universal terminal visualization."""
    if max_val == min_val:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (val - min_val) / (max_val - min_val)))
    filled_len = int(round(ratio * width))
    bar = "=" * filled_len + "-" * (width - filled_len)
    return f"[{bar}]"


def generate_terminal_visualization(
    csv_path: str,
    asset_id: str = "ESP-Well-001",
    parameter_name: str = "motor_temperature",
    limit: int = 10
) -> Dict[str, Any]:
    """Generates an in-terminal bar chart & trend plot for telemetry readings."""
    if not os.path.exists(csv_path):
        return {"status": "error", "message": f"File not found: {csv_path}"}

    df = pd.read_csv(csv_path)
    if df.empty:
        return {"status": "error", "message": "Telemetry file is empty"}

    if "asset_id" in df.columns:
        df = df[df["asset_id"] == asset_id]

    if df.empty:
        return {"status": "error", "message": f"No records found for asset {asset_id}"}

    recent_df = df.tail(limit).copy()

    # Determine mapped parameter
    param_col = None
    for col in recent_df.columns:
        if parameter_name.lower() in col.lower() or col.lower() in parameter_name.lower():
            param_col = col
            break

    if not param_col:
        param_col = "motor_temperature" if "motor_temperature" in recent_df.columns else recent_df.columns[2]

    values = recent_df[param_col].astype(float).tolist()
    timestamps = recent_df["timestamp"].astype(str).tolist()

    min_v = min(values)
    max_v = max(values)

    lines = []
    lines.append(f"\nTerminal Visualization: {param_col} (Last {len(values)} Readings)")
    
    for ts, val in zip(timestamps, values):
        short_ts = ts.split("T")[-1][:5] if "T" in ts else ts[-8:]
        bar = render_ascii_bar(val, min_v * 0.8 if min_v > 0 else min_v, max_v * 1.1 if max_v > 0 else 1.0, width=20)
        alert = " [ALERT]" if ("temp" in param_col and val > 130) or ("vib" in param_col and val > 3.0) or ("intake" in param_col and val < 150) else ""
        lines.append(f"  {short_ts} | {bar} {val:>7.2f}{alert}")

    chart_str = "\n".join(lines)

    return {
        "status": "success",
        "parameter": param_col,
        "record_count": len(values),
        "terminal_chart": chart_str,
        "min_value": min_v,
        "max_value": max_v,
        "latest_value": values[-1]
    }
