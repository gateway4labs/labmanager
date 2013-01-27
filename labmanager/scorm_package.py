import hashlib

from werkzeug.exceptions import Unauthorized
from flask import request, g, Blueprint

from labmanager.database import db_session
from labmanager.models import NewLMS, Credential
from labmanager.views import get_json

scorm_blueprint = Blueprint('basic_auth', __name__)

def check_lms_auth(lmsname, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    # TODO: check if there could be a conflict between two LMSs with same key??
    credential = db_session.query(Credential).filter_by(key = lmsname, secret = hash_password).first()
    print credential, lmsname, password
    print db_session.query(Credential).all()
    if credential is None:
        return False
    g.lms = credential.lms.name
    return 

@scorm_blueprint.before_request
def requires_lms_auth():
    auth = request.authorization
    if not auth:
        json_data = get_json()
        if json_data is None:
            raise Unauthorized("Could not verify your access level for that URL")

        username = json_data.get('lms_username','')
        password = json_data.get('lms_password','')
    else:
        username = auth.username
        password = auth.password

    if not check_lms_auth(username, password):
        raise Unauthorized("Could not verify your access level for that URL")


