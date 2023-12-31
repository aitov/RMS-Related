#!/bin/bash

# Copy all bins + fits from selected folder to selected folder + _bins

echo "Starting bin collecting"

. activate.sh

captured_files="$home_folder/pi/RMS_data/CapturedFiles"

target_folder=$(python -c "import SelectDialog; print(SelectDialog.select_folder('$captured_files'))")

if [ -z "$tar_file" ]; then
  echo "Folder not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

if [ ! -d "$target_folder" ]; then
  echo "Source folder not found: $target_folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

bin_files=$(find "$target_folder" -type f -name "FR_*.bin")
if [ -z "$bin_files" ]; then
  echo "No bin files found, skipping processing"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

processed_folder=$target_folder"_bins_fits"

if [ ! -d "$processed_folder" ]; then
  mkdir "$processed_folder"
fi

echo "Copy bins with fits to folder: $processed_folder"
find "$target_folder" -type f -name "FR_*.bin" -print0 |
    while IFS= read -r -d '' bin_file; do
      bin_file_name=$(basename "$bin_file")
      echo "Copy bin file: $bin_file_name"
      cp "$bin_file" "$processed_folder"
      fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
      fit_file_name="FF${fit_file_base:2}.fits"
      echo "Copy fits file: $fit_file_name"
      cp "$target_folder/$fit_file_name" "$processed_folder"
    done

read -n 1 -s -r -p "Press any key to exit"
echo