#!/bin/bash
#Create User
CREATE USER 'home_user'@'localhost';GRANT USAGE ON *.* TO 'home_user'@'localhost' WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_USER_CONNECTIONS 0;GRANT ALL PRIVILEGES ON `home_user\_%`.* TO 'home_user'@'localhost';
#Create Database
CREATE DATABASE Homessitant;
USE Homessitant;
