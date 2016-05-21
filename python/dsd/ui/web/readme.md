# dsd console web

## database

DB name: `db_dsd`
collections:

| name  | description |
| ------- | ------------- |
| `users` | user table  |
| `containers` | container table  |

users properties:

| name  | description |
| ------- | ------------- |
| `Username` | username |
| `Password` | (TODO, hashed) password |
| `User_Type` | `'Admin'`/`'Common'` |
| `Max_Container_Count` | max number of contrainers |
| `Max_Disk_Space` | max disk space size|

containers properties:

| name  | description |
| ------- | ------------- |
| `container_name` | container_name|
| `container_id` | container_id  |
| `image` | base image |
| `created ` | created time |
| `user` | owner |
| `gpu` | gpu list |
| `max_disk ` | max_disk spaces |
| `max_memory`| max_memory |