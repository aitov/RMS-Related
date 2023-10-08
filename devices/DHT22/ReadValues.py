
# Script to display current values of DHT22 sensor, used by conkyrc widget

import adafruit_dht
import time
# Need specify pin where DHT22 connected
from board import D10
import sys


def readValue(sensor):
    # Need re-read values in case if empty
    while True:
        try:
            dht_device = adafruit_dht.DHT22(D10, use_pulseio=False)

            if sensor == "temperature":
                temperature = dht_device.temperature
                if temperature is not None:
                    print("{0:0.1f}".format(temperature))
                    break
            elif sensor == "humidity":
                humidity = dht_device.humidity
                if humidity is not None:
                    print("{0:0.1f}".format(humidity))
                    break
            else:
                print("Unknown sensor : {}".format(sensor))
                break
            time.sleep(0.1)
        except RuntimeError:
            time.sleep(0.1)


# read sensor name from program argument
readValue(sys.argv[1])
