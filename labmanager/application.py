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

  This will handle the main application routes. It will be in charge of
  registering all the blueprint that it needs and exposing some of the
  basic routes (like login and logout).
"""

import os, sys
from time import time
from functools import wraps
from hashlib import new as new_hash

from flask import Flask, Blueprint, render_template, Response, request, g, abort, flash, redirect, url_for, session
from flask.ext.login import LoginManager, login_user, logout_user, UserMixin, login_required

from labmanager.database import db_session
from labmanager.models import LMS, LabManagerUser as User, Credential

from labmanager.admin import init_admin

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.urandom(32)

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.session_protection = "strong"

init_admin(app, db_session)

@login_manager.user_loader
def load_user(userid):
    return User.find(int(userid))

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


@app.route('/login', methods=['GET'])
def login():
    """Login screen for application"""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def create_session():
    """Creates a user session"""
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        hashed = new_hash("sha", request.form['password']).hexdigest()
        user = User.exists(username, hashed)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                return redirect(url_for('admin.index'))
            else:
                flash(u'Could not log in.')
        else:
            flash(u'Invalid username.')


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    session.pop('loggeduser', None)
    return redirect('login')


@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()
