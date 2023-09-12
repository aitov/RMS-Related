#!/bin/bash
# Script for local use, before you need configure ssh on Raspberry Pi and open access in internet (internet static ip)
# Actions in script:
# 1. Select target archive by file select dialog;
# 2. Unpack archive to folder without _detected suffix (with original name);
# 3. Checks that all FR_*.bin files have FF_*.fits for video processing;
# 4. If some fits files missed - creates text file <folder_name>_missed_fits.txt with list of files and pauses execution;
# 8. After it executes common script folder_processing.sh (see documentation in folder_processing script);
# 9. After folder processing executes common script photo_processing.sh (see documentation in photo_processing.sh script)

. activate.sh

echo "Starting ssh tar processing"

archive_files="$home_folder/pi/RMS_data/ArchivedFiles"
processed_files="$home_folder/pi/RMS_data/ProcessedFiles"
# path on pi
remote_archive_files="/home/pi/RMS_data/ArchivedFiles"

tar_files=($(ssh "$ssh_host" "cd /home/pi/RMS_data/ArchivedFiles && ls -t *.tar.bz2"))
tar_files_string=$(printf ",\"%s\"" "${tar_files[@]}")
tar_files_string=${tar_files_string:1}

tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_from_list('Select tar file', [$tar_files_string]))")

rsync --progress -e ssh "$ssh_host:$remote_archive_files/$tar_file" "$archive_files"
read -n 1 -s -r -p "Press any key to exit"
echo