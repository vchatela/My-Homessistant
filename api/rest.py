import json
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request

import core.database as db
import deg_by_min
from core.manager import Manager

app = Flask(__name__)


@app.route("/__test")
def test():
    return "running"


@app.route("/command")
def command():
    action = request.args.get("action").lower()
    plug = request.args.get("plug")
    if not action in ["on", "off"]:
        return "Error - action must be on or off."
    with open(os.path.join(os.environ["MYH_HOME"], "data", "plugs.json"), 'r') as plugs_file:
        plug_data = json.load(plugs_file)

    if not plug in plug_data:
        return "Error - " + plug + " is not a plug entry."
    else:
        plug_data[plug]["plug_state"] = action
        # save the action for manager
        with open(os.path.join(os.environ["MYH_HOME"], "data", "plugs.json"), 'w') as plugs_file:
            json.dump(plug_data, plugs_file)
        # do the action
        my_manager = Manager()
        my_manager.turn_on_off_plug(plug, action)

    return "done"


@app.route("/deg_by_min")
def compute():
    return str(deg_by_min.compute_deg_by_min())


@app.route("/charts_dev")
def charts_dev():
    if not 'day' in request.args:
        day = 7
    else:
        day = request.args.get('day')
    myh_db = db.MyHomessistantDatabase()
    myh_db.connection()
    data_dict = myh_db.get_charts_dataset(day)

    # Get act temperature
    with open(os.path.join(os.environ["MYH_HOME"], "data", "weather.json"), 'r') as weather_file:
        t_act = json.load(weather_file)["temp_avg"]
    data_dict["t_act"] = "{0:.2f}".format(t_act)

    # Json data_sed ready to be sent to
    myh_db.close()
    return render_template("charts_dev.html", **locals())


@app.route("/dashboard")
def charts():
    if not 'day' in request.args:
        day = 7
    else:
        day = request.args.get('day')
    myh_db = db.MyHomessistantDatabase()
    myh_db.connection()
    data_dict = myh_db.get_charts_dataset(day)

    # Get act temperature
    with open(os.path.join(os.environ["MYH_HOME"], "data", "weather.json"), 'r') as weather_file:
        t_act = json.load(weather_file)["temp_avg"]
    data_dict["t_act"] = "{0:.2f}".format(t_act)

    # Json data_sed ready to be sent to
    myh_db.close()
    return render_template("dashboard.html", **locals())


if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)  # use the native logger of flask
    app.logger.disabled = False
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'rest.log')

    handler = RotatingFileHandler(logfile, mode='a', maxBytes=5 * 1024 * 1024,
                                  backupCount=2, encoding=None, delay=0)
    handler.setFormatter(formatter)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    app.run(debug=True, port=5005, host="0.0.0.0")
