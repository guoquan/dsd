import logging
from flask import session, redirect, url_for, flash, request
from urlparse import urlparse, urljoin
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

def simple(digest, password, salt, iterations):
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
    return dk

def pbkdf2_hmac(digest, password, salt, iterations, **params):
    dk = hashlib.pbkdf2_hmac(digest.name(), password, salt, iterations,
                            **params)
    dk = binascii.hexlify(dk)
    return dk

methods = {"simple": simple, 'pbkdf2_hmac': pbkdf2_hmac}

def encrypt_password(password, username, user_salt,
                    iterations=None, digest=None):
    _logger.debug('encrypt_password: %s | %s | %s | %s | %s' % (password, username, user_salt, iterations, digest))
    config = db.config.find_one()
    if not iterations:
        iterations = config['encrypt_iter']
    if not digest:
        digest = hashlib.new(config['encrypt_algorithm'])

    # get a larger salt
    salt = config['encrypt_salt'] + password + user_salt + username

    # generate the encrypted password
    try:
        dk = methods[config['encrypt_method']['method']](digest, password, salt, iterations,
                                                **config['encrypt_method']['param'])
    except KeyError:
        _logger.warning('Encryption method %s is not supported, plain password is used.' % config['encrypt_method']['method'])
        dk = password
    return dk

def check_login(username, password):
    user = db.users.find_one({'username':username})
    if not user:
        return None, 'No such user!'
    elif encrypt_password(password, user['username'], user['salt']) == user['password']:
        return user, 'Login succeed!'
    else:
        _logger.debug('check_login: %s | %s | %s' % (password, user['username'], user['salt']))
        _logger.debug('check_login: %s != %s' % (encrypt_password(password, user['username'], user['salt']), user['password']))
        return None, 'Password mismatch!'

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def redirect_back(endpoint='index', **values):
    if 'next' in request.form:
        target = request.form['next']
    else:
        target = None
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def invalid_login(message='Invalid login. Login again.', next=None):
    flash(message)
    if not next:
        next = request.url
    return redirect(url_for('login', next=next))

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
