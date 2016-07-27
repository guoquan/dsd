# DSD Console Database

*TODO* provide a document for the database

DB name: `dsd`
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

Some notes provided by @Fe:
using mongodb
DB name: db_dsd
collection names:
    users --user table
        --example document: db.users.save({'Username':'user1','Password':'123','User_Type':'Admin','Max_Container_Count':3,'Max_Disk_Space':1024}) db.users.save({'Username':'user2','Password':'123','User_Type':'Common','Max_Container_Count':3,'Max_Disk_Space':1024})
