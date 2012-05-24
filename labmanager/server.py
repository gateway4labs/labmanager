#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-

# 
# Python imports
import hashlib
import json
import uuid
import cgi
import traceback
import urllib2
from functools import wraps

# 
# Flask imports
# 
from flask import Flask, Response, render_template, request, g, session, redirect, url_for, flash

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS, Course, Laboratory, PermissionOnLaboratory
from labmanager.rlms     import get_supported_types, get_supported_versions, is_supported, get_form_class, get_manager_class, get_permissions_form_class
from labmanager.forms    import AddLmsForm

app = Flask(__name__)

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

def get_json():
    if request.json is not None:
        return request.json
    else:
        try:
            if request.data:
                data = request.data
            else:
                keys = request.form.keys() or ['']
                data = keys[0]
            return json.loads(data)
        except:
            return None

def deletes_elements(table):
    def real_wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method == 'POST' and request.form.get('action','') == 'delete':
                for current_id in request.form:
                    element = db_session.query(table).filter_by(id = current_id).first()
                    if element is not None:
                        db_session.delete(element)
                db_session.commit()

            return f(*args, **kwargs)
        return decorated
    return real_wrapper


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
        login_required = Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})

        auth = request.authorization
        if not auth:
            json_data = get_json()
            if json_data is None:
                return login_required
            username = json_data.get('lms_username','')
            password = json_data.get('lms_password','')
        else:
            username = auth.username
            password = auth.password

        if not check_lms_auth(username, password):
            return login_required

        return f(*args, **kwargs)
    return decorated


@app.route("/lms4labs/requests/", methods = ['GET', 'POST'])
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    if request.method == 'GET':
        return render_template("test_requests.html")

    json_data = get_json()
    if json_data is None: return "Could not process JSON data"

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

        Original request:
        <pre> 
        %(json)s
        </pre>
