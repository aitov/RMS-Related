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

# Static Ip configuration
For RPi4 it could be done by /etc/dhcp.config file

For RPi5 need make next steps:

Check current network settings by command:
```
ip r
```
Check net device name by command:
```
nmcli connection show
```
Edit interfaces file by command:
```
sudo nano /etc/network/interfaces
```
Add static ip configuration like:
```
auto lan0
iface lan0 inet static
address 192.168.1.100 # Enter your desired static IP address
netmask 255.255.255.0 # Subnet mask
gateway 192.168.1.1 # Default gateway
dns-nameservers 192.168.1.1 # DNS server(s)
```
Save file and reboot 





# Camera VEYE-MIPI-IMX462 configuration
Drivers: https://wiki.veye.cc/index.php/V4L2_mode_for_Raspberry_Pi

Manual: https://wiki.veye.cc/index.php/VEYE-MIPI-290/327_i2c/

Forum: https://forum.veye.cc/topic/366/veye-mipi-imx462-manual-gain-not-consistent

For RPi5 camera config please refer to file:
```
devices/VEYE-MIPI-IMX462/rp5_config.md
```

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

