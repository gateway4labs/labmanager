from time import time

from flask import request, abort, Blueprint, session, Response, render_template
from ims_lti_py import ToolProvider

from labmanager.models import PermissionToLmsUser

lti_blueprint = Blueprint('lti', __name__)

@lti_blueprint.before_request
def verify_credentials():
    if 'oauth_consumer_key' in request.form:
        consumer_key = request.form['oauth_consumer_key']
        permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)

        # TODO: check for nonce
        # TODO: check for old requests

        if permission_to_lms_user is None:
            response = Response(render_template('lti/errors.html', message = "Invalid consumer key. Please check it again."))
            # response.status_code = 412
            return response

        secret = permission_to_lms_user.secret
        tool_provider = ToolProvider(consumer_key, secret, request.form.to_dict())

        try:
            return_value = tool_provider.valid_request(request)
        except:
            response = Response(render_template('lti/errors.html', message = "Invalid secret: could not validate request."))
            # response.status_code = 403
            return response
        else:
            if return_value == False:
                response = Response(render_template('lti/errors.html', message = "Request checked and failed. Please check that the 'secret' is correct."))
                # response.status_code = 403
                return response

        session['author_identifier']  = request.form['user_id']
        session['consumer'] = consumer_key
        session['last_request'] = time()

        return

    elif 'consumer' in session:
        if float(session['last_request']) - time() < 60 * 60 * 5: # Five Hours
            session['last_request'] = time()
            return

    else:
        abort(403)
