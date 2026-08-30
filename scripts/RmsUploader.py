# Need register it run on startup
# crontab -e
# @reboot /usr/bin/python3 <RMSRelated path>/RmsUploader.py > <User folder>/rms_uploader.log 2>&1 &
import os
import fcntl
import time
import sys
import configparser
import subprocess
import paramiko

QUEUE_FILE = os.path.expanduser("~/rms_upload_queue.txt")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "processing.ini")


LOCK_FILE = "/tmp/rms_uploader.lock"

# Timing configurations for unstable network conditions
NET_TIMEOUT = 15      # Connection drop threshold if the server doesn't respond in 15 seconds
RETRY_DELAY = 300     # Pause in seconds (5 minutes) before retrying after a network failure
IDLE_DELAY = 60       # How often (in seconds) to poll the queue when the camera is idle
STARTUP_DELAY = 120   # One-time startup wait (2 minutes) to allow network after boot


def read_sftp_config(ini_path):
    """Read SFTP settings from processing.ini."""
    parser = configparser.ConfigParser()
    parser.read(ini_path)

    if "SFTP" not in parser:
        raise ValueError("Missing [SFTP] section")

    section = parser["SFTP"]
    sftp_enabled = section.getboolean("enabled", fallback=True)
    host = section.get("host", fallback="").strip()
    port = section.getint("port", fallback=22)
    user = section.get("user", fallback="").strip()
    key_path_raw = section.get("key_path", fallback=section.get("key_pat", fallback="")).strip()
    key_path = os.path.expanduser(key_path_raw)
    remote_folder = section.get("remote_folder", fallback="uploads").strip()

    if sftp_enabled:
        missing_fields = []
        if not host:
            missing_fields.append("host")
        if not user:
            missing_fields.append("user")
        if not key_path_raw:
            missing_fields.append("key_path")
        if not remote_folder:
            missing_fields.append("remote_folder")

        if missing_fields:
            raise ValueError("Missing SFTP settings: " + ", ".join(missing_fields))

    return {
        "enabled": sftp_enabled,
        "host": host,
        "port": port,
        "user": user,
        "key_path": key_path,
        "remote_folder": remote_folder,
    }

def upload_file_with_resume(sftp, local_path, remote_path):
    """Uploads a file via SFTP with byte-level resume support (reput analog)"""
    local_size = os.path.getsize(local_path)
    part_remote_path = remote_path + ".part"

    try:
        # Check if the final file already exists on the server
        final_size = sftp.stat(remote_path).st_size
        if final_size == local_size:
            print(f"File '{remote_path}' already exists on the server with identical size. Skipping upload.")
            return True
    except Exception:
        # If the file does not exist, we can proceed with the upload
        pass

    try:
        # Check if a partially uploaded file already exists on the Proxmox server
        remote_size = sftp.stat(part_remote_path).st_size
    except IOError:
        # File does not exist on the server yet, start from scratch
        remote_size = 0

    if remote_size >= local_size:
        # File is already fully uploaded as a .part file, just rename it
        sftp.rename(part_remote_path, remote_path)
        return True

    # Open the local file and move the pointer to the last interrupted byte
    with open(local_path, "rb") as local_file:
        local_file.seek(remote_size)

        # 'ab' stands for append (writing data to the end of the file)
        with sftp.open(part_remote_path, "ab") as remote_file:
            # Set timeout for write/read operations within the SFTP channel
            remote_file.settimeout(NET_TIMEOUT)
            while True:
                chunk = local_file.read(32768)  # 32 KB blocks for stability at 30kb/s
                if not chunk:
                    break
                remote_file.write(chunk)

    # Successfully finished uploading - remove the .part extension to make it visible to Samba
    sftp.rename(part_remote_path, remote_path)
    return True

