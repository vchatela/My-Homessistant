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

LINE='export MYH_HOME=$MYH_HOME'
grep -qF "$LINE" "$FILE" || echo "$LINE" >> "$bashrc"
grep -qF "$LINE" "$FILE" || echo "$LINE" >> "$zshrc"

LINE="export PYTHONPATH=\$PYTHONPATH:$MYH_HOME"
grep -qF "$LINE" "$FILE" || echo "$LINE" >> "$zshrc"
grep -qF "$LINE" "$FILE" || echo "$LINE" >> "$bashrc"

# Install package
echo -e "\e[32mInstall Package\e[0m"
$MYH_HOME/install/install_package.sh

echo -e "\e[32mMysql Configuration\e[0m"
# Configure PHP MY ADMIN
LINE='Include /etc/phpmyadmin/apache.conf'
FILE='/etc/apache2/apache2.conf'
grep -qF "$LINE" "$FILE" || echo "$LINE" >> "$FILE"
# Restart apache2
/etc/init.d/apache2 restart

# Create databases and users
$MYH_HOME/install/mysql/mysql.sh

# Add to crontab * * * * * python manager.py
#write out current crontab
crontab -u $MYH_USER -l > mycron
#echo new cron into cron file
LINE='*/10 * * * * export MYH_HOME=$MYH_HOME ; export PYTHONPATH=\$PYTHONPATH:$MYH_HOME ; /usr/bin/python $MYH_HOME/core/weather.py >/dev/null 2>&1'
grep -qF "$LINE" "$FILE" || echo "$LINE" >> mycron
LINE="* * * * * export MYH_HOME=$MYH_HOME ; export PYTHONPATH=\$PYTHONPATH:$MYH_HOME ; /usr/bin/python $MYH_HOME/core/manager.py >/dev/null 2>&1"
grep -qF "$LINE" "$FILE" || echo "$LINE" >> mycron
#install new cron file
crontab mycron
rm mycron