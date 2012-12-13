from hashlib import new as new_hash
from time import time
from functools import wraps

from flask import Response, render_template, request, g, abort, flash, redirect, url_for, session
from flask.ext.login import LoginManager, login_user, logout_user, UserMixin, login_required

from labmanager import app
from labmanager.models import LMS, LabManagerUser as User, Credential
from labmanager.views.ims_lti import lti
from labmanager.views.lms import basic_auth


def check_lms_auth(lmsname, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(lms_login = lmsname, lms_password = hash_password).first()
    g.lms = lmsname
    return lms is not None

@basic_auth.before_request
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
