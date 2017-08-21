#!/usr/bin/env bash

# Argument Parameters
if [ "$#" -ne 1 ]; then
    echo "sudo bash setup.py --home /path/to/home/folder/app"
fi

MYH_HOME="$1"

# Install package
./install_package.sh

# Create databases and users
./mysql/mysql.sh

# Load environment

# Add to crontab * * * * * python manager.py
#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "* * * * * /usr/bin/python $MYH_HOME/core/weather.py >> $MYH_HOME/weather/logs.txt" >> mycron
#install new cron file
crontab mycron
rm mycron