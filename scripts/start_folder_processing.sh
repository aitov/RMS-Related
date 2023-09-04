#!/bin/bash

echo "Starting folder processing"

# Pi
#source ~/vRMS/bin/activate
# Intel
#source ~/anaconda3/envs/RMS/bin/activate
# M2
source ~/.conda/envs/rms/bin/activate

# M2
captured_files=~/home/pi/RMS_data/CapturedFiles
# Pi
#archive_files=~/pi/RMS_data/CapturedFiles

source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

sh ./start_folder_processing.sh "$source_folder"

read -n 1 -s -r -p "Press any key to exit"
echo