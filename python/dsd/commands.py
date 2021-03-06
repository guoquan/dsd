import pymongo
import socket
import hashlib, binascii, os
import pprint
from dsd.ui.web.utils.basic import get_docker, get_nvd
from dsd.ui.web.utils.basic import encrypt_password, UserTypes

def create_sample_data(db):
    config = {}

    # docker config
    # detect the runtime environment
    # opt x.1: try dockerhost hostname
    dockerhost = 'dockerhost'
    try:
        # try resolve dockerhost and init using it
        socket.gethostbyname('dockerhost')
    except socket.error:
        # if failed, now we have to guess the host
        # opt x.2: try default docker network
        dockerhost = '172.17.0.1'
        #if not avaliable
        # opt x.3: try default boot2docker
        #dockerhost = '192.168.99.100'

    config['docker'] = {}
    sock = '/var/run/docker.sock'
    if os.path.exists(sock):
        # opt 1: using the unix sock
        config['docker']['url'] = 'unix://' + sock
        config['docker']['tls'] = {'use_tls':False}
    else:
        # opt 2: using tls
        # opt 2.x: say we have a dockerhost x
        cert_path = os.path.expanduser('~/.docker')
        client_cert = 'cert.pem'
        client_key = 'key.pem'
        ca = 'ca.pem'
        path_client_cert = os.path.join(cert_path, client_cert)
        path_client_key = os.path.join(cert_path, client_key)
        path_ca = os.path.join(cert_path, ca)
        if os.path.isfile(path_client_cert) and os.path.isfile(path_client_key):
            # opt 2.x.1: using tls client verification
            config['docker']['url'] = 'tcp://' + dockerhost + ':2376'
            config['docker']['tls'] = {'use_tls':True,
                                       'path_client_cert':path_client_cert,
                                       'path_client_key':path_client_key}
            if os.path.isfile(path_ca):
                # opt 2.x.1.1: using ca
                config['docker']['tls']['path_ca'] = path_ca
        else:
            # opt 2.x.2: using unencrypted tcp
            config['docker']['url'] = 'tcp://' + dockerhost + ':4243'
            config['docker']['tls'] = {'use_tls':False}

    # nvd is simpler
    config['nvd']={}
    config['nvd']['url'] = 'http://' + dockerhost + ':3476'

    # default config
    config['default'] = {}
    config['default']['user'] = {}
    config['default']['user']['max_container'] = 4
    config['default']['user']['max_live_container'] = 2
    config['default']['user']['max_gpu'] = 1
    config['default']['user']['max_disk'] = 1024

    # resource config
    config['resource'] = {}
    config['resource']['max_gpu_assignment'] = 0
    config['resource']['volume'] = {}
    config['resource']['volume']['workspaces'] = u'workspaces'
    config['resource']['volume']['data'] = u'data'

    # environment config
    config['env'] = {}

    # password encryption config
    config['encrypt'] = {}
    config['encrypt']['salt'] = os.urandom(16).encode('hex')
    config['encrypt']['algorithm'] = 'sha256'
    if callable(getattr(hashlib, 'pbkdf2_hmac', None)):
        # if pbkdf2_hmac is avaliable, use it
        config['encrypt']['method'] = {'method':'pbkdf2_hmac',
                                       'param':{'dklen': None}}
        config['encrypt']['iter'] = 100000
    else:
        # otherwise, fallback to simple implement multiple round digest,
        #   but *much* less secure and posibly slow.
        config['encrypt']['method'] = {'method':'simple', 'param':{}}
        config['encrypt']['iter'] = 100000

    print '-' * 20
    print '[dsd] Save config:'
    db.config.save(config)
    pprint.pprint(config)

    # add gpu lists
    print '-' * 20
    print '[dsd] Save GPU list:'
    nvd = get_nvd(test_config=config)
    if nvd:
        for i in range(len(nvd.gpuInfo())):
            gpu = {'index':i,
                   'container_oids':[]}
            db.gpus.save(gpu)
            pprint.pprint(gpu)
    else:
        print '[dsd] Could not connect to nvidia-docker host'

    # add some init users
    user1={}
    user1['username'] = 'user1'
    user1['active'] = True
    user1['type'] = UserTypes.Administrator
    user1['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user1['password'] = encrypt_password(password, user1['username'], user1['salt'])
    print '-' * 20
    print '[dsd] Save user (administrator):'
    db.users.save(user1)
    pprint.pprint(user1)

    user2={}
    user2['username'] = 'user2'
    user2['active'] = True
    user2['type'] = UserTypes.User
    user2['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user2['password'] = encrypt_password(password, user2['username'], user2['salt'])
    user2['max_container'] = config['default']['user']['max_container']
    user2['max_live_container'] = config['default']['user']['max_live_container']
    user2['max_gpu'] = config['default']['user']['max_gpu']
    user2['max_disk'] = config['default']['user']['max_disk']
    print '-' * 20
    print '[dsd] Save user:'
    db.users.save(user2)
    pprint.pprint(user2)
