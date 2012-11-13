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
import hashlib
import json
import cgi
import traceback
from functools import wraps

# 
# Flask imports
# 
from flask import Response, render_template, request, g

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import LMS, PermissionOnLaboratory
from labmanager.rlms     import get_manager_class

from labmanager import app
from labmanager.views import get_json
from error_codes import messages_codes

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

@app.route("/lms4labs/labmanager/requests/", methods = ['GET', 'POST'])
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    if request.method == 'GET':
        return render_template("test_requests.html")

    json_data = get_json()
    if json_data is None: return "Could not process JSON data"

    courses             = json_data['courses']
    request_payload_str = json_data['request-payload']
    general_role        = json_data.get('is-admin', False)
    author              = json_data['user-id']
    complete_name       = json_data['full-name']
    user_agent          = json_data.get('user-agent', 'unknown user agent')
    origin_ip           = json_data.get('origin-ip', 'unknown IP address')
    referer             = json_data.get('referer', 'unknown referer')

    try:
        request_payload = json.loads(request_payload_str)
    except:
        traceback.print_exc()
        return messages_codes['ERROR_invalid_json']

    try:
        action = request_payload['action']
        if action == 'reserve':
            experiment_identifier = request_payload['experiment']
        else:
            # TODO: other operations: for teachers, etc.
            return messages_codes['ERROR_unsupported']
    except KeyError:
        traceback.print_exc()
        return messages_codes['ERROR_invalid']

    # reserving...
    db_lms = db_session.query(LMS).filter_by(lms_login = g.lms).first()
    permission_on_lab = db_session.query(PermissionOnLaboratory).filter_by(lms_id = db_lms.id, local_identifier = experiment_identifier).first()
    good_msg  = messages_codes['ERROR_no_good']
    error_msg = None
    if permission_on_lab is None:
        error_msg = messages_codes['ERROR_permission']
    else:
        courses_configurations = []
        for course_permission in permission_on_lab.course_permissions:
            if course_permission.course.course_id in courses:
                # Let the server choose among the best possible configuration
                courses_configurations.append(course_permission.configuration)
        if len(courses_configurations) == 0 and not general_role:
            error_msg = messages_codes['ERROR_enrolled']
        else:
            lms_configuration = permission_on_lab.configuration
            db_laboratory   = permission_on_lab.laboratory
            db_rlms         = db_laboratory.rlms
            db_rlms_version = db_rlms.rlms_version
            db_rlms_type    = db_rlms_version.rlms_type

            ManagerClass = get_manager_class(db_rlms_type.name, db_rlms_version.version)
            remote_laboratory = ManagerClass(db_rlms.configuration)
            reservation_url = remote_laboratory.reserve(db_laboratory.laboratory_id, author, lms_configuration, courses_configurations, request_payload, user_agent, origin_ip, referer)

            good_msg = messages_codes['MSG_asigned'] % (db_rlms.name, db_rlms_type.name, db_rlms_version.version, reservation_url, reservation_url)
            
            if app.config.get('DEBUGGING_REQUESTS', True):

                rendering_data = {
                    'name'        : cgi.escape(complete_name),
                    'author'      : cgi.escape(author),
                    'lms'         : cgi.escape(g.lms),
                    'courses'     : courses,
                    'request'     : cgi.escape(request_payload_str),
                    'admin'       : general_role,
                    'json'        : cgi.escape(json.dumps(json_data)),
                    'error_msg'   : cgi.escape(error_msg or 'no error message'),
                    'good_msg'    : good_msg or 'no good message',
                    }

                return render_template('debug.html', data=rendering_data)
            else:
                if error_msg is None:
                    return reservation_url
                else:
                    return messages_codes['ERROR_'] % error_msg