""" % {
    'name'        : cgi.escape(complete_name),
    'author'      : cgi.escape(author),
    'lms'         : cgi.escape(g.lms),
    'course_code' : courses_code,
    'request'     : cgi.escape(request_payload),
    'role'        : cgi.escape(general_role),
    'json'        : cgi.escape(json.dumps(json_data))
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
            return 'Not authorized. Ask your LMS to authenticate you through <a href="%s">%s</a>.' % (url_for('lms_admin_authenticate'), url_for('lms_admin_authenticate'))
        return f(*args, **kwargs)
    return decorated

@app.route("/lms4labs/lms/admin/logout", methods = ['GET', 'POST'])
def lms_admin_logout():
    session.pop('logged_in', None)
    referrer = session['referrer']
    if not referrer:
        return redirect(url_for('index'))
    else:
        return redirect(session['referrer'])

# TODO: this does not scale: should be in database or signed or something
# TODO: this does not expire: memory leak
TOKENS = {
    # token : {
    #      'user_name' : 'complete_name'
    #      'lms'       : 'uned'
    #      'referrer'  : 'http://...'
    # }
}

@app.route("/lms4labs/lms/admin/authenticate/", methods = ['GET', 'POST'])
@requires_lms_auth
def lms_admin_authenticate():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    if request.method == 'GET':
        return render_template("test_admin_authentication.html")

    json_data = get_json()
    if json_data is None: return "Could not process JSON data"
    
    code = uuid.uuid4().hex
    TOKENS[code] = {
        'user_name' : json_data['complete-name'],
        'lms'       : g.lms,
        'referrer'  : ''
    }
    return request.url_root + url_for('lms_admin_redeem_authentication', token = code)

def _login_as_lms(user_name, lms_login):
    session['logged_in']     = True
    session['session_type']  = 'lms_admin'
    session['user_name']     = user_name
    session['lms']           = lms_login
    session['referrer']       = request.referrer

    return redirect(url_for('lms_admin_index'))


@app.route("/lms4labs/lms/admin/authenticate/<token>")
def lms_admin_redeem_authentication(token):
    token_info = TOKENS.pop(token, None)
    if token_info is None:
        return "Token not found"
    return _login_as_lms(token_info['user_name'], token_info['lms'])


@app.route("/lms4labs/lms/")
def lms_index():
    return redirect(url_for('lms_admin_index'))

@app.route("/lms4labs/lms/admin/")
@requires_lms_admin_session
def lms_admin_index():
    return render_template("lms_admin/index.html")

@app.route("/lms4labs/lms/admin/courses/", methods = ['GET', 'POST'])
@requires_lms_admin_session
@deletes_elements(Course)
def lms_admin_courses():
    if request.method == 'POST':
        if request.form['action'] == 'add':
            return redirect(url_for('lms_admin_external_courses'))
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    return render_template("lms_admin/courses.html", courses = db_lms.courses)

@app.route("/lms4labs/lms/admin/courses/external/", methods = ['GET', 'POST'])
@requires_lms_admin_session
def lms_admin_external_courses():
    q = request.args.get('q','')
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    user     = db_lms.labmanager_login
    password = db_lms.labmanager_password
    if q is not None:
        url = "%s?q=%s" % (db_lms.url, q)
    else:
        url = db_lms.url

    req = urllib2.Request(url, '')
    req.add_header('Content-type','application/json')

    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, user, password)
    password_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(password_handler)

    json_courses = opener.open(req).read()
    courses = json.loads(json_courses)

    existing_courses = db_session.query(Course).filter(Course.course_id.in_(courses.keys()), Course.lms == db_lms).all()
    existing_course_ids = [ existing_course.course_id for existing_course in existing_courses ]

    if request.method == 'POST':
        for course_id in request.form:
            if course_id != 'action' and course_id in courses and course_id not in existing_course_ids:
                db_course = Course(db_lms, course_id, courses[course_id])
                db_session.add(db_course)
        db_session.commit()
        return redirect(url_for('lms_admin_courses'))

    return render_template("lms_admin/courses_external.html", courses = courses, existing_course_ids = existing_course_ids, q = q)
    
   

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

@app.route("/lms4labs/admin/logout/show", methods = ['GET', 'POST'])
def admin_before_logout():
    return render_template("labmanager_admin/logout.html")

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

@app.route("/lms4labs/admin/lms/<int:id>/edit/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_edit(id):
    return _add_or_edit_lms(id)

@app.route("/lms4labs/admin/lms/add/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_add():
    return _add_or_edit_lms(id = None)

@app.route("/lms4labs/admin/lms/<lms_login>/login/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_login(lms_login):
    return _login_as_lms(session['user_name'], lms_login)

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

    if id is not None:
        rlms = db_session.query(RLMS).filter_by(id = id).first()
        if rlms is None or rlms.rlms_version != rlms_version:
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

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_edit(rlmstype, rlmsversion, id):
    return _add_or_edit_rlms(rlmstype, rlmsversion, id)

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_list(rlmstype, rlmsversion, id):
    rlms = db_session.query(RLMS).filter_by(id = id).first()
    if rlms is None or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return render_template("labmanager_admin/rlms_errors.html")

    if request.method == 'POST':
        if request.form.get('action','') == 'add':
            return redirect(url_for('admin_rlms_rlms_list_external', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id))

    laboratories = rlms.laboratories

    ManagerClass          = get_manager_class(rlmstype, rlmsversion)
    manager_class         = ManagerClass(rlms.configuration)
    try:
        confirmed_laboratories = manager_class.get_laboratories()
    except:
        traceback.print_exc()
        flash("There was an error retrieving laboratories. Check the trace")
        return render_template("labmanager_admin/rlms_errors.html")

    confirmed_laboratory_ids = [ confirmed_laboratory.laboratory_id for confirmed_laboratory in confirmed_laboratories ]

    return render_template("labmanager_admin/rlms_rlms_list.html", laboratories = laboratories, type_name = rlmstype, version = rlmsversion, rlms_name = rlms.name, confirmed_laboratory_ids = confirmed_laboratory_ids, rlms_id = rlms.id)

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/externals/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_list_external(rlmstype, rlmsversion, id):
    rlms = db_session.query(RLMS).filter_by(id = id).first()
    if rlms is None or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return render_template("labmanager_admin/rlms_errors.html")

    existing_laboratory_ids = [ laboratory.laboratory_id for laboratory in rlms.laboratories ]

    ManagerClass          = get_manager_class(rlmstype, rlmsversion)
    manager_class         = ManagerClass(rlms.configuration)
    try:
        available_laboratories = manager_class.get_laboratories()
    except:
        traceback.print_exc()
        flash("There was an error retrieving laboratories. Check the trace")
        return render_template("labmanager_admin/rlms_errors.html")

    available_laboratory_ids = [ lab.laboratory_id for lab in available_laboratories ]

    if request.method == 'POST':
        if request.form.get('action','') == 'add':
            for laboratory_id in request.form:
                if laboratory_id != 'action' and laboratory_id in available_laboratory_ids and laboratory_id not in existing_laboratory_ids:
                    new_lab = Laboratory(laboratory_id, laboratory_id, rlms)
                    db_session.add(new_lab)
            db_session.commit()
            return redirect(url_for('admin_rlms_rlms_list', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id))

    return render_template("labmanager_admin/rlms_rlms_list_external.html", available_laboratories = available_laboratories, type_name = rlmstype, version = rlmsversion, rlms_name = rlms.name, existing_laboratory_ids = existing_laboratory_ids)

def get_lab_and_lms(rlmstype, rlmsversion, id, lab_id):
    lab  = db_session.query(Laboratory).filter_by(id = lab_id).first()
    if lab is None:
        return None, None

    rlms = lab.rlms
    if rlms is None or rlms.id != id or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return None, None
    return lab, rlms


@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/<int:lab_id>/permissions/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_lab_edit_permissions(rlmstype, rlmsversion, id, lab_id):
    template_variables = {}

    lab, rlms = get_lab_and_lms(rlmstype, rlmsversion, id, lab_id)
    if lab is None or rlms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    if request.method == 'POST':
        if request.form.get('action','').startswith('revoke-'):
            lms_id_str = request.form['action'][len('revoke-'):]
            try:
                lms_id = int(lms_id_str)
            except:
                return render_template("labmanager_admin/rlms_errors.html")

            lms = db_session.query(LMS).filter_by(id = lms_id).first()
            if lms is None:
                return render_template("labmanager_admin/rlms_errors.html")
           
            permission = db_session.query(PermissionOnLaboratory).filter_by(laboratory_id = lab_id, lms_id = lms_id).first()
            if permission is not None:
                db_session.delete(permission)
                db_session.commit()

    granted_lms_ids = [ perm.lms_id for perm in lab.permissions ]

    lmss = db_session.query(LMS).all()

    template_variables['granted_lms_ids'] = granted_lms_ids
    template_variables['type_name']       = rlmstype
    template_variables['version']         = rlmsversion
    template_variables['rlms_name']       = rlms.name
    template_variables['rlms_id']         = id
    template_variables['lab_name']        = lab.name
    template_variables['lab_id']          = lab_id
    template_variables['lmss']            = lmss

    return render_template("labmanager_admin/rlms_rlms_lab_edit_permissions.html", **template_variables)

@app.route("/lms4labs/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/<int:lab_id>/permissions/<int:lms_id>", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_lab_edit_permissions_lms(rlmstype, rlmsversion, id, lab_id, lms_id):
    template_variables = {}

    lab, rlms = get_lab_and_lms(rlmstype, rlmsversion, id, lab_id)
    if lab is None or rlms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    lms = db_session.query(LMS).filter_by(id = lms_id).first()
    if lms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    permission = db_session.query(PermissionOnLaboratory).filter_by(laboratory_id = lab_id, lms_id = lms_id).first()

    PermissionsForm = get_permissions_form_class(rlmstype, rlmsversion)
    form = PermissionsForm()
    if form.validate_on_submit():
        configuration_dict = {}
        for field in form.get_field_names():
            data = getattr(form, field).data
            if data != '':
                configuration_dict[field] = data

        configuration = json.dumps(configuration_dict)

        if permission is None: # Not yet granted: add it
            permission = PermissionOnLaboratory(lms = lms, laboratory = lab, configuration = configuration)
            db_session.add(permission)
        else: # Already granted: edit it
            permission.configuration = configuration

        db_session.commit()
        return redirect(url_for('admin_rlms_rlms_lab_edit_permissions', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id, lab_id = lab_id))

    if permission is not None:
        configuration_dict = json.loads(permission.configuration or '{}')
        for field in configuration_dict:
            getattr(form, field).data = configuration_dict.get(field,'')

    template_variables['type_name']       = rlmstype
    template_variables['version']         = rlmsversion
    template_variables['rlms_name']       = rlms.name
    template_variables['rlms_id']         = id
    template_variables['lab_name']        = lab.name
    template_variables['lab_id']          = lab_id
    template_variables['lms_name']        = lms.name
    template_variables['add_or_edit']     = permission is None
    template_variables['form']            = form

    return render_template("labmanager_admin/rlms_rlms_lab_edit_permissions_add.html", **template_variables)


###############################################################################
# 
# 
# 
#                G E N E R A L     V I E W
# 
# 
# 

@app.route("/fake_list_courses", methods = ['GET','POST'])
def fake_list_courses():
    q = request.args.get('q','')
    auth = request.authorization

    fake_data = { "1" : "Fake electronics course", "2" : "Fake physics course"}
    view = {}
    for key, value in fake_data.items():
        if q in value:
            view[key] = value

    if auth is not None and auth.username in ('test','labmanager') and auth.password in ('test','password'):
        return json.dumps(view)
    return Response('You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route("/lms4labs/")
def lms4labs_index():
    return render_template("index.html")



@app.route("/")
def index():
    return redirect(url_for('lms4labs_index'))

def run():
    app.config.from_object('config')
    app.run(threaded = True, host = '0.0.0.0')

if __name__ == "__main__":
    run()
