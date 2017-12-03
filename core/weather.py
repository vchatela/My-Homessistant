import glob
import json
import logging
import os
from logging.handlers import RotatingFileHandler

import Adafruit_DHT
import numpy

import myh_sensors.sensors as Myh_Sensors
from core.database import MyHomessistantDatabase

os.system('/sbin//modprobe w1-gpio')
os.system('/sbin//modprobe w1-therm')
MYH_HOME = os.environ["MYH_HOME"]


class Application:
    def __init__(self, is_test=False):
        # Check server allow to run
        __myh_file = os.path.join(os.environ["MYH_HOME"], "data", "myh.json")
        with open(__myh_file, 'r') as __myh_file_data:
            __myh_dict = json.load(__myh_file_data)
            if not __myh_dict["app_state"].lower() == "on" and not is_test:
                exit(0)
        self.sensors_list = []
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

        self.logger = logging.getLogger('weather')
        self.logger.setLevel(logging.DEBUG)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def insert_weather(self, temp_avg, temp_out, hum_avg, hum_out, heater_state, velux_state):
        if not hasattr(self, "database") or not self.database:
            self.database = MyHomessistantDatabase()
            self.database.connection()
        self.database.insert_weather(temp_avg, temp_out, hum_avg, hum_out, heater_state, velux_state)

    def __del__(self):
        if hasattr(self, "database") and self.database:
            self.database.close()

    def get_db_credentials(self):
        return self.__myh_db_dict["db_user"], self.__myh_db_dict["db_password"], self.__myh_db_dict["db_base"], \
               self.__myh_db_dict["db_hostname"]

    ##Sensors
    def load_sensors(self):
        # DS18B20
        for ds_sensor_dir in glob.glob(Myh_Sensors.DS18B20TemperatureSensor.base_dir + '28*'):
            self.sensors_list.append(Myh_Sensors.DS18B20TemperatureSensor(ds_sensor_dir))
        # AM 2302
        self.sensors_list.append(Myh_Sensors.AM2302TemperatureSensor(Adafruit_DHT.AM2302, Myh_Sensors.am2302_pin))
        # Hall sensor
        self.sensors_list.append(Myh_Sensors.HallSensor(Myh_Sensors.hall_pin))
        # Rain sensor
        self.sensors_list.append(Myh_Sensors.RainSensor(Myh_Sensors.rain_pin))

    def get_average_temp(self):
        temp_list = []
        for sensor in self.sensors_list:
            if isinstance(sensor,Myh_Sensors.TemperatureSensorAbstract):
                temp_tmp = sensor.get_temperature()
                if temp_tmp is None:
                    continue
                temp_list.append(temp_tmp)
                if hasattr(sensor, "device_file"):
                    self.logger.debug("Temperature of " + sensor.device_file + " is " + str(temp_tmp) + " C")
                else:
                    self.logger.debug("Temperature is " + str(temp_tmp))
        if not temp_list:
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
        if not hum_list:
            average_hum = None
        else:
            average_hum = numpy.average(hum_list)
        self.logger.debug("Average humidity is " + str(average_hum) + " %")
        return average_hum

    @staticmethod
    def get_out_temp():
        out_sensor = Myh_Sensors.OutdoorAPITemperatureSensor()
        return out_sensor.get_temperature()

    @staticmethod
    def get_out_humidity():
        out_sensor = Myh_Sensors.OutdoorAPITemperatureSensor()
        return out_sensor.get_humidity()

    # Files for flask api
    def update_weather_data(self, temp_avg, temp_out, hum_avg, hum_out, heater_state):
        self.__weather_dict["temp_avg"] = temp_avg
        self.__weather_dict["temp_out"] = temp_out
        self.__weather_dict["hum_avg"] = hum_avg
        self.__weather_dict["hum_out"] = hum_out
        self.__weather_dict["heater_state"] = heater_state
        with open(self.__weather_file, 'w') as f:
            json.dump(self.__weather_dict, f)

    def get_heater_state(self):
        self.__plugs_file = os.path.join(os.environ["MYH_HOME"], "data", "plugs.json")
        with open(self.__plugs_file, 'r') as plugs_file_data:
            self.__plugs_dict = json.load(plugs_file_data)
        for plug_number in self.__plugs_dict:
            plug_dict = self.__plugs_dict[plug_number]
            # If here the plug matched for this rule
            # HEATER case
            if plug_dict["plug_state"].lower() == "on" and plug_dict["type"].lower() == "heater":
                return 1
            else:
                return 0

    def is_velux_open(self):
        for sensor in self.sensors_list:
            if isinstance(sensor,Myh_Sensors.HallSensor):
                is_open = sensor.is_velux_open()
                if is_open:
                    self.logger.debug("Velux is open.")
                else :
                    self.logger.debug("Velux is close.")
                return is_open
        return None

    def is_it_raining(self):
        for sensor in self.sensors_list:
            if isinstance(sensor,Myh_Sensors.RainSensor):
                is_raining = sensor.is_it_raining()
                if is_raining:
                    self.logger.debug("Rain detected.")
                else:
                    self.logger.debug("No rain detected.")
                return is_raining
        return None


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
    # Get Velux State
    velux_state = app.is_velux_open()
    # Get Heater State
    heater_state = app.get_heater_state()

    app.update_weather_data(temp_avg, temp_out, hum_avg, hum_out, heater_state)
    app.insert_weather(temp_avg, temp_out, hum_avg, hum_out, heater_state, velux_state)
