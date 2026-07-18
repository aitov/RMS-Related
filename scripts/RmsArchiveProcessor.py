import os
import re
import fcntl
import sys
import shutil
import tarfile
import subprocess
import configparser

# --- CONFIGURATION INITIALIZATION ---
# Get the absolute directory where the script itself is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "archive_processing.ini")

# Enforce secure check for configuration file presence
if not os.path.exists(CONFIG_FILE):
    print(f"Critical Error: Configuration file '{CONFIG_FILE}' not found. Aborting process.")
    sys.exit(1)

# Read the INI configuration profile
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

try:
    SRC_DIR = config.get("PATHS", "source_dir")
    FULL_DIR = config.get("PATHS", "full_dir")
    LOCAL_ARCHIVE_ROOT = config.get("PATHS", "local_archive_root")
    LOCAL_DATA_ROOT = config.get("PATHS", "local_data_root")
    LOCAL_CSV_DIR = config.get("PATHS", "local_csv_dir")
    TIME_CAPSULE_DIR = config.get("PATHS", "time_capsule_dir")
    MAC_MINI_DIR = config.get("PATHS", "mac_mini_dir")

    # Read feature toggle flags from the INI file
    USE_DROPBOX = config.getboolean("PATHS", "use_dropbox")
    USE_TIME_CAPSULE = config.getboolean("PATHS", "use_time_capsule")
    USE_MAC_MINI = config.getboolean("PATHS", "use_mac_mini")

    MAC_MINI_IP = config.get("NETWORK", "mac_mini_ip")
    DROPBOX_REMOTE_FOLDER = config.get("DROPBOX", "remote_folder")
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"Critical Error parsing configuration parameters: {e}")
    sys.exit(1)

LOCK_FILE = "/tmp/rms_manager.lock"

def is_mac_mini_online():
    """Network ping check for Mac Mini availability"""
    if not USE_MAC_MINI:
        return False
    try:
        subprocess.run(["ping", "-c", "1", "-W", "2", MAC_MINI_IP],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def parse_archive_name(filename):
    """Parses standard naming: UA0003_20260717_184607_759092_processed_detected.tar"""
    match = re.match(r"^(UA\d+)_(\d{4})(\d{2})\d+_", filename)
    if match:
        return match.group(1), match.group(2), match.group(3) # cam_name, year, month
    return None

def upload_to_dropbox(local_csv_path):
    """Uploads CSV files to Dropbox using the layout from the INI file"""
    if not USE_DROPBOX or not os.path.exists(local_csv_path):
        return False
    try:
        remote_path = os.path.join(DROPBOX_REMOTE_FOLDER, os.path.basename(local_csv_path))
        print(f"Dropbox: Uploading {os.path.basename(local_csv_path)} -> {remote_path}")
        subprocess.run(["dbxcli", "put", local_csv_path, remote_path], check=True)
        return True
    except Exception as e:
        print(f"Dropbox upload failed for {local_csv_path}: {e}")
        return False

def sync_directory(src, dest):
    """Copies directories recursively acting like a simplified rsync/cp -r"""
    try:
        if os.path.exists(dest):
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dest, item)
                if os.path.isdir(s):
                    sync_directory(s, d)
                else:
                    shutil.copy2(s, d)
        else:
            shutil.copytree(src, dest)
        return True
    except Exception as e:
        print(f"Failed to sync directory from {src} to {dest}: {e}")
        return False

