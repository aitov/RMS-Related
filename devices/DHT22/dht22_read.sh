#!/bin/bash
source /home/pi/vRMS/bin/activate
python /home/pi/source/RMS-Related/devices/DHT22/ReadValues.py $1
exit 0