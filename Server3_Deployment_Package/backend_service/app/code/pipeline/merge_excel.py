"""
High-Performance CCED VFD Hourly Report & Excel Master Merger
============================================================
Merges Excel files/sheets inside a folder into a single clean dataset stacked vertically.

Supports:
1. Raw hourly reports (with timestamp extraction & empty row filtering)
2. Pre-merged backup files (e.g. Merged_VFD_Report_1.xlsx ... 10.xlsx)
3. Smart output handling: CSV (unlimited rows) + Multi-sheet Excel (.xlsx up to 1M rows/sheet)
4. Fast streaming & constant memory so it never freezes or crashes
"""

import os
import sys
import glob
import re
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Any
import openpyxl
import pandas as pd

try:
    import xlsxwriter
    HAS_XLSXWRITER = True
except ImportError:
    HAS_XLSXWRITER = False


STANDARD_COLUMNS = [
    "Report_DateTime",
    "File_DateTime",
    "Report_ID",
    "Wells",
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
    "AP (PSI)",
    "VFD STS",
    "Cluster",
    "Source_File"
]


def parse_filename_metadata(filename: str) -> Tuple[Optional[str], Optional[datetime.datetime]]:
    """
    Extracts Report ID and File DateTime from filename.
    """
    report_id = None
    file_dt = None

    # Pattern 1: Hourly_Report_639046_2025_12_31T20_00_00_000.xlsx
    m1 = re.search(r'Hourly_Report_(\d+)_(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})', filename, re.IGNORECASE)
    if m1:
        report_id = m1.group(1)
        y, m, d, h, mn, s = map(int, m1.groups()[1:7])
        try:
            file_dt = datetime.datetime(y, m, d, h, mn, s)
        except Exception:
            pass
        return report_id, file_dt

    # Pattern 2: Hourly_Report_2025_12_31T20_00_00... (without report id)
    m2 = re.search(r'(\d{4})_(\d{2})_(\d{2})T(\d{2})_(\d{2})_(\d{2})', filename)
    if m2:
        y, m, d, h, mn, s = map(int, m2.groups()[:6])
        try:
            file_dt = datetime.datetime(y, m, d, h, mn, s)
        except Exception:
            pass
        return report_id, file_dt

    # Pattern 3: Hourly_Report29-Jul-26 21_30_00.xlsx
    m3 = re.search(r'(\d{1,2})-([A-Za-z]{3})-(\d{2,4})\s+(\d{2})_(\d{2})_(\d{2})', filename)
    if m3:
        d_str, mon_str, y_str, h_str, mn_str, s_str = m3.groups()
        try:
            y = int(y_str)
            if y < 100:
                y += 2000
            file_dt = datetime.datetime.strptime(f"{d_str}-{mon_str}-{y} {h_str}:{mn_str}:{s_str}", "%d-%b-%Y %H:%M:%S")
        except Exception:
            pass
        return report_id, file_dt

    return report_id, file_dt


