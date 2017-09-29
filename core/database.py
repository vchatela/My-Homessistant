import json
import logging
import os
from datetime import datetime, timedelta
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

    def get_charts_dataset(self, days):
        dateformat = '%H:%M:%S,%d/%m/%Y'
        try:
            cursor = self.__database.cursor()
            limit_date = (datetime.now() - timedelta(days=days)).replace(microsecond=0)
            # Row_T
            query = "SELECT date, temperature_in, heater_state, temperature_out, is_velux_open FROM `Weather` WHERE date > '" + str(
                limit_date) + "'"
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            res = cursor.fetchall()
            row_T = map(list, res)
            for x in row_T:
                # x[0] = x[0].strftime(dateformat)
                x[0] = [str(x[0].year), str(x[0].month), str(x[0].day), str(x[0].hour), str(x[0].minute),
                        str(x[0].second)]
            # Row_H
            query = "SELECT date, humidity_in, heater_state, humidity_out, is_velux_open FROM `Weather` WHERE date > '" + str(
                limit_date) + "'"
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            res = cursor.fetchall()
            row_H = map(list, res)
            for x in row_H:
                # x[0] = x[0].strftime(dateformat)
                x[0] = [str(x[0].year), str(x[0].month), str(x[0].day), str(x[0].hour), str(x[0].minute),
                        str(x[0].second)]
            # Min Max Avg
            query = "SELECT MIN(temperature_in), MAX(temperature_in), AVG(temperature_in) FROM `Weather` WHERE date > '" + str(
                limit_date) + "'"
            self.logger.debug("Query executed : " + query)
            cursor.execute(query)
            res = map(list, cursor.fetchall())
            t_avg = res[0][2]
            t_min = res[0][0]
            t_max = res[0][1]
            final_dict = {
                "t_avg": "{0:.2f}".format(t_avg),
                "t_min": "{0:.2f}".format(t_min),
                "t_max": "{0:.2f}".format(t_max),
                "row_T": row_T,
                "row_H": row_H
            }
            return final_dict
        except Mdb.Error, e:
            self.logger.error(str(e))
            exit(-1)

    def close(self):
        if self.__database:
            self.logger.debug("Database closed")
            self.__database.close()
