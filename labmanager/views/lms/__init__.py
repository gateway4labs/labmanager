# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

#
# Python imports
import json
import cgi
import traceback

#
# Flask imports
#
from flask import render_template, request, g

#
# LabManager imports
#
from labmanager.database import db_session
from labmanager.models   import LMS, PermissionToLms
from labmanager.rlms     import get_manager_class
from labmanager.application import app

from labmanager.views.error_codes import messages_codes
from labmanager.scorm_package import scorm_blueprint


###############################################################################
#
#
#
#               I N T E R A C T I O N     W I T H     L M S
#
#
#

@scorm_blueprint.route("/requests/", methods = ['GET', 'POST'])
def requests():
    """SCORM packages will perform requests to this method, which will
    interact with the permitted laboratories"""
    
    if request.method == 'GET':
        return render_template("test_requests.html")
    
    from labmanager.views import get_json
    json_data = get_json()

    if json_data is None: return messages_codes['ERROR_json']

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
    db_lms = db_session.query(LMS).filter_by(name = g.lms).first()
    permission_to_lms = db_session.query(PermissionToLms).filter_by(lms = db_lms, local_identifier = experiment_identifier).first()
    good_msg  = messages_codes['ERROR_no_good']
    error_msg = None
    reservation_url = ""
    if permission_to_lms is None:
        error_msg = messages_codes['ERROR_permission']
    else:
        courses_configurations = []
        for course_permission in permission_to_lms.course_permissions:
            if course_permission.course.context_id in courses:
                # Let the server choose among the best possible configuration
                courses_configurations.append(course_permission.configuration)
        
        if len(courses_configurations) == 0 and not general_role:
            error_msg = messages_codes['ERROR_enrolled']
        else:
            lms_configuration = permission_to_lms.configuration
            db_laboratory   = permission_to_lms.laboratory
            db_rlms         = db_laboratory.rlms
            rlms_version    = db_rlms.version
            rlms_kind       = db_rlms.kind

            ManagerClass = get_manager_class(rlms_kind, rlms_version)
            remote_laboratory = ManagerClass(db_rlms.configuration)
            
            # XXX TODO: a dictionary should be passed here so as to enable changing details among versions
            reservation_url = remote_laboratory.reserve(laboratory_id             = db_laboratory.laboratory_id,
                                                        username                  = author,
                                                        general_configuration_str = lms_configuration,
                                                        particular_configurations = courses_configurations,
                                                        request_payload           = request_payload,
                                                        user_agent                = user_agent,
                                                        origin_ip                 = origin_ip,
                                                        referer                   = referer)
            good_msg = messages_codes['MSG_asigned'] % (db_rlms.kind,
                                                        db_rlms.version,
                                                        db_rlms.url,
                                                        reservation_url,
                                                        reservation_url)

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
