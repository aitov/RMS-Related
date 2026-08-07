import os
import re
import sys
from datetime import datetime

def parse_filename(filename):
    """
    Parses both standard and manual filenames.
    Matches starting with camera and 8-digit date: e.g., UA0006_20260731_... or UA0003_20260621_..._manual.csv
    """
    pattern = r"^([A-Z0-9]+)_(\d{4})(\d{2})(\d{2})_.*\.csv$"
    match = re.match(pattern, filename)
    if match:
        camera, year, month, day = match.groups()
        return {
            "camera": camera,
            "year": year,
            "month": month,
            "day": day,
            "date_str": f"{year}{month}{day}"
        }
    return None

def clean_line(line):
    """Removes spaces, whitespaces, and newlines for strict raw string comparison"""
    return "".join(line.split())

def verify_daily_data_in_monthly(daily_path, monthly_path):
    """
    Verifies if all data rows from the daily file exist in the aggregated monthly file.
    Skips the header row of the daily file during verification.
    """
    if not os.path.exists(monthly_path):
        return False, "Monthly file does not exist"

    try:
        with open(monthly_path, 'r', encoding='utf-8', errors='ignore') as f:
            monthly_set = {clean_line(line) for line in f if line.strip()}

        with open(daily_path, 'r', encoding='utf-8', errors='ignore') as f:
            daily_lines = f.readlines()

        if not daily_lines:
            return True, "Daily file is empty"

        data_lines = daily_lines[1:]
        if not data_lines:
            return True, "Daily file contains only header"

        missing_count = 0
        for line in data_lines:
            if not line.strip():
                continue
            cleaned = clean_line(line)
            if cleaned not in monthly_set:
                missing_count += 1

        if missing_count > 0:
            return False, f"Missing {missing_count} data rows inside the monthly archive"

        return True, "All rows verified"

    except Exception as e:
        return False, f"Error processing files: {e}"

def fix_and_append_data(daily_path, monthly_path):
    """Integrates the provided aggregation script logic to restore missing data"""
    try:
        with open(daily_path, 'r', encoding='utf-8', errors='ignore') as f:
            daily_lines = f.readlines()

        if not daily_lines:
            return

        header_line = daily_lines[0]  # The very first row containing column names
        data_lines = daily_lines[1:]  # All remaining rows containing meteor data

        os.makedirs(os.path.dirname(monthly_path), exist_ok=True)

        if os.path.exists(monthly_path):
            with open(monthly_path, "r", encoding="utf-8", errors='ignore') as mf:
                existing_lines = mf.readlines()
            existing_set = set(line.strip() for line in existing_lines)

            with open(monthly_path, "a", encoding="utf-8") as mf:
                for line in data_lines:
                    if line.strip() and line.strip() not in existing_set:
                        mf.write(line)
            print(f"[CSV Local] Data appended to monthly report: {monthly_path}")
        else:
            with open(monthly_path, "w", encoding="utf-8") as mf:
                mf.write(header_line)     # Write the single header line
                mf.writelines(data_lines) # Write the data lines
            print(f"[CSV Local] Created new monolithic monthly report: {monthly_path}")

    except Exception as e:
        print(f"[ERROR] Failed to fix data for {os.path.basename(daily_path)}: {e}")


