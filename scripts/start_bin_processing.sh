#!/bin/bash

echo "Starting processing"

#source ~/vRMS/bin/activate
#cd ~/source/RMS
source ~/anaconda3/envs/RMS/bin/activate
cd ~/home/projects/RMS || exit
archive_files=~/home/pi/RMS_data/ArchivedFiles
# tar solution
tar_file=$(ls -1 $archive_files/*.tar.bz2 | tail -1)
# Unpack tar
unpack_folder=$(echo "$tar_file" | cut -f 1 -d '.')
mkdir "$unpack_folder"
echo "Unpack tar : $tar_file to folder: $unpack_folder"
tar -xvf "$tar_file" -C "$unpack_folder"

echo "Generating mp4 for bins in : $unpack_folder"
python -m Utils.FRbinViewer -a -x -f mp4 -c "$unpack_folder/.config" $unpack_folder

processed_folder=$unpack_folder"_processed"
echo "Copy bins with fits to processed folder: $processed_folder"
mkdir "$processed_folder"

find "$unpack_folder" -type f -name "*.bin" -print0 |
    while IFS= read -r -d '' bin_file; do
      bin_file_name=$(basename "$bin_file")
      echo "Copy bin file: $bin_file_name"
      cp "$bin_file" "$processed_folder"
      fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
      fit_file_name="FF${fit_file_base:2}.fits"
      mp4_file_name="${fit_file_base}_line_00.mp4"
      echo "Copy fits file: $fit_file_name"
      cp "$unpack_folder/$fit_file_name" "$processed_folder"
      echo "Copy mp4 file: $mp4_file_name"
      cp "$unpack_folder/$mp4_file_name" "$processed_folder"
    done
cp "$unpack_folder/.config" "$processed_folder"
cp "$unpack_folder/platepar_cmn2010.cal" "$processed_folder"



read -n 1 -s -r -p "Press any key to continue"

python -m Utils.SkyFit2 "$processed_folder" --config "$processed_folder/.config" --fr

echo