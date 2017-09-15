import os
import json
from datetime import datetime

import MySQLdb as Mdb
import numpy

db_struct = {"date": 0, "temp_in": 1, "heater_state": 5}
db_min_heater_minutes = 40.0

def compute_deg_by_min():
    # Database connection
    myh_db_file = os.path.join(os.environ["MYH_HOME"], "data", "myh_db.json")
    with open(myh_db_file, 'r') as myh_db_file_data:
        myh_db_dict = json.load(myh_db_file_data)
    db_login = myh_db_dict["db_user"]
    db_password = myh_db_dict["db_password"]
    db_base = myh_db_dict["db_base"]
    db_hostname = myh_db_dict["db_hostname"]
    try:
        database = Mdb.connect(db_hostname, db_login, db_password, db_base)
    except Mdb.Error, e:
        print "-1"
        exit(-1)

    cursor = database.cursor()
    cursor.execute("SELECT * FROM `Weather` ORDER BY `date` ASC")

    in_on_zone = False
    start_on_zone = {"date": None, "temp_in": None}
    end_on_zone = {"date": None, "temp_in": None}
    coef_list = []
    while (1):
        row = cursor.fetchone()
        # Manage end of list
        if row == None:
            break
        # Manage detection of start
        if bool(row[db_struct["heater_state"]]) and not in_on_zone:
            in_on_zone = True
            start_on_zone["date"] = datetime.strptime(str(row[db_struct["date"]]), "%Y-%m-%d %H:%M:%S")
            start_on_zone["temp_in"] = float(row[db_struct["temp_in"]])
        # Manage end of zone
        if not bool(row[db_struct["heater_state"]]) and in_on_zone:
            in_on_zone = False
            end_on_zone["date"] = datetime.strptime(str(row[db_struct["date"]]), "%Y-%m-%d %H:%M:%S")
            end_on_zone["temp_in"] = float(row[db_struct["temp_in"]])
            # Determine minutes between start and end
            duration_date = end_on_zone["date"] - start_on_zone["date"]
            duration_minutes = duration_date.total_seconds() / 60.0
            if duration_minutes < db_min_heater_minutes:
                continue
            else:
                # Determine coef
                temp_won = end_on_zone["temp_in"] - start_on_zone["temp_in"]
                if temp_won <= 0:
                    # Ignore none temperature won
                    continue
                else:
                    coef = temp_won / duration_minutes
                    if coef > 0:
                        coef_list.append(coef)
    if not coef_list == []:
        average_coef = numpy.average(coef_list)
        return average_coef
    else :
        print "No data with heater_state on found."
        exit(-1)

if __name__=="__main__":
    print compute_deg_by_min()