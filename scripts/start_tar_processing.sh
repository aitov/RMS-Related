#!/bin/bash

. activate.sh

echo "Starting Tar processing"

archive_files="$home_folder/pi/RMS_data/ArchivedFiles"

tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_file('$archive_files', '*.bz2'))")

unpack_folder=$(echo "$tar_file" | cut -f 1 -d '.')
if [ ! -d "$unpack_folder" ]; then
  mkdir "$unpack_folder"
fi

echo "Unpack tar : $tar_file to folder: $unpack_folder"
tar -xvf "$tar_file" -C "$unpack_folder" || exit
missed_fit_files="$unpack_folder/missed_fit_files.txt"
rm -f "$missed_fit_files"

find "$unpack_folder" -type f -name "FR_*.bin" -print0 |
  while IFS= read -r -d '' bin_file; do
    bin_file_name=$(basename "$bin_file")
    fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
    fit_file_name="FF${fit_file_base:2}.fits"
    if [ ! -f "$unpack_folder/$fit_file_name" ]
     then
       echo "Missed : $fit_file_name"
       echo "$fit_file_name" >> "$missed_fit_files"
    fi
  done

if [ -e "$missed_fit_files" ] && [ $(wc -c < "$missed_fit_files") -gt 0 ]
  then
    echo "Exists missed fit files, copy from Captured and then restart script"
    read -n 1 -s -r -p "Press any key to exit"
    echo
    open -e "$missed_fit_files"
    exit
fi

. folder_processing.sh "$rms_folder" "$unpack_folder"

read -n 1 -s -r -p "Press any key to exit"
echo
