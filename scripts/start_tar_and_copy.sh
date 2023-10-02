#!/bin/bash
. activate.sh

IFS=',' read -ra ssh_hosts_list <<< "$ssh_hosts"
for ssh_host in "${ssh_hosts_list[@]}"; do
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

parent_target_folder="$data_folder/$year/$month/$station_name"
if [ ! -d "$parent_target_folder" ]; then
  mkdir -p "$parent_target_folder"
fi

stacks_folder="$data_folder/$year/$month/$station_name/stacks"
if [ ! -d "$stacks_folder" ]; then
  mkdir "$stacks_folder"
fi

target_folder="$parent_target_folder/$folder_name"
meteors_folder="$results_folder/meteors"

done



