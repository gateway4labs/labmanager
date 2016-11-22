# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  This will handle the main application routes. It will be in charge of
  registering all the blueprint that it needs and exposing some of the
  basic routes (like login and logout).
"""

import os

from labmanager.utils import FullyQuotedUrlConverter, EverythingConverter
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)
app.url_map.converters['quoted_url'] = FullyQuotedUrlConverter
app.url_map.converters['everything'] = EverythingConverter
app.config.from_object('config')

# Try to support SQLALCHEMY_ENGINE_STR
if 'SQLALCHEMY_DATABASE_URI' not in app.config and 'SQLALCHEMY_ENGINE_STR' in app.config:
    print "WARNING: SQLALCHEMY_ENGINE_STR is deprecated. Change it for SQLALCHEMY_DATABASE_URI"
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_ENGINE_STR']

if 'SQLALCHEMY_POOL_RECYCLE' not in app.config and app.config['SQLALCHEMY_DATABASE_URI'].startswith('mysql'):
    print "WARNING: SQLALCHEMY_POOL_RECYCLE not set. Defaults to 3600. Put it in the configuration file"
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600

if 'SESSION_COOKIE_PATH' not in app.config or not app.config.get('SESSION_COOKIE_PATH'):
    print "WARNING: You should always set SESSION_COOKIE_PATH to / or /whatever, wherever the application is, to avoid conflicts between different deployments"

if app.config['DEBUG']:
    app.secret_key = 'secret'
    import labmanager.views.fake_lms as fake_lms
    assert fake_lms is not None # Avoid flakes warning
else:
    app.secret_key = os.urandom(32)
app.config['SESSION_COOKIE_NAME'] = 'g4lsession'

from .embed import embed_blueprint
app.register_blueprint(embed_blueprint, url_prefix='/embed')

# Initialize the logging mechanism to send error 500 mails to the administrators
if not app.debug and app.config.get("ADMINS") is not None and app.config.get("SMTP_SERVER") is not None:
    import logging
    import pprint
    from logging.handlers import SMTPHandler

    class MailLoggingFilter(logging.Filter):
        def filter(self, record):
            pass
            record.environ = pprint.pformat(request.environ)
            return True

    app.logger.addFilter(MailLoggingFilter())

    smtp_server = app.config.get("SMTP_SERVER")
    from_addr = app.config.get("SENDER_ADDR")
    to_addrs = app.config.get("ADMINS")
    mail_handler = SMTPHandler(smtp_server,
                                from_addr,
                                to_addrs,
                                "gateway4labs Application Error Report")
    formatter = logging.Formatter(
        '''
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s

        Environment:

        %(environ)s

        Stack Trace:
        ''')
    mail_handler.setFormatter(formatter)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


@app.route("/error")
def error():
    return 2/0


@app.errorhandler(404)
def not_found(e):
    return "404 not found", 404

@app.errorhandler(403)
def forbidden(e):
    return "403 forbidden", 403

@app.errorhandler(412)
def precondition_failed(e):
    return "412 precondition failed", 412

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@app.route("/")
def index():
    """Global index for the whole application."""
    golab = app.config.get('GOLAB', False)
    return render_template("index.html", golab = golab)

@app.route("/developers")
def developers():
    """Developer information about gateway4labs."""
    return render_template("developers.html")

@app.route("/about")
def about():
    """Global information about gateway4labs."""
    return render_template("about.html")

@app.teardown_request
def shutdown_session(exception = None):
    db.session.remove()


from labmanager.babel import Babel
from flask import request

if Babel is None:
    print "Not using Babel. Everything will be in English"
else:
    babel = Babel(app)
    supported_languages = ['en']
    supported_languages.extend([ translation.language for translation in babel.list_translations() ])

    @babel.localeselector
    def get_locale():
        if app.config.get('TRANSLATE_LABMANAGER', True):
            locale = request.args.get('locale',  None)
            if locale is None:
                locale = request.accept_languages.best_match(supported_languages)
            if locale is None:
                locale = 'en'
            # print "Locale requested. Got: ", locale
            return locale 
        else:
            return 'en'

    @babel.timezoneselector
    def get_timezone():
        #timezone = request.args.get('timezone', 'en')
        #print "Timezone requested. Got: ", timezone
        #return timezone
        # TODO 
        return None

# 
# Initialize administration panels
# 
from labmanager.db import db
assert db is not None

from .views.admin import init_admin
init_admin(app)

from .views.public import init_public_admin
init_public_admin(app)

from .views.lms.admin import init_lms_admin
init_lms_admin(app)

from .views.lms.instructor import init_instructor_admin
init_instructor_admin(app)

from .views.ple.admin import init_ple_admin
init_ple_admin(app)

from .views.ple.instructor import init_ple_instructor_admin
init_ple_instructor_admin(app)

# 
# Initialize login subsystem
# 
from .views import authn
assert authn is not None # Avoid warnings


