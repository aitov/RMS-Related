#!/bin/bash

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

source_folder_name=$(basename "$source_folder")

cd "$rms_folder" || exit
missed_fits="$source_folder/missed_fits"
echo "Starting StackFFs"
python -m Utils.StackFFs -s -b -x "$source_folder" png
echo "Starting FF to Image"
python -m Utils.BatchFFtoImage "$source_folder" jpg
if [ -d "$missed_fits" ]; then
  python -m Utils.BatchFFtoImage "$missed_fits" jpg
fi
read -r -p "Do you want to run TrackStack? (y/n) " yn
case $yn in
[yY])
  echo "Starting TrackStack"
  python -m Utils.TrackStack "$source_folder" -c "$source_folder/.config" -x
esac

meteors_folder="$results_folder/meteors"

create_folder "$meteors_folder"

find "$source_folder" -type f -name "FF_*.jpg" -print0 |
  while IFS= read -r -d '' file; do
    parent_dir="$(dirname "$file")"
    if [ "$parent_dir" = "$missed_fits" ]; then
       cp "$file" "$results_folder/missed_fits"
    else
      cp "$file" "$meteors_folder"
    fi
  done

find "$source_folder" -type f -name "*_track_stack.jpg" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$meteors_folder"
  done

find "$source_folder" -type f -name "*_meteors.png" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$meteors_folder"
  done

find "$source_folder" -type f -name "*.csv" -print0 |
  while IFS= read -r -d '' file; do
    cp "$file" "$results_folder"
    cp "$file" "$results_folder/rms"
  done

