#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

import json

with open('$MYH_HOME/data/sensors.json') as sensors_file:
    sensors_data = json.load(sensors_file)
    PIN = sensors_data["RainBlack"]

GPIO.setmode(GPIO.BOARD)
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