def run_reconciliation(year_dir):
    if not os.path.exists(year_dir):
        print(f"[ERROR] Directory {year_dir} does not exist!")
        sys.exit(1)

    now = datetime.now()
    current_month_str = f"{now.month:02d}"
    current_year_str = str(now.year)

    daily_files = []
    unparsed_files = []

    # 1. Scan absolutely ALL CSV files in the directory
    for item in os.listdir(year_dir):
        item_path = os.path.join(year_dir, item)
        if os.path.isfile(item_path) and item.endswith('.csv'):
            parsed = parse_filename(item)
            if parsed:
                # Protect current month files from reconciliation and deletion
                if parsed['year'] == current_year_str and parsed['month'] == current_month_str:
                    continue

                monthly_file_name = f"{parsed['year']}_{parsed['month']}_{parsed['camera']}.csv"
                monthly_path = os.path.join(year_dir, "monthly", parsed['month'], monthly_file_name)

                daily_files.append({
                    "filename": item,
                    "path": item_path,
                    "monthly_path": monthly_path,
                    "info": parsed
                })
            else:
                # Track unparsed files separately to ignore them during deletion
                unparsed_files.append({
                    "filename": item,
                    "path": item_path
                })

    if not daily_files and not unparsed_files:
        print("[INFO] No historical daily CSV files found for reconciliation.")
        return [], [], []

    missing_in_monthly = []
    ready_for_deletion = []

    # 2. Reconcile valid daily files row-by-line
    if daily_files:
        print("[PROCESSING] Running row-level data reconciliation...")
        for file_data in daily_files:
            is_synced, message = verify_daily_data_in_monthly(file_data["path"], file_data["monthly_path"])
            if is_synced:
                ready_for_deletion.append(file_data)
            else:
                file_data["error_message"] = message
                missing_in_monthly.append(file_data)

    # 3. Print report
    print("\n" + "="*60)
    print("DATA RECONCILIATION REPORT")
    print("="*60)
    print(f"Total historical daily files found: {len(daily_files) + len(unparsed_files)}")
    print(f"✅ Verified & Ready for deletion:   {len(ready_for_deletion)}")
    print(f"❌ Discrepancies / Missing data:     {len(missing_in_monthly)}")
    print(f"⚠️ Unrecognized files (Skipped):     {len(unparsed_files)}")
    print("="*60)

    if unparsed_files:
        print("\n[INFO] The following files have unknown names and will be LEFT IN THE FOLDER:")
        for f in unparsed_files:
            print(f" - {f['filename']}")

    if missing_in_monthly:
        print("\n[WARNING] The following files are NOT fully archived in monthly logs:")
        for f in missing_in_monthly:
            print(f" - {f['filename']} ({f['error_message']})")

    return ready_for_deletion, missing_in_monthly, unparsed_files

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Please provide the target directory path as an argument.")
        print("Usage: python3 script.py /path/to/your/storage/2026")
        sys.exit(1)

    target_year_dir = sys.argv[1]

    while True:
        ready_for_deletion, missing_in_monthly, unparsed_files = run_reconciliation(target_year_dir)

        if missing_in_monthly:
            print("\nAvailable Actions:")
            print("1. Fix and append missing data automatically")
            print("2. Exit script without deleting anything")
            choice = input("Select an option (1 or 2): ").strip()

            if choice == '1':
                print("\n[PROCESSING] Appending missing rows to monthly files...")
                for f in missing_in_monthly:
                    fix_and_append_data(f["path"], f["monthly_path"])
                print("\n[INFO] Data fix complete. Restarting verification...")
                continue
            else:
                print("[INFO] Script finished. No files were deleted.")
                break

        if ready_for_deletion:
            print(f"\n[SUCCESS] All scanned historical data matches perfectly inside monthly CSV files.")
            print(f"[INFO] Total files slated for deletion: {len(ready_for_deletion)}")
            if unparsed_files:
                print(f"[INFO] Reminder: {len(unparsed_files)} unrecognized files will NOT be touched.")

            confirm = input("Type 'yes' to CONFIRM DELETION or any other key to abort: ").strip().lower()
            if confirm == 'yes':
                print("\n[PROCESSING] Deleting verified daily files...")
                deleted_count = 0
                for f in ready_for_deletion:
                    try:
                        os.remove(f["path"])
                        deleted_count += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to delete {f['filename']}: {e}")
                print(f"[SUCCESS] Successfully cleaned up {deleted_count} files.")
            else:
                print("[INFO] Deletion cancelled by user.")
            break
        else:
            break

if __name__ == "__main__":
    main()
