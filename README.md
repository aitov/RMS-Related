# RMS-Related
Raspberry Pi Meteor Software scripts

Useful scripts for local or remote (directly on Raspberry Pi) processing meteors results:
1. Generates mp4 from FR bin files;
2. Creates folder for manual fireball detection for SkyFit2;
3. Run bin viewer for meteors confirmation;
4. Creates meteors stacks and jpg for detected meteors;
5. Collects all generated results to one folder for local download;

# Configuration
If you are using heatsink with fans then Pi leds creates polluting light in box (red and green)

Also, if connected ethernet cable it also has 2 leds (green and yellow) which produces some light  

You could to turn off power and activity indicator leds by configuration file.

Edit config.txt:
```Shell
sudo nano /boot/config.txt
```
Add this line to turn off red led:
```
dtparam=pwr_led_activelow=off
```
Add this line to turn off green led:
```
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off
```
Add this lines to disable ethernet port leds:
```
dtparam=eth_led0=4
dtparam=eth_led1=4
```

Reboot

# Camera VEYE-MIPI-IMX462 configuration
Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/

Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent

Download config util script:
```
devices/VEYE-MIPI-IMX462/veye_lib_init.sh
```

Read camera current config script:
```
devices/VEYE-MIPI-IMX462/read_camera_config.sh
```

My camera config
```
devices/VEYE-MIPI-IMX462/camera_config.txt
```

Set to camera my config script:
```
devices/VEYE-MIPI-IMX462/configure_camera.sh
```
