from time import time

from flask import request, abort, Blueprint, session
from ims_lti_py import ToolProvider

from labmanager.models import PermissionToLmsUser

lti_blueprint = Blueprint('lti', __name__)

@lti_blueprint.before_request
def verify_credentials():
    if 'consumer' in session:
        if float(session['last_request']) - time() < 60 * 60 * 5: # Five Hours
            session['last_request'] = time()
            return

    if 'oauth_consumer_key' in request.form:
        consumer_key = request.form['oauth_consumer_key']
        permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)

        # TODO: check for nonce
        # TODO: check for old requests

        if permission_to_lms_user is None:
            abort(412)

        secret = permission_to_lms_user.secret
        tool_provider = ToolProvider(consumer_key, secret, request.form.to_dict())

        if (tool_provider.valid_request(request) == False):
            abort(403)

        session['author_identifier']  = request.form['user_id']
        session['consumer'] = consumer_key
        session['last_request'] = time()

        return

    else:
        abort(403)
