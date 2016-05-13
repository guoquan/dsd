# dsd console web

## setup

### prepare database

We use mongodb. Initialize database by the script `init_db.sh`.
The script will also initialize directories, database, and basic structure that are needed if they are not exist.
Otherwise it will purely run mongodb deamon.

DB name: `db_dsd`
collections:
| name  | description |
|-------|-------------|
| `users` | user table  |

users properties:
| name  | description |
|-------|-------------|
| `Username` | username |
| `Password` | (TODO, hashed) password |
| `User_Type` | `'Admin'`/`'Common'` |
| `Max_Container_Count` | max number of contrainers |
| `Max_Disk_Space` | max disk space size|

### evaluate database

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
Simply run `site.py`.

```bash
python site.py
```
