#!/bin/bash

DB_PATH=/data/db
if [ ! -e $DB_PATH ]; then
    echo "Create database dir"
    mkdir -p $DB_PATH
fi

if [ -z `pgrep mongod` ]; then
echo "Start mongod"
mongod --fork --syslog --dbpath $DB_PATH
echo "Sleep 1 second for mongodb to get prepared"
sleep 1s
fi

echo "Initial database"
python $(dirname $0)/init_db.py $1
