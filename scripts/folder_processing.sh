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
  # todo add -t when timestamp will be fixed
  #python -m Utils.FRbinViewer -a -t -f mp4 -c "$source_folder/.config" "$source_folder"
  python -m Utils.FRbinViewer -a -f mp4 -c "$source_folder/.config" "$source_folder"
  if [ -d "$missed_fits" ]; then
    create_folder "$results_folder/missed_fits"
    echo "Generating mp4 for bins in : $missed_fits"
    python -m Utils.FRbinViewer -a -f mp4 -c "$source_folder/.config" "$missed_fits"
  fi

  sky_fit_folder="${results_folder}_sky_fit"

  create_folder "$sky_fit_folder"

  echo "Copy bins with fits sky fit folder: $sky_fit_folder"
  find "$source_folder" -type f -name "FR_*.bin" -print0 |
    while IFS= read -r -d '' bin_file; do
      parent_dir="$(dirname "$bin_file")"
      bin_file_name=$(basename "$bin_file")
      echo "Copy bin file: $bin_file_name"
      cp "$bin_file" "$sky_fit_folder"
      fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
      fit_file_name="FF${fit_file_base:2}.fits"
      mp4_file_name="${fit_file_base}_line_00.mp4"
      echo "Copy fits file: $fit_file_name"
      cp "$parent_dir/$fit_file_name" "$sky_fit_folder"
      echo "Copy mp4 file: $mp4_file_name"
      if [ "$parent_dir" = "$missed_fits" ]; then
        cp "$parent_dir/$mp4_file_name" "$results_folder/missed_fits"
      else
        cp "$parent_dir/$mp4_file_name" "$results_folder"
      fi

    done
  cp "$source_folder/.config" "$sky_fit_folder"
  cp "$source_folder/platepar_cmn2010.cal" "$sky_fit_folder"

  read -r -p "Do you want to run SkyFit2? (y/n) " yn
  case $yn in
  [yY])
    python -m Utils.SkyFit2 "$sky_fit_folder" --config "$sky_fit_folder/.config" --fr
    ftp_files=$(find "$sky_fit_folder" -type f -name "FTPdetectinfo_*.txt")
    if [ -z "$ftp_files" ]; then
      echo "No FTPdetectinfo files found, skipping converting"
      read -n 1 -s -r -p "Press any key to continue"
      echo
    else
      find "$sky_fit_folder" -type f -name "FTPdetectinfo_*.txt" -print0 |
        while IFS= read -r -d '' ftp_file; do
          echo "Converting FTPdetectinfo to UFO csv: $ftp_file"
          python -m Utils.RMS2UFO "$ftp_file" "$sky_fit_folder/platepar_cmn2010.cal"
          ftp_file_name=$(basename "$ftp_file")
          ftp_file_base="$(echo "$ftp_file_name" | cut -f 1 -d '.')"
          csv_file_name="${ftp_file_base#"FTPdetectinfo_"}.csv"
          echo "Copy converted csv file to results: $csv_file_name"
          cp "$sky_fit_folder/$csv_file_name" "$results_folder"
        done
   fi
  ;;
  esac
fi

rms_results_folder="${results_folder}/rms"

create_folder "$rms_results_folder"

find "$source_folder" -type f -name "FTPdetectinfo_*.txt" -print0 |
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
