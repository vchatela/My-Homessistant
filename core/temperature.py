import time
import os
import glob
import sys
import argparse
import MySQLdb as mdb

import numpy

os.system('/sbin//modprobe w1-gpio')
os.system('/sbin//modprobe w1-therm')

wiring_pin_rpi = 29


class DS18B20TemperatureSensor:
    base_dir = '/sys/bus/w1/devices/'

    def __init__(self, device_dir):
        self.device_file = os.path.join(device_dir, 'w1_slave')

    def get_temperature(self):
        lines = self.__read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.__read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
        return temp_c

    def __read_temp_raw(self):
        with open(self.device_file, 'r') as device_file:
            return device_file.readlines()


class Application:
    def __init__(self):
        # Arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action='store_true', help="Add debug outputs")
        args = parser.parse_args()
        if args.debug:
            self.__debug = True
        else:
            self.__debug = False

    def print_debug(self, str_dbg):
        if self.__debug:
            print "DEBUG : " + str_dbg

    def load_sensors(self):
        self.sensors_list = []
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

    def connect_database(self, db_login, db_password, db_base):
        # Connexion
        self.database = mdb.connect('localhost', db_login, db_password, db_base)

    def insert_temperature_db(self):
        try:
            cursor = self.database.cursor()
            cursor.execute("INSERT INTO Temperature VALUES (0, CURRENT_DATE(), (CURRENT_TIME()), %f, %s)" %(None,None))
            self.database.commit()
        except mdb.Error, e:
            print "Error %d: %s \n" % (e.args[0], e.args[1])
            sys.exit(1)

        finally:
            if self.database:
                self.database.close()

# Main

if __name__ == "__main__":
    app = Application()
    # Determine Average Temperature from all sensors
    # Load sensors
    app.load_sensors()
    # Get Average temp of all sensors
    temp_avg = app.get_average_temp()

    # Add to database
    app.connect_database(db_login="home_user", db_password="", db_base="Homessitant")
    app.insert_temperature_db()
