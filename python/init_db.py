#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt, sys
import pymongo
import socket
import hashlib, binascii, os
import pprint
from dsd.ui.web.utils import db
from dsd.ui.web.utils import get_db, encrypt_password, UserTypes

def usage():
    print 'Usage:'
    print sys.argv[0], '[option]'
    print 'Options:'
    print '-h --help', '\t', 'Help message.'
    print '-f --force', '\t', 'Force save new ones.'
    print '-e --erase', '\t', 'Erase the old database and init new one.'

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hfe", ["help", "output="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    force = False
    erase = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--force"):
            force = True
        elif o in ("-e", "--erase"):
            erase = True
        else:
            assert False, "unhandled option"

    global db
    if erase:
        _, client = get_db()
        client.drop_database('dsd')
        db, _ = get_db()
    if not db:
        print 'Can\'t connet to database'
        sys.exit(1)
    if not force and db.config.find_one():
        print 'Database is not empty!'
        sys.exit(1)

    init(db)

def init(db):
    config = {}

    # docker config
    try:
        # try resolve dockerhost and init using it
        socket.gethostbyname('dockerhost')
        config['docker_url'] = 'tcp://dockerhost:4243'
        config['nvd_url'] = 'http://dockerhost:3476'
    except socket.error:
        # if failed, fallback to local connect
        config['docker_url'] = 'unix:///var/run/docker.sock'
        config['nvd_url'] = 'http://localhost:3476'
    config['docker_tls'] = {'use_tls':False,
                            'path_client_cert':None,
                            'path_client_key':None,
                            'path_ca':None}
    ''' for boot2docker using virtalbox
    config['docker_url'] = tcp://192.168.99.100:2376
    config['docker_tls'] = {'use_tls':True,
                            'path_client_cert':'~/.docker/machine/machines/default/certs/cert.pem'(!on the host!),
                            'path_client_key':'~/.docker/machine/machines/default/certs/key.pem',
                            'path_ca':'~/.docker/machine/machines/default/certs/ca.pem'}
    '''

    # user config
    config['default_user_max_container'] = 3
    config['default_user_max_live_container'] = 2
    config['default_user_max_gpu'] = 1
    config['default_user_max_disk'] = 1024

    # resource config
    config['default_resource_max_gpu_usage'] = 2

    # password encryption config
    config['encrypt_salt'] = os.urandom(16).encode('hex')
    config['encrypt_algorithm'] = 'sha256'
    if callable(getattr(hashlib, "pbkdf2_hmac", None)):
        # if pbkdf2_hmac is avaliable, use it
        config['encrypt_method'] = {'method': 'pbkdf2_hmac', 'param':{'dklen': None}}
        config['encrypt_iter'] = 100000
    else:
        # otherwise, fallback to simple implement multiple round digest,
        #   but *much* less secure and posibly slow.
        config['encrypt_method'] = {'method': 'simple', 'param':{}}
        config['encrypt_iter'] = 100000

    print '-' * 20
    print 'Save config:'
    db.config.save(config)
    pprint.pprint(config)

    # add some init users
    user1={}
    user1['username'] = 'user1'
    user1['active'] = True
    user1['type'] = UserTypes.Administrator
    user1['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user1['password'] = encrypt_password(password, user1['username'], user1['salt'])
    print '-' * 20
    print 'Save user (administrator):'
    db.users.save(user1)
    pprint.pprint(user1)

    user2={}
    user2['username'] = 'user2'
    user2['active'] = True
    user2['type'] = UserTypes.User
    user2['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user2['password'] = encrypt_password(password, user2['username'], user2['salt'])
    user2['max_container'] = config['default_user_max_container']
    user2['max_live_container'] = config['default_user_max_live_container']
    user2['max_gpu'] = config['default_user_max_gpu']
    user2['max_disk'] = config['default_user_max_disk']
    print '-' * 20
    print 'Save user:'
    db.users.save(user2)
    pprint.pprint(user2)

if __name__ == "__main__":
    main()
