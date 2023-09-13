#!/bin/bash

# Copy fits files from missed_fit_files.txt file to selected folder + _missed_fits

echo "Starting bin collecting"

. activate.sh

captured_files="$home_folder/pi/RMS_data/CapturedFiles"
processed_files="$home_folder/pi/RMS_data/ProcessedFiles"

missed_fits_files=$(python -c "import SelectDialog; print(SelectDialog.select_file('$captured_files', '*.txt'))")

if [[ ! $missed_fits_files = *_missed_fits.txt ]]; then
  echo "Missed fits file should ends with : _missed_fits.txt"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

if [ ! -d "$processed_files" ]; then
  mkdir "$processed_files"
fi

target_folder=${missed_fits_files%"_missed_fits.txt"}

if [ ! -d "$target_folder" ]; then
  echo "Source folder not found: $target_folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

target_folder_name=$(basename "$target_folder")
missed_fits_folder="$processed_files/${target_folder_name}_missed_fits"

if [ ! -d "$missed_fits_folder" ]; then
  mkdir "$missed_fits_folder"
fi

while IFS= read -r missed_fit_file; do
  if [ ! -f "$target_folder/$missed_fit_file" ]; then
    echo "Missed fits file not found: $missed_fit_file"
  else
    echo "Copy missed fits file: $missed_fit_file"
    cp "$target_folder/$missed_fit_file" "$missed_fits_folder"
  fi
done <"$missed_fits_files"

rm "$missed_fits_files"

read -n 1 -s -r -p "Press any key to exit"
echo
