#!/bin/bash

. activate.sh
echo "Starting folder processing"

captured_files="$home_folder/pi/RMS_data/CapturedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

if [ -z "$source_folder" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi


. folder_processing.sh "$source_folder"

read -n 1 -s -r -p "Press any key to exit"
echo
