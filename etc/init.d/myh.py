#!/usr/bin/python

"""
Script that allow to turn on/off the My_Homessistant app by stopping flask
and set state in myh.json used in the manager
"""

import getopt
import json
import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler

import psutil


def helper():
    msg = """
        Manage MyHomessistant services
        
        --help|-h|-?
            Display help
        --list|-l
            List of services to send signal to
        --signal|-s
            Send the corresponding signal to MyHomessistant services
        --debug|-d
            Print logs also into console

        :Examples:
        myh.py -h
        myh.py -s status -l flask,app
        myh.py -s stop -l flask
        myh.py -s start -l all
    """
    print msg


def mylogger(debug):
    # Logger
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logfile = os.path.join(os.environ["MYH_HOME"], 'logs', 'manager.log')

    file_handler = RotatingFileHandler(logfile, mode='a', maxBytes=5 * 1024 * 1024,
                                       backupCount=2, encoding=None, delay=0)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    mylogger = logging.getLogger('myh')
    mylogger.setLevel(logging.DEBUG)

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        mylogger.addHandler(console_handler)

    mylogger.addHandler(file_handler)
    return mylogger

def flask_is_up():
    cmd = "bash $MYH_HOME/etc/init.d/myh_check_flask.sh"
    logger.debug("Verify flask running.")
    logger.debug("Command launched : " + cmd)
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    return process.returncode

if __name__ == "__main__":
    help = False
    debug = False
    sig = "status"
    service_list = "all"

    # Get arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:s:", ["help", "list=", "signal="])
    except getopt.GetoptError:
        helper()
        exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help = True
        elif opt in ("-l", "--list"):
            service_list = arg
        elif opt in ("-s", "--signal"):
            sig = arg
        elif opt in ("-d", "--debug"):
            debug = True

    logger = mylogger(debug)
    if not sig in ["status", "start", "restart", "stop"]:
        logger.error("Wrong signal %s" % sig)
        sys.exit(1)

    if help:
        helper()
        sys.exit(0)

    if sig == "restart":
        cmd = "python %s -s stop -l %s" % (os.path.abspath(__file__), service_list)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        process.wait()
        cmd_exit = process.returncode
        logger.debug("python stop exit code %s " % str(cmd_exit))
        cmd = "python %s -s start -l %s" % (os.path.abspath(__file__), service_list)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        process.wait()
        cmd_exit = process.returncode
        logger.debug("python stop exit code %s " % str(cmd_exit))
        exit(cmd_exit)

    # Do the work
    myh_file = os.path.join(os.environ["MYH_HOME"], "data", "myh.json")

    if service_list == "all":
        service_list = "flask,app"
    for service in service_list.split(','):
        with open(myh_file, 'r') as myh_file_data:
            myh_dict = json.load(myh_file_data)
        if service == "flask":
            if sig == "status":
                if myh_dict["flask_state"].lower() == "on":
                    logger.info("Flask should be running")
                    if flask_is_up() != 0:
                        logger.info("Flask is actually stopped")
                else:
                    logger.info("Flask is not running")
                continue
            if myh_dict["flask_state"].lower() == "on":
                if sig == "start":
                    # Verification
                    if flask_is_up() != 0:
                        myh_dict["flask_state"] = "OFF"
                        with open(myh_file, 'w') as f:
                            myh_dict = json.dump(myh_dict, f)
                        logger.info("Relaunch flask")
                        # Relaunch flask
                        cmd = "python %s -s start -l flask" % (os.path.abspath(__file__))
                        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                        process.wait()
                        cmd_exit = process.returncode
                        logger.debug("Python start Flask exit code %s " % str(cmd_exit))
                    else:
                        logger.info("Flask is already running")
                elif sig == "stop":
                    flask_pid = myh_dict["flask_pid"]
                    if str(flask_pid) == "-1":
                        # App not really running
                        myh_dict["flask_state"] = "OFF"
                        with open(myh_file, 'w') as f:
                            myh_dict = json.dump(myh_dict, f)
                        logger.debug("flask_pid at -1 means flask is not really running" + str(process.pid))
                        continue
                    try:
                        os.kill(flask_pid, 0)
                    except OSError:
                        logger.warning("Flask is not running at " + str(flask_pid))
                        continue
                    try:
                        parent = psutil.Process(flask_pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                        logger.info("Flask has been stopped")
                    except OSError:
                        logger.warning("Error while killing flask at " + str(flask_pid))
            else:
                # Flask state is off
                if sig == "stop":
                    logger.info("Flask is already stopped")
                elif sig == "start":
                    rest_api = os.path.join(os.environ["MYH_HOME"], "api", "rest.py")
                    cmd = "python %s" % rest_api
                    logger.debug("Command launched : " + cmd)
                    process = subprocess.Popen(cmd, shell=True)
                    myh_dict["flask_pid"] = int(process.pid)
                    myh_dict["flask_state"] = "ON"
                    with open(myh_file, 'w') as f:
                        myh_dict = json.dump(myh_dict, f)
                    logger.info("Flask has been launched at pid " + str(process.pid))

        elif service == "app":
            if sig == "status":
                if myh_dict["app_state"].lower() == "on":
                    logger.info("App is running")
                else:
                    logger.info("App is not running")
                continue
            if myh_dict["app_state"].lower() == "on":
                if sig == "start":
                    logger.info("App is already running")
                elif sig == "stop":
                    myh_dict["app_state"] = "OFF"
                    with open(myh_file, 'w') as f:
                        json.dump(myh_dict, f)
                    logger.info("App turned off")
            else:
                # Flask state is off
                if sig == "stop":
                    logger.info("App is already stopped")
                elif sig == "start":
                    myh_dict["app_state"] = "ON"
                    with open(myh_file, 'w') as f:
                        json.dump(myh_dict, f)
                    logger.info("App turned on")
        else:
            logger.error("wrong service %s" % service)
            sys.exit(2)
