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

# Add information about sensor values to .conkyrc file widget
```
${font Arial:bold:size=10}${color Tan2}OUTSIDE SENSOR ${color DarkSlateGray}${hr 2}
$font${color DimGray}Temperature: $alignr ${texeci 10 /home/pi/source/RMS-Related/devices/DHT22/dht22_read.sh temperature} C
$font${color DimGray}Humidity: $alignr ${texeci 10 /home/pi/source/RMS-Related/devices/DHT22/dht22_read.sh humidity}%
```




