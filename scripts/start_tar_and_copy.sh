#!/bin/bash
. activate.sh

IFS=',' read -ra ssh_hosts_list <<< "$ssh_hosts"
for ssh_host in "${ssh_hosts_list[@]}"; do
  cd "$rms_related_folder/scripts"
  . start_tar_processing.sh

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


  if [ -n "$csv_shared_folder" ]; then
    if [ ! -d "$csv_shared_folder" ]; then
      echo "Specified csv shared folder doesn't exist : $csv_shared_folder"
      echo "Copy skipped"
    else
      csv_file="$results_folder/rms/${folder_name}.csv"
      if [ -e "$csv_file" ]; then
        # skip empty (only with header) csv files
        file_size=$(wc -c "$csv_file" | awk '{print $1}')
        if [ $file_size -lt 100 ]; then
          echo "csv file is empty: skipping, file: $csv_file"
        else
          csv_folder="$csv_shared_folder/$year"
          create_folder "$csv_folder"
          cp "$csv_file" "$csv_folder"
          # merge all csv to one monthly folder
          monthly_folder="$csv_folder/monthly/$month"
          create_folder "$monthly_folder"
          awk '(NR == 1) || (FNR > 1)' $csv_folder/${station_name}_${year}${month}*.csv > "$monthly_folder/${year}_${month}_${station_name}.csv"
        fi
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
    stack_files=$(find "$meteors_folder" -type f -name "*_meteors.png")
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

  if [ -n "$backup_folder" ]; then
    echo "Copy files to backup drive"
    parent_backup_folder="$backup_folder/$year/$month/$station_name"
    create_folder "$parent_backup_folder"

    cp -R "$target_folder" "$backup_folder/$year/$month/$station_name"

    backup_stacks_folder="$backup_folder/$year/$month/$station_name/stacks"

    create_folder "$backup_stacks_folder"

    if [ -n "$stack_file_name" ] && [ ! -f "$backup_stacks_folder/$stack_file_name" ]; then
      cp "$stacks_folder/$stack_file_name" "$backup_stacks_folder"
    fi
  fi

  if [ -n "$logs_folder" ]; then
     if ssh "$ssh_host" -p "$ssh_port" "[ -d ${logs_folder} ]"; then
        result_log_folder="$data_folder/log"
        echo "$result_log_folder"
        create_folder "$result_log_folder"
        rsync -r -e "ssh -p $ssh_port" "$ssh_host:$logs_folder" "$data_folder"
        if [ -n "$backup_folder" ]; then
          create_folder "$backup_folder/log"
          cp -r "$result_log_folder" "$backup_folder"
        fi
     fi
  fi

done
