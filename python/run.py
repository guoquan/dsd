#!/usr/bin/python
# -*- coding: utf-8 -*-

from dsd.ui.web import app

if __name__ == "__main__":
    app.run(host='0.0.0.0',
            debug = True)
