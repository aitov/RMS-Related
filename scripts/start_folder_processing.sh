#!/bin/bash
# Script for Raspberry Pi use, everything will be generated on station and need download results folder to local PC
# Actions in script:
# 1. ArchivedFiles by folder select dialog, if some fits for bin files missed - it will be copied from CapturedFiles;
# 8. After it executes common script folder_processing.sh (see documentation in folder_processing script);
# 9. Starts CMN_binViewer in selected folder with detect mode and specified FTPdetectinfo_ file
# 10. After confirmation executes common script photo_processing.sh in Confirmed folder with folder name selected in CapturedFiles (see documentation in photo_processing.sh script)

. activate.sh
echo "Starting folder processing"

captured_files="$home_folder/RMS_data/CapturedFiles"
archived_files="$home_folder/RMS_data/ArchivedFiles"
confirmed_files="$home_folder/RMS_data/ConfirmedFiles"
processed_files="$home_folder/RMS_data/ProcessedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$archived_files'))")

if [ -z "$source_folder" ]; then
  echo "Source folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

source_folder_name=$(basename "$source_folder")
create_folder "$processed_files"

results_folder="$processed_files/$source_folder_name"
missed_fits_folder="$source_folder/missed_fits"
confirmed_missed_fits="$confirmed_files/$source_folder_name/missed_fits"

create_folder "$results_folder"

# check if we have have bins without fits - copy it from CapturedFiles
find "$source_folder" -type f -name "FR_*.bin" -print0 |
  while IFS= read -r -d '' bin_file; do
    bin_file_name=$(basename "$bin_file")
    fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
    fit_file_name="FF${fit_file_base:2}.fits"
    if [ ! -f "$source_folder/$fit_file_name" ]; then
      create_folder "$missed_fits_folder"
      create_folder "$confirmed_missed_fits"
      echo "Missed fits: $fit_file_name , copy from captured files"
      # copy to missed_fits folder for detection and recalibration
      cp "$captured_files/$source_folder_name/$fit_file_name" "$missed_fits_folder"
      cp "$captured_files/$source_folder_name/$fit_file_name" "$confirmed_missed_fits"
      # move bin file to missed fits
      mv "$bin_file" "$missed_fits_folder"
    fi
  done

current_dir=$(pwd)

. folder_processing.sh "$source_folder" "$results_folder"


cd "$bin_viewer_folder"

python -m CMN_binViewer "$source_folder" -c -f "FTPdetectinfo_${source_folder_name}.txt"

cd "$current_dir"

if [ ! -d "$confirmed_files/$source_folder_name" ]; then
  echo "Confirmed folder not found: $confirmed_files/$source_folder_name"

  read -n 1 -s -r -p "Press any key to exit"
  echo

  exit
fi

. photo_processing.sh "$confirmed_files/$source_folder_name" "$results_folder"

read -n 1 -s -r -p "Press any key to exit"
echo

