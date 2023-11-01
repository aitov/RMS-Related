#
#  Log values of DHT22 sensor to csv file for statistic collection
#


import adafruit_dht, time, os, subprocess

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
    file.write('Date, Temperature, CPU Temperature, Humidity\n')
else:
    file = open(csvFilePath, "a")

running = True
# loop forever
while running:

    try:
        # read the humidity and temperature
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        # get CPU temp
        cpu_temperature = subprocess.check_output(["/opt/vc/bin/vcgencmd measure_temp | cut -c6-9"], shell=True, encoding="utf-8").strip()

        if temperature is not None and humidity is not None:
            print(cpu_temperature)
            file.write(
                time.strftime("%d.%m.%Y %H:%M:%S") + ", " + "{0:0.1f}".format(temperature) + ", "
                + cpu_temperature  + ", "
                + "{0:0.1f}".format(humidity) + '\n')
            file.flush()
            time.sleep(timeout)
        else:
            time.sleep(0.1)
    except RuntimeError:
        time.sleep(0.1)
    except KeyboardInterrupt:
        print('Program stopped')
        running = False
        file.close()