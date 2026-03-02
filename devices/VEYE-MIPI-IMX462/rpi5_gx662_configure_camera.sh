#!/bin/bash

cd ~/source/raspberrypi_v4l2/gx_i2c_tools
i2cBus=4

./gx_mipi_i2c.sh -w fps 30 -b $i2cBus # 30 fps

# in case if manual gain
#./gx_mipi_i2c.sh - w mgain  -b $i2cBus # need try : on imx462 : 29.4
read -n 1 -s -r -p "Press any key to exit"
echo