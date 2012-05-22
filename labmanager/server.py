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
from labmanager.models   import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS
from labmanager.rlms     import get_supported_types, get_supported_versions, is_supported, get_form_class

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
    request_payload = request.json['request-payload']
    general_role    = request.json.get('general-role', 'no particular role') or 'null role'
    author          = request.json['author']
    complete_name   = request.json['complete-name']

    courses_code = "<table><thead><tr><th>Course ID</th><th>Role</th></tr></thead><tbody>\n"
    for course_id in courses:
        roles_in_course = courses[course_id]
        for role_in_course in roles_in_course:
            courses_code += "<tr><td>%s</td><td>%s</td></tr>\n" % (course_id, role_in_course)
    courses_code += "</tbody></table>"

    return """<html>
    <body>
        Hi %(name)s (username %(author)s),

        I know that your role is %(role)s in the LMS %(lms)s, and that you are.

        Furthermore, you sent me this request:
        <pre>
        %(request)s
        </pre>
        
        And I'll process it!
    </body>
</html>
""" % {
    'name'        : cgi.escape(complete_name),
    'author'      : cgi.escape(author),
    'lms'         : cgi.escape(g.lms),
    'course_code' : courses_code,
    'request'     : cgi.escape(request_payload),
    'role'        : cgi.escape(general_role),
}



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
    retrieved_types = set( (retrieved_type.name for retrieved_type in types) )

    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        for supported_type in get_supported_types():
            if supported_type not in retrieved_types:
                new_type = RLMSType(supported_type)
                db_session.add(new_type)
        db_session.commit()    
        types = db_session.query(RLMSType).all()
        retrieved_types = set( (retrieved_type.name for retrieved_type in types) )

    any_supported_missing = any([ supported_type not in retrieved_types for supported_type in get_supported_types()])

    return render_template("labmanager_admin/rlms_types.html", types = types, supported = get_supported_types(), any_supported_missing = any_supported_missing)

@app.route("/lms4labs/admin/rlms/<rlmstype>/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMSTypeVersion)
def admin_rlms_versions(rlmstype):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        versions = rlms_type.versions

        retrieved_versions = set( (retrieved_version.version for retrieved_version in versions) )

        if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
            for supported_version in get_supported_versions(rlmstype):
                if supported_version not in retrieved_versions:
                    new_version = RLMSTypeVersion(rlms_type, supported_version)
                    db_session.add(new_version)
            db_session.commit()

            versions = rlms_type.versions
            retrieved_versions = set( (retrieved_version.version for retrieved_version in versions) )

        any_supported_missing = any([ supported_version not in retrieved_versions for supported_version in get_supported_versions(rlmstype)])

        return render_template("labmanager_admin/rlms_versions.html", versions = versions, name = rlms_type.name, supported = get_supported_versions(rlmstype), any_supported_missing = any_supported_missing )

    return render_template("labmanager_admin/rlms_errors.html")

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMS)
def admin_rlms_rlms(rlmstype, rlmsversion):
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_rlms_rlms_add', rlmstype = rlmstype, rlmsversion=rlmsversion))

    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        rlms_version = ([ version for version in rlms_type.versions if version.version == rlmsversion ] or [None])[0]
        if rlms_version is not None:
            return render_template("labmanager_admin/rlms_rlms.html", rlmss = rlms_version.rlms, name = rlms_type.name, version = rlms_version.version)

    return render_template("labmanager_admin/rlms_errors.html")


@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/add/", methods = ('GET','POST'))
@requires_session
@deletes_elements(RLMS)
def admin_rlms_rlms_add(rlmstype, rlmsversion):
    if not is_supported(rlmstype, rlmsversion):
        return "Not supported"

    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        rlms_version = ([ version for version in rlms_type.versions if version.version == rlmsversion ] or [None])[0]
        if rlms_version is not None:

            AddForm = get_form_class(rlmstype, rlmsversion)
            form = AddForm()

            if form.validate_on_submit():
                configuration = {}
                for field in form.get_field_names():
                    configuration[field] = getattr(form, field).data
                
                new_rlms = RLMS(name = form.name.data, location = form.location.data, rlms_version = rlms_version, configuration = json.dumps(configuration))
                db_session.add(new_rlms)
                db_session.commit()
                return redirect(url_for('admin_rlms_rlms', rlmstype = rlmstype, rlmsversion = rlmsversion))

            return render_template("labmanager_admin/rlms_rlms_add.html", rlmss = rlms_version.rlms, name = rlms_type.name, version = rlms_version.version, form = form)

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
