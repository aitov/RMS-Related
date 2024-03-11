#!/bin/bash
echo "Focus camera"
i2cBus=6
source ~/vRMS/bin/activate
cd ~/source/raspberrypi/i2c_cmd/bin
# Set color mode
./veye_mipi_i2c.sh -b $i2cBus -w -f daynightmode -p1 0xFF
cd ~/source/RMS-Related/devices/VEYE-MIPI-IMX462

python FocusingHelper.py

cd ~/source/raspberrypi/i2c_cmd/bin
# Rollback black and white mode
./veye_mipi_i2c.sh -b $i2cBus -w -f daynightmode -p1 0xFE


read -n 1 -s -r -p "Press any key to exit"
echo