import json
import cgi
import traceback
import sha

import urlparse
import codecs
import os
import StringIO
import zipfile

# 
# Flask imports
# 
from flask import Response, render_template, flash, request, g, Blueprint

# Labmanager imports
from labmanager.db import db_session
from labmanager.models import LmsCredential
from labmanager.models   import LMS, PermissionToLms
from labmanager.rlms     import get_manager_class
from labmanager.application import app

from labmanager.views.error_codes import messages_codes

########################################################
# 
#  SCORM blueprint and methods
# 

scorm_blueprint = Blueprint('basic_auth', __name__)

def check_lms_auth(lmsname, password):
    hash_password = sha.new(password).hexdigest()
    # TODO: check if there could be a conflict between two LMSs with same key??
    credential = db_session.query(LmsCredential).filter_by(key = lmsname, secret = hash_password).first()
    if credential is None:
        return False
    g.lms = credential.lms.name
    return True

@scorm_blueprint.before_request
def requires_lms_auth():

    UNAUTHORIZED = Response(response="Could not verify your credentials for that URL", status=401, headers = {'WWW-Authenticate':'Basic realm="Login Required"'})

    auth = request.authorization
    if not auth:
        from labmanager.views import get_json
        json_data = get_json()
        if json_data is None:
            return UNAUTHORIZED

        username = json_data.get('lms_username','')
        password = json_data.get('lms_password','')
    else:
        username = auth.username
        password = auth.password

    if not check_lms_auth(username, password):
        return UNAUTHORIZED


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


#################################################
# 
#  SCORM utilities
# 

def get_scorm_object(authenticate = True, laboratory_identifier = '', lms_path = '/', lms_extension = '/', html_body = '''<div id="lms4labs_root" />\n'''):
    import labmanager
    # TODO: better way
    base_dir = os.path.dirname(labmanager.__file__)
    base_scorm_dir = os.path.join(base_dir, 'data', 'scorm')
    if not os.path.exists(base_scorm_dir):
        flash("Error: %s does not exist" % base_scorm_dir)
        return render_template("lms_admin/scorm_errors.html")

    sio = StringIO.StringIO('')
    zf = zipfile.ZipFile(sio, 'w')
    for root, dir, files in os.walk(base_scorm_dir):
        for f in files:
            file_name = os.path.join(root, f)
            arc_name  = os.path.join(root[len(base_scorm_dir)+1:], f)
            content = codecs.open(file_name, 'rb', encoding='utf-8').read()
            if f == 'lab.html' and root == base_scorm_dir:
                content = content % { 
                            u'EXPERIMENT_COMMENT'    : '//' if authenticate else '',
                            u'AUTHENTICATE_COMMENT'  : '//' if not authenticate else '',
                            u'EXPERIMENT_IDENTIFIER' : unicode(laboratory_identifier),
                            u'LMS_URL'               : unicode(lms_path),
                            u'LMS_EXTENSION'         : unicode(lms_extension),
                            u'HTML_CONTENT'          : unicode(html_body),
                        }
            zf.writestr(arc_name, content.encode('utf-8'))

    zf.close()
    return sio.getvalue()

def get_authentication_scorm(lms_url):
    lms_path = urlparse.urlparse(lms_url).path or '/'
    extension = '/'
    if 'lms4labs/' in lms_path:
        extension = lms_path[lms_path.rfind('lms4labs/lms/list') + len('lms4labs/lms/list'):]
        lms_path  = lms_path[:lms_path.rfind('lms4labs/')]

    content = get_scorm_object(True, lms_path=lms_path, lms_extension=extension)
    return Response(content, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=authenticate_scorm.zip'})


