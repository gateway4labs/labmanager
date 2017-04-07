# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from time import time
from hashlib import new as new_hash
from flask import render_template, request, flash, redirect, url_for, session, make_response, current_app
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from labmanager.babel import gettext
from ..application import app
from labmanager.db import db_session
from ..models import LabManagerUser, LtUser, LearningTool, GoLabOAuthUser

import requests
from urlparse import urlparse
from functools import wraps

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.session_protection = "strong"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login/lms?next=' + request.path)

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
    if userid.startswith(u'golab::'):
        email = userid.split('::', 1)[1]
        return db_session.query(GoLabOAuthUser).filter_by(email = email).first()
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
@app.route('/login/lms', methods=['GET', 'POST'])
def login_lms():
    """Login screen for application"""
    DEFAULT_NEXT = url_for('lms_admin.index')
    next = request.args.get('next', DEFAULT_NEXT)
    print next
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

def current_golab_user():
    user_id = current_user.get_id()
    if user_id and user_id.startswith('golab::'):
        return current_user

    return None

def requires_golab_login(f):
    """
    Require that a particular flask URL requires login. It will require the user to be logged,
    and if he's not logged he will be redirected there afterwards.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_golab_user() is None:
            return redirect(url_for('login_golab_oauth',sso='', next=request.url))
        return f(*args, **kwargs)

    return wrapper


PUBLIC_SMARTGATEWAY_ID = 'WfTlrXTbu4AeGexikhau5HDXkpGE8RYh'

@app.route('/graasp/oauth/')
def login_golab_oauth():
    next_url = request.args.get('next')
    if next_url is None:
        return "No next= provided"
    session['oauth_next'] = next_url
    redirect_back_url = url_for('golab_oauth_login_redirect', _external = True)
    return redirect('http://graasp.eu/authorize?client_id=%s&redirect_uri=%s' % (PUBLIC_SMARTGATEWAY_ID, requests.utils.quote(redirect_back_url, '')))

@app.route('/graasp/oauth/redirect/')
def golab_oauth_login_redirect():
    access_token = request.args.get('access_token')
    refresh_token = request.args.get('refresh_token')
    timeout = request.args.get('expires_in')
    next_url = session.get('oauth_next')

    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
    }

    requests_session = requests.Session()
    response = requests_session.get('http://graasp.eu/users/me', headers = headers)
    if response.status_code == 500:
        error_msg = "There has been an error trying to log in with access token: %s and refresh_token %s; attempting to go to %s. Response: %s" % (access_token, refresh_token, next_url, response.text)
        current_app.logger.error(error_msg)
        # TODO
        # sendmail("Error logging in", error_msg)
        return render_template("error_login.html")

    try:
        user_data = response.json()
    except ValueError:
        logging.error("Error logging in user with data: %r" % response.text, exc_info = True)
        raise ValueError("Error logging in user with data: %r" % response.text)

    user = db_session.query(GoLabOAuthUser).filter_by(email = user_data['email']).first()
    if user is None:
        user = GoLabOAuthUser(email = user_data['email'], display_name = user_data['username'])
        db_session.add(user)
        db_session.commit()

    login_user(user)
    return redirect(requests.utils.unquote(next_url or ''))


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    session.pop('loggeduser', None)
    return redirect(url_for('index'))
