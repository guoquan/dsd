#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt, sys
import dsd
from dsd.ui.web.utils.basic import db, get_db

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

    dsd.create_sample_data(db)

if __name__ == "__main__":
    main()
