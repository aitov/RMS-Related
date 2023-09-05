#!/bin/bash

. activate.sh
echo "Starting folder processing"

captured_files="$home_folder/pi/RMS_data/CapturedFiles"

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

. folder_processing.sh "$rms_folder" "$source_folder"

read -n 1 -s -r -p "Press any key to exit"
echo
