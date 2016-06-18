from flask import session
import pymongo
from dsd.sys.docker.pydocker import PyDocker as Docker
from dsd.sys.docker.nvdocker import NvDocker as NVD
import hashlib, binascii
import socket


def getDB():
    client = pymongo.MongoClient()
    db = client.dsd
    return db
db = getDB()

STATIC_SALT = 'jafdNDxe5^M^Zk4v'
def encrypt_password(password, username, salt):
    salt = STATIC_SALT + username + password + salt
    dk = hashlib.pbkdf2_hmac('sha256', password, salt, 100000)
    return binascii.hexlify(dk)

def check_login(username, password):
    user = db.users.find_one({'username':username})
    if not user:
        return None, 'No such user!'
    elif encrypt_password(password, username, user['salt']) == user['password']:
        return user, 'Login succeed!'
    else:
        return None, 'Password mismatch!'

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
