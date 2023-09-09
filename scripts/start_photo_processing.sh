#!/bin/bash
. activate.sh
echo "Starting photo processing"

confirmed_folder="$home_folder/pi/RMS_data/ConfirmedFiles"
source_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$confirmed_folder'))")

if [ -z "$source_folder" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

results_folder=$source_folder"_results"

if [ ! -d "$results_folder" ]; then
  mkdir "$results_folder"
fi

. photo_processing.sh "$source_folder" "$results_folder"

read -n 1 -s -r -p "Press any key to exit"
echo