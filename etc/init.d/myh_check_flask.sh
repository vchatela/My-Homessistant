#!/bin/bash

state=$(cat "$MYH_HOME/data/myh.json" | jq -r '.flask_state')
if [ "$state" == "ON" ]; then
    # Test flask is really running
    content=$(curl --silent -L "192.168.1.76:5005/__test")
    if [ "$content" == "running" ]; then
        exit 0
    else
        exit -1
    fi
fi
exit 0