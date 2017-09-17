import os
from datetime import datetime
import MySQLdb as Mdb
import json
import logging

from logging.handlers import RotatingFileHandler


class MyHomessistantDatabase():
    def __init__(self):
        self.__database = None
        # Logger
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'database.log')

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

    def connection(self):
        myh_db_file = os.path.join(os.environ["MYH_HOME"], "data", "myh_db.json")
        with open(myh_db_file, 'r') as myh_db_file_data:
            myh_db_dict = json.load(myh_db_file_data)
        self.__db_login = myh_db_dict["db_user"]
        self.__db_password = myh_db_dict["db_password"]
        self.__db_base = myh_db_dict["db_base"]
        self.__db_hostname = myh_db_dict["db_hostname"]
        try:
            self.__database = Mdb.connect(self.__db_hostname, self.__db_login, self.__db_password, self.__db_base)
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def insert_weather(self, temperature_out, temperature_in, humidity_in, humidity_out):
        try:
            cursor = self.__database.cursor()
            # Date - In - Out - State
            if temperature_out is None:
                temperature_out = "NULL"
            if temperature_in is None:
                temperature_in = "NULL"
            if humidity_in is None:
                humidity_in = "NULL"
            if humidity_out is None:
                humidity_out = "NULL"
            velux_state = "NULL"
            query = "INSERT INTO Weather VALUES (TIMESTAMP(\'{0}\'),{1},{2},{3},{4},0,{5})".format(str(datetime.now()),
                                                                                                   str(temperature_in),
                                                                                                   str(
                                                                                                       temperature_out),
                                                                                                   str(humidity_in),
                                                                                                   str(humidity_out),
                                                                                                   str(velux_state))
            cursor.execute(query)
            self.__database.commit()
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def get_cursor_programmation(self):
        try:
            cursor = self.__database.cursor()
            query = "SELECT * FROM Programmation"
            cursor.execute(query)
            return cursor
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def get_all_weather_cursor(self):
        try:
            cursor = self.__database.cursor()
            cursor.execute("SELECT * FROM `Weather` ORDER BY `date` ASC")
            return cursor
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def close(self):
        if self.__database:
            self.__database.close()
