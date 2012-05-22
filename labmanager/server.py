#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-

# 
# Python imports
import hashlib
import json
import cgi
import traceback
from functools import wraps

# 
# Flask imports
# 
from flask import Flask, Response, render_template, request, g, session, redirect, url_for

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS
from labmanager.rlms import get_supported_types, get_supported_versions

app = Flask(__name__)

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

###############################################################################
# 
# 
#
#               I N T E R A C T I O N     W I T H     L M S 
#
# 
# 

# 
# LMS authentication
# 
def check_lms_auth(lmsname, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(login = lmsname, password = hash_password).first()
    g.lms = lmsname
    return lms is not None

def requires_lms_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_lms_auth(auth.username, auth.password):
            return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated


@app.route("/lms4labs/requests/", methods = ('GET', 'POST'))
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    courses         = request.json['courses']
    request_payload = request.json['request']
    general_role    = request.json['general-role']
    author          = request.json['author']

    return "Hi lms %s" % g.lms



###############################################################################
# 
# 
# 
#    I N T E R A C T I O N     W I T H     L A B M A N A G E R   A D M I N  
# 
# 
# 

def requires_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logged_in = session.get('logged_in', False)
        if not logged_in:
            return redirect(url_for('admin_login', next = request.url))
        return f(*args, **kwargs)
    return decorated

def deletes_elements(table):
    def real_wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # XXX translate 'delete'
            if request.method == 'POST' and request.form.get('action','').lower() == 'delete':
                for current_id in request.form:
                    element = db_session.query(table).filter_by(id = current_id).first()
                    if element is not None:
                        db_session.delete(element)
                db_session.commit()

            return f(*args, **kwargs)
        return decorated
    return real_wrapper

##############
# 
# L O G I N 
# 

@app.route("/lms4labs/admin/login", methods = ['GET', 'POST'])
def admin_login():
    login_error = False

    if request.method == 'POST':
        login    = request.form['username']
        password = request.form['password']

        hash_password = hashlib.new("sha", password).hexdigest()
        user = db_session.query(LabManagerUser).filter_by(login = login, password = hash_password).first()

        if user is not None:
            session['logged_in'] = True
            session['user_id']   = user.id
            session['user_name'] = user.name
            session['login']     = login

            next = request.args.get('next')
            if next is not None and next.startswith(request.url_root) and next != '':
                return redirect(next)
            return redirect(url_for('admin_index'))

        login_error = True

    return render_template("labmanager_admin/login.html", login_error = login_error, next = request.args.get('next','') )

@app.route("/lms4labs/admin/logout", methods = ['GET', 'POST'])
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

############
# 
# H O M E
# 


@app.route("/lms4labs/admin/")
@requires_session
def admin_index():
    return render_template("labmanager_admin/index.html")

############
# 
# L M S 
# 

@app.route("/lms4labs/admin/lms/")
@requires_session
def admin_lms():
    return render_template("labmanager_admin/lms.html")


############
# 
# R L M S 
# 

@app.route("/lms4labs/admin/rlms/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMSType)
def admin_rlms():
    types = db_session.query(RLMSType).all()

    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):

        retrieved_types = set( (retrieved_type.name for retrieved_type in types) )

        for supported_type in get_supported_types():
            if supported_type not in retrieved_types:
                new_type = RLMSType(supported_type)
                db_session.add(new_type)
        db_session.commit()    
        types = db_session.query(RLMSType).all()

    return render_template("labmanager_admin/rlms.html", types = types, supported = get_supported_types() )

@app.route("/lms4labs/admin/rlms/<rlmstype>/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMSTypeVersion)
def admin_rlms_versions(rlmstype):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:

        if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):

            retrieved_versions = set( (retrieved_version.version for retrieved_version in rlms_type.versions) )

            for supported_version in get_supported_versions(rlmstype):
                if supported_version not in retrieved_versions:
                    new_version = RLMSTypeVersion(rlms_type, supported_version)
                    db_session.add(new_version)
            db_session.commit()    

        return render_template("labmanager_admin/rlms_versions.html", versions = rlms_type.versions, name = rlms_type.name, supported = get_supported_versions(rlmstype) )

    return render_template("labmanager_admin/rlms_errors.html")

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMS)
def admin_rlms_rlms(rlmstype, rlmsversion):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        rlms_version = ([ version for version in rlms_type.versions if version.version == rlmsversion ] or [None])[0]
        if rlms_version is not None:
            return render_template("labmanager_admin/rlms_rlms.html", rlmss = rlms_version.rlms, name = rlms_type.name, version = rlms_version.version)

    return render_template("labmanager_admin/rlms_errors.html")




###############################################################################
# 
# 
# 
#                G E N E R A L     V I E W
# 
# 
# 

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.config.from_object('config')
    app.run()
