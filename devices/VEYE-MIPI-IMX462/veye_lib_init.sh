#!/bin/bash

cd ~
if [ ! -d "source" ]; then
  mkdir "source"
fi

cd "source"

if [ ! -d "raspberrypi" ]; then
  echo "Checkout raspberrypi repository"
  git clone https://github.com/veyeimaging/raspberrypi.git
fi
# TODO pull

cd "raspberrypi/i2c_cmd/bin"

find . -type f -name "*.*" -print0 |
  while IFS= read -r -d '' sh_file; do
    if [[ ! -x "$sh_file" ]]; then
      echo "Make executable : $sh_file"
      chmod +x "$sh_file"
    fi
  done