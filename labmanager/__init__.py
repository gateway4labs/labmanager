# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""

import os, sys

# 
# Blueprints (application modules). The following are present:
# - SCORM blueprint (user requests through LMS using SCORM)
# - LTI blueprint (user requests through LMS using LTI)
# - Labmanager blueprint (labmanager management)
# 
from labmanager.views import lms_admin, load
from labmanager.ims_lti import lti_blueprint
from labmanager.scorm_package import scorm_blueprint

# 
# Load the required modules so as to register the views
# in the blueprints
# 
load()

# 
# Import the Flask global application and the configuration
# It must be imported after the views due to Python circular 
# imports
# 
from application import app
import config as _config

# 
# Register the blueprints in the application
# 
app.register_blueprint(scorm_blueprint, url_prefix='/labmanager')
app.register_blueprint(lms_admin.lms_admin, url_prefix='/labmanager/lms')
app.register_blueprint(lti_blueprint, url_prefix='/lti')

# 
# Initialize the login system
# 
# from labmanager.views.login import init_login
# init_login(app)


def load_rlms_modules():
    """
    Load all the RLMS modules that we are going to use.

    Expand documentation on how to add a new one.
    """
    if len(_config.RLMS) == 0:
        print >> sys.stderr, "Warning: RLMS configuration variable empty or not found."
        print >> sys.stderr, "Warning: This means that this LabManager can not handle any remote lab, which"
        print >> sys.stderr, "Warning: does not make sense. You should add a RLMS = [] variable in your "
        print >> sys.stderr, "Warning: config.py indicating which extensions should be loaded"
        print >> sys.stderr, "Warning: (e.g. weblabdeusto)" # TODO: add more whenever implemented

    for _rlms in _config.RLMS:
        __import__('labmanager.rlms.ext.%s' % _rlms)

# This will register all the RLMSs in the global registry. So it will
# always be called (regardless we're using the Flask debugger or a WSGI
# environment).
load_rlms_modules()

def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded = True)

if __name__ == "__main__":
    run()
