# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from time import time
from hashlib import new as new_hash
from flask import render_template, request, flash, redirect, url_for, session
from flask.ext.login import LoginManager, login_user, logout_user, login_required
from labmanager.babel import gettext
from ..application import app
from ..models import LabManagerUser, LtUser, LearningTool

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(userid):
    if userid.startswith(u'labmanager_admin::'):
        login = userid.split(u'labmanager_admin::')[1]
        return LabManagerUser.find(login = login)
    if userid.startswith(u'lt_user::'):
        try:
            _, lt_name, login = userid.split('::')
        except ValueError:
            print gettext("Invalid format (expected lt_user::lt_name::login)")
            return None
        potential_users = [ user for user in LtUser.all(login = login) if user.lt.name == lt_name ]
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
        hashed = unicode(new_hash("sha", request.form['password'].encode('utf8')).hexdigest())
        user = LabManagerUser.exists(username, hashed)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                session['usertype'] = 'labmanager'
                next = request.args.get('next', url_for('admin.index'))
                return redirect(next)
            else:
                flash(gettext(u'Could not log in.'))
                return render_template('login_admin.html', next=next)
        else:
            flash(gettext(u'Invalid username.'))
            return render_template('login_admin.html', next=next)
    return gettext("Error in create_session")

@app.route('/login/lms/', methods=['GET', 'POST'])
def login_lms():
    """Login screen for application"""
    DEFAULT_NEXT = url_for('lms_admin.index')
    next = request.args.get('next', DEFAULT_NEXT)

    lmss = [ lt for lt in LearningTool.all() if len(lt.shindig_credentials) == 0 ]

    if request.method == 'GET':
        return render_template('login_lms.html', next=next, lmss=lmss, action_url = url_for('login_lms'))
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        hashed = unicode(new_hash("sha", request.form['password'].encode('utf8')).hexdigest())
        lms_id = request.form['lms']
        user = LtUser.exists(username, hashed, lms_id)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                session['usertype'] = 'lms'
                if next == DEFAULT_NEXT:
                    if user.access_level == 'instructor':
                        next = url_for('lms_instructor.index')
                return redirect(next)
            else:
                flash(gettext(u'Could not log in.'))
                return render_template('login_lms.html', next=next, lmss=lmss, action_url = url_for('login_lms'))
        else:
            flash(gettext(u'Invalid username.'))
            return render_template('login_lms.html', next=next, lmss=lmss, action_url = url_for('login_lms'))
    return gettext("Error in create_session")

@app.route('/login/ple/', methods=['GET', 'POST'])
def login_ple():
    """Login screen for application"""
    DEFAULT_NEXT = url_for('ple_admin.index')
    next = request.args.get('next', DEFAULT_NEXT)
    ples = [ lt for lt in LearningTool.all() if len(lt.shindig_credentials) > 0 ]
    if request.method == 'GET':
        return render_template('login_ple.html', next=next, lmss=ples, action_url = url_for('login_ple'))
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        hashed = unicode(new_hash("sha", request.form['password'].encode('utf8')).hexdigest())
        lms_id = request.form['lms']
        user = LtUser.exists(username, hashed, lms_id)
        if user is not None:
            if login_user(user):
                session['loggeduser'] = username
                session['last_request'] = time()
                session['usertype'] = 'lms'
                if next == DEFAULT_NEXT:
                    if user.access_level == 'instructor':
                        next = url_for('ple_instructor.index')
                return redirect(next)
            else:
                flash(gettext(u'Could not log in.'))
                return render_template('login_ple.html', next=next, lmss=ples, action_url = url_for('login_ple'))
        else:
            flash(gettext(u'Invalid username.'))
            return render_template('login_ple.html', next=next, lmss=ples, action_url = url_for('login_ple'))
    return gettext(u"Error in create_session")

@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    session.pop('loggeduser', None)
    return redirect(url_for('index'))
