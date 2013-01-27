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
import urlparse
from functools import wraps

# 
# Flask imports
# 
from flask import render_template, request, g, session, redirect, url_for, flash, Response, Blueprint

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import PermissionOnLaboratory
from labmanager.rlms     import get_permissions_form_class

from labmanager.views import get_json, deletes_elements, get_scorm_object, get_authentication_scorm, retrieve_courses

lms_admin = Blueprint('lms_admin', __name__)

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
            return 'Not authorized. If you are a LabManager administrator, download <a href="%s">this SCORM</a>, install it, and you will be able to administrate the system. Otherwise, you should ask your LMS to authenticate you through <a href="%s">%s</a>.' % (url_for('lms_admin.lms_admin_authenticate_scorm'), url_for('lms_admin.lms_admin_authenticate'), url_for('lms_admin.lms_admin_authenticate'))
        return f(*args, **kwargs)
    return decorated

@lms_admin.route("/admin/logout", methods = ['GET', 'POST'])
def lms_admin_logout():
    session.pop('logged_in', None)
    referrer = session['referrer']
    if not referrer:
        return redirect(url_for('lms_admin.index'))
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

@lms_admin.route("/admin/authenticate/", methods = ['GET', 'POST'])
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

    return redirect(url_for('lms_admin.lms_admin_index'))


@lms_admin.route("/admin/authenticate/<token>")
def lms_admin_redeem_authentication(token):
    token_info = TOKENS.pop(token, None)
    if token_info is None:
        return "Token not found"
    return _login_as_lms(token_info['user_name'], token_info['lms'])


@lms_admin.route("/admin/courses/external/", methods = ['GET', 'POST'])
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

    VISIBLE_PAGES = 10
    results = retrieve_courses(url, user, password)
    if isinstance(results, basestring):
        return "Invalid JSON provided or could not connect to the LMS. Look at the logs for more information"

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
    #    print course_dict
    if request.method == 'POST':
        for course_id in request.form:
            #print "----> %s" % course_id
            if course_id != 'action' and course_id in course_dict.keys() and course_id not in existing_course_ids:
                db_course = Course(db_lms, course_id, course_dict[course_id])
                db_session.add(db_course)
        db_session.commit()
        return redirect(url_for('lms_admin.lms_admin_courses'))

    return render_template("lms_admin/courses_external.html", courses = courses, existing_course_ids = existing_course_ids, q = q, current_page = current_page, number = number, current_pages = current_pages, per_page = per_page, start = start)

