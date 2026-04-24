#!/bin/bash
# Script to download remote archives from multiple hosts and remove them after successful download
. activate.sh

archive_files="$home_folder/RMS_data/ArchivedFiles"

IFS=',' read -ra download_hosts_list <<< "$download_hosts"

# Check which hosts are online and build a list of available hosts
available_download_hosts_list=()
for download_host in "${download_hosts_list[@]}"; do
  # Parse user_host and port if present
  if [[ "$download_host" == *:* ]]; then
    user_host="${download_host%%:*}"
    ssh_port="${download_host##*:}"
    ssh_cmd=(ssh -o ConnectTimeout=3 -o BatchMode=yes -o StrictHostKeyChecking=no -p "$ssh_port" "$user_host" "exit")
  else
    user_host="$download_host"
    ssh_cmd=(ssh -o ConnectTimeout=3 -o BatchMode=yes -o StrictHostKeyChecking=no "$user_host" "exit")
  fi
  "${ssh_cmd[@]}" 2>/dev/null
  if [ $? -eq 0 ]; then
    available_download_hosts_list+=("$download_host")
    echo "Host $download_host is online."
  else
    echo "Host $download_host is offline or unreachable, skipping."
  fi
  unset user_host ssh_port ssh_cmd
done

if [ ${#available_download_hosts_list[@]} -eq 0 ]; then
  echo "No available download hosts found. Exiting."
  exit 0
fi

declare -a downloaded_archives=()
for download_host in "${available_download_hosts_list[@]}"; do
  if [[ "$download_host" == *:* ]]; then
    user_host="${download_host%%:*}"
    ssh_port="${download_host##*:}"
    rsync_cmd=(rsync -avz --out-format='%n' -e "ssh -p $ssh_port" "$user_host:$download_source_folder/*.tar.bz2" "$archive_files/")
    ssh_rm_cmd=(ssh -p "$ssh_port" "$user_host")
  else
    user_host="$download_host"
    rsync_cmd=(rsync -avz --out-format='%n' -e "ssh" "$user_host:$download_source_folder/*.tar.bz2" "$archive_files/")
    ssh_rm_cmd=(ssh "$user_host")
  fi
  echo "Downloading archives from $download_host..."
  rsync_output=$(mktemp)
  "${rsync_cmd[@]}" > "$rsync_output"
  if [ $? -eq 0 ]; then
    rsync_lines=()
    while IFS= read -r archive_name || [ -n "$archive_name" ]; do
      rsync_lines+=("$archive_name")
    done < "$rsync_output"
    for archive_name in "${rsync_lines[@]}"; do
      if [[ "$archive_name" == *.tar.bz2 ]]; then
        echo "Downloaded: $archive_name"
        downloaded_archives+=("$archive_files/$archive_name")
        "${ssh_rm_cmd[@]}" "rm -f '$download_source_folder/$archive_name'"
      fi
    done
  else
    echo "Rsync failed for $download_host. Skipping removal."
  fi
  rm -f "$rsync_output"
  unset user_host ssh_port rsync_cmd ssh_rm_cmd
done

# --- Process only downloaded archives ---
if [ ${#downloaded_archives[@]} -gt 0 ]; then
    echo "Processing only downloaded archives:"
    for file_path in "${downloaded_archives[@]}"; do
      file=$(basename "$file_path")
      base="${file:0:29}"
      suffix="${file:29}"
      if [[ "$suffix" == _processed_detected.tar.bz2 || "$suffix" == _full_detected.tar.bz2 || "$suffix" == _detected.tar.bz2 ]]; then
        folder_name="$base"
        station_name="${folder_name:0:6}"
        year="${folder_name:7:4}"
        month="${folder_name:11:2}"
        target_path="$data_folder/$year/$month/$station_name/$folder_name"
        if [ ! -d "$target_path" ]; then
          tar_file_name="$file"
          tar_file="$archive_files/$tar_file_name"
          unpack_folder=${tar_file%"_detected.tar.bz2"}
          if [[ "$unpack_folder" == *_full ]]; then
            unpack_folder=${unpack_folder%"_full"}
          fi
          if [[ "$unpack_folder" == *_processed ]]; then
            unpack_folder=${unpack_folder%"_processed"}
          fi
          if [[ "$tar_file" == *processed_detected.tar.bz2 ]]; then
            echo "Archive $tar_file was already processed on remote PC. Unpacking and copying all files to results folder."
            create_folder "$unpack_folder"
            tar -xvf "$tar_file" -C "$unpack_folder" || exit
            results_folder="$processed_files/$(basename "$unpack_folder")"
            create_folder "$results_folder"
            cp -a "$unpack_folder"/. "$results_folder"/
            echo "All files copied to $results_folder."
          else
            create_folder "$unpack_folder"
            echo "Unpack tar : $tar_file to folder: $unpack_folder"
            tar -xvf "$tar_file" -C "$unpack_folder" || exit
            unpack_folder_name=$(basename "$unpack_folder")
            parent_dir="$(dirname "$unpack_folder")"
            missed_fits_files="$parent_dir/${unpack_folder_name}_missed_fits.txt"
            missed_fits_folder="$parent_dir/${unpack_folder_name}_missed_fits"
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
              missed_folder="$archive_files/$unpack_folder_name/missed_fits"
              create_folder "$missed_folder"
              processFits=true
              records=$(wc -l <"$missed_fits_files")
              if [ "$records" -gt 20 ]; then
                echo "Missed fits more than 20 : $records"
                read -r -p "Do you want continue to process missed fits? (y/n) " yn
                      case $yn in
                      [yY])
                        echo "loading $records missed fits"
                        ;;
                      *)
                        echo "Continue without missed fits files"
                        while IFS= read -r missed_fit_file; do
                          fit_file_without_ext="$(echo "$missed_fit_file" | cut -f 1 -d '.')"
                          mv "$archive_files/$unpack_folder_name/FR${fit_file_without_ext:2}.bin" "$missed_folder"
                        done <"$missed_fits_files"
                        processFits=false
                        ;;
                      esac
              fi
              if [ "$processFits" = true ]; then
                echo  "Exists missed fit files, copy from Captured and then press any key"
                open -e "$missed_fits_files"
                read -n 1 -s -r -p "Press any key to continue"
                echo
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
                      cp "$missed_fits_folder/$missed_fit_file" "$missed_folder"
                      fit_file_without_ext="$(echo "$missed_fit_file" | cut -f 1 -d '.')"
                      mv "$archive_files/$unpack_folder_name/FR${fit_file_without_ext:2}.bin" "$missed_folder"
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
            create_folder "$processed_files"
            results_folder="$processed_files/$unpack_folder_name"
            create_folder "$results_folder"
            current_dir=$(pwd)
            . folder_processing.sh "$unpack_folder" "$results_folder"
            cd "$current_dir"
            . photo_processing.sh "$unpack_folder" "$results_folder"
            delete_folder "$missed_fits_folder"
            delete_file "$missed_fits_files"
          fi
          delete_folder "$unpack_folder"
          delete_file "$tar_file"
          echo "Tar processing completed (downloaded)"
          if [ ! -d "$results_folder" ]; then
            echo "Please specify processed folder"
            read -n 1 -s -r -p "Press any key to exit"
            echo
            exit
          fi
          folder_name=$(basename "$results_folder")
          if [ ! "${folder_name:6:1}" = "_" ] || [ ! "${folder_name:15:1}" = "_" ]; then
            echo "Folder should in RMS format : XX0000_yyyymmdd_..."
            read -n 1 -s -r -p "Press any key to exit"
            echo
            exit
          fi
          station_name=${folder_name:0:6}
          year=${folder_name:7:4}
          month=${folder_name:11:2}
          if [ -n "$csv_shared_folders" ]; then
            csv_file="$results_folder/rms/${folder_name}.csv"
            if [ -e "$csv_file" ]; then
              file_size=$(wc -c "$csv_file" | awk '{print $1}')
              if [ "$file_size" -lt 100 ]; then
                echo "csv file is empty: skipping, file: $csv_file"
              else
                IFS=',' read -ra csv_shared_folder_list <<< "$csv_shared_folders"
                for csv_shared_folder in "${csv_shared_folder_list[@]}"; do
                    if [ ! -d "$csv_shared_folder" ]; then
                      echo "Specified csv shared folder doesn't exist : $csv_shared_folder"
                      echo "Copy skipped"
                    else
                      csv_folder="$csv_shared_folder/$year"
                      create_folder "$csv_folder"
                      echo "Copy csv to backup drive: $csv_folder"
                      cp "$csv_file" "$csv_folder"
                      monthly_folder="$csv_folder/monthly/$month"
                      create_folder "$monthly_folder"
                      awk '(NR == 1) || (FNR > 1)' $csv_folder/${station_name}_${year}${month}*.csv > "$monthly_folder/${year}_${month}_${station_name}.csv"
                    fi
                done
              fi
           fi
          fi
          parent_target_folder="$data_folder/$year/$month/$station_name"
          create_folder "$parent_target_folder"
          stacks_folder="$data_folder/$year/$month/$station_name/stacks"
          create_folder "$stacks_folder"
          target_folder="$parent_target_folder/$folder_name"
          meteors_folder="$results_folder/meteors"
          if [ -d "$target_folder" ]; then
            echo "Folder already exists: $target_folder "
            read -n 1 -s -r -p "Press any key to exit"
            echo
            continue
          fi
          stack_file_name=""
          if [ -d "$meteors_folder" ]; then
            echo "copy meteors stack to stacks"
            stack_files=$(find "$meteors_folder" -type f \( -name "*_meteors.png" -o -name "*_meteors.jpg" \))
            if [ -n "$stack_files" ]; then
              stack_file=${stack_files[0]}
              stack_file_name=$(basename "$stack_file")
              if [ ! -f "$stacks_folder/$stack_file_name" ]; then
                echo "Copy stack file : $stack_file_name"
                cp "$stack_file" "$stacks_folder"
              else
                echo "Stack file $stack_file_name already exists, skip copy"
              fi
            fi
          fi
          echo "Move folder to data: $folder_name"
          mv "$results_folder" "$target_folder"
          if [ -n "$backup_folders" ]; then
            IFS=',' read -ra backup_folder_list <<< "$backup_folders"
            for backup_folder in "${backup_folder_list[@]}"; do
              echo "Copy files to backup drive: $backup_folder"
              parent_backup_folder="$backup_folder/$year/$month/$station_name"
              create_folder "$parent_backup_folder"
              cp -R "$target_folder" "$backup_folder/$year/$month/$station_name"
              backup_stacks_folder="$backup_folder/$year/$month/$station_name/stacks"
              create_folder "$backup_stacks_folder"
              if [ -n "$stack_file_name" ] && [ ! -f "$backup_stacks_folder/$stack_file_name" ]; then
                cp "$stacks_folder/$stack_file_name" "$backup_stacks_folder"
              fi
            done
          fi
          # Remove original archive after successful processing
          rm -f "$archive_files/$tar_file_name"
        fi
      fi
    done
fi
