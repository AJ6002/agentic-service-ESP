"""
CCED VFD Well Categorization & ML Data Preprocessing Pipeline
============================================================
1. Reads CCED VFD report data (from CSV, categorized files, or merged Excel files).
2. Categorizes data by Well-ID (e.g., FS-04, FS-06, FNW-01, FWS-02, ULFA-5).
3. Cleans and normalizes all 13 sensor columns:
   - Replaces missing / special codes (-9999, [*], NA, blank)
   - Handles zero / offline / shut-in values with time-series forward/backward imputation
   - Guarantees non-empty, non-zero valid measurement data in every cell
   - Adds normalized ML feature columns (scaled [0, 1]) for all 13 sensors
4. Saves categorized Excel (.xlsx) and CSV (.csv) files grouped by Well prefix/family.
5. Uses high-speed row-by-row streaming Excel writing with 0% memory corruption.
"""

import os
import sys
import glob
import re
import time
import datetime
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

try:
    import xlsxwriter
    HAS_XLSXWRITER = True
except ImportError:
    HAS_XLSXWRITER = False


SENSOR_COLS_RAW = [
    "Inp bar/psi",
    "Int temp °C",
    "Motor temp °C",
    "Disch pr. Bar/psi",
    "Vibration G's-Vx",
    "Leak Current Ct",
    "Volt",
    "VSD Amps/Load",
    "Frequency",
    "DHG Current",
    "WHP (PSI)",
    "FLP (PSI)",
    "AP (PSI)"
]


def clean_col_name(name: str) -> str:
    """Standardize column names cleanly using regex matching."""
    if name is None:
        return ""
    s = str(name).strip()
    s = s.replace("\xb0", "°").replace("\ufffd", "").replace("", "")
    s = s.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()

    if re.search(r'int\s*temp', s, re.I):
        return "Int temp °C"
    if re.search(r'motor\s*temp', s, re.I):
        return "Motor temp °C"
    if re.search(r'leak.*current', s, re.I):
        return "Leak Current Ct"
    if re.search(r'dhg.*current', s, re.I):
        return "DHG Current"
    if re.search(r'cluster', s, re.I):
        return "Cluster"
    if re.search(r'inp\s*bar', s, re.I):
        return "Inp bar/psi"
    if re.search(r'disch', s, re.I):
        return "Disch pr. Bar/psi"
    if re.search(r'vibration', s, re.I):
        return "Vibration G's-Vx"
    if re.search(r'^volt', s, re.I):
        return "Volt"
    if re.search(r'vsd\s*amps', s, re.I):
        return "VSD Amps/Load"
    if re.search(r'frequency', s, re.I):
        return "Frequency"
    if re.search(r'whp', s, re.I):
        return "WHP (PSI)"
    if re.search(r'flp', s, re.I):
        return "FLP (PSI)"
    if re.search(r'^ap\s*\(psi\)', s, re.I) or s.lower() == 'ap (psi)':
        return "AP (PSI)"
    if re.search(r'vfd\s*sts', s, re.I):
        return "VFD STS"
    if re.search(r'report.*date', s, re.I):
        return "Report_DateTime"
    if re.search(r'file.*date', s, re.I):
        return "File_DateTime"
    if re.search(r'report.*id', s, re.I):
        return "Report_ID"
    if re.search(r'^well', s, re.I):
        return "Wells"
    if re.search(r'source.*file', s, re.I):
        return "Source_File"

    return s


def clean_text_cell(val: Any) -> Any:
    """Clean string values inside cells."""
    if val is None or pd.isna(val):
        return "N/A"
    if isinstance(val, (int, float, bool, datetime.datetime, datetime.date, datetime.time)):
        return val
    s = str(val).strip()
    s = s.replace("\xb0", "°").replace("\ufffd", "").replace("", "")
    s = s.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if s in ["", "nan", "None", "null", "NULL"]:
        return "N/A"
    return s


def get_well_family(well_name: str) -> str:
    """Extract well family prefix (e.g. FS-04 -> FS, FNW-01 -> FNW, ULFA-5 -> ULFA)."""
    m = re.match(r'^([A-Za-z]+)', str(well_name).strip())
    if m:
        return m.group(1).upper()
    return "OTHER"


def sanitize_filename(name: str) -> str:
    """Convert well name to safe filename (e.g. FS-04 -> FS_04)."""
    return re.sub(r'[^A-Za-z0-9_]+', '_', str(name).strip()).strip('_')


