#!/bin/bash
# Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/
# Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent

cd ~/source/raspberrypi/i2c_cmd/bin
i2cBus=6

#PAL	PAL(50Hz)	25fps
./veye_mipi_i2c.sh -b $i2cBus -w -f videoformat -p1 NTSC
#0x0	sharppen disable
./veye_mipi_i2c.sh -b $i2cBus -w -f sharppen -p1 0
#Polarity setting of the day/night switching external trigger mode pin.
#0x1	Reversed.
./veye_mipi_i2c.sh -b $i2cBus -w -f irtrigger -p1 0xfe
#0x0F	1/25*(FRAME RATE)
#0x11	1/30*(FRAME RATE)
#0x00	Fixed frame rate (25/30)
# need to be check all 3 parameters
./veye_mipi_i2c.sh -b $i2cBus -w -f lowlight -p1 0  # fixed 25 fps
#0x00	Back Light Mode OFF
./veye_mipi_i2c.sh -b $i2cBus -w -f wdrmode -p1 0  # back light mode off
#0x02	NR 2D Mode = OFF; NR 3D Mode = MIDDLE
./veye_mipi_i2c.sh -b $i2cBus -w -f denoise -p1 0x02
#0xFE	Black&White Mode
./veye_mipi_i2c.sh -b $i2cBus -w -f daynightmode -p1 0xfe	# B&W mode
# Uncomment this if need manual settings same as for IP camera (auto brightness will be off and only in dark picture will be visible )
# Whether the new version of manual exposure is enabled.
./veye_mipi_i2c.sh -b $i2cBus -w -f new_expmode -p1 0
#./veye_mipi_i2c.sh -b $i2cBus -w -f new_mshutter -p1 40000 # fixed 40 ms
#./veye_mipi_i2c.sh -b $i2cBus -w -f new_mgain -p1 23	# 0.1 - 0.3 # between 20 and 25
# 0x41 1/30 (25)
./veye_mipi_i2c.sh -b $i2cBus-w -f mshutter -p1 0x41
./veye_mipi_i2c.sh -b $i2cBus -w -f brightness -p1 0x07
#./veye_mipi_i2c.sh -b $i2cBus -w -f csienable -p1 0x0
# special code for sky imaging, to turn automatic bad point correction off
./i2c_write $i2cBus 0x3b 0x0007 0xFE
./i2c_write $i2cBus 0x3b 0x0010 0xDB
./i2c_write $i2cBus 0x3b 0x0011 0x9F
./i2c_write $i2cBus 0x3b 0x0012 0x00
./i2c_write $i2cBus 0x3b 0x0013 0x00
./i2c_read $i2cBus 0x3b 0x0014 1
./veye_mipi_i2c.sh -b $i2cBus -w -f paramsave

read -n 1 -s -r -p "Press any key to exit"
echo