# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from time import time
from hashlib import new as new_hash

from flask import render_template, request, flash, redirect, url_for, session
from flask.ext.login import LoginManager, login_user, logout_user, login_required


from .application import app
from .models import LabManagerUser, LmsUser, LMS

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(userid):

    if userid.startswith(u'labmanager_admin::'):
        login = userid.split(u'labmanager_admin::')[1]
        return LabManagerUser.find(login = login)

    if userid.startswith(u'lms_user::'):
        try:
            _, lms_name, login = userid.split('::')
        except ValueError:
            print "Invalid format (expected lms_user::lms_name::login"
            return None

        potential_users = [ user for user in LmsUser.all(login = login) if user.lms.name == lms_name ]
        if len(potential_users) == 0:
            return None
        else:
            return potential_users[0]

    return None

@app.route('/login/admin/', methods=['GET', 'POST'])
def login_admin():
    """Login screen for application"""

    next = request.args.get('next',url_for('admin.index'))

    if request.method == 'GET':
        return render_template('login_admin.html', next=next)

    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        hashed = new_hash("sha", request.form['password']).hexdigest()
        user = LabManagerUser.exists(username, hashed)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                session['usertype'] = 'labmanager'
                next = request.args.get('next', url_for('admin.index'))
                return redirect(next)
            else:
                flash(u'Could not log in.')
                return render_template('login_admin.html', next=next)
        else:
            flash(u'Invalid username.')
            return render_template('login_admin.html', next=next)

    return "Error in create_session"


@app.route('/login/lms/', methods=['GET', 'POST'])
def login_lms():
    """Login screen for application"""

    # TODO: /lms_admin => url_for(... lms.index or something
    next = request.args.get('next', '/lms_admin')
    lmss = LMS.all()

    if request.method == 'GET':
        return render_template('login_lms.html', next=next, lmss=lmss)

    if request.method == 'POST' and 'username' in request.form:
        print "Checking..."

        username = request.form['username']
        hashed = new_hash("sha", request.form['password']).hexdigest()
        lms_id = request.form['lms']
        user = LmsUser.exists(username, hashed, lms_id)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                session['usertype'] = 'lms'
                return redirect(next)
            else:
                flash(u'Could not log in.')
                return render_template('login_lms.html', next=next, lmss=lmss)
        else:
            flash(u'Invalid username.')
            return render_template('login_lms.html', next=next, lmss=lmss)
    return "Error in create_session"

@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    session.pop('loggeduser', None)
    return redirect(url_for('index'))

