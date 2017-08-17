import time
import os
import glob
import sys
import argparse
import MySQLdb as Mdb
import numpy
import pyowm
from datetime import datetime
from abc import ABCMeta, abstractmethod

os.system('/sbin//modprobe w1-gpio')
os.system('/sbin//modprobe w1-therm')

wiring_pin_rpi = 29


class TemperatureSensorAbstract:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_temperature(self):
        raise NotImplementedError('Subclasses must override get_temperature()!')


class DS18B20TemperatureSensor(TemperatureSensorAbstract):
    base_dir = '/sys/bus/w1/devices/'

    def __init__(self, device_dir):
        self.device_file = os.path.join(device_dir, 'w1_slave')

    def get_temperature(self):
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

    def __read_temp_raw(self):
        with open(self.device_file, 'r') as device_file:
            return device_file.readlines()

    def __str__(self):
        return self.__read_temp_raw()


class OutdoorAPITemperatureSensor(TemperatureSensorAbstract):
    def __init__(self):
        self.owm = pyowm.OWM('124db9b65e41932220cdc2392bad7ebf')

    def get_temperature(self):
        observation = self.owm.weather_at_place('Lescar,fr')
        w = observation.get_weather()
        if 'temp' in w.get_temperature('celsius'):
            return w.get_temperature('celsius')['temp']
        else:
            return None


class Application:
    def __init__(self):
        self.sensors_list = []
        self.database = None
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
        for ds_sensor_dir in glob.glob(DS18B20TemperatureSensor.base_dir + '28*'):
            self.sensors_list.append(DS18B20TemperatureSensor(ds_sensor_dir))
            # If other sensors type - add here

    def get_average_temp(self):
        temp_list = []
        for sensor in self.sensors_list:
            temp_tmp = sensor.get_temperature()
            temp_list.append(temp_tmp)
            self.print_debug("Temperature of " + sensor.device_file + " is " + str(temp_tmp) + " C")
        average_temp = numpy.average(temp_list)
        self.print_debug("Average temp is " + str(average_temp) + " C")
        return average_temp

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
            query = "INSERT INTO Temperature VALUES (TIMESTAMP(\'{0}\'),{1},{2},0)".format(str(datetime.now()),
                                                                                           str(temperature_in),
                                                                                           str(temperature_out))
            self.print_debug(query)
            cursor.execute(query)
            self.database.commit()
        except Mdb.Error, e:
            self.print_error(str(e))
        finally:
            if self.database:
                self.database.close()

    def get_out_temp(self):
        out_sensor = OutdoorAPITemperatureSensor()
        return out_sensor.get_temperature()


# Main

if __name__ == "__main__":
    app = Application()
    # Determine Average Temperature from all sensors
    # Load sensors
    app.load_sensors()
    # Get Average temp of all sensors
    temp_avg = app.get_average_temp()
    temp_out = app.get_out_temp()

    # Add to database
    app.connect_database(db_login="home_user", db_password="", db_base="Homessistant")
    if not temp_avg is None:
        app.insert_temperature_db(temp_avg, temp_out)
    else:
        app.print_error("Error while getting average temperature.")
