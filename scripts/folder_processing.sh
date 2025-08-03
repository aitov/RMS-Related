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
missed_fits_folder="$source_folder/missed_fits"
bin_files=$(find "$source_folder" -type f -name "FR_*.bin")
if [ -z "$bin_files" ]; then
  echo "No bin files found, skipping processing"
else
  # search only in current folder
  source_bin_files=$(find "$source_folder" -maxdepth 1 -type f -name "FR_*.bin")
  if [ -n "$source_bin_files" ]; then
    echo "Generating mp4 for bins in : $source_folder"
    python -m Utils.FRbinViewer -a -t -m $meteor_shower -f mp4 -c "$source_folder/.config" "$source_folder"
  fi

  if [ -d "$missed_fits_folder" ]; then
    fits_files=$(find "$missed_fits_folder" -type f -name "FF_*.fits")
    if [ -z "$fits_files" ]; then
      echo "No missed fits files found, skipping processing"
    else
      create_folder "$results_folder/missed_fits"
      echo "Generating mp4 for bins in : $missed_fits_folder"
      python -m Utils.FRbinViewer -a -t -m -f mp4 -c "$source_folder/.config" "$missed_fits_folder"
      # try to generate track for missed fits
      if [ ! -f "$source_folder/.config" ] || [ ! -f "$source_folder/platepar_cmn2010.cal" ]; then
        echo ".config or platepar_cmn2010.cal file found, skipping calibration"
      else
        cp "$source_folder/platepar_cmn2010.cal" "$missed_fits_folder"
        find "$source_folder" -type f -name "CALSTARS_*.txt" -print0 |
          while IFS= read -r -d '' file; do
            cp "$file" "$missed_fits_folder"
          done
        echo "Starting detection in missed fits"
        python -m RMS.Detection "$missed_fits_folder" -c "$source_folder/.config"
        echo "Starting calibration"
        python -m RMS.Astrometry.ApplyRecalibrate "$missed_fits_folder" -c "$source_folder/.config"

        # if no cal star file need run RMS2UFO manually
        cal_star_files=$(find "$missed_fits_folder" -type f -name "CALSTARS_*.txt")
        if [ -z "$cal_star_files" ]; then
          echo "No cal star file - run RMS2UFO manually"
          ftp_files=$(find "$missed_fits_folder" -type f -name "FTPdetectinfo_*.txt")
          if [ -z "$ftp_files" ]; then
            echo "No ftp files found, exiting"
            exit
          else
            IFS=$'\r\n' read -d '' -ra ftp_files_list <<< "$ftp_files"
            for ftp_file in "${ftp_files_list[@]}"; do
               # process ftp file without _uncalibrated.txt at the end
               if [[ ! "$ftp_file" = *_uncalibrated.txt ]] && [[ ! "$ftp_file" = *_backup_*.txt ]]; then
                  echo "$ftp_file"
                  python -m Utils.RMS2UFO "$ftp_file" "$missed_fits_folder/platepar_cmn2010.cal"
               fi
            done
          fi
        fi
        find "$missed_fits_folder" -type f -name "*.csv" -print0 |
            while IFS= read -r -d '' csv_file; do
               cp "$csv_file" "$results_folder/missed_fits"
            done
      fi
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
        if [ "$parent_dir" = "$missed_fits_folder" ]; then
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

cal_star_file="$source_folder/CALSTARS_$source_folder_name.txt"

if [ -f "$cal_star_file" ]; then
  cal_star_file_name=$(basename "$cal_star_file")
  zip -j "$source_folder/${cal_star_file_name}.zip" "$cal_star_file"
  cp "$source_folder/${cal_star_file_name}.zip" "$rms_results_folder"
fi

without_full="${source_folder_name}"
# remove full for custom upload mode
if [[ "$source_folder_name" == *_full ]]; then
  without_full=${source_folder_name%"_full"}
fi

cp "$source_folder/.config" "$rms_results_folder"
cp "$source_folder/platepar_cmn2010.cal" "$rms_results_folder"
cp "$source_folder/${without_full}_timelapse.mp4" "$rms_results_folder"
