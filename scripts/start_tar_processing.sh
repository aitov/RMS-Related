#!/bin/bash
# Script for local processing RMS results
# Actions in script:
# 1. Check variable ssh_host from local.properties and if exists (ssh access configured) then:
# 1.1 connect to station and list all tar files from ArchivedFiles folder sorted by date desc;
# 1.2 Opens dialog with listbox with this list to select required archive file;
# 1.3 Downloads selected file from station to local ArchivedFiles folder and passes file name to item 3;
# 2. ssh_host from local.properties empty (ssh access not configured) and you downloaded manually required archive to local ArchivedFiles folder;
# 2.1 Opens file select dialog in ArchivedFiles folder;
# 2.3 Passes selected file name to item 3;
# 3 Unpack archive to folder without _detected suffix (with original name);
# 3.1 Checks that all FR_*.bin files have FF_*.fits for video processing;
# 3.2 If some fits files missed (fireballs, bright meteors not detected  );
# 3.2.1 In case ssh configured - download missed files from CapturedFiles of station and go to item 4;
# 3.2.2 In case ssh not configured - creates text file <folder_name>_missed_fits.txt with list of files and pauses execution;
# 3.2.3 You need upload this file to CapturedFiles folder and execute on station script: copy_required_fits.sh;
# 3.2.4 In select file dialog select uploaded txt file;
# 3.2.5 It will create folder : ProcessedFiles/<folder_name>_missed_fits;
# 3.2.6 You need download this folder to local folder ArchivedFiles;
# 3.3. After press any key : it reads file <folder_name>_missed_fits.txt and tries copy fits from ArchivedFiles/<folder_name>_missed_fits;
# 3.4. If something missed it will ask to stop or continue (it leads to generate transparent videos);
# 4. After it executes common script folder_processing.sh (see documentation in folder_processing script);
# 5. After folder processing executes common script photo_processing.sh (see documentation in photo_processing.sh script);

. activate.sh

echo "Starting Tar processing"

archive_files="$home_folder/pi/RMS_data/ArchivedFiles"
processed_files="$home_folder/pi/RMS_data/ProcessedFiles"

# path on pi
remote_archive_files="/home/pi/RMS_data/ArchivedFiles"
remote_captured_files="/home/pi/RMS_data/CapturedFiles"

if [ ! -z "$ssh_host" ]; then
    ssh_port=22
    # if custom port specified - extract it
    if [[ $ssh_host == *":"* ]]; then
      ssh_port=${ssh_host#*":"}
      ssh_host=${ssh_host%":$ssh_port"}
    fi

    tar_files=($(ssh "$ssh_host" -p "$ssh_port" "cd $remote_archive_files && ls -t *.tar.bz2"))
    tar_files_string=$(printf ",\"%s\"" "${tar_files[@]}")
    tar_files_string=${tar_files_string:1}

    tar_file_name=$(python -c "import SelectDialog; print(SelectDialog.select_from_list('Select tar file', [$tar_files_string]))")

    if [ -z "$tar_file_name" ]; then
      echo "File not selected, please select local tar file"
      read -n 1 -s -r -p "Press any key to continue"
      echo
    else
      rsync --progress -e "ssh -p $ssh_port" "$ssh_host:$remote_archive_files/$tar_file_name "  "$archive_files"
      tar_file="$archive_files/$tar_file_name"
    fi

fi

if [ -z "$tar_file" ]; then
  tar_file=$(python -c "import SelectDialog; print(SelectDialog.select_file('$archive_files', '*.bz2'))")
fi

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
  # copy from station directly
  if [ ! -z "$ssh_host" ]; then
    while IFS= read -r missed_fit_file; do
      rsync --progress -e ssh "$ssh_host:$remote_captured_files/$unpack_folder_name/$missed_fit_file" "$archive_files/$unpack_folder_name"
    done <"$missed_fits_files"
  else
    # Waiting for manual copy
    echo  "Exists missed fit files, copy from Captured and then press any key"
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
rm "$tar_file"

read -n 1 -s -r -p "Press any key to exit"
echo
