# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Sergio Botero
  :license: BSD, see LICENSE for more details
"""

from flask import render_template, request, redirect, session

from labmanager.models import PermissionToLmsUser

from labmanager.ims_lti import lti_blueprint as lti
from labmanager.rlms import get_manager_class

@lti.route("/", methods = ['POST'])
def start_ims():
#    import pprint
#    pprint.pprint(request.form)

    consumer_key = request.form.get('oauth_consumer_key')
    permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)

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

    laboratory       = permission_to_lms_user.permission_to_lms.laboratory
    local_identifier = permission_to_lms_user.permission_to_lms.local_identifier

    return render_template('lti/display_lab.html', laboratory = laboratory, local_identifier = local_identifier)

@lti.route("/experiment/", methods = ['GET', 'POST'])
def launch_experiment():
    consumer_key = session.get('consumer')
    if consumer_key is None:
        return "consumer key not found"

    permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)
    if permission_to_lms_user is None:
        return "permission not found"

    p_to_lms = permission_to_lms_user.permission_to_lms

    # 
    # TODO:
    # 
    # author (from session?)
    # referer
    courses_configurations = [] # No such concept in the LTI version
    request_payload = {} # This could be populated in the HTML. Pending.
    lms_configuration = p_to_lms.configuration
    db_laboratory     = p_to_lms.laboratory
    db_rlms           = db_laboratory.rlms
    author            = session.get('author_identifier', '(not in session)')
    referer           = ""

    ManagerClass = get_manager_class(db_rlms.kind, db_rlms.version)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    response = remote_laboratory.reserve(db_laboratory.laboratory_id,
                                         author,
                                         lms_configuration,
                                         courses_configurations,
                                         request_payload,
                                         unicode(request.user_agent),
                                         request.remote_addr,
                                         referer)
    return redirect(response)

