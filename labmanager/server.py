#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-

# 
# Python imports
import hashlib
import json
import uuid
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
from labmanager.forms    import AddLmsForm

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
    lms = db_session.query(LMS).filter_by(lms_login = lmsname, lms_password = hash_password).first()
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


@app.route("/lms4labs/requests/", methods = ['GET', 'POST'])
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    if request.method == 'GET':
        return render_template("test_requests.html")

    try:
        json_data = request.json or json.loads(request.data)
    except:
        return "Could not process JSON data"

    courses         = json_data['courses']
    request_payload = json_data['request-payload']
    general_role    = json_data.get('general-role', 'no particular role') or 'null role'
    author          = json_data['author']
    complete_name   = json_data['complete-name']

    courses_code = "<table><thead><tr><th>Course ID</th><th>Role</th></tr></thead><tbody>\n"
    for course_id in courses:
        roles_in_course = courses[course_id]
        for role_in_course in roles_in_course:
            courses_code += "<tr><td>%s</td><td>%s</td></tr>\n" % (course_id, role_in_course)
    courses_code += "</tbody></table>"

    return """Hi %(name)s (username %(author)s),

        I know that your role is %(role)s in the LMS %(lms)s, and that you are.

        Furthermore, you sent me this request:
        <pre>
        %(request)s
        </pre>
        
        And I'll process it!
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
#   I N T E R A C T I O N     W I T H     L M S     A D M I N
#
# 
# 

def requires_lms_admin_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logged_in    = session.get('logged_in', False)
        session_type = session.get('session_type', '')
        if not logged_in or session_type != 'lms_admin':
            return "Not authorized"
        return f(*args, **kwargs)
    return decorated

@app.route("/lms4labs/lms/logout", methods = ['GET', 'POST'])
def lms_admin_logout():
    session.pop('logged_in', None)
    return "fine"

# TODO: this does not scale: should be in database or signed or something
# TODO: this does not expire: memory leak
TOKENS = {}

@app.route("/lms4labs/authenticate/", methods = ['GET', 'POST'])
@requires_lms_auth
def lms_admin_authenticate():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    if request.method == 'GET':
        return render_template("test_admin_authentication.html")

    try:
        json_data = request.json or json.loads(request.data)
    except:
        return "Could not process JSON data"
    
    code = uuid.uuid4().hex
    TOKENS[code] = json_data['complete-name']
    return request.url_root + url_for('lms_admin_redeem_authentication', token = code)

@app.route("/lms4labs/authenticate/<token>")
def lms_admin_redeem_authentication(token):
    complete_name = TOKENS.pop(token, None)
    if complete_name is None:
        return "Token not found"

    session['user_name']     = complete_name
    session['logged_in']     = True
    session['session_type']  = 'lms_admin'

    return redirect(url_for('lms_admin_index'))


@app.route("/lms4labs/lms/")
@requires_lms_admin_session
def lms_admin_index():
    return render_template("lms_admin/index.html")

###############################################################################
# 
# 
# 
#    I N T E R A C T I O N     W I T H     L A B M A N A G E R   A D M I N  
# 
# 
# 

def requires_labmanager_admin_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logged_in    = session.get('logged_in', False)
        session_type = session.get('session_type', '')
        if not logged_in or session_type != 'labmanager_admin':
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
            session['logged_in']    = True
            session['session_type'] = 'labmanager_admin'
            session['user_id']      = user.id
            session['user_name']    = user.name
            session['login']        = login

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
@requires_labmanager_admin_session
def admin_index():
    return render_template("labmanager_admin/index.html")

############
# 
# L M S 
# 

@app.route("/lms4labs/admin/lms/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
@deletes_elements(LMS)
def admin_lms():
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_lms_add'))

    lmss = db_session.query(LMS).all()
    return render_template("labmanager_admin/lms.html", lmss = lmss)

def _add_or_edit_lms(id):
    form = AddLmsForm(id is None)

    if form.validate_on_submit():
        if id is None:
            new_lms = LMS(name = form.name.data, url = form.url.data, 
                            lms_login           = form.lms_login.data, 
                            lms_password        = form.lms_password.data, 
                            labmanager_login    = form.labmanager_login.data, 
                            labmanager_password = form.labmanager_password.data)
            db_session.add(new_lms)
        else:
            lms = db_session.query(LMS).filter_by(id = id).first()
            if lms is None:
                return render_template("labmanager_admin/lms_errors.html")


            lms.url               = form.url.data
            lms.name              = form.name.data
            lms.lms_login         = form.lms_login.data
            lms.labmanager_login  = form.labmanager_login.data
            if form.lms_password.data:
                lms.lms_password        = form.lms_password.data
            if form.labmanager_password.data:
                lms.labmanager_password = form.labmanager_password.data

        db_session.commit()
        return redirect(url_for('admin_lms'))
    
    if id is not None:
        lms = db_session.query(LMS).filter_by(id = id).first()
        if lms is None:
            return render_template("labmanager_admin/lms_errors.html")

        name = lms.name

        form.url.data              = lms.url
        form.name.data             = lms.name
        form.lms_login.data        = lms.lms_login
        form.labmanager_login.data = lms.labmanager_login
    else:
        name = None

    return render_template("labmanager_admin/lms_add.html", form = form, name = name)

@app.route("/lms4labs/admin/lms/edit/<int:id>", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_edit(id):
    return _add_or_edit_lms(id)

@app.route("/lms4labs/admin/lms/add/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_add():
    return _add_or_edit_lms(id = None)

############
# 
# R L M S 
# 

@app.route("/lms4labs/admin/rlms/", methods = ('GET','POST'))
@requires_labmanager_admin_session
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
@requires_labmanager_admin_session
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

def _get_rlms_version(rlmstype, rlmsversion):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        rlms_version = ([ version for version in rlms_type.versions if version.version == rlmsversion ] or [None])[0]
        if rlms_version is not None:
            return rlms_version
    return None

def _add_or_edit_rlms(rlmstype, rlmsversion, id):
    if not is_supported(rlmstype, rlmsversion):
        return "Not supported"

    rlms_version = _get_rlms_version(rlmstype, rlmsversion)
    if rlms_version is None:
        return render_template("labmanager_admin/rlms_errors.html")

    AddForm = get_form_class(rlmstype, rlmsversion)
    form = AddForm(id is None)

    if form.validate_on_submit():
        configuration_dict = {}
        for field in form.get_field_names():
            if field not in ('location', 'name'):
                configuration_dict[field] = getattr(form, field).data

        configuration = json.dumps(configuration_dict)
        
        if id is None:
            new_rlms = RLMS(name = form.name.data, location = form.location.data, rlms_version = rlms_version, configuration = configuration)
            db_session.add(new_rlms)
        else:
            rlms = db_session.query(RLMS).filter_by(id = id).first()
            if rlms is None:
                return render_template("labmanager_admin/rlms_errors.html")
            rlms.name          = form.name.data
            rlms.location      = form.location.data
            rlms.configuration = AddForm.process_configuration(rlms.configuration, configuration)

        db_session.commit()
        return redirect(url_for('admin_rlms_rlms', rlmstype = rlmstype, rlmsversion = rlmsversion))

    if id is not None:
        rlms = db_session.query(RLMS).filter_by(id = id).first()
        if rlms is None:
            return render_template("labmanager_admin/rlms_errors.html")

        form.name.data     = rlms.name
        form.location.data = rlms.location
        if rlms.configuration is not None and rlms.configuration != '':
            configuration = json.loads(rlms.configuration)
            for key in configuration:
                getattr(form, key).data = configuration[key]

    return render_template("labmanager_admin/rlms_rlms_add.html", rlmss = rlms_version.rlms, name = rlms_version.rlms_type.name, version = rlms_version.version, form = form)


@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(RLMS)
def admin_rlms_rlms(rlmstype, rlmsversion):
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_rlms_rlms_add', rlmstype = rlmstype, rlmsversion=rlmsversion))

    rlms_version = _get_rlms_version(rlmstype, rlmsversion)
    if rlms_version is None:
        return render_template("labmanager_admin/rlms_errors.html")

    return render_template("labmanager_admin/rlms_rlms.html", rlmss = rlms_version.rlms, name = rlms_version.rlms_type.name, version = rlms_version.version)


@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/add/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_add(rlmstype, rlmsversion):
    return _add_or_edit_rlms(rlmstype, rlmsversion, None)

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/edit/<int:id>", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_edit(rlmstype, rlmsversion, id):
    return _add_or_edit_rlms(rlmstype, rlmsversion, id)


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
