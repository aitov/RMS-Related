#!/bin/bash

echo "Starting ShowerAssociation"
cd ~/home/projects/RMS || exit
# Pi
#source ~/vRMS/bin/activate
# Intel
#source ~/anaconda3/envs/RMS/bin/activate
# M2
source ~/.conda/envs/rms/bin/activate

# M2
confirmed_files=~/home/pi/RMS_data/ConfirmedFiles

#capdir=$(ls -1 /home/pi/Desktop/RMS_data/ConfirmedFiles/ | tail -1)
capdir=UA0003_20230904_171233_737111

echo "cd ~/source/RMS"

python Utils/ShowerAssociation.py -c.config "$confirmed_files/$capdir/FTPdetectinfo_$capdir.txt" -x
echo "StackFFs"
python -m Utils.StackFFs -s -b -x "$confirmed_files/$capdir" png
echo "TrackStack"
python -m Utils.TrackStack "$confirmed_files/$capdir" -x

python -m Utils.BatchFFtoImage -t "$confirmed_files/$capdir" jpg

read -n 1 -s -r -p "Press any key to exit"
echo