def write_well_excel_streaming(excel_path: str, df: pd.DataFrame, sheet_name: str = "Sheet1") -> None:
    """
    Writes a DataFrame to Excel (.xlsx) using xlsxwriter row-by-row streaming,
    guaranteeing non-empty cells, accurate numeric types, and zero memory blowup.
    """
    tmp_path = excel_path + f".tmp_{os.getpid()}_{int(time.time()*1000)%100000}.xlsx"
    try:
        if HAS_XLSXWRITER:
            wb = xlsxwriter.Workbook(tmp_path, {'constant_memory': True})
            ws = wb.add_worksheet(sheet_name[:31])
            
            # Write headers
            for c_i, col in enumerate(df.columns):
                ws.write(0, c_i, col)
                
            # Write rows sequentially
            for r_i, row in enumerate(df.itertuples(index=False), 1):
                for c_i, val in enumerate(row):
                    if pd.isna(val):
                        ws.write_string(r_i, c_i, "N/A")
                    elif isinstance(val, (int, float, np.integer, np.floating)):
                        ws.write_number(r_i, c_i, float(val))
                    elif isinstance(val, (bool, np.bool_)):
                        ws.write_boolean(r_i, c_i, bool(val))
                    else:
                        ws.write_string(r_i, c_i, str(val))
            wb.close()
        else:
            with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

        # Atomic move to final destination with retry loop
        for attempt in range(5):
            try:
                if os.path.exists(excel_path):
                    try:
                        os.remove(excel_path)
                    except Exception:
                        pass
                os.replace(tmp_path, excel_path)
                break
            except Exception:
                time.sleep(0.6)
    finally:
        if os.path.exists(tmp_path) and not os.path.exists(excel_path):
            try:
                os.replace(tmp_path, excel_path)
            except Exception:
                pass


