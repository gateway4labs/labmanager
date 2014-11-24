#!/usr/bin/env python

import os
import sys

sys.stdout = sys.stderr

LABMANAGER_DIR = os.path.dirname(__file__)

sys.path.insert(0, LABMANAGER_DIR)
os.chdir(LABMANAGER_DIR)

sys.stdout = open('stdout.txt', 'w', 0)
sys.stderr = open('stderr.txt', 'w', 0)

import config

from labmanager import app as application
application.config.from_object('config')

import logging
file_handler = logging.FileHandler(filename='errors.log')
file_handler.setLevel(logging.INFO)
application.logger.addHandler(file_handler)
