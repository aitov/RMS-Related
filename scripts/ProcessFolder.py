import os
import shutil
import subprocess
import glob
import sys
import zipfile
import argparse
from Utils.FRbinViewer import view as convertFRbinToMp4
from Utils.FRbinViewer import loadShowerAssociations
from Utils.BatchFFtoImage import batchFFtoImage
from RMS.ConfigReader import loadConfigFromDirectory

import RMS.ConfigReader as cr

import configparser

def read_sftp_config(ini_path):
    parser = configparser.ConfigParser()
    parser.read(ini_path)
    sftp_enabled = False
    sftp_command = None
    if 'SFTP' in parser:
        section = parser['SFTP']
        sftp_enabled = section.getboolean('enabled', fallback=False)
        sftp_command = section.get('command', fallback=None)
    return sftp_enabled, sftp_command

def upload_archive_sftp(archive_path, sftp_command):
    import subprocess
    # Replace placeholder in command if present
    cmd = sftp_command.replace('{archive}', archive_path)
    print(f"Uploading archive via SFTP: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("SFTP upload output:\n" + result.stdout)
        print("SFTP upload completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"SFTP upload failed: {e.stderr}")
        return False
    return True


def processFiles(captured_folder, source_folder, target_folder):
    print("Processing files in  : {}".format(source_folder))
    copyRmsFiles(source_folder, target_folder)
    processMp4Files(captured_folder, source_folder, target_folder)
    runDetectionOnMissedFits(source_folder)
    processMeteorFiles(source_folder, target_folder)
    copyCsvFiles(source_folder, target_folder)

    archive_name = os.path.join(os.path.abspath(os.path.join(source_folder, os.pardir)),
                                os.path.basename(target_folder) + '_detected')

    archive_name = shutil.make_archive(os.path.join(target_folder, archive_name), 'bztar', target_folder)
    print("Archived to  : {}".format(archive_name))

    # SFTP upload step
    config_path = os.path.join(os.path.dirname(__file__), 'processing.ini')
    sftp_enabled, sftp_command = read_sftp_config(config_path)
    if sftp_enabled and sftp_command:
        upload_archive_sftp(archive_name, sftp_command)
    else:
        print("SFTP upload not enabled or command not set in processing.ini.")

    shutil.rmtree(target_folder)


def processFilesTask(captured_night_dir, archived_night_dir, config):
    print("Executing processing files task")
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

    processFiles(captured_night_dir, archived_night_dir,  archived_night_dir + "_processed")

    # Release lock file so RMS is authorized to reboot, if needed
    os.remove(lockfile)


def getListOfMissedFits(source_folder):
    """
    Find all FR_*.bin files in source_folder, check for corresponding FF*.fits files,
    and return a list of missing fits file names.
    """
    missed_fits = []
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.startswith('FR_') and file.endswith('.bin'):
                fit_file_base = file.split('.', 1)[0]
                fit_file_name = "FF{}.fits".format(fit_file_base[2:])
                fit_file_path = os.path.join(source_folder, fit_file_name)
                if not os.path.isfile(fit_file_path):
                    print("Missed fits: {}".format(fit_file_name))
                    missed_fits.append(fit_file_name)
    return missed_fits


def copyMissedFits(capture_folder, source_folder):
    missedFits = getListOfMissedFits(source_folder)
    if not missedFits:
        print("No missed fits files found.")
        return
    missed_fits_folder = os.path.join(source_folder, "missed_fits")
    createFolder(missed_fits_folder)

    # copy the missed fits files and move the corresponding bin files
    for fit_file in missedFits:
        fit_file_base = fit_file.split('.', 1)[0]
        fr_file_name = "FR{}.bin".format(fit_file_base[2:])
        fr_file_path = os.path.join(source_folder, fr_file_name)
        fr_dest_path = os.path.join(missed_fits_folder, fr_file_name)
        shutil.move(fr_file_path, fr_dest_path)
        print("Moved bin file to missed fits folder: {}".format(fr_file_name))
        fit_file_path = os.path.join(capture_folder, fit_file)
        fit_dest_path = os.path.join(missed_fits_folder, fit_file)
        if os.path.isfile(fit_file_path):
            shutil.copy2(fit_file_path, fit_dest_path)
            print("Copied missed fits file: {}".format(fit_file))
        else:
            print("Source missed fits file not found: {}".format(fit_file))


def processMp4Files(capture_folder, source_folder, target_folder):
    copyMissedFits(capture_folder, source_folder)

    config_files = [os.path.join(source_folder, '.config')]
    config = cr.loadConfigFromDirectory(config_files, 'notused')
    try:
        associations = loadShowerAssociations(source_folder, config)
    except Exception as e:
        print("Error loading shower associations: {}".format(e))
        associations = {}

    # convert all FR_*.bin files to mp4 in root folder
    convertToMp4(source_folder, config, associations)
    copyMp4(source_folder, target_folder)
    # convert all FR_*.bin files to mp4 in missed_fits folder
    missed_fits_folder = os.path.join(source_folder, "missed_fits")
    if os.path.exists(missed_fits_folder):
        if missedFitsLimitReached(missed_fits_folder):
            return
        convertToMp4(missed_fits_folder, config, associations)
        target_missed_fits_folder = os.path.join(target_folder, "missed_fits")
        createFolder(target_missed_fits_folder)
        copyMp4(missed_fits_folder, target_missed_fits_folder)


def convertToMp4(source_folder, config, associations=None):
    if associations is None:
        associations = {}
    add_shower_name = True
    if not associations:
        print("Shower Associations not loaded, skipping add shower name")
        add_shower_name = False
    for file_name in os.listdir(source_folder):
        if file_name.startswith('FR_') and file_name.endswith('.bin'):
            fit_file_base = file_name.split('.', 1)[0]
            fit_file_name = "FF{}.fits".format(fit_file_base[2:])
            if not os.path.isfile(os.path.join(source_folder, fit_file_name)):
                fit_file_name = None
            print("Converting {} to mp4".format(os.path.join(source_folder, file_name)))
            convertFRbinToMp4(source_folder, fit_file_name, file_name, config, append_ff_to_video=True,
                              extract_format='mp4', hide=True, avg_background=True, add_timestamp=True,
                              associations=associations, add_shower_name=add_shower_name)


def copyMp4(source_folder, target_folder):
    for file_name in os.listdir(source_folder):
        if file_name.startswith('FR_') and file_name.endswith('.mp4'):
            source_file = os.path.join(source_folder, file_name)
            target_file = os.path.join(target_folder, file_name)
            shutil.copy2(source_file, target_file)


def processMeteorFiles(source_folder, target_folder):
    meteors_folder = os.path.join(target_folder, "meteors")
    batchFFtoImage(source_folder, 'jpg')
    copyMeteorFiles(source_folder, meteors_folder)
    missed_fits_folder = os.path.join(source_folder, "missed_fits")
    target_missed_fits_folder = os.path.join(target_folder, "missed_fits")

    if os.path.exists(missed_fits_folder):
        if missedFitsLimitReached(missed_fits_folder):
            return
        batchFFtoImage(missed_fits_folder, 'jpg')
        copyMeteorFiles(missed_fits_folder, target_missed_fits_folder)


def copyMeteorFiles(source_folder, target_folder):
    for file_name in os.listdir(source_folder):
        if (file_name.startswith('FF_') and file_name.endswith('.jpg')) or file_name.endswith('_meteors.jpg'):
            if not os.path.exists(target_folder):
                createFolder(target_folder)
            source_file = os.path.join(source_folder, file_name)
            target_file = os.path.join(target_folder, file_name)
            shutil.copy2(source_file, target_file)


def copyCsvFiles(source_folder, target_folder):
    for file_name in os.listdir(source_folder):
        if file_name.endswith('.csv'):
            source_file = os.path.join(source_folder, file_name)
            target_file = os.path.join(target_folder, file_name)
            shutil.copy2(source_file, target_file)
    missed_fits_folder = os.path.join(source_folder, "missed_fits")
    target_missed_fits_folder = os.path.join(target_folder, "missed_fits")
    if os.path.exists(missed_fits_folder):
        if missedFitsLimitReached(missed_fits_folder):
            return
        for file_name in os.listdir(missed_fits_folder):
            if file_name.endswith('.csv'):
                source_file = os.path.join(missed_fits_folder, file_name)
                target_file = os.path.join(target_missed_fits_folder, file_name)
                shutil.copy2(source_file, target_file)


def copyRmsFiles(source_path, target_path):
    rms_folder = os.path.join(target_path, "rms")
    createFolder(rms_folder)
    zipBigFiles(source_path, rms_folder)
    rms_files = getProcessedFiles(source_path)
    for file_name in rms_files:
        source_file = os.path.join(source_path, file_name)
        target_file = os.path.join(rms_folder, file_name)
        shutil.copy2(source_file, target_file)


# Get files list to include in the processed archive
def getProcessedFiles(source_path):
    allowed_exts = ['.kml', '.ecsv', '.txt', '.csv', '.cal', '.png', '.jpg', '_timelapse.mp4', '.bmp', '.bz2',
                    '.config']
    fileList = []

    for file_name in os.listdir(source_path):
        # Include by extension
        if any(file_name.endswith(ext) for ext in allowed_exts) and not file_name.startswith('CALSTARS_') and not file_name.endswith('_FT.tar.bz2'):
            fileList.append(file_name)

    return fileList


def zipBigFiles(source_folder, target_folder):
    platepars_file = os.path.join(source_folder, 'platepars_all_recalibrated.json')
    zipFile(platepars_file, target_folder)

    source_folder_name = os.path.basename(source_folder)
    # Remove '_full' suffix if present
    if source_folder_name.endswith('_full'):
        source_folder_name = source_folder_name[: -len('_full')]

    cal_star_file = os.path.join(source_folder, f'CALSTARS_{source_folder_name}.txt')

    zipFile(cal_star_file, target_folder)


def zipFile(file_path, target_folder):
    if os.path.isfile(file_path):
        file_name = os.path.basename(file_path)
        zip_path = os.path.join(os.path.dirname(file_path), file_name + '.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=file_name)
        shutil.copy(zip_path, target_folder)


def runDetectionOnMissedFits(source_folder):
    missed_fits_folder = os.path.join(source_folder, 'missed_fits')

    if not os.path.exists(missed_fits_folder) or missedFitsLimitReached(missed_fits_folder):
        print('No missed_fits folder found, skipping detection on missed fits')
        return

    config_file = os.path.join(source_folder, '.config')
    cal_file = os.path.join(source_folder, 'platepar_cmn2010.cal')

    if not (os.path.isfile(config_file) and os.path.isfile(cal_file)):
        print('.config or platepar_cmn2010.cal file not found, skipping calibration')
        return
    else:
        shutil.copy(cal_file, missed_fits_folder)
        for file in glob.glob(os.path.join(source_folder, 'CALSTARS_*.txt')):
            shutil.copy(file, missed_fits_folder)
        print('Starting detection in missed fits')
        subprocess.run([
            sys.executable, '-m', 'RMS.Detection', missed_fits_folder, '-c', config_file
        ])
        print('Starting calibration')
        subprocess.run([
            sys.executable, '-m', 'RMS.Astrometry.ApplyRecalibrate', missed_fits_folder, '-c', config_file
        ])

        cal_star_files = glob.glob(os.path.join(missed_fits_folder, 'CALSTARS_*.txt'))
        if not cal_star_files:
            print('No cal star file - run RMS2UFO manually')
            ftp_files = glob.glob(os.path.join(missed_fits_folder, 'FTPdetectinfo_*.txt'))
            if not ftp_files:
                print('No ftp files found, exiting')
                return
            else:
                for ftp_file in ftp_files:
                    if not (ftp_file.endswith('_uncalibrated.txt') or '_backup_' in ftp_file):
                        print(ftp_file)
                        subprocess.run([
                            sys.executable, '-m', 'Utils.RMS2UFO', ftp_file,
                            os.path.join(missed_fits_folder, 'platepar_cmn2010.cal')
                        ])


def createFolder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)


def missedFitsLimitReached(missed_fits_folder):
    """
    Check the number of FR_*.bin files in the missed_fits_folder.
    Print the count and a warning if more than 20 are found.
    Returns True if limit exceeded (should skip), False otherwise.
    """
    num_fr_bin_files = len([f for f in os.listdir(missed_fits_folder) if f.startswith('FR_') and f.endswith('.bin')])
    print("Number of FR_*.bin files in missed_fits folder: {}".format(num_fr_bin_files))
    if num_fr_bin_files > 20:
        print("Warning: More than 20 missed fits files detected ({}).".format(num_fr_bin_files))
        print("Skipping processing of missed fits")
        return True
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process captured meteor files or upload archive via SFTP.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--upload', action='store_true', help='Upload a specified archive via SFTP')
    group.add_argument('--process', action='store_true', help='Process captured meteor files (default)')
    parser.add_argument('args', nargs='*', help='Arguments: for --upload, path to archive; for --process, captured_folder source_folder target_folder')

    args_ns = parser.parse_args()

    if args_ns.upload:
        if not args_ns.args or len(args_ns.args) < 1:
            print('Please provide the path to the archive to upload.')
            sys.exit(1)
        archive_path = args_ns.args[0]
        config_path = os.path.join(os.path.dirname(__file__), 'processing.ini')
        sftp_enabled, sftp_command = read_sftp_config(config_path)
        if sftp_enabled and sftp_command:
            upload_archive_sftp(archive_path, sftp_command)
        else:
            print('SFTP upload not enabled or command not set in processing.ini.')
    else:
        if len(args_ns.args) < 3:
            print('Please provide captured_folder, source_folder, and target_folder.')
            sys.exit(1)
        captured_folder, source_folder, target_folder = args_ns.args[:3]
        processFiles(captured_folder, source_folder, target_folder)
