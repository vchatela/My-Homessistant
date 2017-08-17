import json
import os


def main():
    myh_plug_file = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir))
    myh_plug_dict = json.loads(myh_plug_file)
    if myh_plug_dict["remain_time_db"] == 0:
        os.system("python temperature.py ---debug")
    else:
        myh_plug_dict["remain_time_db"] -= 1
        with open(myh_plug_file,'w') as f:
            json.dump(myh_plug_dict,f)

if __name__ == "__main__":
    main()