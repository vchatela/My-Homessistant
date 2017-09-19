# My-Homessitant

## Architecture
- api : restAPI
	- rest.py : flask implementation
- bin : contain binaries
	- radioEmission : allow to send radio
- core: main functionnalities
	- db.py : script db
	- plug.py : functions to turn on or turn off - manage the plug (turn on/off)
- data: contain references values
	- myh_ref_tmp.data : reference temperature file for room
	- myh_plug_state.data : plug on/off
	- myh_plug_type.data : heater/antimoustique
- etc : contain conf files
	- init.d : 
		- myh_check.sh : check for flask up, database up 
		- myh.sh : inform state and can launch/stop/restart
		- myh_android.sh : send notification to android app
	- env
		- myh_env.sh : set environment
		
## Installation
```
git clone --recursive My-Homessistant.git
cd My-Homesisstant
chmod +x install/setup.sh
sudo -H bash install/setup.sh /abs/path/to/My-Homessitant user_to_run

```