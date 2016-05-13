#!/bin/bash

if [ -e /data/db ]; then
    mongod --fork --syslog --dbpath /data/db
else
    mkdir -p /data/db
    mongod --fork --syslog --dbpath /data/db
    mongo init_db.js
fi
