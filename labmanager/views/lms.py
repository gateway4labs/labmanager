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
import cgi
import traceback
from sets import Set
from yaml import load as yload

#
# Flask imports
#
from flask import Response, render_template, request, g, abort

#
# LabManager imports
#
from labmanager.database import db_session
from labmanager.models   import LMS, PermissionOnLaboratory, RLMS, Laboratory
from labmanager.models import NewLMS, Credential, NewRLMS, Permission, Experiment, NewCourse
from labmanager.rlms     import get_manager_class

from labmanager import app
from labmanager.views import get_json
from error_codes import messages_codes
from login import requires_lms_auth

configs = yload(open('labmanager/config.yaml'))

###############################################################################
#
#
#
#               I N T E R A C T I O N     W I T H     L M S
#
#
#

@app.route("/lms4labs/labmanager/requests/", methods = ['GET', 'POST'])
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will
    interact with the permitted laboratories"""
    
    if request.method == 'GET':
        return render_template("test_requests.html")
    
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
    db_lms = db_session.query(LMS).filter_by(lms_login = g.lms).first()
    permission_on_lab = db_session.query(PermissionOnLaboratory).filter_by(lms_id = db_lms.id, local_identifier = experiment_identifier).first()
    good_msg  = messages_codes['ERROR_no_good']
    error_msg = None
    reservation_url = ""
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
            reservation_url = remote_laboratory.reserve(db_laboratory.laboratory_id,
                                                        author,
                                                        lms_configuration,
                                                        courses_configurations,
                                                        request_payload,
                                                        user_agent,
                                                        origin_ip,
                                                        referer)
            good_msg = messages_codes['MSG_asigned'] % (db_rlms.name,
                                                        db_rlms_type.name,
                                                        db_rlms_version.version,
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


@app.route("/t", methods=['GET'])
def just_for_the_fun_of_testing_app(id = None):
    ans = ":)"
    print Permission.find_by_lms_and_resource(NewLMS.find(1), 2)

    return ans

@app.route('/labmanager/ims/tool_linking/', methods = ['POST'])
def tool_link_ims():
    return render_template('lti/request_status.html', info={})

@app.route('/ims/admin/request_permission/', methods = ['POST'])
def permission_request():
    data = {}
    choice_data = []

    for exps in request.form.getlist('rlmsexperiments'):
        split_choice = exps.split(':')
        rlms_id, exp_id = int(split_choice[0]), int(split_choice[1])
        choice_data.append((rlms_id, exp_id))

    lms_id = int(request.form['lms_id'])
    context_id = request.form['context_id']
    context_label = request.form['context_label']
    newlms = NewLMS.find(lms_id)

    local_context = NewCourse.find_or_create(lms = newlms,
                                             context = context_id,
                                             name = context_label)
    exp_status = []
    for rlms_id, exp_id in choice_data:
        experiment = Experiment.find_with_id_and_rlms_id(exp_id, rlms_id)
        permission = Permission.find_or_create(lms = newlms,
                                               experiment = experiment,
                                               context = local_context)
        exp_status.append(permission)

    data['access_requests'] = exp_status

    return render_template('lti/request_status.html', info=data)

@app.route("/ims/admin/", methods = ['POST'])
def admin_ims():
    message = ""
    response = ""

    consumer_key = request.form['oauth_consumer_key']
    auth = Credential.find_by_key(consumer_key)

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : auth.newlms.name,
             'lms_id' : auth.newlms.id,
             'context_label' : request.form['context_label'],
             'context_id' : request.form['context_id'],
             }

    # Defined by the standard. After this comes the role of the user as in
    # 'urn:lti:sysrole:ims/lis/Administrator' or 'urn:lti:sysrole:ims/lis/SysAdmin'
    urn_role_base = 'urn:lti:sysrole:ims/lis/'
    roles = Set()

    split_roles = request.form['roles'].split(',')
    for role in split_roles:
        if role.startswith(urn_role_base):
            roles.add(role[len(urn_role_base):])

    admin_roles = Set(configs['standard_urn_admin_roles'])
    current_users_roles = roles & admin_roles # Set intersection

    if len(current_users_roles) > 0:

        data['role'] = current_users_roles.pop() # Returns an arbitrary element
        data['rlms'] = {}
        data['rlms_ids'] = {}

        local_context = NewCourse.find_or_create(lms = auth.newlms,
                                                 context = request.form['context_id'],
                                                 name = request.form['context_label'])

        current_permissions = Permission.find_all_with_lms_and_context(lms = auth.newlms,
                                                                       context = local_context)

        data['access_requests'] = current_permissions

        for remote in NewRLMS.all(): # filter by allowed RLMSs
            experiments_in_rlms = remote.experiments
            data['rlms'][remote.kind] = [ exp for exp in experiments_in_rlms ]
            data['rlms_ids'][remote.kind] = remote.id

        return render_template('lti/administrator_tool_setup.html', info=data)

    else:
        data['role'] = split_roles[0]
        return render_template('lti/unknown_role.html', info=data)


@app.route("/labmanager/ims/", methods = ['POST'])
def start_ims():
    message = ""
    response = ""

    consumer_key = request.form['oauth_consumer_key']
    auth = Credential.find_by_key(consumer_key)

    # check for nonce
    # check for old requests

    # Cross reference information
    current_role = Set(request.form['roles'].split(','))
    req_course_data = request.form['lis_result_sourcedid']

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : auth.newlms.name,
             'lms_id' : auth.newlms.id,
             'context_label' : request.form['context_label'],
             'context_id' : request.form['context_id'],
             'resource_name' : request.form['resource_link_title'],
             'resource_id' : request.form['resource_link_id'],
             'access' : False
             }

    if app.config.get('DEBUGGING_REQUESTS', True):
        message += printdebug(request)
        data['message'] = message

    context = NewCourse.find_by_lms_and_context(auth.newlms, data['context_id'])

    if context is None:
        context_name = request.form['context_label']
        context = NewCourse.new(name = context_name,
                                lms = auth.newlms,
                                context_id = data['context_id'])

    exp_access = Permission.find_with_params(lms=auth.newlms,
                                             resource_id=data['resource_id'],
                                             context=context)

    if ('Instructor' in current_role):

        data['role'] = 'Instructor'
        data['rlms'] = {}
        data['rlms_ids'] = {}

        if exp_access is None:
#             for remote in NewRLMS.all(): # filter by allowed RLMSs
#                 experiments_in_rlms = remote.experiments
#                 data['rlms'][remote.kind] = [ exp for exp in experiments_in_rlms ]
#                 data['rlms_ids'][remote.kind] = remote.id

            response = render_template('lti/instructor_tool_setup.html', info=data)
        else:
            data['status'] = exp_access.access
            response = render_template('lti/request_status.html', info=data)

    elif ('Learner' in current_role):

        data['role'] = 'Learner'
        # retrieve experiment for course

        if exp_access is not None:
            data['access'] = True
            data['experiment'] = exp_access.experiment.name
            data['experiment_url'] = exp_access.experiment.url

        response = render_template('lti/learner_launch_tool.html', info=data)

    else:
        response = render_template('lti/unknown_role.html', info=data)

    return response

@app.route("/lms4labs/labmanager/ims/<experiment>", methods = ['GET'])
def launch_experiment(experiment=None):
    response = ""

    if (experiment):
        response = experiment
    else:
        response = "No soup for you!"

    return response


def create_lab_with_data(lab_info):
    requestform = lab_info['request.form']
    experiment = lab_info['experiment']
    general_role = True

    db_lms = db_session.query(LMS).filter_by(lms_login = g.lms).first()
    permission_on_lab = db_session.query(PermissionOnLaboratory).filter_by(lms_id = db_lms.id, local_identifier = experiment).first()
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
            origin_ip = lab_info['origin_ip']
            user_agent = lab_info['user_agent']
            referer = "google.com"

            if 'custom_require_student_privacy' in requestform:
                username = requestform['user_id']
            else:
                username = requestform['lis_person_name_full']

            ManagerClass = get_manager_class(db_rlms_type.name, db_rlms_version.version)
            remote_laboratory = ManagerClass(db_rlms.configuration)
            reservation_url = remote_laboratory.reserve(db_laboratory.laboratory_id, username, lms_configuration, courses_configurations, {}, str(user_agent), origin_ip, referer)
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

        if error_msg is None:
            return reservation_url
        else:
            return messages_codes['ERROR_'] % error_msg

def printdebug(request):
    message = ""
    dict = request.form.keys()
    dict.sort()
    message += "<br/>"
    message += '<br/>'.join(["%s = <strong>%s</strong>" % (x,request.form[x]) for x in dict])
    return message
