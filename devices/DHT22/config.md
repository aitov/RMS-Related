# Log DHT22 values to CSV file at raspberry start
Edit rc.local file:
```Shell
sudo nano /etc/rc.local
```
Add this line:
```
sudo /home/pi/source/RMS-Related/devices/DHT22/dht22_log.sh &
```
Save and reboot

# Add information about sensor values to conkyrc widget
TBD




