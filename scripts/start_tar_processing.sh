#!/bin/bash

echo "Starting Tar processing"

# Pi
#source ~/vRMS/bin/activate
# Intel
#source ~/anaconda3/envs/RMS/bin/activate
# M2
source ~/.conda/envs/rms/bin/activate
# M2
archive_files=~/home/pi/RMS_data/ArchivedFiles
# Pi
#archive_files=~/pi/RMS_data/ArchivedFiles

tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_file('$archive_files', '*.bz2'))")

# Unpack tar
unpack_folder=$(echo "$tar_file" | cut -f 1 -d '.')
if [ ! -d "$unpack_folder" ]; then
  mkdir "$unpack_folder"
fi

echo "Unpack tar : $tar_file to folder: $unpack_folder"
tar -xvf "$tar_file" -C "$unpack_folder" || exit

sh ./start_folder_processing.sh "$unpack_folder"

read -n 1 -s -r -p "Press any key to exit"
echo