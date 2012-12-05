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
from sets import Set

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

from ims_lti_py import ToolProvider

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

    print "**-",reservation_url,"-**"

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

@app.before_first_request
def verify_credentials():
    auth = None

    if 'oauth_consumer_key' in request.form:
        consumer_key = request.form['oauth_consumer_key']
        auth = Credential.find_by_key(consumer_key)

    if auth is None:
        abort(412)

    secret = auth.secret
    tool_provider = ToolProvider(consumer_key, secret, request.form.to_dict())

    if (tool_provider.valid_request(request) == False):
        abort(403)

@app.route('/labmanager/ims/request_permission/', methods = ['POST'])
def permission_request():
    data = {}
    choice_data = request.form['experiment'].split(':')
    rlms_id, exp_id = int(choice_data[0]), int(choice_data[1])

    lms_id = int(request.form['lms_id'])
    r_id = int(request.form['resource_id'])
    c_id = request.form['context_id']

    exp = Experiment.find_with_id_and_rlms_id(exp_id, rlms_id)
    newlms = NewLMS.find(lms_id)
    context = NewCourse.find_by_lms_and_context(newlms, c_id)

    permission_request = Permission.find_with_params(lms=newlms,
                                                     context=context,
                                                     resource_id=r_id)

    if permission_request is None:
        permission_request = Permission.new(lms=newlms, context=context,
                                            resource_link_id=r_id, experiment=exp)


    data['status'] = permission_request.access

    return render_template('lti/request_status.html', info=data)

@app.route("/labmanager/ims/", methods = ['POST'])
@app.route("/labmanager/ims/<experiment>", methods = ['POST'])
def start_ims(experiment=None):
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
             'experiment' : experiment,
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
        context = NewCourse.new(name = context_name, lms = auth.newlms, context_id = data['context_id'])

    exp_access = Permission.find_with_params(lms=auth.newlms, resource_id=data['resource_id'], context=context)

    if ('Instructor' in current_role):

        data['role'] = 'Instructor'
        data['rlms'] = {}
        data['rlms_ids'] = {}

        if exp_access is None:
            for remote in NewRLMS.all(): # filter by allowed RLMSs
                experiments_in_rlms = remote.experiments
                data['rlms'][remote.kind] = [ exp for exp in experiments_in_rlms ]
                data['rlms_ids'][remote.kind] = remote.id

            response = render_template('lti/instructor_setup_tool.html', info=data)
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
