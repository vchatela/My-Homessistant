import time
import os
import glob
import sys
import argparse
import simplejson
import Adafruit_DHT
import MySQLdb as Mdb
import numpy
import pyowm
from datetime import datetime
from abc import ABCMeta, abstractmethod

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
    def __init__(self, myh_plug_file):
        self.sensors_list = []
        self.database = None
        # self.myh_plug_dict = simplejson.loads(myh_plug_file)
        # Arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action='store_true', help="Add debug outputs")
        args = parser.parse_args()
        if args.debug:
            self.__debug = True
        else:
            self.__debug = False

    ##Printers
    def print_debug(self, str_dbg):
        if self.__debug:
            print "DEBUG : " + str_dbg

    @staticmethod
    def print_error(str_error):
        print "ERROR : " + str_error
        sys.exit(-1)

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
            temp_list.append(temp_tmp)
            if hasattr(sensor, "device_file"):
                self.print_debug("Temperature of " + sensor.device_file + " is " + str(temp_tmp) + " C")
            else:
                self.print_debug("Temperature is " + str(temp_tmp))
        average_temp = numpy.average(temp_list)
        self.print_debug("Average temp is " + str(average_temp) + " C")
        return average_temp

    def get_humidity(self):
        hum_list = []
        for sensor in self.sensors_list:
            if "get_humidity" in dir(sensor):
                hum_tmp = sensor.get_humidity()
                hum_list.append(hum_tmp)
                self.print_debug("Humidity is " + str(hum_tmp))
        average_hum = numpy.average(hum_list)
        self.print_debug("Average humidity is " + str(average_hum) + " %")
        return average_hum

    def get_out_temp(self):
        out_sensor = OutdoorAPITemperatureSensor()
        return out_sensor.get_temperature()

    def get_out_humidity(self):
        out_sensor = OutdoorAPITemperatureSensor()
        return out_sensor.get_humidity()

    ##Database
    def connect_database(self, db_login, db_password, db_base):
        # Connexion
        try:
            self.database = Mdb.connect('localhost', db_login, db_password, db_base)
        except Mdb.Error, e:
            self.print_error(str(e))

    def insert_temperature_db(self, temperature_in, temperature_out):
        try:
            cursor = self.database.cursor()
            # Date - In - Out - State
            if temperature_out is None:
                temperature_out = "NULL"
            if temperature_in is None:
                temperature_in = "NULL"
            query = "INSERT INTO Temperature VALUES (TIMESTAMP(\'{0}\'),{1},{2},0)".format(str(datetime.now()),
                                                                                           str(temperature_in),
                                                                                           str(temperature_out))
            self.print_debug(query)
            cursor.execute(query)
            self.database.commit()
        except Mdb.Error, e:
            self.print_error(str(e))

    def insert_humidity(self, humidity_in, humidity_out):
        try:
            cursor = self.database.cursor()
            # Date - In - Out - State
            if humidity_in is None:
                humidity_in = "NULL"
            if humidity_out is None:
                humidity_out = "NULL"
            query = "INSERT INTO Humidity VALUES (TIMESTAMP(\'{0}\'),{1},{2},0)".format(str(datetime.now()),
                                                                                        str(humidity_in),
                                                                                        str(humidity_out))
            self.print_debug(query)
            cursor.execute(query)
            self.database.commit()
        except Mdb.Error, e:
            self.print_error(str(e))

    def close_database(self):
        if self.database:
            self.database.close()


# Main

if __name__ == "__main__":
    app = Application(myh_plug_file=os.path.abspath(
        os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, "data", "myh_plug.json")))

    # if app.myh_plug_dict["remain_time_db"] == 0:

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

    # Add to database
    app.connect_database(db_login="home_user", db_password="", db_base="Homessistant")
    app.insert_temperature_db(temp_avg, temp_out)
    app.insert_humidity(hum_avg, hum_out)

    # app.myh_plug_dict["remain_time_db"] = app.myh_plug_dict["default_remain_time_db"]

    # else:
    #     if app.myh_plug_dict["remain_time_db"] < 0:
    #         app.myh_plug_dict["remain_time_db"] = app.myh_plug_dict["default_remain_time_db"]
    #     else:
    #         app.myh_plug_dict["remain_time_db"] -= 1
    #
    # app.print_debug("Remaining time to db : " + str(app.myh_plug_dict["remain_time_db"]))
    #
    # with open(app.myh_plug_file, 'w') as f:
    #     simplejson.dump(app.myh_plug_dict, f)



    # Turn On/Off Plug
