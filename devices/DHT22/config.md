# This sensor is optional for RMS station! 

##It is just for collecting temperature statistics inside box which is different from CPU temperature

### Code modification

You need update in `LogValues.py` and `ReadValues.py` pin where connected sensor (D10 in my case)
```Python
# Need specify pin where DHT22 connected
from board import D10
```

### Log DHT22 values to CSV file at raspberry start
Edit rc.local file:
```Shell
sudo nano /etc/rc.local
```
Add this line:
```
# start log outside sensor values
bash /home/pi/source/RMS-Related/devices/DHT22/dht22_log.sh &
```
Save and reboot

Check status after restart and make sure that no errors:
```Shell
systemctl status rc-local.service
```


Logs will be available in:

`/home/pi/logs/<mm.yyyy>_outside_sensor_values.csv`

files split by month and data logged for every 5 min

### Add information about sensor values to conkyrc file widget

Edit: `/home/pi/.conkyrc`
And add at the end next strings:

```
${font Arial:bold:size=10}${color Tan2}OUTSIDE SENSOR ${color DarkSlateGray}${hr 2}
$font${color DimGray}Temperature: $alignr ${texeci 10 /home/pi/source/RMS-Related/devices/DHT22/dht22_read.sh temperature} C
$font${color DimGray}Humidity: $alignr ${texeci 10 /home/pi/source/RMS-Related/devices/DHT22/dht22_read.sh humidity}%
```




