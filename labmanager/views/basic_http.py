import json
import cgi
import traceback
import hashlib

# 
# Flask imports
# 
from flask import Response, render_template, request, g, Blueprint

# Labmanager imports
from labmanager.db import db_session
from labmanager.models import BasicHttpCredentials
from labmanager.models   import LMS, PermissionToLms
from labmanager.rlms     import get_manager_class
from labmanager.application import app

from labmanager.views import get_json
from labmanager.views.error_codes import messages_codes

########################################################
# 
#  Basic HTTP blueprint and methods
# 

basic_http_blueprint = Blueprint('basic_auth', __name__)

@basic_http_blueprint.before_request
def requires_lms_auth():

    UNAUTHORIZED = Response(response="Could not verify your credentials for that URL", status=401, headers = {'WWW-Authenticate':'Basic realm="Login Required"'})

    auth = request.authorization
    if not auth:
        json_data = get_json()
        if json_data is None:
            return UNAUTHORIZED

        username = json_data.get('lms_username','')
        password = json_data.get('lms_password','')
    else:
        username = auth.username
        password = auth.password

    hash_password = hashlib.new('sha', password).hexdigest()
    # TODO: check if there could be a conflict between two LMSs with same key??
    print username, hash_password
    credential = db_session.query(BasicHttpCredentials).filter_by(lms_login = username, lms_password = hash_password).first()
    if credential is None:
        return UNAUTHORIZED
    g.lms = credential.lms.name


@basic_http_blueprint.route("/requests/", methods = ['GET', 'POST'])
def requests():
    """SCORM packages will perform requests to this method, which will
    interact with the permitted laboratories"""
    
    db_lms = db_session.query(LMS).filter_by(name = g.lms).first()

    if request.method == 'GET':
        local_identifiers = [ permission.local_identifier for permission in  db_lms.lab_permissions ]
        return render_template("http/requests.html", local_identifiers = local_identifiers, remote_addr = request.remote_addr, courses = db_lms.courses)
    
    from labmanager.views import get_json
    json_data = get_json()

    if json_data is None:
        return messages_codes['ERROR_json']

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
            # TODO: other operations: for instructors, booking, etc.
            return messages_codes['ERROR_unsupported']
    except KeyError:
        traceback.print_exc()
        return messages_codes['ERROR_invalid']


    # reserving...
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
            db_laboratory     = permission_to_lms.laboratory
            db_rlms           = db_laboratory.rlms
            rlms_version      = db_rlms.version
            rlms_kind         = db_rlms.kind

            # 
            # Load the plug-in for the current RLMS, and instanciate it
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

    if app.config.get('DEBUGGING_REQUESTS', False):
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
    
    if error_msg:
        return error_msg

    return reservation_url


