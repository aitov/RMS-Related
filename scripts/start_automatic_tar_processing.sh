#!/bin/bash
. activate.sh

echo "Starting Tar processing"

archive_files="$home_folder/RMS_data/ArchivedFiles"
processed_files="$home_folder/RMS_data/ProcessedFiles"

pi_user=${ssh_host%"@"*}

# path on RPi
remote_archive_files="/home/$pi_user/RMS_data/ArchivedFiles"
remote_captured_files="/home/$pi_user/RMS_data/CapturedFiles"

if [ -n "$ssh_host" ]; then
    ssh_port=22
    # if custom port specified - extract it
    if [[ $ssh_host == *":"* ]]; then
      ssh_port=${ssh_host#*":"}
      ssh_host=${ssh_host%":$ssh_port"}
    fi

    # List all tar.bz2 files and check for missing processed archives
    all_tar_files=( $(ssh "$ssh_host" -p "$ssh_port" "cd $remote_archive_files && ls *.tar.bz2 2>/dev/null" ) )
    archive_bases=()
    for file in "${all_tar_files[@]}"; do
      base="${file:0:29}"
      suffix="${file:29}"
      if [[ "$suffix" == _processed_detected.tar.bz2 || "$suffix" == _full_detected.tar.bz2 || "$suffix" == _detected.tar.bz2 ]]; then
        if [[ ! " ${archive_bases[@]} " =~ " ${base} " ]]; then
          archive_bases+=("$base")
        fi
      fi
    done
    # Filter archive_bases to only new items (not already processed/copied)
    filtered_archive_bases=()
    for base in "${archive_bases[@]}"; do
      folder_name="$base"
      station_name="${folder_name:0:6}"
      year="${folder_name:7:4}"
      month="${folder_name:11:2}"
      target_path="$data_folder/$year/$month/$station_name/$folder_name"
      if [ ! -d "$target_path" ]; then
        echo "New archive found: $base"
        filtered_archive_bases+=("$base")
      fi
    done

    processed_archives=()
    for base in "${filtered_archive_bases[@]}"; do
      if [[ " ${all_tar_files[@]} " =~ " ${base}_processed_detected.tar.bz2 " ]]; then
        processed_archives+=("${base}_processed_detected.tar.bz2")
      elif [[ " ${all_tar_files[@]} " =~ " ${base}_full_detected.tar.bz2 " ]]; then
        processed_archives+=("${base}_full_detected.tar.bz2")
        echo "Missed _processed_detected for $base, adding _full_detected"
      elif [[ " ${all_tar_files[@]} " =~ " ${base}_detected.tar.bz2 " ]]; then
        processed_archives+=("${base}_detected.tar.bz2")
        echo "Missed _processed_detected for $base, adding _detected"
      fi
    done
    current_dir=$(pwd)
    # Print the list of processed archive file names
    for tar_file_name in "${processed_archives[@]}"; do
      echo "Processing $archive_file"
      rsync --progress -e "ssh -p $ssh_port" "$ssh_host:$remote_archive_files/$tar_file_name"  "$archive_files"

      tar_file="$archive_files/$tar_file_name"
      unpack_folder=${tar_file%"_detected.tar.bz2"}
      # remove full for custom upload mode
      if [[ "$unpack_folder" == *_full ]]; then
        unpack_folder=${unpack_folder%"_full"}
      fi
      # remove processed for already processed
      if [[ "$unpack_folder" == *_processed ]]; then
        unpack_folder=${unpack_folder%"_processed"}
      fi

      # Check if tar file is already processed on remote PC
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
            # copy from station directly and move to missed_fits folder
            if [ -n "$ssh_host" ]; then
              while IFS= read -r missed_fit_file; do
                rsync --progress -e "ssh -p $ssh_port" "$ssh_host:$remote_captured_files/$unpack_folder_name/$missed_fit_file" "$missed_folder"
                fit_file_without_ext="$(echo "$missed_fit_file" | cut -f 1 -d '.')"
                mv "$archive_files/$unpack_folder_name/FR${fit_file_without_ext:2}.bin" "$missed_folder"
              done <"$missed_fits_files"
            else
              # Waiting for manual copy
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
        cd "$current_dir"
        . folder_processing.sh "$unpack_folder" "$results_folder"
        cd "$current_dir"
        . photo_processing.sh "$unpack_folder" "$results_folder"
        delete_folder "$missed_fits_folder"
        delete_file "$missed_fits_files"
      fi
      # cleanup files and folders
      delete_folder "$unpack_folder"
      delete_file "$tar_file"
      #read -n 1 -s -r -p "Press any key to exit"
      echo "Tar processing completed"

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
          # skip empty (only with header) csv files
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
                  # merge all csv to one monthly folder
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

      # Refactored backup section to support multiple backup locations
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

    done
fi

