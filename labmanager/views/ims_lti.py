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

from sets import Set
from yaml import load as yload

from flask import render_template, request, redirect

from labmanager.models import LMS, LmsCredential, Course
from labmanager.models import PermissionToCourse, PermissionToLms, Laboratory, PermissionToLmsUser

from labmanager.ims_lti import lti_blueprint as lti
from labmanager.rlms import get_manager_class

config = yload(open('labmanager/config.yml'))

@lti.route("/", methods = ['POST'])
def start_ims():
    consumer_key = request.form.get('oauth_consumer_key')
    permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)

    # current_role = Set(request.form['roles'].split(','))
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

    lms = permission_to_lms_user.lms_user.lms
    local_identifier = permission_to_lms_user.permission_to_lms.local_identifier
    laboratory = unicode(permission_to_lms_user.permission_to_lms.laboratory)

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : lms.name,
             'lms_id' : lms.id,
             'context_label' : request.form.get('context_label'),
             'context_id' : request.form.get('context_id'),
             'access' : False,
             'consumer_key': consumer_key
             }

    data['laboratory'] = laboratory
    return render_template('lti/administrator_tool_setup.html', info=data)

@lti.route("/experiment/", methods = ['POST'])
def launch_experiment():

    import pprint
    pprint.pprint(request.form)

    consumer_key = request.form.get('oauth_consumer_key')
    permission_to_lms_user = PermissionToLmsUser.find(key = consumer_key)

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
    author = ""
    referer = ""

    ManagerClass = get_manager_class(db_rlms.kind, db_rlms.version)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    response = remote_laboratory.reserve(db_laboratory.laboratory_id,
                                         author,
                                         lms_configuration,
                                         courses_configurations,
                                         request_payload,
                                         str(request.user_agent),
                                         request.remote_addr,
                                         referer)
    return redirect(response)

