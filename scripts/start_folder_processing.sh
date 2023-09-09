#!/bin/bash
# Script for Raspberry Pi use, everything will be generated on station and need download results folder to local PC
# Actions in script:
# 1. Select target folder in CapturedFiles or ArchivedFiles by folder select dialog (better in Captured, as in Archived could be not all fits for bins) ;
# 8. After it executes common script folder_processing.sh (see documentation in folder_processing script);
# 9. Starts CMN_binViewer in selected folder with detect mode and specified FTPdetectinfo_ file
# 10. After confirmation executes common script photo_processing.sh in Confirmed folder with folder name selected in CapturedFiles (see documentation in photo_processing.sh script)

. activate.sh
echo "Starting folder processing"

captured_files="$home_folder/pi/RMS_data/CapturedFiles"
confirmed_files="$home_folder/pi/RMS_data/ConfirmedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

if [ -z "$source_folder" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

current_dir=$(pwd)

. folder_processing.sh "$source_folder"

if [ -d "${source_folder}_processed" ]; then
  rm -r "${source_folder}_processed"
fi


cd "$bin_viewer_folder"

folder_name=$(basename "$source_folder")

python -m CMN_binViewer "$source_folder" -c -f "FTPdetectinfo_${folder_name}.txt"

cd "$current_dir"

if [ ! -d "$confirmed_files/$folder_name" ]; then
  echo "Confirmed folder not found: $confirmed_files/$folder_name"

  read -n 1 -s -r -p "Press any key to exit"
  echo

  exit
fi

. photo_processing.sh "$confirmed_files/$folder_name" "${source_folder}_results"

read -n 1 -s -r -p "Press any key to exit"
echo

