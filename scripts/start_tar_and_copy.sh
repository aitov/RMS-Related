#!/bin/bash

# start processing
#. start_folder_processing.sh

processed_folder=~/home/pi/RMS_data/ProcessedFiles/UA0004_20230929_163816_494732
data_folder=~/home/pi/data
backup_folder=/Volumes/Data/pi/data

if [ ! -d "$processed_folder" ]; then
  echo "Please specify processed folder"
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi

folder_name=$(basename "$processed_folder")

if [ ! "${folder_name:6:1}" = "_" ] && [ ! "${folder_name:6:1}" = "_" ]; then
  echo "Folder should in RMS format : XX0000_yyyymmdd_..."
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
fi


station_name=${folder_name:0:6}
year=${folder_name:7:4}
month=${folder_name:11:2}

parent_target_folder="$data_folder/$year/$month/$station_name"
if [ ! -d "$parent_target_folder" ]; then
  mkdir -p "$parent_target_folder"
fi

stacks_folder="$data_folder/$year/$month/$station_name/stacks"
if [ ! -d "$stacks_folder" ]; then
  mkdir "$stacks_folder"
fi

target_folder="$parent_target_folder/$folder_name"
meteors_folder="$processed_folder/meteors"


if [ -d "$target_folder" ]; then
  echo "Folder already exists: $target_folder "
  read -n 1 -s -r -p "Press any key to exit"
  echo
  exit
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
mv "$processed_folder" "$target_folder"

if [ -n "$backup_folder" ]; then
  echo "Copy files to backup drive"
  parent_backup_folder="$backup_folder/$year/$month/$station_name"
  if [ ! -d "$parent_backup_folder" ]; then
    mkdir -p "$parent_backup_folder"
  fi

  cp -R "$target_folder" "$backup_folder/$year/$month/$station_name"

  backup_stacks_folder="$backup_folder/$year/$month/$station_name/stacks"


  if [ ! -d "$backup_stacks_folder" ]; then
    mkdir "$backup_stacks_folder"
  fi

  if [ -n "$stack_file_name" ] && [ ! -f "$backup_stacks_folder/$stack_file_name" ]; then
    cp "$stacks_folder/$stack_file_name" "$backup_stacks_folder"
  fi
fi