def clean_text_value(val: Any) -> Any:
    """Clean text values from encoding artifacts without destroying regular letters."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool, datetime.datetime, datetime.date, datetime.time)):
        return val
    s = str(val).strip()
    # Normalize degree Celsius variants
    s = s.replace("\xb0", "°").replace("\ufffdC", "°C").replace("C", "°C").replace("", "")
    s = s.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_single_file(file_path: str) -> Tuple[Optional[datetime.datetime], List[List[Any]], Optional[List[str]]]:
    """
    Parses a single Excel file (either raw hourly report OR pre-merged report).
    """
    filename = os.path.basename(file_path)
    report_id, file_dt = parse_filename_metadata(filename)

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_name = wb.sheetnames[0]
        ws = wb[sheet_name]
        row_iter = ws.iter_rows(values_only=True)
        first_row = next(row_iter, None)
    except Exception:
        return file_dt, [], None

    if first_row is None:
        return file_dt, [], None

    # Check if this is ALREADY a pre-merged report (first row has 'Report_DateTime' or 'Wells')
    first_row_cleaned = [clean_text_value(c) for c in first_row if c is not None]
    if any(h in ["Report_DateTime", "Report_ID", "File_DateTime"] for h in first_row_cleaned):
        # This is a pre-merged file! Read all rows directly
        headers = [clean_text_value(c) for c in first_row]
        data_rows = []
        for r in row_iter:
            if not any(c is not None for c in r):
                continue
            data_rows.append([clean_text_value(c) for c in r])
        wb.close()
        return file_dt, data_rows, headers

    # Otherwise, this is a raw hourly report file:
    rows = [first_row] + list(row_iter)
    wb.close()

    # 1. Extract Report DateTime from internal Time row (usually Row 7)
    sheet_dt = None
    for r in rows[:12]:
        non_none = [x for x in r if x is not None]
        if non_none and str(non_none[0]).strip().lower() == 'time':
            d_val = r[2] if len(r) > 2 else None
            t_val = r[3] if len(r) > 3 else None
            if isinstance(d_val, datetime.datetime) and isinstance(t_val, datetime.time):
                sheet_dt = datetime.datetime.combine(d_val.date(), t_val)
            elif isinstance(d_val, datetime.datetime):
                sheet_dt = d_val
            elif isinstance(d_val, str) and isinstance(t_val, str):
                try:
                    sheet_dt = datetime.datetime.strptime(f"{d_val.strip()} {t_val.strip()}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            break

    sort_dt = sheet_dt or file_dt or datetime.datetime.min

    # 2. Locate Header Row (usually row 9 with 'Wells' and 'Cluster')
    header_idx = None
    col_start = None
    col_end = None

    for idx, r in enumerate(rows[:15]):
        str_row = [str(x).strip() if x is not None else "" for x in r]
        for c_idx, c_val in enumerate(str_row):
            if c_val.lower() == 'wells' or c_val.lower() == 'well':
                header_idx = idx
                col_start = c_idx
                break
        if header_idx is not None:
            for c_idx in range(col_start, len(str_row)):
                if 'cluster' in str_row[c_idx].lower():
                    col_end = c_idx
            if col_end is None:
                for c_idx in range(len(str_row) - 1, col_start, -1):
                    if str_row[c_idx]:
                        col_end = c_idx
                        break
            break

    if header_idx is None or col_start is None or col_end is None:
        return sort_dt, [], None

    headers = [clean_text_value(rows[header_idx][i]) for i in range(col_start, col_end + 1)]

    # 3. Extract and filter data rows
    data_rows = []
    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        if len(row) <= col_start:
            continue

        first_cell = row[col_start]
        if first_cell is None:
            continue

        first_str = str(first_cell).strip()
        if not first_str or first_str.lower().startswith('note'):
            continue

        # Check middle columns: if all middle columns are empty, SKIP row!
        middle_values = [row[i] for i in range(col_start + 1, min(col_end, len(row)))]
        has_middle_data = any(
            v is not None and str(v).strip() != "" and str(v).strip() != "-"
            for v in middle_values
        )

        if not has_middle_data:
            continue

        row_vals = [clean_text_value(row[i]) if i < len(row) else None for i in range(col_start, col_end + 1)]
        
        full_row = [
            sheet_dt.strftime("%Y-%m-%d %H:%M:%S") if sheet_dt else None,
            file_dt.strftime("%Y-%m-%d %H:%M:%S") if file_dt else None,
            report_id,
        ] + row_vals + [filename]

        data_rows.append(full_row)

    return sort_dt, data_rows, headers


def write_excel_fast_streaming(xlsx_path: str, headers: List[str], final_rows: List[List[Any]]) -> None:
    """
    Writes large datasets to Excel using xlsxwriter constant memory mode with real-time live progress.
    """
    total_rows = len(final_rows)
    max_sheet_rows = 1_000_000
    t0 = time.time()

    if HAS_XLSXWRITER:
        workbook = xlsxwriter.Workbook(xlsx_path, {'constant_memory': True})
        
        num_sheets = (total_rows // max_sheet_rows) + (1 if total_rows % max_sheet_rows != 0 else 0)
        if num_sheets == 0:
            num_sheets = 1

        for sheet_idx in range(num_sheets):
            sheet_name = "Merged_VFD_Data" if num_sheets == 1 else f"Part_{sheet_idx + 1}"
            worksheet = workbook.add_worksheet(sheet_name)
            
            # Header
            for c_i, h_val in enumerate(headers):
                worksheet.write(0, c_i, h_val)
                
            start_row = sheet_idx * max_sheet_rows
            end_row = min(start_row + max_sheet_rows, total_rows)
            
            for r_i, row in enumerate(final_rows[start_row:end_row], 1):
                for c_i, val in enumerate(row):
                    if val is None:
                        continue
                    if isinstance(val, (int, float)):
                        worksheet.write_number(r_i, c_i, val)
                    elif isinstance(val, bool):
                        worksheet.write_boolean(r_i, c_i, val)
                    else:
                        worksheet.write_string(r_i, c_i, str(val))
                        
                current_global = start_row + r_i
                if current_global % 50000 == 0 or current_global == total_rows:
                    elapsed = time.time() - t0
                    pct = (current_global / total_rows) * 100
                    rate = current_global / elapsed if elapsed > 0 else 0
                    eta = (total_rows - current_global) / rate if rate > 0 else 0
                    print(
                        f"  [Excel Progress] {pct:5.1f}% ({current_global:,}/{total_rows:,} rows) "
                        f"| Speed: {rate:5.0f} rows/s | ETA: {eta:3.0f}s",
                        end="\r" if current_global < total_rows else "\n",
                        flush=True
                    )
                    
        print(f"\nFinalizing and saving Excel file...", flush=True)
        workbook.close()
    else:
        df = pd.DataFrame(final_rows, columns=headers)
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Merged_VFD_Data", index=False)


def process_folder(
    folder_path: str,
    output_base: Optional[str] = None,
    recursive: bool = False,
    max_workers: int = 16,
    save_csv: bool = True,
    save_excel: bool = True,
) -> None:
    """
    High-speed scanner and merger for all Excel files in folder.
    """
    if not os.path.exists(folder_path):
        print(f"[!] Error: Folder does not exist: {folder_path}", flush=True)
        return

    # Determine output file paths in advance so we never re-read destination outputs
    if not output_base:
        output_base = os.path.join(folder_path, "Master_Combined_Report")

    base_no_ext = os.path.splitext(output_base)[0]
    csv_path = os.path.abspath(f"{base_no_ext}.csv")
    xlsx_path = os.path.abspath(f"{base_no_ext}.xlsx")

    print(f"\n=======================================================", flush=True)
    print(f" Scanning folder: {folder_path}", flush=True)
    print(f" Recursive: {recursive} | Max Workers: {max_workers}", flush=True)
    print(f" Output Target: {base_no_ext}.[csv/xlsx]", flush=True)
    print(f"=======================================================\n", flush=True)

    # Find all Excel files
    all_files = []
    if recursive:
        for root, _, files in os.walk(folder_path):
            for f in files:
                full_f = os.path.abspath(os.path.join(root, f))
                if (f.lower().endswith(".xlsx") or f.lower().endswith(".xls")) and not f.startswith("~$"):
                    if full_f != xlsx_path and full_f != csv_path:
                        all_files.append(full_f)
    else:
        for f in os.listdir(folder_path):
            full_f = os.path.abspath(os.path.join(folder_path, f))
            if os.path.isfile(full_f) and (f.lower().endswith(".xlsx") or f.lower().endswith(".xls")) and not f.startswith("~$"):
                if full_f != xlsx_path and full_f != csv_path:
                    all_files.append(full_f)

    # Natural sort
    all_files.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', os.path.basename(x))])

    total_files = len(all_files)
    if total_files == 0:
        print(f"No Excel files found in '{folder_path}'.", flush=True)
        return

    print(f"Found {total_files:,} Excel file(s) to merge. Starting extraction...\n", flush=True)

    start_time = time.time()
    collected_results = []
    sample_headers = None
    processed_count = 0
    total_valid_rows = 0

    # If small number of large pre-merged files, use direct worker pool
    workers = min(max_workers, total_files) if total_files > 0 else 1
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_file = {executor.submit(parse_single_file, fp): fp for fp in all_files}

        for future in as_completed(future_to_file):
            processed_count += 1
            try:
                sort_dt, data_rows, headers = future.result()
                if headers and not sample_headers:
                    sample_headers = headers

                if data_rows:
                    collected_results.append((sort_dt, data_rows, future_to_file[future]))
                    total_valid_rows += len(data_rows)
            except Exception as e:
                print(f"  [!] Error reading file: {e}", flush=True)

            if processed_count % 10 == 0 or processed_count == total_files:
                elapsed = time.time() - start_time
                pct = (processed_count / total_files) * 100
                print(
                    f"  [{processed_count:,}/{total_files:,}] ({pct:5.1f}%) "
                    f"| Rows collected: {total_valid_rows:,} "
                    f"| Time: {elapsed:.1f}s",
                    end="\r" if processed_count < total_files else "\n",
                    flush=True
                )

    extraction_time = time.time() - start_time
    print(f"\nExtraction completed in {extraction_time:.2f} seconds!", flush=True)
    print(f"Total valid data rows collected: {total_valid_rows:,}", flush=True)

    if not collected_results:
        print("[!] No data extracted. Please check file format.", flush=True)
        return

    print("\nOrdering dataset...", flush=True)
    # If files are pre-merged reports (e.g. Merged_VFD_Report_1..10), sort by filename natural order
    is_premerged = any("Merged_VFD_Report" in os.path.basename(fpath) for _, _, fpath in collected_results)
    if is_premerged:
        collected_results.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', os.path.basename(x[2]))])
    else:
        collected_results.sort(key=lambda x: x[0] if x[0] else datetime.datetime.min)

    # Flatten rows
    final_rows = []
    for _, rows, _ in collected_results:
        final_rows.extend(rows)

    # Check headers
    if sample_headers:
        if "Report_DateTime" in sample_headers:
            column_names = sample_headers
        else:
            column_names = ["Report_DateTime", "File_DateTime", "Report_ID"] + sample_headers + ["Source_File"]
    else:
        column_names = STANDARD_COLUMNS

    print(f"Total dataset: {len(final_rows):,} rows x {len(column_names)} columns.", flush=True)

    # 1. Save CSV (Universal, handles millions of rows in seconds)
    if save_csv:
        print(f"\nSaving CSV to: {csv_path} ...", flush=True)
        t_csv = time.time()
        df = pd.DataFrame(final_rows, columns=column_names)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        del df
        print(f" [OK] CSV saved in {time.time() - t_csv:.2f}s ({os.path.getsize(csv_path) / (1024*1024):.1f} MB)", flush=True)

    # 2. Save Excel (.xlsx)
    if save_excel:
        print(f"\nSaving Excel (.xlsx) to: {xlsx_path} ...", flush=True)
        t_xlsx = time.time()
        write_excel_fast_streaming(xlsx_path, column_names, final_rows)
        print(f" [OK] Excel saved in {time.time() - t_xlsx:.2f}s ({os.path.getsize(xlsx_path) / (1024*1024):.1f} MB)", flush=True)

    print(f"\n=======================================================", flush=True)
    print(f" [SUCCESS] Merging Complete!")
    print(f" Processed {total_files:,} files -> {len(final_rows):,} rows.")
    print(f" Files created:")
    if save_csv and os.path.exists(csv_path):
        print(f"  - CSV:   {csv_path}")
    if save_excel and os.path.exists(xlsx_path):
        print(f"  - Excel: {xlsx_path}")
    print(f"=======================================================\n", flush=True)


def select_folder_gui() -> Optional[str]:
    """Graphical folder picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="Select Folder with Excel Files to Merge")
        root.destroy()
        return folder if folder else None
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Merge CCED VFD hourly reports into one clean timestamped dataset.")
    parser.add_argument("-f", "--folder", type=str, default=None, help="Input folder path")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output base filename / path")
    parser.add_argument("-r", "--recursive", action="store_true", help="Scan subfolders recursively")
    parser.add_argument("--workers", type=int, default=16, help="Number of parallel threads (default: 16)")
    parser.add_argument("--no-csv", action="store_true", help="Do not save CSV output")
    parser.add_argument("--no-excel", action="store_true", help="Do not save Excel (.xlsx) output")

    args = parser.parse_args()

    folder = args.folder
    if not folder:
        print("Opening folder selection window...", flush=True)
        folder = select_folder_gui()
        if not folder:
            folder = input("Please enter or paste folder path: ").strip().strip('"').strip("'")

    if not folder or not os.path.exists(folder):
        print("Invalid folder. Exiting.", flush=True)
        sys.exit(1)

    has_subfolders = any(os.path.isdir(os.path.join(folder, d)) for d in os.listdir(folder))
    recursive = args.recursive
    if not recursive and has_subfolders:
        direct_files = [f for f in os.listdir(folder) if f.lower().endswith(('.xlsx', '.xls'))]
        if len(direct_files) == 0:
            print("No Excel files in top-level, automatically scanning subfolders...", flush=True)
            recursive = True

    process_folder(
        folder_path=folder,
        output_base=args.output,
        recursive=recursive,
        max_workers=args.workers,
        save_csv=not args.no_csv,
        save_excel=not args.no_excel,
    )


if __name__ == "__main__":
    main()
