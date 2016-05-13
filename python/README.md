# python docker interface

## Requirements

```bash
pip install docker-py
```

## tutorial usage
See `tutorial-pydocker.ipynb`.


# dsd-console

## prepare database

We use mongodb. Initialize database by the script `init_db.sh`.

```bash
chmod u+x init_db.sh
./init_db.sh
```

The script will also initialize directories, database, and basic structure that are needed if they are not exist.
Otherwise it will purely run mongodb deamon.

## evaluate database

It is possible to connect to the database with mongodb client and see what is in it.

```bash
mongo
```

Inside mongodb client console, we can inspect `users`.

```
use db_dsd
db.users.find()
```

### run server

The server is a `flask` web app.
Simply run `run.py`.

```bash
chmod u+x run.py
./run.py
```
