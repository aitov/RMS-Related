import os
import argparse
from copy import deepcopy
from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
from RMS.ArchiveDetections import selectFiles, archiveDir
from RMS.ConfigReader import loadConfigFromDirectory


def createFullArchive(captured_night_dir, archived_night_dir, config):
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
        archive_name = archiveDir(captured_path, file_list, archived_path, archive_name, True, extra_files)
        return archive_name
    return None


def getExtraFiles(captured_path):
    extra_files = []
    extra_files.append(os.path.join(captured_path, ".config"))
    extra_files.append("mask.bmp")
    for file_name in os.listdir(captured_path):
        if ((file_name.lower().endswith('.kml'))
                or (file_name.lower().endswith('.json'))
                or (file_name.lower().endswith('.ecsv'))
                or (file_name.lower().endswith('.txt'))
                or (file_name.lower().endswith('.csv'))
                or (file_name.lower().endswith('.cal'))
                or (file_name.lower().startswith('flux_') and file_name.lower().endswith('.png'))
                or (file_name.lower().endswith('_timelapse.mp4'))):
            extra_files.append(os.path.join(captured_path, file_name))
    return extra_files

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="Create a full archive of the captured night.",)
    arg_parser.add_argument('captured_dir_path', metavar='CAP_DIR_PATH', type=str,
                            help='Path to captured directory with FF files.')
    arg_parser.add_argument('archived_dir_path', metavar='ARC_DIR_PATH', type=str,
                            help='Path to archived directory to create archive.')
    cml_args = arg_parser.parse_args()

    captured_dir_path = os.path.normpath(cml_args.captured_dir_path)
    archived_dir_path = os.path.normpath(cml_args.archived_dir_path)
    # Create the full archive
    createFullArchive(captured_dir_path, archived_dir_path, None)
