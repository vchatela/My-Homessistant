#!/bin/bash
# For PHP MY ADMIN
apt-get install mysql-server php5 php5-mysql phpmyadmin
# For OpenWeatherMap wrapper
pip install pyowm
pip install rson
# Install imported Libraries
## Adafruit Python DHT
apt-get install build-essential python-dev
cd $MYH_HOME/libs
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
python setup.py install