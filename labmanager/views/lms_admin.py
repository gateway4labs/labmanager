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
"""

#
# Python imports
import json
import uuid
import traceback
import urllib2
from functools import wraps

# 
# Flask imports
# 
from flask import render_template, request, g, session, redirect, url_for, flash

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import LMS, Course, PermissionOnLaboratory, PermissionOnCourse
from labmanager.rlms     import get_permissions_form_class

from labmanager.server import app
from labmanager.views import get_json, deletes_elements
from labmanager.views.lms import requires_lms_auth


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

@app.route("/lms4labs/labmanager/lms/admin/logout", methods = ['GET', 'POST'])
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

@app.route("/lms4labs/labmanager/lms/admin/authenticate/", methods = ['GET', 'POST'])
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
        'user_name' : json_data['full-name'],
        'lms'       : g.lms,
        'referrer'  : ''
    }

    return app.config.get('URL_ROOT', request.url_root) + url_for('lms_admin_redeem_authentication', token = code)

def _login_as_lms(user_name, lms_login):
    session['logged_in']     = True
    session['session_type']  = 'lms_admin'
    session['user_name']     = user_name
    session['lms']           = lms_login
    session['referrer']       = request.referrer

    return redirect(url_for('lms_admin_index'))


@app.route("/lms4labs/labmanager/lms/admin/authenticate/<token>")
def lms_admin_redeem_authentication(token):
    token_info = TOKENS.pop(token, None)
    if token_info is None:
        return "Token not found"
    return _login_as_lms(token_info['user_name'], token_info['lms'])


@app.route("/lms4labs/labmanager/lms/")
def lms_index():
    return redirect(url_for('lms_admin_index'))

@app.route("/lms4labs/labmanager/lms/admin/")
@requires_lms_admin_session
def lms_admin_index():
    return render_template("lms_admin/index.html")

@app.route("/lms4labs/labmanager/lms/admin/courses/", methods = ['GET', 'POST'])
@requires_lms_admin_session
@deletes_elements(Course)
def lms_admin_courses():
    if request.method == 'POST':
        if request.form['action'] == 'add':
            return redirect(url_for('lms_admin_external_courses'))
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    return render_template("lms_admin/courses.html", courses = db_lms.courses)

@app.route("/lms4labs/labmanager/lms/admin/courses/<int:course_id>/", methods = ['GET', 'POST'])
@requires_lms_admin_session
@deletes_elements(PermissionOnCourse)
def lms_admin_courses_permissions(course_id):
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    course = db_session.query(Course).filter_by(id = course_id, lms = db_lms).first()

    if course is None:
        return render_template("lms_admin/course_errors.html")

    granted_permission_ids = [ permission.permission_on_lab_id for permission in course.permissions ]

    if request.method == 'POST':
        if request.form.get('action','').startswith('revoke-'):
            try:
                permission_on_lab_id = int(request.form['action'][len('revoke-'):])
            except:
                flash("Error parsing permission on lab identifier")
                return render_template("lms_admin/course_errors.html")

            permission_on_course = db_session.query(PermissionOnCourse).filter_by(course = course, permission_on_lab_id = permission_on_lab_id).first()
            if permission_on_course is not None:
                db_session.delete(permission_on_course)
                db_session.commit()
                
            return redirect(url_for('lms_admin_courses_permissions', course_id = course_id))

    return render_template("lms_admin/courses_permissions.html", permissions = db_lms.permissions, course = course, granted_permission_ids = granted_permission_ids)

@app.route("/lms4labs/labmanager/lms/admin/courses/<int:course_id>/permissions/<int:permission_on_lab_id>/", methods = ['GET', 'POST'])
@requires_lms_admin_session
def lms_admin_courses_permissions_edit(course_id, permission_on_lab_id):
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    course = db_session.query(Course).filter_by(id = course_id, lms = db_lms).first()
    permission_on_lab = db_session.query(PermissionOnLaboratory).filter_by(id = permission_on_lab_id, lms = db_lms).first()

    if course is None or permission_on_lab is None:
        return render_template("lms_admin/course_errors.html")

    lab             = permission_on_lab.laboratory
    db_rlms         = lab.rlms
    db_rlms_version = db_rlms.rlms_version
    db_rlms_type    = db_rlms_version.rlms_type
    rlmstype        = db_rlms_type.name
    rlmsversion     = db_rlms_version.version

    permission = db_session.query(PermissionOnCourse).filter_by(permission_on_lab = permission_on_lab, course = course).first()

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
            permission = PermissionOnCourse(permission_on_lab = permission_on_lab, course = course, configuration = configuration)
            db_session.add(permission)
        else: # Already granted: edit it
            permission.configuration    = configuration
        db_session.commit()
        return redirect(url_for('lms_admin_courses_permissions', course_id = course_id))

    if permission is not None:
        configuration_dict = json.loads(permission.configuration or '{}')
        for field in configuration_dict:
            if hasattr(form, field):
                getattr(form, field).data = configuration_dict.get(field,'')

    return render_template("lms_admin/courses_permissions_add.html", course = course, form = form, lab = lab)

@app.route("/lms4labs/labmanager/lms/admin/courses/external/", methods = ['GET', 'POST'])
@requires_lms_admin_session
def lms_admin_external_courses():
    q     = request.args.get('q','')
    try:
        start = int(request.args.get('start','0'))
    except:
        start = 0
    db_lms = db_session.query(LMS).filter_by(lms_login = session['lms']).first()
    user     = db_lms.labmanager_login
    password = db_lms.labmanager_password
    url = "%s?q=%s&start=%s" % (db_lms.url, q, start)

    req = urllib2.Request(url, '')
    req.add_header('Content-type','application/json')

    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, user, password)
    password_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(password_handler)

    json_results= opener.open(req).read()
    VISIBLE_PAGES = 10
    try:
        results = json.loads(json_results)
    except:
        print "Invalid JSON: ", json_results
        return "Invalid JSON provided. Look at the logs for more information"
    
    try:
        courses_data = results['courses']
        courses = [ (course['id'], course['name']) for course in courses_data ]
        course_dict = dict(courses)
        number   = int(results['number'])
        per_page = int(results['per-page'])
        number_of_pages = ((number - 1) / per_page ) + 1
        current_page    = ((start - 1)  / per_page ) + 1

        THEORICAL_BEFORE_PAGES = VISIBLE_PAGES / 2
        if current_page < THEORICAL_BEFORE_PAGES:
            BEFORE_PAGES = current_page
            AFTER_PAGES  = VISIBLE_PAGES - current_page
        else:
            BEFORE_PAGES = THEORICAL_BEFORE_PAGES
            AFTER_PAGES  = BEFORE_PAGES

        min_page = (start/VISIBLE_PAGES - BEFORE_PAGES)
        max_page = (start/VISIBLE_PAGES + AFTER_PAGES)
        if max_page >= number_of_pages:
            max_page = number_of_pages
        if min_page <= -1:
            min_page = 0
        current_pages   = range(min_page, max_page)
    except:
        traceback.print_exc()
        return "Malformed data retrieved. Look at the logs for more information"

    existing_courses = db_session.query(Course).filter(Course.course_id.in_(course_dict.keys()), Course.lms == db_lms).all()
    existing_course_ids = [ existing_course.course_id for existing_course in existing_courses ]

    if request.method == 'POST':
        for course_id in request.form:
            if course_id != 'action' and course_id in course_dict and course_id not in existing_course_ids:
                db_course = Course(db_lms, course_id, course_dict[course_id])
                db_session.add(db_course)
        db_session.commit()
        return redirect(url_for('lms_admin_courses'))

    return render_template("lms_admin/courses_external.html", courses = courses, existing_course_ids = existing_course_ids, q = q, current_page = current_page, number = number, current_pages = current_pages, per_page = per_page, start = start)
    

