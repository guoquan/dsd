import logging
from flask import session, redirect, url_for
import pymongo
from dsd.sys.docker.pydocker import PyDocker as Docker
from dsd.sys.docker.nvdocker import NvDocker as NVD
import hashlib, binascii
import socket

_logger = logging.getLogger()

class UserTypes:
    Administrator, User = range(2)

def get_db():
    client = pymongo.MongoClient()
    db = client.dsd
    return db, client
db, client = get_db()

def encrypt_password(password, username, user_salt,
        iterations=None, digest=None):
    _logger.debug('encrypt_password: %s | %s | %s | %s | %s' % (password, username, user_salt, iterations, digest))
    config = db.config.find_one()
    if not iterations:
        iterations = config['encrypt_iter']
    if not digest:
        digest = hashlib.new(config['encrypt_algorithm'])

    #password = force_bytes(password)
    salt = config['encrypt_salt'] + password + user_salt + username
    #salt = force_bytes(salt)

    if config['encrypt_method']['method'] == 'pbkdf2_hmac':
        dk = hashlib.pbkdf2_hmac(digest.name(), password, salt, iterations,
                                **config['encrypt_method']['param'])
        dk = binascii.hexlify(dk)
    elif config['encrypt_method']['method'] == 'simple':
        dk = password
        for i in range(iterations):
            d = digest.copy()
            if i % 2:
                d.update(dk)
                d.update(salt)
            else:
                d.update(salt)
                d.update(dk)
            dk = d.hexdigest()
    else:
        _logger.warning('Encryption method %s is not supported, plain password is used.' % config['encrypt_method']['method'])
        dk = password
    return dk

def check_login(username, password):
    user = db.users.find_one({'username':username})
    if not user:
        return None, 'No such user!'
    elif encrypt_password(password, user['username'], user['salt']) == user['password']:
        del user['_id']
        return user, 'Login succeed!'
    else:
        _logger.debug('check_login: %s | %s | %s' % (password, user['username'], user['salt']))
        _logger.debug('check_login: %s != %s' % (encrypt_password(password, user['username'], user['salt']), user['password']))
        return None, 'Password mismatch!'

def invalid_login_redirect(message='Invalid login. Login again.', source='index', **params):
    flash(message)
    return redirect(url_for(source, **params))

def is_login():
    return 'is_login' in session and session['is_login']

def is_admin():
    return is_login() and session['user']['type'] is UserTypes.Administrator

def get_docker():
    try:
        socket.gethostbyname('dockerhost')
        base_url = 'http://dockerhost:4243'
    except socket.error:
        base_url = 'unix:///var/run/docker.sock'

    return Docker(base_url=base_url)
docker = get_docker()

def get_nvd():
    try:
        socket.gethostbyname('dockerhost')
        base_url = 'http://dockerhost:3476'
    except socket.error:
        base_url = 'http://localhost:3476'

    return NVD(base_url=base_url)
nvd = get_nvd()
