#!/usr/bin/env python

import sys
sys.stdout = sys.stderr

import sys
sys.path.insert(0, '/home/weblab/lms4labs/labmanager')

activate_this = '/home/weblab/lms4labs/labmanager/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from labmanager.server import app as application
application.config.from_object('config')
