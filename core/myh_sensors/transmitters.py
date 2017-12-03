import json
import os


class HF_transmitter:
    def __init__(self,plug_id,radio_wiringpi_number):
        self.plug_id = plug_id
        self.radio_wiringpi_number = radio_wiringpi_number

    def turn_on_off_plug(self, new_state):
        plug_id = str(self.plug_id)
        command = " ".join(
            [str(os.path.join(os.environ["MYH_HOME"], "bin", "radioEmission")), self.radio_wiringpi_number, plug_id,
             "1", new_state.lower()])
        #print("Command launched : " + command)
        os.system(command)