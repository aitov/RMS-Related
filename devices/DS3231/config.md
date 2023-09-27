# RTC Module configuration
Manual on RMS Github (for Pi 3 but will work for Pi 4) :
https://github.com/CroatianMeteorNetwork/RMS/blob/master/Guides/rpi3_rtc_setup.md

But for raspberry Pi 4 you could skip items:
6. Install the NTP daemon and
7. Edit /etc/rc.local and add the hwclock command above the line that says exit 0

As it already covered by service : timedatectl

To get status run in terminal:

```Shell
timedatectl
```
Output will be similar to :
```
Local time: Wed 2023-09-27 18:21:13 UTC
Universal time: Wed 2023-09-27 18:21:13 UTC
RTC time: Wed 2023-09-27 18:21:13
Time zone: Etc/UTC (UTC, +0000)
System clock synchronized: yes
NTP service: active
RTC in local TZ: no
```

if clock synchronised and NPT service inactive like:
```
System clock synchronized: yes
NTP service: inactive
``` 
it means ntp lib installed and used ntpd service instead, if you want use embedded service - uninstall ntp 

Also in case of manual time set, it could be enabled by command: 
```Shell
sudo timedatectl set-ntp on
```
  

Useful  commands for checking rtc after connection to Pi

Check if RTC module could be detected   
```Shell
sudo i2cdetect -y 1
```

Read time from RTC module
```Shell
sudo hwclock -r
```
Set current time to RTC module
```Shell
sudo hwclock -w
```