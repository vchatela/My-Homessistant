from flask import Flask
import deg_by_min
app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome to my world !"

@app.route("/deg_by_min")
def compute():
    return deg_by_min.compute_deg_by_min()