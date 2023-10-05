#!/bin/bash
# Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/
# Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent

. veye_lib_init.sh

cd ~/source/raspberrypi/i2c_cmd/bin

./veye_mipi_i2c.sh -r -f videoformat
./veye_mipi_i2c.sh -r -f agc
./veye_mipi_i2c.sh -r -f ircutdir
./veye_mipi_i2c.sh -r -f mshutter
./veye_mipi_i2c.sh -r -f cameramode
./veye_mipi_i2c.sh -r -f nodf
./veye_mipi_i2c.sh -r -f capture
./veye_mipi_i2c.sh -r -f csienable
./veye_mipi_i2c.sh -r -f aespeed
./veye_mipi_i2c.sh -r -f contrast
./veye_mipi_i2c.sh -r -f saturation
./veye_mipi_i2c.sh -r -f wdrtargetbr
./veye_mipi_i2c.sh -r -f wdrbtargetbr
./veye_mipi_i2c.sh -r -f awbgain
./veye_mipi_i2c.sh -r -f wbmode
./veye_mipi_i2c.sh -r -f mwbgain
./veye_mipi_i2c.sh -r -f yuvseq
./veye_mipi_i2c.sh -r -f sharppen
./veye_mipi_i2c.sh -r -f irtrigger
./veye_mipi_i2c.sh -r -f lowlight  # fixed 25 fps
./veye_mipi_i2c.sh -r -f wdrmode  # back light mode off
./veye_mipi_i2c.sh -r -f denoise
./veye_mipi_i2c.sh -r -f daynightmode
./veye_mipi_i2c.sh -r -f new_expmode
./veye_mipi_i2c.sh -r -f new_mshutter # fixed 40 ms
./veye_mipi_i2c.sh -r -f new_mgain	# 0.1 - 0.3 # between 20 and 25
./veye_mipi_i2c.sh -r -f brightness
./veye_mipi_i2c.sh -r -f auto_shutter_max
./i2c_read 10 0x3b 0x0014 1

read -n 1 -s -r -p "Press any key to exit"
echo




