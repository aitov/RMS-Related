#!/bin/bash
# Script for Raspberry Pi, will collect al bins with fits to separated folder and start SkyFit2 application

. activate.sh
echo "Starting SkyFit2 processing"

captured_files="$home_folder/pi/RMS_data/CapturedFiles"
processed_files="$home_folder/pi/RMS_data/ProcessedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

if [ -z "$source_folder" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

create_folder "$processed_files"

source_folder_name=$(basename "$source_folder")
results_folder="$processed_files/$source_folder_name"
create_folder "$results_folder"

. sky_fit2_processing.sh "$source_folder" "$results_folder"

delete_folder "${results_folder}_sky_fit"
read -n 1 -s -r -p "Press any key to exit"
echo

