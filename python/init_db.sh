#!/bin/bash

if [ -e /data/db ]; then
    mongod --fork --syslog --dbpath /data/db
else
    mkdir -p /data/db
    mongod --fork --syslog --dbpath /data/db
    echo "Sleep 1 second for mongodb to get prepared."
    sleep 1s
    mongo init_db.js
fi
