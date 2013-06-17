import sha

from flask import request, g, Blueprint, Response

from labmanager.db import db_session
from labmanager.models import LmsCredential

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


