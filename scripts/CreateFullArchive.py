from copy import deepcopy
from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
from RMS.ArchiveDetections import archiveDetections
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
    ff_detected = readFTPdetectinfo(captured_night_dir, ftp_detect_file)
    full_archive_dir = archived_night_dir + "full"
    newConfig = deepcopy(config)
    newConfig.upload_mode = 1
    archive_name = archiveDetections(captured_night_dir, full_archive_dir, ff_detected, newConfig)
    print("Archived to  : {}".format(archive_name))
