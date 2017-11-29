#!/usr/bin/env python
import json
import os
import time

import RPi.GPIO as GPIO

MYH_HOME = os.environ["MYH_HOME"]
with open(MYH_HOME + '/data/sensors.json') as sensors_file:
    sensors_data = json.load(sensors_file)
    GPIO_MODE = sensors_data["GPIO_MODE"]
    PIN = sensors_data["Rain"]

if GPIO_MODE == "BCM":
    GPIO.setmode(GPIO.BCM)
else:
    raise Exception("GPIO MODE %s not supported" % GPIO_MODE)
GPIO.setup(PIN, GPIO.IN)


def read_loop():
    while True:
        print read()
        time.sleep(1)


def read():
    state = GPIO.input(PIN)
    if (state == 0):
        print "Water detected !"
        return True
    else:
        print "No water detected..."
        return False


if __name__ == "__main__":
    try:
        read_loop()
    except KeyboardInterrupt:
        pass
