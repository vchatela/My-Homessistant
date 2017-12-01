import datetime
import json
import logging
import os
from logging.handlers import RotatingFileHandler

from core.database import MyHomessistantDatabase

db_struct = {"temp_ref": 0, "plug_state": 1, "start_time": 2, "day_of_week": 3, "plug_type": 4, "plug_number": 5}


class Manager:
    def __init__(self):
        # Check server allow to run
        __myh_file = os.path.join(os.environ["MYH_HOME"], "data", "myh.json")
        __sensor_file = os.path.join(os.environ["MYH_HOME"], "data", "sensors.json")
        with open(__myh_file, 'r') as __myh_file_data:
            __myh_dict = json.load(__myh_file_data)
            if not __myh_dict["app_state"].lower() == "on":
                exit(0)
        with open(__sensor_file, 'r') as __sensor_file_data:
            __sensor_dict = json.load(__sensor_file_data)
            self.__radio_wiringpi_number = str(__sensor_dict["HF"])
        # Do work
        self.database = MyHomessistantDatabase()
        self.database.connection()
        self.__plugs_file = os.path.join(os.environ["MYH_HOME"], "data", "plugs.json")
        with open(self.__plugs_file, 'r') as plugs_file_data:
            self.__plugs_dict = json.load(plugs_file_data)
        self.__weather_file = os.path.join(os.environ["MYH_HOME"], "data", "weather.json")
        with open(self.__weather_file, 'r') as weather_file_data:
            self.__weather_dict = json.load(weather_file_data)

        # Logger
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'manager.log')

        file_handler = RotatingFileHandler(logfile, mode='a', maxBytes=5 * 1024 * 1024,
                                           backupCount=2, encoding=None, delay=0)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)

        self.logger = logging.getLogger('manager')
        self.logger.setLevel(logging.DEBUG)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def __del__(self):
        if hasattr(self, "database") and self.database:
            self.database.close()

    def turn_on_off_plug(self, plug_number, new_state):
        plug_id = str(self.__plugs_dict[plug_number]["plug_id"])
        command = " ".join(
            [str(os.path.join(os.environ["MYH_HOME"], "bin", "radioEmission")), self.__radio_wiringpi_number, plug_id,
             "1", new_state.lower()])
        self.logger.debug("Command launched : " + command)
        os.system(command)
        self.__plugs_dict[plug_number]["plug_state"] = new_state.lower()
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)

    def update_plug(self, plug_number, temp, plug_state, mustbe_plug_state):
        self.__plugs_dict[plug_number]["temp_ref"] = temp
        self.__plugs_dict[plug_number]["plug_state"] = plug_state
        self.__plugs_dict[plug_number]["plug_state_mustbe"] = mustbe_plug_state
        with open(self.__plugs_file, 'w') as f:
            json.dump(self.__plugs_dict, f)

    def check_rules(self):
        cursor_prog = self.database.get_cursor_programmation()
        while 1:
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
            new_plug_state = "on" if row[db_struct["plug_state"]] else "off"
            self.update_plug(plug_number, row[db_struct["temp_ref"]], new_plug_state,
                             new_plug_state)  # Here we suppose the mustbe_plug_state is the real plug state

    def apply_actions(self):
        for plug_number in self.__plugs_dict:
            plug_dict = self.__plugs_dict[plug_number]
            # If here the plug matched for this rule
            # Turn off heater/mosquito if velux is open
            if plug_dict["type"] in ["HEATER", "MOSQUITO"] and bool(self.__weather_dict["velux_open"]):
                if plug_dict["plug_state"].lower() == "on":
                    # TODO Send Android Notification - Plug must be ON but velux is open
                    # On notification : click to restart
                    self.logger.debug(plug_dict["type"] + " turned off because of velux open")
                self.turn_on_off_plug(plug_number, "off")
                continue
            # If velux close : reapply state
            elif plug_dict["type"] in ["HEATER", "MOSQUITO"] and not bool(self.__weather_dict["velux_open"]):
                if plug_dict["plug_state"].lower() != plug_dict["plug_state_mustbe"].lower():
                    self.logger.debug(plug_dict["type"] + " restored to " + plug_dict[
                        "plug_state_mustbe"].lower() + " because velux has been closed")
                    self.turn_on_off_plug(plug_number, plug_dict["plug_state_mustbe"].lower())
            # HEATER case
            if plug_dict["plug_state"].lower() == "on":
                if plug_dict["type"] == "HEATER":
                    if self.__weather_dict["temp_avg"] < plug_dict["temp_ref"]:
                        # TODO Update after 10 minutes minimum before last change
                        self.turn_on_off_plug(plug_number, "on")
                    else:
                        self.turn_on_off_plug(plug_number, "off")
                # MOSQUITO case
                elif plug_dict["type"] == "MOSQUITO":
                    self.turn_on_off_plug(plug_number, plug_dict["plug_state"])
                elif plug_dict["type"] == "LIGHT":
                    self.turn_on_off_plug(plug_number, plug_dict["plug_state"])
            else:
                self.turn_on_off_plug(plug_number, "off")


if __name__ == "__main__":
    my_manager = Manager()
    my_manager.check_rules()
    my_manager.apply_actions()
