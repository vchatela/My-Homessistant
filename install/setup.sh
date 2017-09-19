#!/usr/bin/env bash

# Argument Parameters
if [ "$#" -ne 2 ]; then
    echo "sudo bash setup.sh /path/to/home/folder/app user"
    exit -1
fi

export MYH_HOME="$1"
export MYH_USER="$2"

# Execute rights for sh scripts
chmod +x $MYH_HOME/install/*.sh $MYH_HOME/install/mysql/*.sh

# Prepare shell
zshrc=/home/$MYH_USER/.zshrc
bashrc=/home/$MYH_USER/.bashrc
echo "export MYH_HOME=$MYH_HOME" >> $bashrc
echo "export MYH_HOME=$MYH_HOME" >> $zshrc

# Install package
$MYH_HOME/install/install_package.sh

# Create databases and users
$MYH_HOME/install/mysql/mysql.sh

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
echo -e "export MYH_HOME='$MYH_HOME'\n" >> $zshrc
echo -e "export PYTHONPATH=\$PYTHONPATH:$MYH_HOME\n" >> $zshrc
echo -e "export MYH_HOME='$MYH_HOME'\n" >> $bashrc
echo -e "export PYTHONPATH=\$PYTHONPATH:$MYH_HOME\n" >> $bashrc