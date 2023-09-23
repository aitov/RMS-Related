#!/bin/sh
# Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/
# Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent


cd /home/pi/source/RMS/raspberrypi/i2c_cmd/bin/veye_mipi_i2c.sh -r -f brightness
chmod 777 *.sh
sleep 1
#PAL	PAL(50Hz)	25fps
./veye_mipi_i2c.sh -w -f videoformat -p1 PAL
sleep 3
#0x0	sharppen disable
./veye_mipi_i2c.sh -w -f sharppen -p1 0
sleep 1
#Polarity setting of the day/night switching external trigger mode pin.
#0x1	Reversed.
./veye_mipi_i2c.sh -w -f irtrigger -p1 1
sleep 1
#0x0F	1/25*(FRAME RATE)
#0x11	1/30*(FRAME RATE)
#0x00	Fixed frame rate (25/30)
# need to be check all 3 parameters
./veye_mipi_i2c.sh -w -f lowlight -p1 0  # fixed 25 fps
sleep 1
#0x00	Back Light Mode OFF
./veye_mipi_i2c.sh -w -f wdrmode -p1 0  # back light mode off
sleep 1
#0x0C	NR 2D Mode =HIGH; NR 3D Mode = OFF
./veye_mipi_i2c.sh -w -f denoise -p1 0xc
sleep 1
#0xFE	Black&White Mode
./veye_mipi_i2c.sh -w -f daynightmode -p1 0xfe	# B&W mode
sleep 1
# Uncomment this if need manual settings same as for IP camera (auto brightness will be off and only in dark picture will be visible )
# Whether the new version of manual exposure is enabled.
#./veye_mipi_i2c.sh -w -f new_expmode -p1 1
#sleep 1
#./veye_mipi_i2c.sh -w -f new_mshutter -p1 40000 # fixed 40 ms
#sleep 1
#./veye_mipi_i2c.sh -w -f new_mgain -p1 23	# 0.1 - 0.3 # between 20 and 25
sleep 1
./veye_mipi_i2c.sh -w -f brightness -p1 0
sleep 1
# special code for sky imaging, to turn automatic bad point correction off
./i2c_write 10 0x3b 0x0007 0xFE
./i2c_write 10 0x3b 0x0010 0xDB
./i2c_write 10 0x3b 0x0011 0x9F
./i2c_write 10 0x3b 0x0012 0x00
./i2c_write 10 0x3b 0x0013 0x00
sleep 1
./i2c_read 10 0x3b 0x0014 1
./veye_mipi_i2c.sh -w -f paramsave
sleep 1
# make sure the params are correct
./veye_mipi_i2c.sh -r -f new_expmode
./veye_mipi_i2c.sh -r -f new_mgain
./veye_mipi_i2c.sh -r -f new_mshutter



