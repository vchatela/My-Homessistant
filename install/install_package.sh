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
cd $MYH_HOME/libs/Adafruit_Python_DHT
python setup.py install
## wiringPi
apt-get install gcc
cd $MYH_HOME/libs/wiringPi
./build
## For chacon relais
apt-get install g++
g++ $MYH_HOME/libs/radio_relais/radioEmission.cpp -o bin/radioEmission -lwiringPi
chmod 777 bin/radioEmission
chmod +s bin/radioEmission

# For checking parsing json
apt-get install jq -y
# For killing flask
pip install psutil

# Cleanup
apt-get autoremove -y