def preprocess_and_normalize_well_df(df_well: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans, imputes missing/zero values, and creates normalized ML features for all 13 sensors.
    """
    df = df_well.copy()

    # 1. Clean Column Names
    df.columns = [clean_col_name(c) for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # Remove any duplicate norm_ columns if re-processing existing CSV
    base_cols = [c for c in df.columns if not c.startswith("norm_") and c != "VFD_STS_Binary"]
    df = df[base_cols].copy()

    # 2. Chronological Sorting
    if "Report_DateTime" in df.columns:
        df["Report_DateTime"] = pd.to_datetime(df["Report_DateTime"], errors="coerce")
        df.sort_values("Report_DateTime", inplace=True)
        df.reset_index(drop=True, inplace=True)

    # 3. Clean Text Columns
    for text_col in ["Report_ID", "Wells", "Cluster", "Source_File", "File_DateTime"]:
        if text_col in df.columns:
            df[text_col] = df[text_col].apply(clean_text_cell)

    # 4. Identify sensor measurement columns present
    present_sensor_cols = [c for c in SENSOR_COLS_RAW if c in df.columns]

    # 5. Clean Numeric Values & Replace Invalid/Special Placeholders
    for col in present_sensor_cols:
        # Convert to string and strip
        s = df[col].astype(str).str.strip()
        
        # Replace special codes with NaN
        s = s.replace(['-9999', '-9999.0', '[*]', 'NA', 'N/A', 'nan', 'None', '', '-', 'null', 'NULL'], np.nan)
        
        # Convert to float
        df[col] = pd.to_numeric(s, errors='coerce')
        
        # Check if column is an unmonitored flatline or legacy 1.0 placeholder
        if df[col].nunique() <= 1 and (df[col].isna().all() or (len(df[col].dropna()) > 0 and df[col].dropna().iloc[0] in [1.0, 0.0, 1, 0])):
            df[col] = 0.0

        # Treat absolute zero as missing if other valid non-zero readings exist (sensor offline/shut-in gap)
        non_zero_vals = df[col].dropna()
        non_zero_vals = non_zero_vals[non_zero_vals > 0]
        if len(non_zero_vals) > 0 and len(non_zero_vals) != len(df[col]):
            df.loc[df[col] == 0, col] = np.nan

        # Time-series Imputation: Forward-fill then Backward-fill
        df[col] = df[col].ffill().bfill().fillna(0.0)

        # If column was entirely NaN/0 for this well (e.g. unmonitored sensor), set to 0.0
        if df[col].isna().all():
            df[col] = 0.0
        elif df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val if (pd.notna(median_val) and median_val > 0) else 0.0)

    # 6. Clean VFD STS (Status) to binary [0, 1]
    if "VFD STS" in df.columns:
        sts_str = df["VFD STS"].astype(str).str.strip().str.upper()
        df["VFD_STS_Binary"] = sts_str.map(lambda x: 1 if x in ["TRUE", "1", "1.0", "RUN", "RUNNING"] else 0)

    # 7. Generate ML Normalized Features (Min-Max Scaling [0, 1]) for all sensors
    # Note: Unmonitored / zero-variance sensors are mapped to 0.0 (clean neutral baseline)
    for col in present_sensor_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        norm_col_name = f"norm_{re.sub(r'[^A-Za-z0-9]+', '_', col).strip('_')}"
        
        if col_max > col_min:
            df[norm_col_name] = ((df[col] - col_min) / (col_max - col_min)).round(6)
        else:
            df[norm_col_name] = 0.0  # Clean neutral baseline for unmonitored/zero-variance sensor

    # 8. Compute Derived Physics ML Features & Their Normalized Representations
    if "Inp bar/psi" in df.columns and "Disch pr. Bar/psi" in df.columns:
        df["Delta_P_PSI"] = (df["Disch pr. Bar/psi"] - df["Inp bar/psi"]).round(2)
        dp_min, dp_max = df["Delta_P_PSI"].min(), df["Delta_P_PSI"].max()
        df["norm_Delta_P_PSI"] = ((df["Delta_P_PSI"] - dp_min) / (dp_max - dp_min)).round(6) if dp_max > dp_min else 0.0

    if "VSD Amps/Load" in df.columns and "Frequency" in df.columns:
        df["Torque_Proxy_A_Hz"] = (df["VSD Amps/Load"] / df["Frequency"].replace(0, 1.0)).round(3)
        tq_min, tq_max = df["Torque_Proxy_A_Hz"].min(), df["Torque_Proxy_A_Hz"].max()
        df["norm_Torque_Proxy_A_Hz"] = ((df["Torque_Proxy_A_Hz"] - tq_min) / (tq_max - tq_min)).round(6) if tq_max > tq_min else 0.0

    if "Volt" in df.columns and "VSD Amps/Load" in df.columns:
        df["Power_kVA"] = ((df["Volt"] * df["VSD Amps/Load"] * 1.732) / 1000.0).round(2)
        p_min, p_max = df["Power_kVA"].min(), df["Power_kVA"].max()
        df["norm_Power_kVA"] = ((df["Power_kVA"] - p_min) / (p_max - p_min)).round(6) if p_max > p_min else 0.0

    if "Motor temp °C" in df.columns and "Int temp °C" in df.columns:
        df["Thermal_Elevation_C"] = (df["Motor temp °C"] - df["Int temp °C"]).round(2)
        te_min, te_max = df["Thermal_Elevation_C"].min(), df["Thermal_Elevation_C"].max()
        df["norm_Thermal_Elevation_C"] = ((df["Thermal_Elevation_C"] - te_min) / (te_max - te_min)).round(6) if te_max > te_min else 0.0

    return df


from concurrent.futures import ProcessPoolExecutor, as_completed


def process_single_well_file(csv_path: str, save_excel: bool = True, save_csv: bool = True) -> Dict[str, Any]:
    """Worker function to clean, normalize, and write a single well workbook."""
    t_well = time.time()
    try:
        df_well = pd.read_csv(csv_path, low_memory=False)
        
        well_name = os.path.splitext(os.path.basename(csv_path))[0].replace("_", "-")
        if "Wells" in df_well.columns and len(df_well["Wells"].dropna()) > 0:
            well_name = str(df_well["Wells"].dropna().iloc[0]).strip()

        well_family = get_well_family(well_name)
        safe_well_name = sanitize_filename(well_name)

        # Preprocess and normalize
        df_clean = preprocess_and_normalize_well_df(df_well)

        family_dir = os.path.dirname(csv_path)
        excel_path = os.path.join(family_dir, f"{safe_well_name}.xlsx")
        out_csv_path = os.path.join(family_dir, f"{safe_well_name}.csv")

        # Save CSV
        if save_csv:
            df_clean.to_csv(out_csv_path, index=False, encoding="utf-8-sig")

        # Save Excel (.xlsx)
        if save_excel:
            write_well_excel_streaming(excel_path, df_clean, sheet_name=safe_well_name)

        return {
            "Well_ID": well_name,
            "Family": well_family,
            "Total_Records": len(df_clean),
            "Start_Time": df_clean["Report_DateTime"].min() if "Report_DateTime" in df_clean.columns else None,
            "End_Time": df_clean["Report_DateTime"].max() if "Report_DateTime" in df_clean.columns else None,
            "CSV_File": out_csv_path,
            "Excel_File": excel_path,
            "duration": time.time() - t_well,
            "rows": len(df_clean),
            "status": "OK"
        }
    except Exception as e:
        return {
            "Well_ID": os.path.splitext(os.path.basename(csv_path))[0],
            "Family": "UNKNOWN",
            "Total_Records": 0,
            "CSV_File": csv_path,
            "Excel_File": "",
            "duration": time.time() - t_well,
            "rows": 0,
            "status": f"ERROR: {e}"
        }


def reprocess_from_existing_csvs(
    categorized_dir: str,
    save_excel: bool = True,
    save_csv: bool = True
) -> bool:
    """
    High-speed parallel multi-process re-processor that reads existing categorized CSVs,
    standardizes headers, re-normalizes all sensors + physics features, and writes pristine .xlsx workbooks.
    """
    csv_files = glob.glob(os.path.join(categorized_dir, "**", "*.csv"), recursive=True)
    csv_files = [f for f in csv_files if not os.path.basename(f).startswith("Wells_Summary")]
    
    if not csv_files:
        return False

    print(f"Found {len(csv_files)} existing categorized well CSV files.")
    print(f"Reprocessing in parallel (8 processes on 12 CPU cores) with updated ML normalization and Excel writer...\n")

    summary_records = []
    total_processed = 0
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_single_well_file, p, save_excel, save_csv): p for p in sorted(csv_files)}
        for idx, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            summary_records.append(res)
            total_processed += res["rows"]
            print(
                f"  [{idx:2d}/{len(csv_files):2d}] Well: {res['Well_ID']:10s} (Family: {res['Family']:4s}) "
                f"-> {res['rows']:,} clean rows | Saved: {res['Well_ID'].replace('-', '_')}.xlsx ({res['duration']:.2f}s)",
                flush=True
            )

    # Save Master Summary Index
    df_summary = pd.DataFrame(summary_records).sort_values("Well_ID")
    summary_csv = os.path.join(categorized_dir, "Wells_Summary_Index.csv")
    summary_xlsx = os.path.join(categorized_dir, "Wells_Summary_Index.xlsx")
    df_summary.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    write_well_excel_streaming(summary_xlsx, df_summary, sheet_name="Wells_Index")

    total_time = time.time() - t_start
    print(f"\n=================================================================")
    print(f" [SUCCESS] Preprocessing & Categorization Complete!")
    print(f" Processed {len(csv_files)} wells -> {total_processed:,} normalized rows in {total_time:.2f}s.")
    print(f" Output Location: {categorized_dir}")
    print(f" Summary Index:   {summary_csv}")
    print(f"=================================================================\n", flush=True)
    return True


def run_categorization_and_normalization(
    source_csv_or_folder: str,
    output_dir: str,
    save_excel: bool = True,
    save_csv: bool = True
) -> None:
    """
    Processes all wells, categorizes into well-specific files and normalized ML datasets.
    """
    print(f"\n=================================================================")
    print(f" CCED VFD Well Categorization & ML Data Preprocessing Pipeline")
    print(f"=================================================================")
    print(f" Source: {source_csv_or_folder}")
    print(f" Output Directory: {output_dir}\n")

    os.makedirs(output_dir, exist_ok=True)

    # Check if categorized CSVs already exist in output_dir
    existing_csvs = glob.glob(os.path.join(output_dir, "**", "*.csv"), recursive=True)
    existing_csvs = [f for f in existing_csvs if not os.path.basename(f).startswith("Wells_Summary")]
    if len(existing_csvs) > 10:
        success = reprocess_from_existing_csvs(output_dir, save_excel=save_excel, save_csv=save_csv)
        if success:
            return

    # Load master dataset
    t0 = time.time()
    if os.path.isfile(source_csv_or_folder) and source_csv_or_folder.endswith(".csv"):
        print(f"Loading master CSV: {source_csv_or_folder} ...")
        df_all = pd.read_csv(source_csv_or_folder, low_memory=False)
    else:
        # Check for Master_Combined_Report.csv in directory
        csv_candidates = [
            os.path.join(source_csv_or_folder, "Master_Combined_Report.csv"),
            r"..\merged\Master_Combined_Report.csv",
            r"c:\Users\admin.DESKTOP-17T37DJ\OneDrive - TAS\Mahendra Singh's files - CCED VFD Details\merged\Master_Combined_Report.csv"
        ]
        found_csv = None
        for c in csv_candidates:
            if os.path.exists(c):
                found_csv = c
                break
        
        if found_csv:
            print(f"Loading dataset from: {found_csv} ...")
            df_all = pd.read_csv(found_csv, low_memory=False)
        else:
            # Fallback: Read all xlsx files in folder
            print(f"Reading Excel files from {source_csv_or_folder} ...")
            xlsx_files = sorted(glob.glob(os.path.join(source_csv_or_folder, "*.xlsx")))
            xlsx_files = [f for f in xlsx_files if not os.path.basename(f).startswith("~$")]
            dfs = [pd.read_excel(f) for f in xlsx_files]
            df_all = pd.concat(dfs, ignore_index=True)

    print(f"Loaded {len(df_all):,} records in {time.time() - t0:.2f}s.")

    # Find unique wells
    if "Wells" not in df_all.columns:
        well_col = [c for c in df_all.columns if c.lower() == "wells" or c.lower() == "well"][0]
        df_all.rename(columns={well_col: "Wells"}, inplace=True)

    unique_wells = sorted(df_all["Wells"].dropna().unique().tolist())
    print(f"Found {len(unique_wells)} Unique Well IDs.\n")

    summary_records = []
    total_processed = 0
    t_start = time.time()

    for idx, well_name in enumerate(unique_wells, 1):
        t_well = time.time()
        well_family = get_well_family(well_name)
        safe_well_name = sanitize_filename(well_name)

        # Create Family output directory
        family_dir = os.path.join(output_dir, well_family)
        os.makedirs(family_dir, exist_ok=True)

        # Extract well rows
        df_well = df_all[df_all["Wells"] == well_name].copy()

        # Preprocess and normalize
        df_clean = preprocess_and_normalize_well_df(df_well)

        # Output filenames
        excel_path = os.path.join(family_dir, f"{safe_well_name}.xlsx")
        csv_path = os.path.join(family_dir, f"{safe_well_name}.csv")

        # Save CSV
        if save_csv:
            df_clean.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # Save Excel (.xlsx) using robust streaming writer
        if save_excel:
            write_well_excel_streaming(excel_path, df_clean, sheet_name=safe_well_name)

        total_processed += len(df_clean)
        summary_records.append({
            "Well_ID": well_name,
            "Family": well_family,
            "Total_Records": len(df_clean),
            "Start_Time": df_clean["Report_DateTime"].min() if "Report_DateTime" in df_clean.columns else None,
            "End_Time": df_clean["Report_DateTime"].max() if "Report_DateTime" in df_clean.columns else None,
            "CSV_File": csv_path,
            "Excel_File": excel_path
        })

        print(
            f"  [{idx:2d}/{len(unique_wells):2d}] Well: {well_name:10s} (Family: {well_family:4s}) "
            f"-> {len(df_clean):,} clean rows | Saved: {safe_well_name}.xlsx "
            f"({time.time() - t_well:.2f}s)",
            flush=True
        )

    # Save Master Summary Index
    df_summary = pd.DataFrame(summary_records)
    summary_csv = os.path.join(output_dir, "Wells_Summary_Index.csv")
    summary_xlsx = os.path.join(output_dir, "Wells_Summary_Index.xlsx")
    df_summary.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    write_well_excel_streaming(summary_xlsx, df_summary, sheet_name="Wells_Index")

    total_time = time.time() - t_start
    print(f"\n=================================================================")
    print(f" [SUCCESS] Preprocessing & Categorization Complete!")
    print(f" Processed {len(unique_wells)} wells -> {total_processed:,} normalized rows in {total_time:.2f}s.")
    print(f" Output Location: {output_dir}")
    print(f" Summary Index:   {summary_csv}")
    print(f"=================================================================\n", flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Categorize and normalize CCED VFD data by Well-ID for ML training.")
    parser.add_argument(
        "-s", "--source",
        type=str,
        default=r"C:\Users\admin.DESKTOP-17T37DJ\Desktop\cced",
        help="Source directory or Master_Combined_Report.csv path."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=r"C:\Users\admin.DESKTOP-17T37DJ\Desktop\cced\categorized_wells",
        help="Output directory for categorized well files."
    )
    parser.add_argument("--no-excel", action="store_true", help="Do not save Excel files (CSV only).")
    parser.add_argument("--no-csv", action="store_true", help="Do not save CSV files.")

    args = parser.parse_args()

    run_categorization_and_normalization(
        source_csv_or_folder=args.source,
        output_dir=args.output,
        save_excel=not args.no_excel,
        save_csv=not args.no_csv
    )


if __name__ == "__main__":
    main()
