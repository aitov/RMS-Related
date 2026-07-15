# Need register it run on startup
# crontab -e
# @reboot /usr/bin/python3 <RMSRelated path>/RmsUploader.py > <User folder>/rms_uploader.log 2>&1 &
import os
import fcntl
import time
import sys
import configparser
import paramiko

QUEUE_FILE = os.path.expanduser("~/rms_upload_queue.txt")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "processing.ini")


LOCK_FILE = "/tmp/rms_uploader.lock"

# Timing configurations for unstable network conditions
NET_TIMEOUT = 15      # Connection drop threshold if the server doesn't respond in 15 seconds
RETRY_DELAY = 300     # Pause in seconds (5 minutes) before retrying after a network failure
IDLE_DELAY = 60       # How often (in seconds) to poll the queue when the camera is idle


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

    # INFINITE MONITORING LOOP (Runs continuously until RPi reboots or shuts down)
    while True:
        try:
            sftp_config = read_sftp_config(CONFIG_FILE)
        except Exception as e:
            print(f"SFTP config error ({e}). Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            continue

        if not sftp_config["enabled"]:
            print("SFTP is disabled in processing.ini. Waiting for next check...")
            time.sleep(IDLE_DELAY)
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
            
            for local_file in files:
                if not os.path.exists(local_file):
                    # If the file was deleted manually, mark it as successful to clear the queue
                    successful_files.append(local_file)
                    continue

                filename = os.path.basename(local_file)
                print(f"Syncing: {filename}...")

                if upload_file_with_resume(sftp, local_file, filename):
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
