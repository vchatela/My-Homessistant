import time
import os
import argparse
import glob
import json
import Adafruit_DHT
import numpy
import pyowm
import logging
from logging.handlers import RotatingFileHandler
from abc import ABCMeta, abstractmethod

from core.database import MyHomessistantDatabase

os.system('/sbin//modprobe w1-gpio')
os.system('/sbin//modprobe w1-therm')

wiring_pin_rpi = 29
am2302_pin = 27


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


class Application:
    def __init__(self):
        self.sensors_list = []
        self.database = MyHomessistantDatabase()
        self.database.connection()
        # Args Parse
        parser = argparse.ArgumentParser()
        parser.add_argument("--insert", help="ignore verification of db_time", action="store_true")
        self.args = parser.parse_args()
        # Dicts
        self.__myh_db_file = os.path.join(os.environ["MYH_HOME"], "data", "myh_db.json")
        with open(self.__myh_db_file, 'r') as myh_db_file_data:
            self.__myh_db_dict = json.load(myh_db_file_data)
        self.__weather_file = os.path.join(os.environ["MYH_HOME"], "data", "weather.json")
        with open(self.__weather_file, 'r') as weather_file:
            self.__weather_dict = json.load(weather_file)
        # Logger
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'weather.log')

        file_handler = RotatingFileHandler(logfile, mode='a', maxBytes=5 * 1024 * 1024,
                                           backupCount=2, encoding=None, delay=0)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)

        self.logger = logging.getLogger('root')
        self.logger.setLevel(logging.DEBUG)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def __del__(self):
        self.database.close()

    def get_db_credentials(self):
        return self.__myh_db_dict["db_user"], self.__myh_db_dict["db_password"], self.__myh_db_dict["db_base"], \
               self.__myh_db_dict["db_hostname"]

    ##Sensors
    def load_sensors(self):
        # DS18B20
        for ds_sensor_dir in glob.glob(DS18B20TemperatureSensor.base_dir + '28*'):
            self.sensors_list.append(DS18B20TemperatureSensor(ds_sensor_dir))
        # AM 2302
        self.sensors_list.append(AM2302TemperatureSensor(Adafruit_DHT.AM2302, am2302_pin))

    def get_average_temp(self):
        temp_list = []
        for sensor in self.sensors_list:
            temp_tmp = sensor.get_temperature()
            if temp_tmp is None:
                continue
            temp_list.append(temp_tmp)
            if hasattr(sensor, "device_file"):
                self.logger.debug("Temperature of " + sensor.device_file + " is " + str(temp_tmp) + " C")
            else:
                self.logger.debug("Temperature is " + str(temp_tmp))
        if temp_list == []:
            return None
        average_temp = numpy.average(temp_list)
        self.logger.debug("Average temp is " + str(average_temp) + " C")
        return average_temp

    def get_humidity(self):
        hum_list = []
        for sensor in self.sensors_list:
            if "get_humidity" in dir(sensor):
                hum_tmp = sensor.get_humidity()
                hum_list.append(hum_tmp)
                self.logger.debug("Inside humidity is " + str(hum_tmp))
        average_hum = numpy.average(hum_list)
        self.logger.debug("Average humidity is " + str(average_hum) + " %")
        return average_hum

    def get_out_temp(self):
        out_sensor = OutdoorAPITemperatureSensor()
        return out_sensor.get_temperature()

    def get_out_humidity(self):
        out_sensor = OutdoorAPITemperatureSensor()
        return out_sensor.get_humidity()

    # Files for flask api
    def update_weather_data(self, temp_avg, temp_out, hum_avg, hum_out):
        self.__weather_dict["temp_avg"] = temp_avg
        self.__weather_dict["temp_out"] = temp_out
        self.__weather_dict["hum_avg"] = hum_avg
        self.__weather_dict["hum_out"] = hum_out
        with open(self.__weather_file, 'w') as f:
            json.dump(self.__weather_dict, f)


# Main

if __name__ == "__main__":
    app = Application()

    # Insert into database
    # Determine Average Temperature from all sensors
    # Load sensors
    app.load_sensors()
    # Get Average temp of all sensors
    temp_avg = app.get_average_temp()
    temp_out = app.get_out_temp()
    # Get Average humidity
    hum_avg = app.get_humidity()
    hum_out = app.get_out_humidity()

    app.update_weather_data(temp_avg, temp_out, hum_avg, hum_out)
    app.database.insert_weather(temp_avg, temp_out, hum_avg, hum_out)
