# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from time import time
from hashlib import new as new_hash
from flask import render_template, request, flash, redirect, url_for, session, make_response
from flask.ext.login import LoginManager, login_user, logout_user, login_required
from labmanager.babel import gettext
from ..application import app
from labmanager.db import db_session
from ..models import LabManagerUser, LtUser, LearningTool, SiWaySAMLUser

from urlparse import urlparse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils


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

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=app.config['SAML_PATH'])
    return auth


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': request.query_string
    }


@app.route('/saml/', methods=['GET', 'POST'])
@app.route('/saml', methods=['GET', 'POST'])
def login_saml():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    user = None

    if 'sso' in request.args:
        print 'Redirecting to login page'
        return redirect(auth.login())
    elif 'slo' in request.args:
        name_id = None
        session_index = None
        if 'samlNameId' in session:
            name_id = session['samlNameId']
        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']
        return redirect(auth.logout(name_id=name_id, session_index=session_index))
    elif 'acs' in request.args:
        auth.process_response()
        errors = auth.get_errors()
        if len(errors) == 0:
            session['samlUserdata'] = auth.get_attributes()
            session['samlNameId'] = auth.get_nameid()
            session['samlSessionIndex'] = auth.get_session_index()
            if 'samlUserdata' in session:
                if len(session['samlUserdata']) > 0:
                    attributes = session['samlUserdata'].items()
                    new_user = False
                    for attr in attributes:
                        if attr[0] == 'mail':
                            email = attr[1][0]
                            user = SiWaySAMLUser.query.filter_by(email=email).first()
                            if user is None:
                                new_user = True
                            break

                    if new_user:
                        for attr in attributes:
                            if attr[0] == 'employeeType':
                                employee_type = attr[1][0]
                            elif attr[0] == 'uid':
                                uid = attr[1][0]
                            elif attr[0] == 'o':
                                school_name = attr[1][0]
                            elif attr[0] == 'sn':
                                short_name = attr[1][0]
                            elif attr[0] == 'mail':
                                email = attr[1][0]
                            elif attr[0] == 'ou':
                                group = attr[1][0]
                            elif attr[0] == 'cn':
                                full_name = attr[1][0]
                            elif attr[0] == 'userPassword':
                                password = attr[1][0]
                        user = SiWaySAMLUser(employee_type=employee_type,
                                             uid=int(uid),
                                             school_name=school_name,
                                             short_name=short_name,
                                             email=email,
                                             group=group,
                                             full_name=full_name,
                                             password=password
                                             )
                        db_session.add(user)
                        db_session.commit()
                        print 'New user pushed to db'
                    else:
                        print 'User already in db'

                    return render_template('saml/loged.html',user=user)

    elif 'sls' in request.args:
        #TODO:User logout here
        dscb = lambda: session.clear()
        url = auth.process_slo(delete_session_cb=dscb)
        print url
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                print 'Redirecting to session delete url (sls)'
                return redirect(url)
    golab = app.config.get('GOLAB', False)
    return render_template("index.html", golab = golab)



@app.route('/saml/metadata/')
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(', '.join(errors), 500)
    return resp



@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    session.pop('loggeduser', None)
    return redirect(url_for('index'))
