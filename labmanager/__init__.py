# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import os
import sys
import optparse

# 
# Import the Flask global application and the configuration
# 
from application import app
import config as _config

# 
# Blueprints (application modules). The following are present:
# - Basic HTTP blueprint (user requests through LMS using SCORM)
# - LTI blueprint (user requests through LMS using LTI)
# 
from .views import load as load_views
from .views.ims_lti import lti_blueprint
from .views.basic_http import basic_http_blueprint
from .views.opensocial import opensocial_blueprint

if hasattr(os, 'uname') and os.uname()[1] in ('plunder','scabb'): # TODO: Deusto servers
    print "Installing proxy handler...",
    import urllib2
    proxy = urllib2.ProxyHandler({'http': 'http://proxy-s-priv.deusto.es:3128/'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
    print "done"

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

def register_blueprints():
    # 
    # Register the blueprints in the application
    # 
    app.register_blueprint(basic_http_blueprint, url_prefix='/labmanager')
    app.register_blueprint(lti_blueprint, url_prefix='/lti')
    app.register_blueprint(opensocial_blueprint, url_prefix='/opensocial')

    from labmanager.rlms.base import _BLUEPRINTS
    for url, blueprint in _BLUEPRINTS.items():
        app.register_blueprint(blueprint, url_prefix='/rlms' + url)

def bootstrap():
    load_views()
    load_rlms_modules()
    register_blueprints()
    # print app.url_map

def run():
    from .db import check_version
    if not check_version():
        print >> sys.stderr, "Database not upgraded!!! Run:"
        print >> sys.stderr, "  alembic upgrade head"
        print >> sys.stderr, "And then run this script again"
        sys.exit(-1)

    bootstrap()

    parser = optparse.OptionParser(usage =  "Run in development mode the LabManager. In production, please use WSGI.")

    parser.add_option('-p', '--port', dest='port', metavar="PORT",
                        help="Port to be used",
                        type='int', default=5000)

    parser.add_option('--register-fake-rlms', dest='register_fake_rlms', help="Register the fake RLMS", default=False, action='store_true')
    parser.add_option('--testing', dest='testing', help="Enter in testing mode", default=False, action='store_true')
    
    args, _ = parser.parse_args() 
    
    if args.register_fake_rlms:
        from labmanager.tests.unit.fake_rlms import register_fake
        register_fake()

    if args.testing:
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['DEBUG'] = False

    port = int(os.environ.get('PORT', args.port))
    app.run(host='0.0.0.0', port=port, threaded = True)