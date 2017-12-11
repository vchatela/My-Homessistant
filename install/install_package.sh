#!/bin/bash
apt-get install debconf -y
# For PHP MY ADMIN
echo -e "\e[32mEnter again '$MYSQL_PASSWD' for mysql root password\e[0m"
echo "mysql-server-5.7 mysql-server/root_password password $MYSQL_PASSWD" | debconf-set-selections
echo "mysql-server-5.7 mysql-server/root_password_again password $MYSQL_PASSWD" | debconf-set-selections
apt-get install mysql-server-5.7 -y
echo -e "\e[32mYou can set the phpmyadmin password you want\e[0m"
apt-get install phpmyadmin -y
# For mysql client
apt-get install mysql-client -y
# For pip
apt-get install python-pip
pip install --upgrade pip
# For OpenWeatherMap wrapper
pip install pyowm
pip install rson
# For rest API
pip install jsondiff
# For FCM
pip install pyfcm

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