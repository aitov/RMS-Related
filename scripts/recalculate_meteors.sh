#!/bin/bash
activate() {
    . activate.sh
}

activate

cleanupDir() {
 if [ -z "$1" ]; then
    echo "Please specify folder name"
    read -n 1 -s -r -p "Press any key to exit"
    echo
    exit
  fi
  target_folder="$1"
  if [ -f "$target_folder/.config" ]; then
    rm "$target_folder/.config"
  fi
  if [ -f "$target_folder/platepar_cmn2010.cal" ]; then
    rm "$target_folder/platepar_cmn2010.cal"
  fi

  find "$target_folder" -type f -name "FF_*.fits" -print0 |
    while IFS= read -r -d '' file; do
      rm "$file"
    done
  find "$target_folder" -type f -name "*.txt" -print0 |
    while IFS= read -r -d '' file; do
      rm "$file"
    done
  find "$target_folder" -type f -name "*.png" -print0 |
    while IFS= read -r -d '' file; do
      rm "$file"
    done
  find "$target_folder" -type f -name "*.json" -print0 |
    while IFS= read -r -d '' file; do
      rm "$file"
    done
}


if [ -z "$1" ]; then
  echo "Please specify source folder"
  exit
fi
source_folder="$1"

if [ ! -d "$source_folder" ]; then
  echo "Source folder not found: $source_folder"
  exit
fi

recalibration_folder="${source_folder}_recalibrated"
# clean up if exists
delete_folder "$recalibration_folder"
create_folder "$recalibration_folder"

echo "Copy fits to recalibration folder: $recalibration_folder"
find "$source_folder" -type f -name "FF_*.fits" -print0 |
  while IFS= read -r -d '' fits_file; do
    parent_dir="$(dirname "$fits_file")"
    bin_file_name=$(basename "$fits_file")

    echo "Copy Fits file: $bin_file_name"
    cp "$fits_file" "$recalibration_folder"

    fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
    fit_file_name="FF${fit_file_base:2}.fits"
    echo "Copy fits file: $fit_file_name"
    cp "$parent_dir/$fit_file_name" "$recalibration_folder"
  done

find "$source_folder" -type f -name "CALSTARS_*.txt" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$recalibration_folder"
  done

if [ ! -f "$source_folder/.config" ] || [ ! -f "$source_folder/platepar_cmn2010.cal" ]; then
  echo ".config or platepar_cmn2010.cal file found, skipping processing"
else
  cp "$source_folder/.config" "$recalibration_folder"
  cp "$source_folder/platepar_cmn2010.cal" "$recalibration_folder"
  cd "$rms_folder" || exit
  echo "Starting detection"
  python -m RMS.Detection "$recalibration_folder" -c "$recalibration_folder/.config"
  echo "Starting calibration"
  python -m RMS.Astrometry.ApplyRecalibrate "$recalibration_folder" -c "$recalibration_folder/.config"
  # if no cal star file need run RMS2UFO manually
  cal_star_files=$(find "$recalibration_folder" -type f -name "CALSTARS_*.txt")
  if [ -z "$cal_star_files" ]; then
    echo "No cal star file - run RMS2UFO manually"
    ftp_files=$(find "$recalibration_folder" -type f -name "FTPdetectinfo_*.txt")
    if [ -z "$ftp_files" ]; then
      echo "No ftp files found, exiting"
      exit
    else
      IFS=$'\r\n' read -d '' -ra ftp_files_list <<< "$ftp_files"
      for ftp_file in "${ftp_files_list[@]}"; do
         # process ftp file without _uncalibrated.txt at the end
         if [[ ! "$ftp_file" = *_uncalibrated.txt ]]; then
            echo "$ftp_file"
            python -m Utils.RMS2UFO "$ftp_file" "$recalibration_folder/platepar_cmn2010.cal"
         fi
      done

    fi
  fi
  cleanupDir "$recalibration_folder"
fi



