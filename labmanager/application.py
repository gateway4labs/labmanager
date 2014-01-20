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

from flask import Flask, render_template, redirect, url_for

from labmanager.db import db_session

app = Flask(__name__)
app.config.from_object('config')
if app.config['DEBUG']:
    app.secret_key = 'secret'
    import labmanager.views.fake_lms as fake_lms
    assert fake_lms is not None # Avoid flakes warning
else:
    app.secret_key = os.urandom(32)
app.config['SESSION_COOKIE_NAME'] = 'g4lsession'

@app.errorhandler(404)
def not_found(e):
    return "404 not found", 404

@app.errorhandler(403)
def forbidden(e):
    return "403 forbidden", 403

@app.errorhandler(412)
def precondition_failed(e):
    return "412 precondition failed", 412


# 
# Initialize administration panels
# 
from .views.admin import init_admin
init_admin(app, db_session)

from .views.public import init_public_admin
init_public_admin(app, db_session)

from .views.lms.admin import init_lms_admin
init_lms_admin(app, db_session)

from .views.lms.instructor import init_instructor_admin
init_instructor_admin(app, db_session)

from .views.ple.admin import init_ple_admin
init_ple_admin(app, db_session)

# 
# Initialize login subsystem
# 
from .views import authn
assert authn is not None # Avoid warnings

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@app.route("/")
def index():
    """Global index for the whole application."""
    return render_template("index.html")

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
    db_session.remove()
