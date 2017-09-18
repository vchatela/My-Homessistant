import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import MySQLdb as Mdb


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

        self.logger = logging.getLogger('database')
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
            self.logger.debug("Database connection established")
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def insert_weather(self, temperature_in, temperature_out, humidity_in, humidity_out, heater_state):
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
            query = "INSERT INTO Weather VALUES (TIMESTAMP(\'{0}\'),{1},{2},{3},{4},{5},{6})".format(
                str(datetime.now()),
                str(temperature_in),
                str(
                    temperature_out),
                str(humidity_in),
                str(humidity_out),
                str(heater_state),
                str(velux_state))
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            self.__database.commit()
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def get_cursor_programmation(self):
        try:
            cursor = self.__database.cursor()
            query = "SELECT * FROM Programmation"
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            return cursor
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def get_all_weather_cursor(self):
        try:
            cursor = self.__database.cursor()
            query = "SELECT * FROM `Weather` ORDER BY `date` ASC"
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            return cursor
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def close(self):
        if self.__database:
            self.logger.debug("Database closed")
            self.__database.close()
