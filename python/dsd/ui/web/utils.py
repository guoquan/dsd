from flask import session
import pymongo
from dsd.sys.docker.pydocker import PyDocker as Docker
from dsd.sys.docker.nvdocker import NvDocker as NVD
import socket

def db():
    client = pymongo.MongoClient()
    db = client.db_dsd
    return db

def encrypt_password(password):#TBC
    return password

def check_login(username, password):
    cursor = db().users.find({'Username':username})
    if cursor.count() == 0:
        return False, 'No such user!', None
    elif encrypt_password(password) == cursor[0]['Password']:
        return True, 'Login succeed!', cursor[0]['User_Type']
    else:
        return False, 'Password mismatch!', None

def is_login():
    return 'Is_Login' in session and session['Is_Login'] == '1'
            
def is_admin():
    return is_login() and session['User_Type'] == 'Admin'

def docker():
    try:
        socket.gethostbyname('dockerhost')
        base_url = 'http://dockerhost:4243'
    except socket.error:
        base_url = 'unix:///var/run/docker.sock'

    return Docker(base_url=base_url)

def nvd():
    try:
        socket.gethostbyname('dockerhost')
        base_url = 'http://dockerhost:3476'
    except socket.error:
        base_url = 'http://localhost:3476'

    return NVD(base_url=base_url)
    