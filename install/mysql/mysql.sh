#!/bin/bash
if [ -z "$MYSQL_PASSWD" ]; then
    mysql -h localhost -u root < $MYH_HOME/install/mysql/mysql_query.mysql
else
    mysql -h localhost -u root -p"$MYSQL_PASSWD" < $MYH_HOME/install/mysql/mysql_query.mysql
fi