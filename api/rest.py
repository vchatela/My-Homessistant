import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

import deg_by_min

app = Flask(__name__)


@app.route("/")
def hello():
    return "Welcome to my world !"


@app.route("/__test")
def test():
    return "running"


@app.route("/deg_by_min")
def compute():
    return str(deg_by_min.compute_deg_by_min())


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
