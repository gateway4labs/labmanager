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

#
# Flask imports
#
import os, sys

from labmanager.views import lms, ims_lti, lms_admin, load, labmanager_admin
from labmanager.views.admin import init_admin
from labmanager.views.login import init_login
from config import RLMS as _RLMSs
from application import app, db_session

app.register_blueprint(lms.basic_auth)
app.register_blueprint(labmanager_admin.labmanager, url_prefix='/lms4labs/labmanager')
app.register_blueprint(ims_lti.lti, url_prefix='/lti')

# app.register_blueprint(lms_admin.lms_admin, url_prefix='/lms4labs/labmanager/lms')

init_admin(app, db_session)
init_login(app)

load()

def load_rlms_modules():
    """
    Load all the RLMS modules that we are going to use.

    Expand documentation on how to add a new one.
    """
    if len(_RLMSs) == 0:
        print >> sys.stderr, "Warning: RLMS configuration variable empty or not found."
        print >> sys.stderr, "Warning: This means that this LabManager can not handle any remote lab, which"
        print >> sys.stderr, "Warning: does not make sense. You should add a RLMS = [] variable in your "
        print >> sys.stderr, "Warning: config.py indicating which extensions should be loaded"
        print >> sys.stderr, "Warning: (e.g. weblabdeusto)" # TODO: add more whenever implemented

    for _rlms in _RLMSs:
        __import__('labmanager.rlms.ext.%s' % _rlms)


def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded = True)

if __name__ == "__main__":
    run()
    load_rlms_modules()
