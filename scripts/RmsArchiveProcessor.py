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

    USE_DROPBOX = config.getboolean("DROPBOX", "use_dropbox")
    USE_TIME_CAPSULE = config.getboolean("TIME_CAPSULE", "use_time_capsule")
    USE_MAC = config.getboolean("MAC", "use_mac")

    MAC_IP = config.get("MAC", "mac_ip")
    TC_IP = config.get("TIME_CAPSULE", "tc_ip")
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"Critical Error parsing configuration parameters: {e}")
    sys.exit(1)

LOCK_FILE = "/tmp/rms_manager.lock"

def is_mac_online():
    """Network ping check for Mac Mini availability"""
    if not USE_MAC:
        return False
    try:
        subprocess.run(["ping", "-c", "1", "-W", "2", MAC_IP],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def is_tc_online():
    """Network ping check for Mac Mini availability"""
    if not USE_TIME_CAPSULE:
        return False
    try:
        subprocess.run(["ping", "-c", "1", "-W", "2", TC_IP],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def parse_archive_name(filename):
    """Parses standard naming: UA0003_20260717_184607_759092_processed_detected.tar"""
    match = re.match(r"^(UA\w+)_(\d{4})(\d{2})\d+_", filename)
    if match:
        return match.group(1), match.group(2), match.group(3) # cam_name, year, month
    return None

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

def copy_meteor_stack(unpacked_day_dir, base_camera_dir):
    """
    Finds a meteor stack image (_meteors.png/jpg) inside the 'meteors' folder
    of the freshly unpacked day and copies it to the camera's central 'stacks' directory.
    """
    meteors_folder = os.path.join(unpacked_day_dir, "meteors")
    if not os.path.exists(meteors_folder) or not os.path.isdir(meteors_folder):
        print("No 'meteors' subdirectory found in the extracted results. Skipping stack copy.")
        return

    # Create the central 'stacks' folder on the upper camera level
    stacks_target_dir = os.path.join(base_camera_dir, "stacks")

    # Look for files ending with _meteors.png or _meteors.jpg inside the meteors folder
    stack_file = None
    try:
        for file in os.listdir(meteors_folder):
            if file.lower().endswith("_meteors.png") or file.lower().endswith("_meteors.jpg"):
                stack_file = file
                break  # We only need the first matching stack file (0 or 1 expected)
    except Exception as e:
        print(f"Failed to scan meteors folder: {e}")
        return

    if stack_file:
        src_stack_path = os.path.join(meteors_folder, stack_file)
        dst_stack_path = os.path.join(stacks_target_dir, stack_file)

        if not os.path.exists(dst_stack_path):
            try:
                os.makedirs(stacks_target_dir, exist_ok=True)
                print(f"Stacks: Copying stack index file -> {stack_file}")
                shutil.copy2(src_stack_path, dst_stack_path)
            except Exception as e:
                print(f"Failed to copy stack file to {stacks_target_dir}: {e}")
        else:
            print(f"Stacks: File {stack_file} already exists in central stacks directory. Skipping.")
        return dst_stack_path
    return None


def process_and_backup_csv(folder_name, final_local_unpacked_dir, local_csv_dir):
    """
    Processes daily RMS CSV files, manages a local deduplicated monthly archive,
    and optionally distributes backups to network shares and Dropbox.
    """
    # 1. Parse station metadata and dates from the folder name (e.g., UA0001_20260718_...)
    try:
        station_name = folder_name[0:6]
        year = folder_name[7:11]
        month = folder_name[11:13]
    except IndexError:
        print(f"[CSV] Error: Invalid folder name format: {folder_name}")
        return None

    # Define path directly inside the unpacked day directory
    csv_file_path = os.path.join(final_local_unpacked_dir, "rms", f"{folder_name}.csv")

    # Verify source file existence
    if not os.path.exists(csv_file_path):
        print(f"[CSV] Source file not found: {csv_file_path}")
        return None

    # Skip empty or header-only files (less than 100 bytes)
    if os.path.getsize(csv_file_path) < 100:
        print(f"[CSV] File is empty or header-only, skipping: {csv_file_path}")
        return None

    # Read the content of the daily file for deduplicated merging
    try:
        with open(csv_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except IOError as e:
        print(f"[CSV] Error reading source file {csv_file_path}: {e}")
        return None

    if not lines:
        return None

    header = lines[0]
    data_lines = lines[1:]

    # -------------------------------------------------------------------------
    # STEP 0: MANDATORY LOCAL BACKUP & MONOLITHIC MERGE
    # -------------------------------------------------------------------------
    local_monthly_file_path = None
    try:
        # Create local target structure: LOCAL_CSV_DIR/2026/monthly/07
        local_year_dir = os.path.join(local_csv_dir, year)
        local_monthly_dir = os.path.join(local_year_dir, "monthly", month)
        os.makedirs(local_monthly_dir, exist_ok=True)

        # Copy the raw daily CSV file locally
        local_day_csv = os.path.join(local_year_dir, f"{folder_name}.csv")
        if not os.path.exists(local_day_csv):
            shutil.copy2(csv_file_path, local_day_csv)
            print(f"[CSV Local] Successfully backed up daily file: {local_day_csv}")
        else:
            print(f"[CSV Local] Daily file already exists: {local_day_csv}. Merging data anyway.")

        # Smart merge into local monthly report
        local_monthly_file_path = os.path.join(local_monthly_dir, f"{year}_{month}_{station_name}.csv")

        if os.path.exists(local_monthly_file_path):
            with open(local_monthly_file_path, "r", encoding="utf-8") as mf:
                existing_lines = mf.readlines()
            existing_set = set(line.strip() for line in existing_lines)

            with open(local_monthly_file_path, "a", encoding="utf-8") as mf:
                for line in data_lines:
                    if line.strip() not in existing_set:
                        mf.write(line)
            print(f"[CSV Local] Data appended to monthly report: {local_monthly_file_path}")
        else:
            with open(local_monthly_file_path, "w", encoding="utf-8") as mf:
                mf.write(header)
                mf.writelines(data_lines)
            print(f"[CSV Local] Created new monolithic monthly report: {local_monthly_file_path}")

    except Exception as e:
        print(f"[CSV Local] Critical error during local processing: {e}")
        return None
    return csv_file_path

def backup_to_time_capsule(folder_name, local_unpacked_dir, local_stack_file, local_day_csv, local_monthly_csv, config):
    """
    Synchronizes processed day results (unpacked folder, meteor stack, and monthly CSV)
    directly to Apple Time Capsule via smbclient using historical golden source data.
    """
    if not USE_TIME_CAPSULE:
        return True

    # 1. Parse configuration parameters
    tc_ip = config.get('TIME_CAPSULE', 'tc_ip')
    tc_share = config.get('TIME_CAPSULE', 'tc_share')
    tc_user = config.get('TIME_CAPSULE', 'tc_user')
    tc_password = config.get('TIME_CAPSULE', 'tc_password')

    data_prefix = config.get('TIME_CAPSULE', 'tc_data_prefix').strip('/')
    csv_prefix = config.get('TIME_CAPSULE', 'tc_csv_prefix').strip('/')

    try:
        station_name = folder_name[0:6]
        year = folder_name[7:11]
        month = folder_name[11:13]
    except IndexError:
        print(f"[Time Capsule] Error: Malformed folder name structure: {folder_name}")
        return False

    print(f"[Time Capsule] Initializing configuration-driven sync for: {folder_name}")

    # Build base execution array with strict compatibility flags
    smb_base_cmd = [
        "smbclient", f"//{tc_ip}/{tc_share}",
        "-U", f"{tc_user}%{tc_password}",
        "--option=client min protocol=NT1",
        "--option=client use spnego=no",
        "--option=client ntlmv2 auth=no"
    ]

    # Resolve target deep layouts
    remote_day_dir = f"{data_prefix}/{year}/{month}/{station_name}/{folder_name}"
    stacks_dir = f"{data_prefix}/{year}/{month}/{station_name}/stacks"
    remote_monthly_csv_dir = f"{csv_prefix}/{year}/monthly/{month}"
    remote_day_csv_dir = f"{csv_prefix}/{year}"

    # Helper inline logic to convert a nested path like "a/b/c" into a safe sequence of "mkdir a; mkdir a/b; mkdir a/b/c"
    def generate_sequential_mkdir(target_path):
        parts = [p for p in target_path.split('/') if p]
        commands = []
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else part
            commands.append(f"mkdir {current}")
        return "; ".join(commands)

    try:
        # Step A: Generate and enforce full deep path baseline infrastructure
        mkdir_sequence = (
            f"{generate_sequential_mkdir(remote_day_dir)}; "
            f"{generate_sequential_mkdir(stacks_dir)}; "
            f"{generate_sequential_mkdir(remote_monthly_csv_dir)}; "
            f"{generate_sequential_mkdir(remote_day_csv_dir)}"
        )
        subprocess.run(smb_base_cmd + ["-c", mkdir_sequence], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Step B: Mirror the entire Unpacked Day Folder content recursively from Golden Source
        for root, _, files in os.walk(local_unpacked_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_file_path, local_unpacked_dir).replace(os.sep, '/')
                remote_file_target = f"{remote_day_dir}/{rel_path}"

                if "/" in rel_path:
                    sub_dir_rel = rel_path.rpartition('/')[0]
                    sub_dir_full = f"{remote_day_dir}/{sub_dir_rel}"
                    subprocess.run(smb_base_cmd + ["-c", generate_sequential_mkdir(sub_dir_full)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                upload_file_cmd = smb_base_cmd + ["-c", f"put {local_file_path} {remote_file_target}"]
                subprocess.run(upload_file_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        print(f"[Time Capsule] Success: Raw data folder deployed to: {remote_day_dir}")

        # Step C: Upload Meteor Stack Image into central stacks directory
        if local_stack_file and os.path.exists(local_stack_file):
            stack_name = os.path.basename(local_stack_file)
            upload_stack_cmd = smb_base_cmd + ["-c", f"put {local_stack_file} {stacks_dir}/{stack_name}"]
            subprocess.run(upload_stack_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print(f"[Time Capsule] Success: Central meteor stack image mirrored to: {stacks_dir}/{stack_name}")

        # Step D: Upload the Monolithic Monthly CSV Report (Overwrites with latest state)
        if local_monthly_csv and os.path.exists(local_monthly_csv):
            csv_name = os.path.basename(local_monthly_csv)
            upload_csv_cmd = smb_base_cmd + ["-c", f"put {local_monthly_csv} {remote_monthly_csv_dir}/{csv_name}"]
            subprocess.run(upload_csv_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print(f"[Time Capsule] Success: Aggregated monthly CSV report updated in: {remote_monthly_csv_dir}/{csv_name}")
        # Copy day csv
        if local_day_csv and os.path.exists(local_day_csv):
            csv_name = os.path.basename(local_day_csv)
            upload_csv_cmd = smb_base_cmd + ["-c", f"put {local_day_csv} {remote_day_csv_dir}/{csv_name}"]
            subprocess.run(upload_csv_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print(f"[Time Capsule] Success: Day csv updated in: {remote_day_csv_dir}/{csv_name}")

    except subprocess.CalledProcessError as e:
        print(f"[Time Capsule] Transmission pipeline aborted. Remote diagnostic: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"[Time Capsule] Unexpected architecture fault within sync block: {e}")
        return False
    return True

def backup_to_dropbox(folder_name, local_day_csv, local_monthly_csv, config):
    """
    Deploys verified daily and aggregated monthly CSV reports directly to Dropbox Cloud
    using the Go-based dbxcli CLI tool from the server's user space environment.
    """
    if not USE_DROPBOX:
        return True

    # 1. Parse structural and security parameters from the INI file
    csv_prefix = config.get('DROPBOX', 'dbx_csv_prefix').strip('/')
    access_token = config.get('DROPBOX', 'dbx_access_token').strip()

    if not access_token:
        print("[Dropbox] Error: Missing dynamic 'dbx_access_token' inside configuration profile.")
        return False

    try:
        year = folder_name[7:11]
        month = folder_name[11:13]
    except IndexError:
        print(f"[Dropbox] Error: Malformed folder name structure: {folder_name}")
        return False

    print(f"[Dropbox] Initializing environment-driven cloud sync sequence for: {folder_name}")

    # Inject the token safely into the subprocess execution environment dictionary
    custom_env = os.environ.copy()
    custom_env["DBXCLI_ACCESS_TOKEN"] = access_token

    # Resolve target deep layouts inside Dropbox (forward slashes are native here)
    remote_day_dir = f"/{csv_prefix}/{year}"
    remote_monthly_dir = f"/{csv_prefix}/{year}/monthly/{month}"

    # Step A: Sync Daily Raw CSV File
    if local_day_csv and os.path.exists(local_day_csv):
        day_csv_name = os.path.basename(local_day_csv)
        remote_day_target = f"{remote_day_dir}/{day_csv_name}"

        # dbxcli put syntax: dbxcli put <local_path> <remote_path>
        cmd_day = ["dbxcli", "put", local_day_csv, remote_day_target]
        try:
            # Passing custom_env securely bypasses files authorization completely
            subprocess.run(cmd_day, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, env=custom_env)
            print(f"[Dropbox] Success: Daily log transmitted -> {remote_day_target}")
        except subprocess.CalledProcessError as e:
            print(f"[Dropbox] Daily file deployment rejected. API return log: {e.stderr.strip()}")
            return False
        except Exception as e:
            print(f"[Dropbox] Unexpected error during daily upload: {e}")
            return False

    # Step B: Sync Monolithic Monthly CSV Report (Overwrites cloud state with latest golden source data)
    if local_monthly_csv and os.path.exists(local_monthly_csv):
        monthly_csv_name = os.path.basename(local_monthly_csv)
        remote_monthly_target = f"{remote_monthly_dir}/{monthly_csv_name}"

        cmd_monthly = ["dbxcli", "put", local_monthly_csv, remote_monthly_target]
        try:
            subprocess.run(cmd_monthly, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, env=custom_env)
            print(f"[Dropbox] Success: Monolithic monthly report updated -> {remote_monthly_target}")
        except subprocess.CalledProcessError as e:
            print(f"[Dropbox] Monthly archive refresh rejected. API return log: {e.stderr.strip()}")
            return False
        except Exception as e:
            print(f"[Dropbox] Unexpected error during monthly upload: {e}")
            return False
    return True

def backup_to_mac(folder_name, local_unpacked_dir, local_stack_file, config):
    """
    Synchronizes processed day results (unpacked folder, meteor stack)
    directly to Mac mini internal storage via modern smbclient protocol context.
    """
    if not USE_MAC:
        return True

    # 1. Parse operational credentials
    mac_ip = config.get('MAC', 'mac_ip')
    mac_share = config.get('MAC', 'mac_share')
    mac_user = config.get('MAC', 'mac_user')
    mac_password = config.get('MAC', 'mac_password')

    try:
        station_name = folder_name[0:6]
        year = folder_name[7:11]
        month = folder_name[11:13]
    except IndexError:
        print(f"[Mac] Error: Malformed folder name structure: {folder_name}")
        return False

    print(f"[Mac] Initializing transmission sync pipeline for: {folder_name}")

    # Base modern smbclient array (No legacy flags required for macOS SMB v2/v3)
    smb_base_cmd = [
        "smbclient", f"//{mac_ip}/{mac_share}",
        "-U", f"{mac_user}%{mac_password}"
    ]

    # Resolve target paths using forward slashes
    remote_day_dir = f"{year}/{month}/{station_name}/{folder_name}"
    remote_camera_stacks_dir = f"/{year}/{month}/{station_name}/stacks"

    # Isolated folder creator using native Windows/Samba backslashes for macOS compatibility
    def safe_remote_mkdir(target_path):
        parts = [p for p in target_path.split('/') if p]
        current = ""
        for part in parts:
            current = f"{current}\\{part}" if current else part
            # Execute mkdir with explicitly escaped backslashes
            cmd = smb_base_cmd + ["-c", f"mkdir \"{current}\""]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        # Step A: Enforce deep path baseline setup on Mac mini
        safe_remote_mkdir(remote_day_dir)
        safe_remote_mkdir(remote_camera_stacks_dir)

        # Step B: Mirror the entire Unpacked Day Folder content recursively from Golden Source
        for root, _, files in os.walk(local_unpacked_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_file_path, local_unpacked_dir).replace(os.sep, '/')
                remote_file_target = f"{remote_day_dir}/{rel_path}"

                if "/" in rel_path:
                    sub_dir_rel = rel_path.rpartition('/')[0]
                    sub_dir_full = f"{remote_day_dir}/{sub_dir_rel}"
                    subprocess.run(smb_base_cmd + ["-c", safe_remote_mkdir(sub_dir_full)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                upload_file_cmd = smb_base_cmd + ["-c", f"put {local_file_path} {remote_file_target}"]
                subprocess.run(upload_file_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        print(f"[Mac] Success: Raw data folder deployed to: {remote_day_dir}")

        if local_stack_file and os.path.exists(local_stack_file):
            stack_name = os.path.basename(local_stack_file)
            upload_stack_cmd = smb_base_cmd + ["-c", f"put {local_stack_file} {remote_camera_stacks_dir}/{stack_name}"]
            subprocess.run(upload_stack_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print(f"[Mac] Success: Central meteor stack image mirrored to: {remote_camera_stacks_dir}/{stack_name}")

    except Exception as e:
        print(f"[Mac] Unexpected architecture fault within backup sync block: {e}")
        return False
    return True


def main():
    # --- CRON OVERLAP PROTECTION ---
    lock_f = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Previous manager instance is still running. Exiting.")
        sys.exit(0)

    # Active configuration status display
    tc_online = is_tc_online() if USE_TIME_CAPSULE else False
    mac_online = is_mac_online() if USE_MAC else False

    print("--- Active Configuration Modules ---")
    print(f"Dropbox Integration:  {'ENABLED' if USE_DROPBOX else 'DISABLED'}")
    print(f"Time Capsule Vault:   {'ENABLED (Online)' if tc_online else 'ENABLED (Offline)' if USE_TIME_CAPSULE else 'DISABLED'}")
    print(f"Mac Mini Storage:     {'ENABLED (Online)' if mac_online else 'ENABLED (Offline)' if USE_MAC else 'DISABLED'}")
    print("------------------------------------")

    os.makedirs(LOCAL_CSV_DIR, exist_ok=True)

    # Scan the root of uploads directory
    for filename in os.listdir(SRC_DIR):
        if filename.startswith("."):
            continue

        if not filename.endswith("_processed_detected.tar.bz2") or filename.endswith(".part"):
            continue

        local_file_path = os.path.join(SRC_DIR, filename)
        parsed_data = parse_archive_name(filename)

        if not parsed_data:
            print(f"Skipping unknown format file: {filename}")
            continue

        cam_name, year, month = parsed_data
        relative_target_path = os.path.join(year, month, cam_name)

        # : pi/data/2026/07/UA000A
        base_camera_dir = os.path.join(LOCAL_DATA_ROOT, relative_target_path)

        # Extract from  UA000A_20260716_184742_250666_processed_detected.tar.bz2
        # folder name UA000A_20260716_184742_250666
        folder_name_only = filename.replace("_processed_detected.tar.bz2", "")

        # Final unpacked directory path: pi/data/2026/07/UA000A/UA000A_20260716_184742_250666
        final_local_unpacked_dir = os.path.join(base_camera_dir, folder_name_only)

        print(f"\nProcessing archive: {filename}")

        # check if already unpacked for this specific day
        if os.path.exists(final_local_unpacked_dir) and os.listdir(final_local_unpacked_dir):
            print(f"Directory for this specific day '{final_local_unpacked_dir}' already exists and is not empty. Skipping extraction.")
            extraction_success = True
        else:
            print(f"Creating day directory and extracting results to: {final_local_unpacked_dir}")
            os.makedirs(final_local_unpacked_dir, exist_ok=True)
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
        sync_to_dropbox_done = False

        if extraction_success:
            print("Enforcing group write permissions (775/664) for extracted files...")
            try:
                # Change permissions of the unpacked directory itself
                os.chmod(final_local_unpacked_dir, 0o775)

                # Change permissions recursively for all subdirectories and files
                for root, dirs, files in os.walk(final_local_unpacked_dir):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o775)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o664)
            except Exception as e:
                print(f"Warning: Failed to enforce permissions: {e}")

            golden_stack_file = copy_meteor_stack(final_local_unpacked_dir, base_camera_dir)

            # 2. Process and backup CSV files (Replaces the old commented block)
            # Extract the raw folder name (e.g., "UA0001_20260718_123456") from the full path
            extracted_folder_name = os.path.basename(os.path.normpath(final_local_unpacked_dir))

            # Call the upgraded function including LOCAL_CSV_DIR
            golden_day_csv = process_and_backup_csv(
                folder_name=extracted_folder_name,
                final_local_unpacked_dir=final_local_unpacked_dir, # Passed directly
                local_csv_dir=LOCAL_CSV_DIR
            )

            # 1. Capture the exact output path of your local golden sources
            golden_unpacked_dir = final_local_unpacked_dir

            # Compile path to the verified deduplicated local monthly CSV
            golden_monthly_csv = os.path.join(LOCAL_CSV_DIR, year, "monthly", month, f"{year}_{month}_{cam_name}.csv")

            # 2. Fire the Time Capsule backup engine sequence
            if USE_TIME_CAPSULE:
                if tc_online:
                    sync_to_tc_done = backup_to_time_capsule(
                        folder_name=extracted_folder_name,
                        local_unpacked_dir=golden_unpacked_dir,
                        local_stack_file=golden_stack_file,
                        local_day_csv=golden_day_csv,
                        local_monthly_csv=golden_monthly_csv,
                        config=config  # Pass the parsed configparser object down
                    )
                else:
                    print("Time Capsule is offline. Postponing data folder sync.")
                    sync_to_tc_done = False
            else:
                sync_to_tc_done = True

            if USE_DROPBOX:
                # 4. Fire the Dropbox upload engine sequence
                sync_to_dropbox_done = backup_to_dropbox(
                    folder_name=extracted_folder_name,
                    local_day_csv=golden_day_csv,
                    local_monthly_csv=golden_monthly_csv,
                    config=config
                )
            else:
                sync_to_dropbox_done = True

            if USE_MAC:
                if mac_online:
                    sync_to_mac_done = backup_to_mac(
                        folder_name=extracted_folder_name,
                        local_unpacked_dir=golden_unpacked_dir,
                        local_stack_file=golden_stack_file,
                        config=config
                    )
                else:
                    print("Mac is offline. Postponing data folder sync.")
                    sync_to_mac_done = False
            else:
                # If module is disabled, consider sync complete to allow local file relocation
                sync_to_mac_done = True

        # --- 4. SECOND TASK LOGIC: ARCHIVE RELOCATION & CLEANUP ---
        # If external syncing targets are disabled or successful, run local folder consolidation
        if sync_to_tc_done and sync_to_mac_done and sync_to_dropbox_done:
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
            print("Keeping archives in root uploads folder until all drives comes synced.")

    fcntl.flock(lock_f, fcntl.LOCK_UN)

if __name__ == "__main__":
    main()
