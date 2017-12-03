import json
import os
import time
import pyowm
import RPi.GPIO as GPIO
from abc import ABCMeta, abstractmethod
import Adafruit_DHT

MYH_HOME = os.environ["MYH_HOME"]
with open(MYH_HOME + '/data/sensors.json') as sensors_file:
    sensors_data = json.load(sensors_file)
    GPIO_MODE = sensors_data["GPIO_MODE"]
    am2302_pin = int(sensors_data["AM2032"])
    hall_pin = int(sensors_data["A1120"])
    rain_pin = int(sensors_data["Rain"])
    light_pin = sensors_data["Light"]

class Myh_Sensor:
    def __init__(self):
        if GPIO_MODE == "BCM":
            GPIO.setmode(GPIO.BCM)
        else:
            raise Exception("GPIO MODE %s not supported" % GPIO_MODE)

class LightSensor(Myh_Sensor):
    def __init__(self, pin):
        Myh_Sensor.__init__(self)
        self.pin = pin

    def is_light_on(self):
        GPIO.setup(self.pin, GPIO.IN)
        if not GPIO.input(self.pin):
            return True
        else:
            return False

class RainSensor(Myh_Sensor):
    def __init__(self, pin):
        Myh_Sensor.__init__(self)
        self.pin = pin

    def is_it_raining(self):
        GPIO.setup(self.pin, GPIO.IN)
        if not GPIO.input(self.pin):
            return True
        else:
            return False

class HallSensor(Myh_Sensor):
    def __init__(self, pin):
        Myh_Sensor.__init__(self)
        self.pin = pin

    def is_velux_open(self):
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if GPIO.input(self.pin):
            return True
        else:
            return False

class TemperatureSensorAbstract:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_temperature(self):
        raise NotImplementedError('Subclasses must override get_temperature()!')


class AM2302TemperatureSensor(TemperatureSensorAbstract):
    def __init__(self, model, pin):
        self.model = model
        self.pin = pin

    def get_temperature(self):
        try:
            _, temperature = Adafruit_DHT.read_retry(self.model, self.pin)
            return temperature
        except:
            return None

    def get_humidity(self):
        try:
            humidity, _ = Adafruit_DHT.read_retry(self.model, self.pin)
            return humidity
        except:
            return None


class DS18B20TemperatureSensor(TemperatureSensorAbstract):
    base_dir = '/sys/bus/w1/devices/'

    def __init__(self, device_dir):
        self.device_file = os.path.join(device_dir, 'w1_slave')

    def get_temperature(self):
        try:
            lines = self.__read_temp_raw()
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.__read_temp_raw()
            equals_pos = lines[1].find('t=')
            temp_c = None
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0
            return temp_c
        except:
            return None

    def __read_temp_raw(self):
        with open(self.device_file, 'r') as device_file:
            return device_file.readlines()

    def __str__(self):
        return self.__read_temp_raw()


class OutdoorAPITemperatureSensor(TemperatureSensorAbstract):
    def __init__(self):
        observation = pyowm.OWM('124db9b65e41932220cdc2392bad7ebf').weather_at_place('Lescar,fr')
        self.weather = observation.get_weather()

    def get_temperature(self):
        if 'temp' in self.weather.get_temperature('celsius'):
            return self.weather.get_temperature('celsius')['temp']
        else:
            return None

    def get_humidity(self):
        try:
            return self.weather.get_humidity()
        except:
            return None