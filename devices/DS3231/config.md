# RTC Module configuration
Manual on RMS Github (for Pi 3 but will work for Pi 4) :
https://github.com/CroatianMeteorNetwork/RMS/blob/master/Guides/rpi3_rtc_setup.md

Some commands for checking rtc after connection to Pi

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