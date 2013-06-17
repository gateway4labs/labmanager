# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  This will handle the main application routes. It will be in charge of
  registering all the blueprint that it needs and exposing some of the
  basic routes (like login and logout).
"""

import os

from flask import Flask, render_template, redirect, url_for

from labmanager.database import db_session

app = Flask(__name__)
app.config.from_object('config')
if app.config['DEBUG']:
    app.secret_key = 'secret'
else:
    app.secret_key = os.urandom(32)

# 
# Initialize administration panels
# 
from .views.admin import init_admin as init_admin
init_admin(app, db_session)

from .views.lms.admin import init_lms_admin
init_lms_admin(app, db_session)

from .views.lms.instructor import init_instructor_admin
init_instructor_admin(app, db_session)


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
    # if login
    #  redirect /admin
    # else
    #  redirect /login
    """Global index for the whole application."""
    return render_template("index.html")

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()
