#!/bin/bash
# Script for Raspberry Pi, will collect al bins with fits to separated folder and start SkyFit2 application

. activate.sh
echo "Creating full archive"

captured_files="$home_folder/RMS_data/CapturedFiles"
archived_files="$home_folder/RMS_data/ArchivedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

if [ -z "$source_folder" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

source_folder_name=$(basename "$source_folder")
results_folder="$archived_files/$source_folder_name"

cd "$rms_folder"
python /home/rms/source/RMS-Related/scripts/CreateFullArchive.py "$source_folder" "$results_folder" "False"

read -n 1 -s -r -p "Press any key to exit"
echo

