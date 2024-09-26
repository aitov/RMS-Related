#!/bin/bash
echo "Starting processing"
echo

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

if [ -z "$2" ]; then
  echo "Please specify results folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi
results_folder="$2"

if [ ! -d "$results_folder" ]; then
  echo "Results folder not found: $results_folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

cd "$rms_folder" || exit

echo "Using source folder : $source_folder"
missed_fits="$source_folder/missed_fits"
bin_files=$(find "$source_folder" -type f -name "FR_*.bin")
if [ -z "$bin_files" ]; then
  echo "No bin files found, skipping processing"
  read -n 1 -s -r -p "Press any key to continue"
  echo
else
  echo "Generating mp4 for bins in : $source_folder"

  python -m Utils.FRbinViewer -a -t -m $meteor_shower -f mp4 -c "$source_folder/.config" "$source_folder"

  if [ -d "$missed_fits" ]; then
    fits_files=$(find "$missed_fits" -type f -name "FF_*.fits")
    if [ -z "$fits_files" ]; then
      echo "No fits files found, skipping processing"
    else
      create_folder "$results_folder/missed_fits"
      echo "Generating mp4 for bins in : $missed_fits"
      python -m Utils.FRbinViewer -a -t -m -f mp4 -c "$source_folder/.config" "$missed_fits"
    fi
  fi

  find "$source_folder" -type f -name "FR_*.bin" -print0 |
    while IFS= read -r -d '' bin_file; do
      parent_dir="$(dirname "$bin_file")"
      bin_file_name=$(basename "$bin_file")
      fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
      mp4_file_name="${fit_file_base}_line_00.mp4"
      if [ -f "$parent_dir/$mp4_file_name" ]; then
        echo "Copy mp4 file: $mp4_file_name"
        if [ "$parent_dir" = "$missed_fits" ]; then
          cp "$parent_dir/$mp4_file_name" "$results_folder/missed_fits"
        else
          cp "$parent_dir/$mp4_file_name" "$results_folder"
        fi
      fi
    done
fi

rms_results_folder="${results_folder}/rms"

create_folder "$rms_results_folder"

find "$source_folder" -type f -name "FTPdetectinfo_*.txt" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*_radiants.txt" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.png" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.jpg" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.csv" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.ecsv" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.kml" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done

find "$source_folder" -type f -name "*.bmp" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$rms_results_folder"
  done


platepars_file="$source_folder/platepars_all_recalibrated.json"

if [ -f "$platepars_file" ]; then
  platepars_file_name=$(basename "$platepars_file")
  zip -j "$source_folder/${platepars_file_name}.zip" "$platepars_file"
  cp "$source_folder/${platepars_file_name}.zip" "$rms_results_folder"
fi
source_folder_name=$(basename "$source_folder")

cp "$source_folder/.config" "$rms_results_folder"
cp "$source_folder/platepar_cmn2010.cal" "$rms_results_folder"
cp "$source_folder/${source_folder_name}_timelapse.mp4" "$rms_results_folder"
