#
#  Log values of DHT22 sensor to csv file for statistic collection
#

import adafruit_dht, time, os
# Need specify pin where DHT22 connected
from board import D10

dht_device = adafruit_dht.DHT22(D10, use_pulseio=False)

# check temperature and save once in 5 minutes
timeout = 60 * 5

csvFolder = "/home/pi/log"
#  RMS should restart Raspberry every day, it should force create new file in next month
csvFile = time.strftime("%m.%Y") + "_outside_sensor_values.csv"

if not os.path.isdir(csvFolder):
    os.makedirs(csvFolder)

csvFilePath = os.path.join(csvFolder, csvFile)

if not os.path.isfile(csvFilePath):
    file = open(csvFilePath, "w")
    file.write('Date, Temperature, Humidity\n')
else:
    file = open(csvFilePath, "a")

running = True
# loop forever
while running:

    try:
        # read the humidity and temperature
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        if temperature is not None and humidity is not None:
            file.write(
                time.strftime("%d.%m.%Y %H:%M:%S") + ", " + "{0:0.1f}".format(temperature) + ", "
                + "{0:0.1f}".format(humidity) + '\n')
            file.flush()
            time.sleep(timeout)
        else:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print('Program stopped')
        running = False
        file.close()
