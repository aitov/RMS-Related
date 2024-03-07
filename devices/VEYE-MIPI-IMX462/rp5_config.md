# VEYE-MIPI-IMX462 on RPi5
For RPi5 with Bookworm 64bit camera required different steps to driver install and configuration than on RPi4

# Drivers install
Drivers download manual could be found on: https://wiki.veye.cc/index.php/V4L2_mode_for_Raspberry_Pi

For driver install we need use script with parameter `veyecam2m`:
```Shell
sudo ./install_driver_rpi5.sh veyecam2m
```

# Init camera during system start

On RPi5 current version of driver requires execution script to make camera available for apps, it could be done by execution script:
```Shell
./media_setting_rpi5.sh veyecam2m
```
It needs add to `rc.local` file to execute during system start

Execute:
```Shell
sudo nano /etc/rc.local
```
Add full path to script with parameter : `veyecam2m`, example:
```
/home/rms/source/raspberrypi_v4l2/rpi5_scripts/media_setting_rpi5.sh veyecam2m
```
before: `exit 0`

After system start need make sure that script executed correctly by command:
```Shell
sudo systemctl status rc-local.service
```
It should look like : 
```
rc.local[1549]: This is a Raspberry Pi 5.
rc.local[1549]: camera is YUV type
rc.local[1549]: camera name veyecam2m; width 1920; height 1080; media_fmt UYVY8_1X16; pixel_fmt UYVY
rc.local[1549]: veyecam2m 4 NOT FOUND
rc.local[1549]: CAM0 probed:  media device is  /dev/media2
rc.local[1549]: set CAM0 finish, plese get frame from /dev/video0 and use /dev/v4l-subdev2 for camera
```

# Configuration

On RPi5 we have 2 MIPI ports and we need specify bus (4 or 6) by variable: `i2cBus`

current my configuration has it = 6 (on RPi4 it is 10 and don't need it specify)

To configure camera with my settings need execute script:
```Shell
./rpi5_configure_camera.sh
```
For Bookworm 64bit I had to compile i2c_write and i2c_read to make configration work (for version from repository I got errors)

To read configuration need execute script:
```Shell
./rp5_read_camera_config.sh
```
The result of read configuration could be compared with:
```
rpi5_camera_config.txt
```



