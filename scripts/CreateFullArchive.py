import os
import argparse
import shutil
from copy import deepcopy
from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
from RMS.ArchiveDetections import selectFiles, archiveDir
from RMS.ConfigReader import loadConfigFromDirectory
from ProcessFolder import processFiles
import configparser
QUEUE_FILE = os.path.expanduser("~/rms_upload_queue.txt")

config_defaults = {}
sftp_config = {}
config_path = os.path.join(os.path.dirname(__file__), 'processing.ini')
if os.path.exists(config_path):
    parser = configparser.ConfigParser()
    parser.read(config_path)
    if parser.sections():
       config_defaults.update(parser[parser.sections()[0]])
       if 'SFTP' in parser:
           sftp_config.update(parser['SFTP'])

def register_new_archive_for_upload(archive_path):
    """Call this right after creating your archive in your RMS script.
       It appends the file path to the queue instantly (takes milliseconds) and exits."""
    if archive_path and os.path.exists(archive_path):
        with open(QUEUE_FILE, "a") as f:
            f.write(f"{archive_path}\n")
        print(f"File {os.path.basename(archive_path)} added to the upload queue.")

def createFullArchive(captured_night_dir, archived_night_dir, config):
    delete_folder = boolValue(config_defaults.get('delete_folder', 'false'))
    process_folder = boolValue(config_defaults.get('process_folder', 'false'))
    print("Delete folder: {}".format(delete_folder))
    print("Process folder: {}".format(process_folder))
    createFullArchiveInteral(captured_night_dir, archived_night_dir, config, delete_folder, process_folder)


def createFullArchiveInteral(captured_night_dir, archived_night_dir, config, delete_folder=False, process_folder=False):
    print("Executing creating full archive")
    print("Captured dir path : {}".format(captured_night_dir))
    print("Archived dir path : {}".format(archived_night_dir))

    if config is None:
        print("No config file provided")
        config = loadConfigFromDirectory(None, 'notused')
        print("Loaded default config")

    # Create lock file to avoid RMS rebooting the system
    lockfile = os.path.join(config.data_dir, config.reboot_lock_file)
    with open(lockfile, 'w') as _:
        pass

    ftp_detect_file = findFTPdetectinfoFile(captured_night_dir)
    ff_detected = getDetectedMeteors(readFTPdetectinfo(captured_night_dir, ftp_detect_file))
    full_archive_dir = archived_night_dir + "_full"
    newConfig = deepcopy(config)
    newConfig.upload_mode = 1
    print("Full archive dir  : {}".format(full_archive_dir))
    archive_name = archiveDetections(captured_night_dir, full_archive_dir, ff_detected, newConfig)
    print("Archived to  : {}".format(archive_name))

    if process_folder:
        processFiles(captured_night_dir, full_archive_dir, archived_night_dir + "_processed")

    if delete_folder:
        shutil.rmtree(full_archive_dir)

    # upload full archive if enabled in processing.ini (for fast internet)
    sftp_enabled = boolValue(sftp_config.get('enabled', 'false'))
    upload_full = boolValue(sftp_config.get('upload_full', 'false'))
    if sftp_enabled and upload_full:
       register_new_archive_for_upload(archive_name)

    # Release lock file so RMS is authorized to reboot, if needed
    os.remove(lockfile)


def getDetectedMeteors(meteor_list):
    meteors = []
    for meteor in meteor_list:
        meteors.append(meteor[0])
    return meteors


def archiveDetections(captured_path, archived_path, ff_detected, config):
    # Get the list of files to archive
    file_list = selectFiles(config, captured_path, ff_detected)
    extra_files = getExtraFiles(captured_path)

    if file_list:
        # Create the archive ZIP in the parent directory of the archive directory
        archive_name = os.path.join(os.path.abspath(os.path.join(archived_path, os.pardir)),
                                    os.path.basename(archived_path) + '_detected')
        # Archive the files
        archive_name = archiveDir(captured_path, file_list, archived_path, archive_name, False, extra_files)
        return archive_name
    return None


def getExtraFiles(captured_path):
    allowed_extra_exts = ['.kml', '.json', '.ecsv', '.txt', '.csv', '.cal']
    extra_files = []
    extra_files.append(os.path.join(captured_path, ".config"))
    extra_files.append("mask.bmp")

    # Allowed extensions for extra files
    for file_name in os.listdir(captured_path):
        lower = file_name.lower()
        # Include by extension
        if any(lower.endswith(ext) for ext in allowed_extra_exts):
            extra_files.append(os.path.join(captured_path, file_name))
            continue
        # Special cases
        if lower.startswith('flux_') and lower.endswith('.png'):
            extra_files.append(os.path.join(captured_path, file_name))
            continue
        if lower.endswith('_timelapse.mp4'):
            extra_files.append(os.path.join(captured_path, file_name))
            continue

    return extra_files

def boolValue(val):
    return str(val).lower() == 'true'


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Create a full archive of the captured night.")
    arg_parser.add_argument('captured_dir_path', metavar='CAP_DIR_PATH', type=str,
                            help='Path to captured directory with FF files.')
    arg_parser.add_argument('archived_dir_path', metavar='ARC_DIR_PATH', type=str,
                            help='Path to archived directory to create archive.')
    cml_args = arg_parser.parse_args()

    captured_dir_path = os.path.normpath(cml_args.captured_dir_path)
    archived_dir_path = os.path.normpath(cml_args.archived_dir_path)
    # Create the full archive
    createFullArchive(captured_dir_path, archived_dir_path, None)
