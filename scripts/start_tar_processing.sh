#!/bin/bash

. activate.sh

echo "Starting Tar processing"

archive_files="$home_folder/pi/RMS_data/ArchivedFiles"

tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_file('$archive_files', '*.bz2'))")

# Unpack tar
unpack_folder=$(echo "$tar_file" | cut -f 1 -d '.')
if [ ! -d "$unpack_folder" ]; then
  mkdir "$unpack_folder"
fi

echo "Unpack tar : $tar_file to folder: $unpack_folder"
tar -xvf "$tar_file" -C "$unpack_folder" || exit

. folder_processing.sh "$rms_folder" "$unpack_folder"

read -n 1 -s -r -p "Press any key to exit"
echo
