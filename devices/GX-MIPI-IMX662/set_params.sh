#!/bin/bash

# set 4 or 6 according to the i2c bus you use
i2cBus=6

cd ~/source/raspberrypi_v4l2/gx_i2c_tools

./gx_mipi_i2c.sh -w fps 30 -b $i2cBus
./gx_mipi_i2c.sh -w expmode 0 -b $i2cBus 
./gx_mipi_i2c.sh -w metime 33333 -b $i2cBus
./gx_mipi_i2c.sh -w mgain 40 -b $i2cBus
./gx_mipi_i2c.sh -w denoise_strength_3D 40 -b $i2cBus
./gx_mipi_i2c.sh -w denoise_strength_2D 0 -b $i2cBus
./gx_mipi_i2c.sh -w sharppen 0 -b $i2cBus
./gx_mipi_i2c.sh -w gamma_index 5 -b $i2cBus

./gx_mipi_i2c.sh -r fps -b $i2cBus
./gx_mipi_i2c.sh -r expmode -b $i2cBus
./gx_mipi_i2c.sh -r metime -b $i2cBus
./gx_mipi_i2c.sh -r mgain -b $i2cBus
./gx_mipi_i2c.sh -r denoise_strength_3D -b $i2cBus
./gx_mipi_i2c.sh -r denoise_strength_2D -b $i2cBus
./gx_mipi_i2c.sh -r sharppen -b $i2cBus
./gx_mipi_i2c.sh -r gamma_index -b $i2cBus
