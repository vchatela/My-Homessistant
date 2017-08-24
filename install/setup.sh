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
echo "* * * * * export MYH_HOME=$MYH_HOME ; /usr/bin/python $MYH_HOME/core/weather.py --info " >> mycron
#install new cron file
crontab mycron
rm mycron

# bashrc or zshrc source myh_rc
#echo -e "\nexport MYH_HOME='$MYH_HOME'\n" >> ~/.zshrc
echo -e "\nexport MYH_HOME='$MYH_HOME'\n" >> ~/.bashrc