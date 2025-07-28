#!/bin/bash
# Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/
# Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent

cd ~/source/raspberrypi/i2c_cmd/bin
i2cBus=6
./veye_mipi_i2c.sh -b $i2cBus -r -f videoformat
./veye_mipi_i2c.sh -b $i2cBus -r -f agc
./veye_mipi_i2c.sh -b $i2cBus -r -f ircutdir
./veye_mipi_i2c.sh -b $i2cBus -r -f mshutter
./veye_mipi_i2c.sh -b $i2cBus -r -f cameramode
./veye_mipi_i2c.sh -b $i2cBus -r -f nodf
./veye_mipi_i2c.sh -b $i2cBus -r -f capture
./veye_mipi_i2c.sh -b $i2cBus -r -f csienable
./veye_mipi_i2c.sh -b $i2cBus -r -f aespeed
./veye_mipi_i2c.sh -b $i2cBus -r -f contrast
./veye_mipi_i2c.sh -b $i2cBus -r -f saturation
./veye_mipi_i2c.sh -b $i2cBus -r -f wdrtargetbr
./veye_mipi_i2c.sh -b $i2cBus -r -f wdrbtargetbr
./veye_mipi_i2c.sh -b $i2cBus -r -f awbgain
./veye_mipi_i2c.sh -b $i2cBus -r -f wbmode
./veye_mipi_i2c.sh -b $i2cBus -r -f mwbgain
./veye_mipi_i2c.sh -b $i2cBus -r -f yuvseq
./veye_mipi_i2c.sh -b $i2cBus -r -f sharppen
./veye_mipi_i2c.sh -b $i2cBus -r -f irtrigger
./veye_mipi_i2c.sh -b $i2cBus -r -f lowlight  # fixed 25 fps
./veye_mipi_i2c.sh -b $i2cBus -r -f wdrmode  # back light mode off
./veye_mipi_i2c.sh -b $i2cBus -r -f denoise
./veye_mipi_i2c.sh -b $i2cBus -r -f daynightmode
./veye_mipi_i2c.sh -b $i2cBus -r -f new_expmode
./veye_mipi_i2c.sh -b $i2cBus -r -f new_mshutter # fixed 40 ms
./veye_mipi_i2c.sh -b $i2cBus -r -f new_mgain	# 0.1 - 0.3 # between 20 and 25
./veye_mipi_i2c.sh -b $i2cBus -r -f brightness
./veye_mipi_i2c.sh -b $i2cBus -r -f auto_shutter_max
./veye_mipi_i2c.sh -b $i2cBus -r -f mshutter

./i2c_read $i2cBus 0x3b 0x0014 1

read -n 1 -s -r -p "Press any key to exit"
echo




