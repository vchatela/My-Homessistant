import datetime
import os
import json

import logging

from logging.handlers import RotatingFileHandler

from core.database import MyHomessistantDatabase

db_struct = {"temp_ref": 0, "plug_state": 1, "start_time": 2, "day_of_week": 3, "plug_type": 4, "plug_number": 5}


class Manager():
    def __init__(self):
        self.database = MyHomessistantDatabase()
        self.database.connection()
        self.__plugs_file = os.path.join(os.environ["MYH_HOME"], "data", "plugs.json")
        with open(self.__plugs_file, 'r') as plugs_file_data:
            self.__plugs_dict = json.load(plugs_file_data)
        self.__weather_file = os.path.join(os.environ["MYH_HOME"], "data", "weather.json")
        with open(self.__weather_file, 'r') as weather_file_data:
            self.__weather_dict = json.load(weather_file_data)
        __myh_file = os.path.join(os.environ["MYH_HOME"], "data", "myh.json")
        with open(__myh_file, 'r') as __myh_file_data:
            __myh_dict = json.load(__myh_file_data)
            self.__radio_wiringpi_number = str(__myh_dict["radio_wiringpi"])

        # Logger
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'manager.log')

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

    def turn_on_off_plug(self, plug_number, new_state):
        plug_id = str(self.__plugs_dict[plug_number]["plug_id"])
        command = " ".join(
            [str(os.path.join(os.environ["MYH_HOME"], "bin", "radioEmission")), self.__radio_wiringpi_number, plug_id,
             "1", new_state])
        self.logger.debug("Command launched : " + command)
        os.system(command)
        self.__plugs_dict[plug_number]["state"] = new_state
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)
        self.reset_last_update(plug_number)

    def decrease_last_update(self, plug_number):
        if self.__plugs_dict[plug_number]["remain_time_update"] > 0:
            self.__plugs_dict[plug_number]["remain_time_update"] -= 1
        else:
            self.__plugs_dict[plug_number]["remain_time_update"] = 0
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)

    def reset_last_update(self, plug_number):
        self.__plugs_dict[plug_number]["remain_time_update"] = self.__plugs_dict[plug_number]["default_time_update"]
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)

    def update_plug(self, plug_number, temp, state):
        self.__plugs_dict[plug_number]["temp_ref"] = temp
        self.__plugs_dict[plug_number]["plug_state"] = state
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)

    def check_rules(self):
        cursor_prog = self.database.get_cursor_programmation()
        while (1):
            row = cursor_prog.fetchone()
            # Manage end of list
            if row is None:
                break
            # For each rule
            # Check day
            now = datetime.datetime.now()
            today = now.strftime("%A")
            if not today in row[db_struct["day_of_week"]].split(','):
                break
            # Check time
            time_now = datetime.datetime.strptime(now.strftime("%X"), '%H:%M:%S').time()
            t1 = datetime.datetime.strptime(str(time_now), '%H:%M:%S')
            t2 = datetime.datetime.strptime(str(row[db_struct["start_time"]]), '%H:%M:%S')
            if not abs(t1 - t2) < datetime.timedelta(minutes=1):
                break
            # Check plug
            plug_number = str(row[db_struct["plug_number"]])
            if not self.__plugs_dict[plug_number]["type"] == row[db_struct["plug_type"]]:
                break
            # If here, the rules match so update the plug into plugs
            self.update_plug(plug_number, row[db_struct["temp_ref"]], row[db_struct["plug_state"]])

    def apply_actions(self):
        for plug_number in self.__plugs_dict:
            plug_dict = self.__plugs_dict[plug_number]
            # If here the plug matched for this rule
            # HEATER case
            if plug_dict["state"].lower() == "on":
                if plug_dict["type"] == "HEATER":
                    if self.__weather_dict["temp_avg"] < plug_dict["temp_ref"]:
                        # Update after 10 minutes minimum before last change
                        if plug_dict["remain_time_update"] == 0:
                            # Turn on heater
                            self.turn_on_off_plug(plug_number, "on")
                    else:
                        self.turn_on_off_plug(plug_number, "off")
                    self.decrease_last_update(plug_number)
                # MOSQUITO case
                elif plug_dict["type"] == "MOSQUITO":
                    self.turn_on_off_plug(plug_number, plug_dict["plug_state"])
            else:
                self.turn_on_off_plug(plug_number, "off")

if __name__ == "__main__":
    my_manager = Manager()
    my_manager.check_rules()
    my_manager.apply_actions()
