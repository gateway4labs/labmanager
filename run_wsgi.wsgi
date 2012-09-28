#!/usr/bin/env python

import os
import sys

sys.stdout = sys.stderr

LABMANAGER_DIR = os.path.dirname(__file__)

sys.path.insert(0, LABMANAGER_DIR)

import config

from labmanager import app as application
application.config.from_object('config')
