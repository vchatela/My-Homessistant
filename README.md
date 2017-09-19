# My-Homessitant

## Warning Security
This application is designed to be used inside a **private** network. Do not expose the raspberry-pi outside of your network, it would be at your risk.

My personal recommendation is to expose a secure hardware (the raspberry isn't the best secured) as a NAS and connect yourself to it by using VPN.

## Architecture
- api : usefull myh_tools
	- **rest.py** : flask implementation
	- **deg_by_min.py** : compute degrees won by minutes under heater
- bin : contain compiled binaries from libs
- core: main functionalities
	- **database.py** : allow connections to mysql database easily
	- **hall.py** : get hall sensor value
	- **weather.py** : get values from sensors and request to insert into database
	- **manager.py** : manage all the plugs using data files that have been updated by **weather.py**
- data: contain references values
	- **myh.json**: state of myh and configuration ports as radio wiringpi port
	- **myh_db.json** : database configuration credentials 
	- **plugs.json** : informations on plugs, type, reference value etc.
	- **weather.json** : last information computed by **weather.py** 
- etc : contain conf files
	- init.d : 
		- **myh.py** : inform state and launch/stop/restart _flask_ and _app_ services
		- **myh_check_flask.sh** : ensure flask is running for android app
- install : contain installation scripts
    - **setup.sh** : the only script to launch
- libs : submodules
    - **Adafruit DHT** for AM2302 sensor
    - **Radio_relais** to use HF radio signals
    - **WiringPi** required for radio_relais

## Installation
```
git clone --recursive My-Homessistant.git
cd My-Homesisstant
chmod +x install/setup.sh
sudo -H bash install/setup.sh /abs/path/to/My-Homessitant user_to_run
```

## Tech
### Git
* Submodules
* Branches
* Issues
* Project
* SSH-keys
### Continious Integration
* Travis
* Docker
### Standards
|Langage | Standard used|
| ------ | ------       |
|Python  |  PEP8        |
