#!/usr/bin/env bash

# Argument Parameters
if [ "$#" -ne 2 ]; then
    echo "sudo bash setup.py /path/to/home/folder/app user"
fi

export MYH_HOME="$1"
echo "export MYH_HOME=$MYH_HOME" >> ~/.bashrc
# Install package
./install_package.sh

# Create databases and users
./mysql/mysql.sh

# Load environment

# Add to crontab * * * * * python manager.py
#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "*/10 * * * * export MYH_HOME=$MYH_HOME ; export PYTHONPATH=\$PYTHONPATH:$MYH_HOME ; /usr/bin/python $MYH_HOME/core/weather.py >/dev/null 2>&1" >> mycron
echo "* * * * * export MYH_HOME=$MYH_HOME ; export PYTHONPATH=\$PYTHONPATH:$MYH_HOME ; /usr/bin/python $MYH_HOME/core/manager.py >/dev/null 2>&1" >> mycron
#install new cron file
crontab mycron
rm mycron

# bashrc or zshrc source myh_rc
zshrc=/home/"$2"/.zshrc
bashrc=/home/"$2"/.bashrc
echo -e "export MYH_HOME='$MYH_HOME'\n" >> $zshrc
echo -e "export PYTHONPATH=\$PYTHONPATH:$MYH_HOME\n" >> $zshrc
echo -e "export MYH_HOME='$MYH_HOME'\n" >> $bashrc
echo -e "export PYTHONPATH=\$PYTHONPATH:$MYH_HOME\n" >> $bashrc

# Compile libraries
g++ libs/radio_relais/radioEmission.cpp -o bin/radioEmission -lwiringPi
chmod 777 bin/radioEmission
chmod +s bin/radioEmission