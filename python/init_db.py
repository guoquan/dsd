#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt, sys
import pymongo
import socket
import hashlib, binascii, os
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
        config['docker_url'] = 'http://dockerhost:4243'
        config['nvd_url'] = 'http://dockerhost:3476'
    except socket.error:
        # if failed, fallback to local connect
        config['docker_url'] = 'unix:///var/run/docker.sock'
        config['nvd_url'] = 'http://localhost:3476'

    # user config
    config['default_max_container'] = 3
    config['default_max_disk'] = 1024

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

    print 'Save config:'
    print config
    db.config.save(config)

    # add some init users
    user1={}
    user1['username'] = 'user1'
    user1['type'] = UserTypes.Administrator
    user1['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user1['password'] = encrypt_password(password, user1['username'], user1['salt'])
    print 'Save user:'
    print user1
    db.users.save(user1)

    user2={}
    user2['username'] = 'user2'
    user2['type'] = UserTypes.User
    user2['salt'] = os.urandom(16).encode('hex')
    password = '123'
    user2['password'] = encrypt_password(password, user2['username'], user2['salt'])
    user2['max_container'] = 3
    user2['max_disk'] = 1024
    print 'Save user:'
    print user2
    db.users.save(user2)

if __name__ == "__main__":
    main()
