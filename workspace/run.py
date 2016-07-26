#!/usr/bin/python
# -*- coding: utf-8 -*-

from dsd.ui.web import app
import os

if __name__ == "__main__":
    if 'DSD_DEV' in os.environ and os.environ['DSD_DEV']=='1':
        # NB: flask app debug mode must be invoke in a file directly run from outside
        #       because flask debug mode restarts app using this file
        app.run(host='0.0.0.0', debug=True)
    else:
        app.run(host='0.0.0.0')