def check_ping(hostname):
    """
    Checks if the local server is alive using a network ping.
    Returns True if reachable, False otherwise.
    """
    # '-c 1' sends 1 packet (Linux/Raspberry Pi flag)
    # '-W 2' sets a 2-second timeout so the script won't hang if the server is off
    command = ['ping', '-c', '1', '-W', '2', hostname]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def upload_to_windows_with_resume(local_file_path, ini_path):
    """
    Loads configuration settings and uploads a file to the Windows server via SFTP.
    Supports resuming interrupted transfers by appending missing bytes.
    """
    if not os.path.exists(local_file_path):
        print(f"[LOCAL] Error: Local file '{local_file_path}' does not exist.")
        return False

    # Initialize the configuration parser
    config = configparser.ConfigParser()
    config.read(ini_path)

    # Check if the local Windows upload is enabled in settings
    if not config.has_section('LOCAL_WINDOWS') or not config.getboolean('LOCAL_WINDOWS', 'enabled'):
        print("[LOCAL] Local Windows upload is disabled in config.")
        return False

    # Extract connection variables
    host = config.get('LOCAL_WINDOWS', 'host')
    port = config.getint('LOCAL_WINDOWS', 'port', fallback=22)
    user = config.get('LOCAL_WINDOWS', 'user')
    password = config.get('LOCAL_WINDOWS', 'password')
    remote_folder = config.get('LOCAL_WINDOWS', 'remote_folder')

    # 1. Verify network availability
    print(f"[LOCAL] Checking network availability for host {host}...")
    if not check_ping(host):
        print(f"[LOCAL] Error: Server {host} is unreachable. Skipping upload.")
        return False

    # 2. Establish connection and upload/resume the archive
    transport = None
    sftp = None
    try:
        print(f"[LOCAL] Connecting to {host}:{port} as user '{user}'...")
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        # Extract filename and construct destination path
        file_name = os.path.basename(local_file_path)
        if not remote_folder.endswith('/'):
            remote_folder += '/'
        remote_file_path = f"{remote_folder}{file_name}"

        local_file_size = os.path.getsize(local_file_path)
        remote_file_size = 0

        # Check if the file already exists on the remote Windows server
        try:
            remote_stat = sftp.stat(remote_file_path)
            remote_file_size = remote_stat.st_size
            print(f"[LOCAL] Remote file found. Size: {remote_file_size} bytes.")
        except IOError:
            # IOError means the file does not exist yet on the remote server
            print("[LOCAL] Remote file does not exist. Starting a fresh upload.")

        # Evaluate transfer strategy based on file size mismatch
        if remote_file_size == local_file_size:
            print(f"[LOCAL] File '{file_name}' is already fully uploaded. Skipping.")
            return True
        elif remote_file_size > local_file_size:
            print(
                f"[LOCAL] Warning: Remote file is LARGER than local file ({remote_file_size} > {local_file_size}). Overwriting entirely.")
            remote_file_size = 0  # Reset offset to force full overwrite

        # Open local and remote files to perform the block-by-block upload chunk stream
        if remote_file_size > 0:
            print(f"[LOCAL] Resuming upload from offset {remote_file_size} bytes...")
            # 'r+b' opens the file for update (reading and writing) without truncating it
            remote_file = sftp.open(remote_file_path, mode='r+b')
            remote_file.seek(remote_file_size)
        else:
            # 'wb' opens a brand new file or truncates an existing one to zero length
            remote_file = sftp.open(remote_file_path, mode='wb')

        with open(local_file_path, 'rb') as local_file:
            if remote_file_size > 0:
                local_file.seek(remote_file_size)

            # Stream the remaining data in chunks (32KB blocks)
            chunk_size = 32768
            while True:
                chunk = local_file.read(chunk_size)
                if not chunk:
                    break
                remote_file.write(chunk)

        remote_file.close()
        print(f"[LOCAL] File '{file_name}' successfully processed/resumed on the Windows server!")
        return True

    except Exception as e:
        print(f"[LOCAL] SFTP Upload Error occurred: {e}")
        return False

    finally:
        # Always clean up and close connections
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def main():
    # 1. Rigid process protection using a file descriptor lock.
    # If the daemon is already running from startup, any duplicate process exits instantly.
    lock_f = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Uploader is already running in the background as a daemon. Exiting duplicate.")
        sys.exit(0)

    print("Background upload daemon successfully started. Monitoring queue...")
    print(f"Waiting {STARTUP_DELAY} seconds before first network attempt...")
    time.sleep(STARTUP_DELAY)

    # INFINITE MONITORING LOOP (Runs continuously until RPi reboots or shuts down)
    while True:
        try:
            sftp_config = read_sftp_config(CONFIG_FILE)
        except Exception as e:
            print(f"SFTP config error ({e}). Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            continue

        # Check if there is any work in the queue file
        if not os.path.exists(QUEUE_FILE) or os.path.getsize(QUEUE_FILE) == 0:
            # Queue is empty - sleep for 1 minute and go to the next check cycle
            time.sleep(IDLE_DELAY)
            continue

        # If something appears in the queue, read the list of files
        with open(QUEUE_FILE, "r") as f:
            files = [line.strip() for line in f.readlines() if line.strip()]

        if not files:
            time.sleep(IDLE_DELAY)
            continue
        # If the local Windows upload is enabled, attempt to upload each file in the queue
        for local_file in files:
              upload_to_windows_with_resume(local_file, CONFIG_FILE)

        if not sftp_config["enabled"]:
            print("SFTP is disabled in processing.ini. Waiting for next check...")
            time.sleep(IDLE_DELAY)
            continue
        # Establish connection with your Proxmox server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Bypasses StrictHostKeyChecking

        try:
            print("Files detected in queue. Connecting to the file server...")
            private_key = paramiko.RSAKey.from_private_key_file(sftp_config["key_path"])

            # Apply hard network timeout for connection
            ssh.connect(
                sftp_config["host"],
                port=sftp_config["port"],
                username=sftp_config["user"],
                pkey=private_key,
                timeout=NET_TIMEOUT,
            )
            sftp = ssh.open_sftp()
            try:
                sftp.chdir(sftp_config["remote_folder"])
                print(f"Successfully changed remote directory to '{sftp_config['remote_folder']}'")
            except IOError:
                print(f"Error: '{sftp_config['remote_folder']}' directory not found on the server!")
                sftp.close()
                ssh.close()
                time.sleep(RETRY_DELAY)
                continue
            successful_files = []
            full_subdir_ready = False
            
            for local_file in files:
                if not os.path.exists(local_file):
                    # If the file was deleted manually, mark it as successful to clear the queue
                    successful_files.append(local_file)
                    continue

                filename = os.path.basename(local_file)
                print(f"Syncing: {filename}...")

                remote_filename = filename
                if "_full_" in filename:
                    if not full_subdir_ready:
                        try:
                            sftp.stat("full")
                        except IOError:
                            sftp.mkdir("full")
                            print("Created remote subfolder 'full'.")
                        full_subdir_ready = True
                    remote_filename = f"full/{filename}"

                if upload_file_with_resume(sftp, local_file, remote_filename):
                    successful_files.append(local_file)
                    # OPTIONAL: Uncomment the line below to delete the archive from the RPi
                    # SD card immediately after a successful upload to your 4TB disk
                    # os.remove(local_file)

            sftp.close()
            ssh.close()

            # Rewrite the queue file, removing successfully uploaded items
            remaining_files = [f for f in files if f not in successful_files]
            with open(QUEUE_FILE, "w") as f:
                for f_path in remaining_files:
                    f.write(f"{f_path}\n")

            print("Batch uploaded successfully. Returning to idle monitoring state.")

        except Exception as e:
            print(f"Network or server error ({e}). Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            # On connection error, we do not exit the loop.
            # We take a 5-minute pause and try again.

    # This line is unreachable, but cleanly releases the lock just in case
    fcntl.flock(lock_f, fcntl.LOCK_UN)

if __name__ == "__main__":
    main()
