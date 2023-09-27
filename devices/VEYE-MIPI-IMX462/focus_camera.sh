#!/bin/bash

echo "Show camera"

source ~/vRMS/bin/activate
cd ~/source/raspberrypi/i2c_cmd/bin
# Set color mode
./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFF
cd ~/source/RMS-Related/devices/VEYE-MIPI-IMX462

python FocusingHelper.py

cd ~/source/raspberrypi/i2c_cmd/bin
# Set black and white mode
./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFE
sleep 1
