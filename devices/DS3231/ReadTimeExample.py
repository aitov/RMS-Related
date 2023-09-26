#
# Python example how to read time from RTC DS3231 module
#
import time
import board
import adafruit_ds3231

i2c = board.I2C()  # uses board.SCL and board.SDA

rtc = adafruit_ds3231.DS3231(i2c)

if False:  # change to True if you want to set the time!
    currentTime = time.localtime()
    print("Setting time to:", currentTime)
    rtc.datetime = currentTime
    print()

# Main loop:
while True:
    t = rtc.datetime
    # print(t)     # uncomment for debugging
    print(
        "The date is {} {}/{}/{}".format(
            days[int(t.tm_wday)], t.tm_mday, t.tm_mon, t.tm_year
        )
    )
    print("The time is {}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec))
    time.sleep(1)  # wait a second
