#!/bin/bash

DB_PATH=/data/db
if [ ! -e $DB_PATH ]; then
    echo "[dsd] Create database dir"
    mkdir -p $DB_PATH
fi

if [ -z `pgrep mongod` ]; then
echo "[dsd] Start mongod"
mongod --fork --syslog --dbpath $DB_PATH
echo "[dsd] Sleep 1 second for mongodb to get prepared"
sleep 1s
fi

echo "[dsd] Initialize database"
python $(dirname $0)/init_db.py $1