def main():
    # --- CRON OVERLAP PROTECTION ---
    lock_f = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Previous manager instance is still running. Exiting.")
        sys.exit(0)

    # Active configuration status display
    tc_online = os.path.exists(TIME_CAPSULE_DIR) if USE_TIME_CAPSULE else False
    mac_online = is_mac_mini_online() if USE_MAC_MINI else False

    print("--- Active Configuration Modules ---")
    print(f"Dropbox Integration:  {'ENABLED' if USE_DROPBOX else 'DISABLED'}")
    print(f"Time Capsule Vault:   {'ENABLED (Online)' if tc_online else 'ENABLED (Offline)' if USE_TIME_CAPSULE else 'DISABLED'}")
    print(f"Mac Mini Storage:     {'ENABLED (Online)' if mac_online else 'ENABLED (Offline)' if USE_MAC_MINI else 'DISABLED'}")
    print("------------------------------------")

    os.makedirs(LOCAL_CSV_DIR, exist_ok=True)

    # Scan the root of uploads directory
    for filename in os.listdir(SRC_DIR):
        if not filename.endswith("_processed_detected.tar.bz2") or filename.endswith(".part"):
            continue

        local_file_path = os.path.join(SRC_DIR, filename)
        parsed_data = parse_archive_name(filename)

        if not parsed_data:
            print(f"Skipping unknown format file: {filename}")
            continue

        cam_name, year, month = parsed_data
        relative_target_path = os.path.join(year, month, cam_name)

        # Exact local destination for unpacked data
        final_local_unpacked_dir = os.path.join(LOCAL_DATA_ROOT, relative_target_path)
        os.makedirs(final_local_unpacked_dir, exist_ok=True)

        print(f"\nProcessing archive: {filename}")

        # --- 1. LOCAL UNPACKING (FIRST TASK) ---
        if os.path.exists(final_local_unpacked_dir) and os.listdir(final_local_unpacked_dir):
            print(f"Directory {final_local_unpacked_dir} already exists and is not empty. Skipping extraction.")
            extraction_success = True
        else:
            print(f"Extracting results to local HDD: {final_local_unpacked_dir}")
            try:
                with tarfile.open(local_file_path, "r:bz2") as tar:
                    tar.extractall(path=final_local_unpacked_dir)
                extraction_success = True
            except Exception as e:
                print(f"Extraction failed for {filename}: {e}")
                extraction_success = False
                continue

        # --- 2. FAN-OUT SYNC FOR CSV AND UNPACKED DATA ---
        sync_to_tc_done = False
        sync_to_mac_done = False

        if extraction_success:
            # Scan for CSV files inside the freshly extracted folder
            for root, dirs, files in os.walk(final_local_unpacked_dir):
                for file in files:
                    if file.lower().endswith(".csv"):
                        csv_src_path = os.path.join(root, file)

                        # Always replicate CSV locally to the 4TB disk
                        shutil.copy2(csv_src_path, os.path.join(LOCAL_CSV_DIR, file))

                        # Replicate CSV to Dropbox Cloud (if enabled)
                        if USE_DROPBOX:
                            upload_to_dropbox(csv_src_path)

                        # Replicate CSV to Time Capsule (if enabled and online)
                        if USE_TIME_CAPSULE and tc_online:
                            tc_csv_dir = os.path.join(TIME_CAPSULE_DIR, "pi/CSV/Meteors.ua/Alex_Aitov")
                            os.makedirs(tc_csv_dir, exist_ok=True)
                            shutil.copy2(csv_src_path, os.path.join(tc_csv_dir, file))

                        # Replicate CSV to Mac Mini (if enabled and online)
                        if USE_MAC_MINI and mac_online:
                            mac_csv_dir = os.path.join(MAC_MINI_DIR, "pi/CSV/Meteors.ua/Alex_Aitov")
                            os.makedirs(mac_csv_dir, exist_ok=True)
                            shutil.copy2(csv_src_path, os.path.join(mac_csv_dir, file))

            # 3. Replicate the whole unpacked directory to network nodes
            if USE_TIME_CAPSULE and tc_online:
                tc_data_dir = os.path.join(TIME_CAPSULE_DIR, "pi/data", relative_target_path)
                print(f"Syncing unpacked data to Time Capsule...")
                sync_to_tc_done = sync_directory(final_local_unpacked_dir, tc_data_dir)
            else:
                # If module is disabled, consider sync complete to allow local file relocation
                sync_to_tc_done = True

            if USE_MAC_MINI:
                if mac_online:
                    mac_data_dir = os.path.join(MAC_MINI_DIR, "pi/data", relative_target_path)
                    print(f"Syncing unpacked data to Mac Mini...")
                    sync_to_mac_done = sync_directory(final_local_unpacked_dir, mac_data_dir)
                else:
                    print("Mac Mini is offline. Postponing data folder sync.")
                    sync_to_mac_done = False
            else:
                # If module is disabled, consider sync complete to allow local file relocation
                sync_to_mac_done = True

        # --- 4. SECOND TASK LOGIC: ARCHIVE RELOCATION & CLEANUP ---
        # If external syncing targets are disabled or successful, run local folder consolidation
        if sync_to_tc_done and (sync_to_mac_done or not mac_online):
            if sync_to_tc_done and (sync_to_mac_done or not USE_MAC_MINI):
                final_archive_dir = os.path.join(LOCAL_ARCHIVE_ROOT, relative_target_path)
                os.makedirs(final_archive_dir, exist_ok=True)

                print("Verifications aligned. Relocating original bz2/tar archives internally...")
                shutil.move(local_file_path, os.path.join(final_archive_dir, filename))

                # Move raw full data archive from 'full' directory if present
                full_filename = filename.replace("_processed_detected.tar", "_full_detected.tar")
                local_full_path = os.path.join(FULL_DIR, full_filename)

                if os.path.exists(local_full_path):
                    print(f"Matching raw archive spotted: {full_filename}. Relocating to {final_archive_dir}...")
                    try:
                        shutil.move(local_full_path, os.path.join(final_archive_dir, full_filename))
                    except Exception as e:
                        print(f"Failed to move raw archive file {full_filename}: {e}")
            else:
                print("Keeping archives in root uploads folder until Mac Mini host comes online.")

    fcntl.flock(lock_f, fcntl.LOCK_UN)

if __name__ == "__main__":
    main()
