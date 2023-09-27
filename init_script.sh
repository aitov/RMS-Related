#!/bin/bash
cd ~

if [ ! -d "source" ]; then
  mkdir "source"
fi

cd "source"

if [ ! -d "RMS-Related" ]; then
  echo "Checkout RMS-Related"
  git clone https://github.com/aitov/RMS-Related.git
  git checkout dev
  cd "RMS-Related"
else
  cd "RMS-Related"
  git reset --hard HEAD
  git pull
fi

find . -type f -name "*.sh" -print0 |
  while IFS= read -r -d '' sh_file; do
    if [[ ! -x "$sh_file" ]]; then
      echo "Make executable : $sh_file"
      chmod +x "$sh_file"
    fi
  done

cd "scripts"
find . -type f -name "*.sh" -print0 |
    while IFS= read -r -d '' sh_file; do
      if [[ ! -x "$sh_file" ]]; then
        echo "Make executable : $sh_file"
        chmod +x "$sh_file"
      fi
    done

. create_desktop_links.sh


