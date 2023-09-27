#!/bin/bash
# Start script which need copy to Desktop of Raspberry Pi and run in order to fetch/update project and start processing
# 1. Checks if RMS-Related project exist in user home folder (/home/pi)
# 2. If not - checkout it from Github
# 3. If yes - update project
# 4. Checks if all sh files have executable permission and add if no
# 5. Starts start_folder_processing.sh script form ~/RMS-Related/scripts folder

cd ~

if [ ! -d "source" ]; then
  mkdir "source"
fi

cd "source"

if [ ! -d "RMS-Related" ]; then
  echo "Checkout RMS-Related"
  git clone https://github.com/aitov/RMS-Related.git
  cd "RMS-Related/scripts"
  find . -type f -name "*.sh" -print0 |
    while IFS= read -r -d '' sh_file; do
      if [[ ! -x "$sh_file" ]]; then
        echo "Make executable : $sh_file"
        chmod +x "$sh_file"
      fi
    done
else
  cd "RMS-Related"
  git reset --hard HEAD
  git pull
  cd "scripts"
fi

. start_folder_processing.sh
