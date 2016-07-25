import logging
import pymongo
from dsd.sys.docker.pydocker import PyDocker as Docker
from dsd.sys.docker.pydocker import HC, HCP, ContainerState
from dsd.sys.docker.nvdocker import NvDocker as NVD
import hashlib, binascii
import itertools
import re
import os
import random
import socket

_logger = logging.getLogger()

class UserTypes:
    STR = ['Administrator', 'User']
    Administrator, User = range(2)

def get_db():
    client = pymongo.MongoClient()
    db = client.dsd
    return db, client
db, client = get_db()

_docker = None
def get_docker(update=False, base_url=None, config=None):
    global _docker
    if update or not _docker:
        if not base_url:
            if not config:
                config = db.config.find_one()
            base_url = config['docker_url']
        if config['docker_tls']['use_tls']:
            tls = {'client_cert': (config['docker_tls']['path_client_cert'],
                                   config['docker_tls']['path_client_key']),
                   'verify': config['docker_tls']['path_ca'],
                   'assert_hostname': False}
        else:
            tls={}
        _docker = Docker(base_url, **tls)
        if not _docker.alive():
            _docker = None
        update_env(_docker)
    return _docker

_nvd = None
def get_nvd(update=False, base_url=None, config=None):
    global _nvd
    if update or not _nvd:
        if not base_url:
            if not config:
                config = db.config.find_one()
            base_url=config['nvd_url']
        _nvd = NVD(base_url)
        if not _nvd.alive():
            _nvd = None
    return _nvd

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

_methods = {"simple": simple, 'pbkdf2_hmac': pbkdf2_hmac}

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
        dk = _methods[config['encrypt_method']['method']](digest, password, salt, iterations,
                                                **config['encrypt_method']['param'])
    except KeyError:
        _logger.warning('Encryption method %s is not supported, plain password is used.' % config['encrypt_method']['method'])
        dk = password
    return dk

def save_name(name, accpet=r'a-zA-Z0-9_\.\-'):
    return re.sub(r'[^' + accpet + r']', '_', name)

def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

def gpu_dispatch(num):
    # TODO control which dev to be assigned
    config = db.config.find_one()
    max_gpu_assignment = config['resource']['max_gpu_assignment']
    nvd = get_nvd()
    if max_gpu_assignment:
        gpus = [gpu['index'] for gpu in list(db.gpus.find()) \
                    if len(gpu['container_oids']) < max_gpu_assignment ]
    else:
        gpus = [gpu['index'] for gpu in list(db.gpus.find())]
    if len(gpus) < num:
        raise SystemError('There is no sufficient GPU(s) for your request now. Please adjust your setting or wait for GPU resources.')
    # use random dispatch
    return random.sample(gpus, num)

def groupby(data, keyfunc):
    data = sorted(data, key=keyfunc)
    keys = []
    groups = []
    for k, g in itertools.groupby(data, keyfunc):
        keys.append(k)
        groups.append(list(g))      # Store group iterator as a list
    return dict(zip(keys, groups))

def dict_deep_update(dst, src):
    if not isinstance(dst, dict):
        raise ValueError('First parameter dst must be a dict.')
    for k, v in src.iteritems():
        if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
            dict_deep_update(dst[k], v)
        elif k in dst and isinstance(dst[k], list) and isinstance(v, list):
            dst[k].extend(v)
        else:
            dst[k] = v

VOLUME_PREFIX = u'/volumes'
def update_env(docker):
    if docker:
        dsd_ps = docker.container(socket.gethostname())
        host_volume_prefix = None
        if dsd_ps:
            mounts = dsd_ps['raw']['Mounts']
            for mount in mounts:
                if mount['Destination'] == VOLUME_PREFIX:
                    host_volume_prefix = mount['Source']
                    break
        # if not detected, we have to assume it is in the same filesystem
        if not host_volume_prefix:
            host_volume_prefix = VOLUME_PREFIX
        volume_base = {'volume_prefix':VOLUME_PREFIX,
                       'host_volume_prefix':host_volume_prefix}
    else:
        volume_base = {'volume_prefix':VOLUME_PREFIX,
                       'host_volume_prefix':'<Cannot connect to the docker host>'}
    config = db.config.find_one()
    config['env'].update(volume_base)
    db.config.save(config)
