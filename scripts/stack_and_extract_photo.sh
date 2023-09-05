#!/bin/bash
. activate.sh

echo "Starting ShowerAssociation"

confirmed_folder="$home_folder/pi/RMS_data/ConfirmedFiles"
source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$confirmed_folder'))")
source_folder_name=$(basename "$source_folder")

cd "$rms_folder" || exit

python Utils/ShowerAssociation.py -c .config "$source_folder/FTPdetectinfo_$source_folder_name.txt" -x
echo "StackFFs"
python -m Utils.StackFFs -s -b -x "$source_folder" png
python -m Utils.BatchFFtoImage -t "$source_folder" jpg

read -r -p "Do you want to run TrackStack? (y/n) " yn
case $yn in
[yY])
  echo "TrackStack"
  python -m Utils.TrackStack "$source_folder" -x
esac

read -n 1 -s -r -p "Press any key to exit"
echo