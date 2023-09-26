#!/bin/bash

echo "Show camera"

source ~/vRMS/bin/activate
cd /home/pi/source/raspberrypi/i2c_cmd/bin
./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFF
cd ~/source/RMS-Related/camera
python FocusingHelper.py
cd /home/pi/source/raspberrypi/i2c_cmd/bin
./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFE
sleep 1

#read -p "Press any key to continue... "

#$SHELL
