#!/usr/bin/python
# -*- coding: utf-8 -*-

import dsd
import os

if __name__ == "__main__":
    if 'DSD_DEV' in os.environ and os.environ['DSD_DEV']=='1':
        dsd.DSD.start(dev=True)
    else:
        dsd.DSD.start()
