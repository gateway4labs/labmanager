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

from flask import Response, render_template, request, abort, Blueprint

from labmanager.database import db_session
from labmanager.models import NewLMS, Credential, NewRLMS, Permission, Experiment, NewCourse
#from labmanager.rlms     import get_manager_class

from error_codes import messages_codes

configs = yload(open('labmanager/config.yaml'))
lti = Blueprint('lti', __name__)

@lti.route("/admin/", methods = ['POST'])
def admin_ims():
    message = ""
    response = ""

    consumer_key = request.form['oauth_consumer_key']
    auth = Credential.find_by_key(consumer_key)

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : auth.newlms.name,
             'lms_id' : auth.newlms.id,
             'context_label' : request.form['context_label'],
             'context_id' : request.form['context_id'],
             }

    # Defined by the standard. After this comes the role of the user as in
    # 'urn:lti:sysrole:ims/lis/Administrator' or 'urn:lti:sysrole:ims/lis/SysAdmin'
    urn_role_base = 'urn:lti:sysrole:ims/lis/'
    roles = Set()

    split_roles = request.form['roles'].split(',')
    for role in split_roles:
        if role.startswith(urn_role_base):
            roles.add(role[len(urn_role_base):])

    admin_roles = Set(configs['standard_urn_admin_roles'])
    current_users_roles = roles & admin_roles # Set intersection

    if len(current_users_roles) > 0:

        data['role'] = current_users_roles.pop() # Returns an arbitrary element
        data['rlms'] = {}
        data['rlms_ids'] = {}

        local_context = NewCourse.find_or_create(lms = auth.newlms,
                                                 context = request.form['context_id'],
                                                 name = request.form['context_label'])

        current_permissions = Permission.find_all_with_lms_and_context(lms = auth.newlms,
                                                                       context = local_context)

        data['access_requests'] = current_permissions

        for remote in NewRLMS.all(): # filter by allowed RLMSs
            experiments_in_rlms = remote.experiments
            data['rlms'][remote.kind] = [ exp for exp in experiments_in_rlms ]
            data['rlms_ids'][remote.kind] = remote.id

        return render_template('lti/administrator_tool_setup.html', info=data)

    else:
        data['role'] = split_roles[0]
        return render_template('lti/unknown_role.html', info=data)


@lti.route('/request_permission/', methods = ['POST'])
def permission_request():
    data = {}
    choice_data = []

    for exps in request.form.getlist('rlmsexperiments'):
        split_choice = exps.split(':')
        rlms_id, exp_id = int(split_choice[0]), int(split_choice[1])
        choice_data.append((rlms_id, exp_id))

    lms_id = int(request.form['lms_id'])
    context_id = request.form['context_id']
    context_label = request.form['context_label']
    newlms = NewLMS.find(lms_id)

    local_context = NewCourse.find_or_create(lms = newlms,
                                             context = context_id,
                                             name = context_label)

    if 'rlmsexperiments' in request.form:
        for rlms_id, exp_id in choice_data:
            experiment = Experiment.find_with_id_and_rlms_id(exp_id, rlms_id)
            Permission.find_or_create(lms = newlms, experiment = experiment,
                                      context = local_context)

    exp_status = Permission.find_all_with_lms_and_context(lms = newlms, context = local_context)
    data['context_experiments'] = exp_status

    return render_template('lti/experiments.html', info=data)


@lti.route("/", methods = ['POST'])
def start_ims():
    message = ""
    response = ""

    consumer_key = request.form['oauth_consumer_key']
    auth = Credential.find_by_key(consumer_key)

    current_role = Set(request.form['roles'].split(','))
    req_course_data = request.form['lis_result_sourcedid']

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : auth.newlms.name,
             'lms_id' : auth.newlms.id,
             'context_label' : request.form['context_label'],
             'context_id' : request.form['context_id'],
             'access' : False
             }

    local_context = NewCourse.find_or_create(lms = auth.newlms,
                                             context = data['context_id'],
                                             name = data['context_label'])

    context_experiments = Permission.find_all_with_lms_and_context(auth.newlms,
                                                                   local_context)

    if context_experiments:
        data['context_experiments'] = context_experiments

    if ('Instructor' in current_role):
        data['role'] = 'Instructor'

        if context_experiments:
            response = render_template('lti/experiments.html', info=data)
        else:
            response = render_template('lti/instructions.html', info=data)

    elif ('Learner' in current_role):
        data['role'] = 'Learner'

        if context_experiments:
            wo_denied = []
            for exp in context_experiments:
                if exp.access != 'denied':
                    wo_denied.append(exp)
            data['context_experiments'] = wo_denied

            response = render_template('lti/experiments.html', info=data)
        else:
            response = render_template('lti/no_experiments_info.html', info=data)

    else:
        response = render_template('lti/unknown_role.html', info=data)

    return response

@lti.route("/experiment/<experiment>", methods = ['GET'])
def launch_experiment(experiment=None):
    response = ""

    if (experiment):
        response = experiment
    else:
        response = "No soup for you!"

    return response
