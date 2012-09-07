#!/usr/bin/env python

import os
import config

LABMANAGER_DIR = '/home/weblab/lms4labs/labmanager'

if not os.path.exists(LABMANAGER_DIR):
    raise Exception("LABMANAGER PATH NOT FOUND")

VIRTUALENV_SCRIPT = os.path.join(LABMANAGER_DIR, 'env', 'bin', 'activate_this.py')
if not os.path.exists(VIRTUALENV_SCRIPT):
    VIRTUALENV_SCRIPT = os.path.join(LABMANAGER_DIR, 'env', 'Scripts', 'activate_this.py')
    if not os.path.exists(VIRTUALENV_SCRIPT):
        raise Exception("virtualenv not found")

import sys
sys.stdout = sys.stderr

import sys
sys.path.insert(0, LABMANAGER_DIR)

execfile(VIRTUALENV_SCRIPT, dict(__file__=VIRTUALENV_SCRIPT))

from labmanager import app as application
application.config.from_object('config')
