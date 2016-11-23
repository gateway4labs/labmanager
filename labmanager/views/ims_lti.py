# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Sergio Botero, Pablo Orduña
  :license: BSD, see LICENSE for more details
"""

from time import time
from ims_lti_py import ToolProvider
from flask import request, Blueprint, session, Response, render_template, redirect
from labmanager.models import PermissionToLtUser
from labmanager.rlms import get_manager_class
from labmanager.babel import gettext
from labmanager.utils import remote_addr

lti_blueprint = Blueprint('lti', __name__)

@lti_blueprint.before_request
def verify_credentials():
    if 'oauth_consumer_key' in request.form:
        consumer_key = request.form['oauth_consumer_key']
        permission_to_lt_user = PermissionToLtUser.find(key = consumer_key)
        # TODO: check for nonce
        # TODO: check for old requests
        if permission_to_lt_user is None:
            response = Response(render_template('lti/errors.html', message = gettext("Invalid consumer key. Please check it again.")))
            # response.status_code = 412
            return response
        secret = permission_to_lt_user.secret
        # The original dict is in unicode, which does not work with ToolProvider
        USE_UNICODE = False
        if USE_UNICODE:
            data_dict = request.form.to_dict()
        else:
            data_dict = {} 
            for key, value in request.form.to_dict().iteritems():
                data_dict[key.encode('utf8')] = value.encode('utf8')
        tool_provider = ToolProvider(consumer_key, secret, data_dict)
        try:
            return_value = tool_provider.valid_request(request)
        except:
            response = Response(render_template('lti/errors.html', message = gettext("Invalid secret: could not validate request.")))
            # response.status_code = 403
            return response
        else:
            if return_value == False:
                response = Response(render_template('lti/errors.html', message = gettext("Request checked and failed. Please check that the 'secret' is correct.")))
                # response.status_code = 403
                return response
        session['author_identifier']  = request.form['user_id']
        if 'lis_person_name_full' in request.form:
            session['user_fullname'] = request.form['lis_person_name_full']
        if 'context_id' in request.form:
            session['group_id'] = request.form['context_id']
        if 'context_title' in request.form:
            session['group_name'] = request.form['context_title']
        if 'launch_presentation_locale' in request.form:
            session['launch_locale'] = request.form['launch_presentation_locale']
        if 'launch_presentation_document_target' in request.form:
            session['launch_presentation_document_target'] = request.form['launch_presentation_document_target']
        if 'launch_presentation_return_url' in request.form:
            session['launch_presentation_return_url'] = request.form['launch_presentation_return_url']
        session['consumer'] = consumer_key
        session['last_request'] = time()
        return
    elif 'consumer' in session:
        if float(session['last_request']) - time() < 60 * 60 * 5: # Five Hours
            session['last_request'] = time()
            return
    else:
        response = Response(render_template('lti/errors.html', message = gettext("Session not initialized. Are you a LMS?")))
        # response.status_code = 403
        return response

@lti_blueprint.route("/", methods = ['GET', 'POST'])
def start_ims():
    consumer_key = session.get('consumer')
    return_url = session.get('launch_presentation_return_url') or ''
    permission_to_lt_user = PermissionToLtUser.find(key = consumer_key)

    # current_role = set(request.form['roles'].split(','))
    # 
    # We could do something with the role (e.g., defining "oh, you're an instructor, do you want to use who used the system?").
    # However, at this moment, we don't do anything.
    # In the future, do:
    # 
    # if 'Learner' in current_role:
    #    ...
    # elif 'Instructor' in current_role:
    #    ....
    # 

    laboratory       = permission_to_lt_user.permission_to_lt.laboratory
    local_identifier = permission_to_lt_user.permission_to_lt.local_identifier
    return render_template('lti/display_lab.html', laboratory = laboratory, local_identifier = local_identifier, return_url = return_url)

@lti_blueprint.route("/experiment/", methods = ['GET', 'POST'])
def launch_experiment():
    consumer_key = session.get('consumer')
    if consumer_key is None:
        return gettext("consumer key not found")
    permission_to_lt_user = PermissionToLtUser.find(key = consumer_key)
    if permission_to_lt_user is None:
        return gettext("permission not found")
    p_to_lt = permission_to_lt_user.permission_to_lt
    courses_configurations = [] # No such concept in the LTI version
    request_payload = {} # This could be populated in the HTML. Pending.
    lt_configuration = p_to_lt.configuration
    db_laboratory     = p_to_lt.laboratory
    db_rlms           = db_laboratory.rlms
    author            = session.get('author_identifier', '(not in session)')
    referer           = request.referrer
    ManagerClass = get_manager_class(db_rlms.kind, db_rlms.version, db_rlms.id)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    request_info = { 
        'user_agent' : unicode(request.user_agent),
        'from_ip'    : remote_addr(),
        'referer'    : referer,
    }
    for key in 'group_name', 'group_id', 'user_fullname':
        if key in session:
            request_info[key] = session[key]
    kwargs = {}
    if 'launch_locale' in session:
        kwargs['locale'] = session['launch_locale'].split('-')[0].split('_')[0]

    response = remote_laboratory.reserve(db_laboratory.laboratory_id,
                                         author,
                                         p_to_lt.lt.name,
                                         lt_configuration,
                                         courses_configurations,
                                         request_payload,
                                         request_info,
                                         **kwargs)
    load_url = response['load_url']
    return redirect(load_url)
