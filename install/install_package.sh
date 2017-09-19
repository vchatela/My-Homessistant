#!/bin/bash
# For PHP MY ADMIN
apt-get install mysql-server php5 php5-mysql phpmyadmin -y
# For pip
apt-get install python-pip
pip install --upgrade pip
# For OpenWeatherMap wrapper
pip install pyowm
pip install rson
# Install imported Libraries
## Adafruit Python DHT
apt-get install build-essential python-dev -y
cd Adafruit_Python_DHT
python setup.py install
# For checking parsing json
apt-get install jq -y
# For killing flask
pip install psutil

# Cleanup
apt-get autoremove -y