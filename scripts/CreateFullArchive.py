import os
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

    ftp_detect_file = findFTPdetectinfoFile(captured_night_dir)
    ff_detected = getDetectedMeteors(readFTPdetectinfo(captured_night_dir, ftp_detect_file))
    print(ff_detected)
    full_archive_dir = archived_night_dir + "_full"
    newConfig = deepcopy(config)
    newConfig.upload_mode = 1
    print("Full archive dir  : {}".format(full_archive_dir))
    archive_name = archiveDetections(captured_night_dir, full_archive_dir, ff_detected, newConfig)
    print("Archived to  : {}".format(archive_name))

def getDetectedMeteors(meteor_list):
    meteors = []
    for meteor in meteor_list:
        meteors.append(meteor[0])
    return meteors

def archiveDetections(captured_path, archived_path, ff_detected, config):
    # Get the list of files to archive
    file_list = selectFiles(config, captured_path, ff_detected)
    if file_list:
        # Create the archive ZIP in the parent directory of the archive directory
        archive_name = os.path.join(os.path.abspath(os.path.join(archived_path, os.pardir)),
                                    os.path.basename(archived_path) + '_detected')
        # Archive the files
        archive_name = archiveDir(captured_path, file_list, archived_path, archive_name)
        return archive_name
    return None

createFullArchive("/home/rms/RMS_data/CapturedFiles/UA0006_20250701_185701_383448", "/home/rms/RMS_data/ArchivedFiles/UA0006_20250701_185701_383448", None)