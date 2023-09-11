#!/bin/bash
# Script for local use, before you need download required file *_detected.tar.bz2 from ArchivedFiles to local PC
# Actions in script:
# 1. Select target archive by file select dialog;
# 2. Unpack archive to folder without _detected suffix (with original name);
# 3. Checks that all FR_*.bin files have FF_*.fits for video processing;
# 4. If some fits files missed - creates text file <folder_name>_missed_fits.txt with list of files and pauses execution;
# 5. If some fits missed it expects folder created by copy_required_fits.sh : <folder_name>_missed_fits and copied to parent folder;
# 6. After press any key : it reads file <folder_name>_missed_fits.txt and tries copy fits from <folder_name>_missed_fits;
# 7. If something missed it will ask to stop or continue (it leads to generate transparent videos);
# 8. After it executes common script folder_processing.sh (see documentation in folder_processing script);
# 9. After folder processing executes common script photo_processing.sh (see documentation in photo_processing.sh script)

. activate.sh

echo "Starting Tar processing"

archive_files="$home_folder/pi/RMS_data/ArchivedFiles"
processed_files="$home_folder/pi/RMS_data/ProcessedFiles"

tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_file('$archive_files', '*.bz2'))")

if [ -z "$tar_file" ]; then
  echo "File not selected"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi


unpack_folder=${tar_file%"_detected.tar.bz2"}

if [ ! -d "$unpack_folder" ]; then
  mkdir "$unpack_folder"
fi

echo "Unpack tar : $tar_file to folder: $unpack_folder"
tar -xvf "$tar_file" -C "$unpack_folder" || exit

unpack_folder_name=$(basename "$unpack_folder")
parent_dir="$(dirname "$unpack_folder")"
missed_fits_files="$parent_dir/${unpack_folder_name}_missed_fits.txt"
rm -f "$missed_fits_files"

find "$unpack_folder" -type f -name "FR_*.bin" -print0 |
  while IFS= read -r -d '' bin_file; do
    bin_file_name=$(basename "$bin_file")
    fit_file_base="$(echo "$bin_file_name" | cut -f 1 -d '.')"
    fit_file_name="FF${fit_file_base:2}.fits"
    if [ ! -f "$unpack_folder/$fit_file_name" ]; then
      echo "Missed fits: $fit_file_name"
      echo "$fit_file_name" >>"$missed_fits_files"
    fi
  done

if [ -e "$missed_fits_files" ] && [ $(wc -c <"$missed_fits_files") -gt 0 ]; then
  echo "Exists missed fit files, copy from Captured and then press any key"
  open -e "$missed_fits_files"
  read -n 1 -s -r -p "Press any key to continue"
  echo
  missed_fits_folder="$parent_dir/${unpack_folder_name}_missed_fits"
  if [ ! -d "$missed_fits_folder" ]; then
    echo "Missed fits folder not found: $missed_fits_folder"
    read -r -p "Do you want continue without missed fits? (y/n) " yn
    case $yn in
    [yY])
      echo "Continue without missed fits files"
      ;;
    *)
      read -n 1 -s -r -p "Press any key to exit"
      echo
      exit
      ;;
    esac
  else
    missed_files=()
    while IFS= read -r missed_fit_file; do
      if [ ! -f "$missed_fits_folder/$missed_fit_file" ]; then
        echo "Missed fits file not found: $missed_fit_file"
        missed_files+=(" $missed_fit_file")
      else
        echo "Copy missed fits file: $missed_fit_file"
        cp "$missed_fits_folder/$missed_fit_file" "$unpack_folder"
      fi
    done <"$missed_fits_files"
  fi
fi

if [ ${#missed_files[@]} -gt 0 ]; then
  echo "Not all missed fits not found in folder : $missed_fits_folder"
  echo "Missed fits: ${missed_files[*]}"
  read -r -p "Do you want continue without missed fits? (y/n) " yn
  case $yn in
  [yY])
    echo "Continue without missed fits file"
    ;;
  *)
    read -n 1 -s -r -p "Press any key to exit"
    echo
    exit
    ;;
  esac
fi

if [ ! -d "$processed_files" ]; then
  mkdir "$processed_files"
fi

results_folder="$processed_files/$unpack_folder_name"

if [ ! -d "$results_folder" ]; then
  mkdir "$results_folder"
fi

current_dir=$(pwd)

. folder_processing.sh "$unpack_folder" "$results_folder"

cd "$current_dir"

. photo_processing.sh "$unpack_folder" "$results_folder"
if [ -d "${unpack_folder}" ]; then
  rm -r "$unpack_folder"
fi

if [ -d "${results_folder}_sky_fit" ]; then
  rm -r "${results_folder}_sky_fit"
fi
#rm "$tar_file"

read -n 1 -s -r -p "Press any key to exit"
echo
