#!/bin/bash

echo "Starting processing"
cd ~/home/projects/RMS || exit

if [ -z "$1" ]; then
    echo "Please specify source folder"
    read -n 1 -s -r -p "Press any key to exit"
    echo
    exit
fi

source_folder="$1"

if [ ! -d "$source_folder" ]; then
  echo "Source folder not found: $source_folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

bin_files=$(find "$source_folder" -type f -name "*.bin")
if [ ${#bin_files[@]} -eq 0 ]; then
  echo "No bin files found, skipping processing"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

echo "Generating mp4 for bins in : $source_folder"
python -m Utils.FRbinViewer -a -f mp4 -c "$source_folder/.config" "$source_folder"

processed_folder=$source_folder"_processed"

if [ ! -d "$processed_folder" ]; then
  mkdir "$processed_folder"
fi

results_folder="$processed_folder/results"
if [ ! -d "$results_folder" ]; then
  mkdir "$results_folder"
fi
echo "Copy bins with fits and mp4 to processed folder: $processed_folder"
find "$source_folder" -type f -name "*.bin" -print0 |
    while IFS= read -r -d '' bin_file; do
      bin_file_name=$(basename "$bin_file")
      echo "Copy bin file: $bin_file_name"
      cp "$bin_file" "$processed_folder"
      fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
      fit_file_name="FF${fit_file_base:2}.fits"
      mp4_file_name="${fit_file_base}_line_00.mp4"
      echo "Copy fits file: $fit_file_name"
      cp "$source_folder/$fit_file_name" "$processed_folder"
      echo "Copy mp4 file: $mp4_file_name"
      cp "$source_folder/$mp4_file_name" "$results_folder"
    done
cp "$source_folder/.config" "$processed_folder"
cp "$source_folder/platepar_cmn2010.cal" "$processed_folder"



read -r -p "Do you want to run SkyFit2? (y/n) " yn
case $yn in
	[yY] ) python -m Utils.SkyFit2 "$processed_folder" --config "$processed_folder/.config" --fr;
	  find "$processed_folder" -type f -name "FTPdetectinfo_*.txt" -print0 |
        while IFS= read -r -d '' ftp_file; do
          echo "Converting FTPdetectinfo to UFO csv: $ftp_file"
          python -m Utils.RMS2UFO "$ftp_file" "$processed_folder/platepar_cmn2010.cal"
          ftp_file_name=$(basename "$ftp_file")
          ftp_file_base="$(echo "$ftp_file_name" | cut -f 1 -d '.')"
          csv_file_name="${ftp_file_base#"FTPdetectinfo_"}.csv"
          echo "Copy converted csv file to results: $csv_file_name"
          cp "$processed_folder/$csv_file_name" "$results_folder"
        done;;
esac
