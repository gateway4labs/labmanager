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

from flask import render_template, request, redirect, session

from labmanager.models import LMS, Credential, RLMS, Course
from labmanager.models import Permission, PermissionOnLaboratory, Laboratory

from labmanager.ims_lti import lti_blueprint as lti
from labmanager.rlms import get_manager_class

config = yload(open('labmanager/config.yml'))

@lti.route('/request_permission/', methods = ['POST'])
def permission_request():
    data = {}
    choice_data = []

    lms_id = int(request.form['lms_id'])
    context_id = request.form['context_id']
    context_label = request.form['context_label']

    incoming_lms = LMS.find(lms_id)
    local_context = Course.find_or_create(lms = incoming_lms,
                                             context = context_id,
                                             name = context_label)

    for labs in request.form.getlist('rlmslaboratories'):
        split_choice = labs.split(':')
        rlms_id, lab_id = int(split_choice[0]), int(split_choice[1])
        requested_lab = Laboratory.find(lab_id)
        if( requested_lab.rlms.id == rlms_id ):
            p_on_lab = PermissionOnLaboratory.find_for_lms_on_lab(incoming_lms,
                                                                  requested_lab)
            if(p_on_lab):
                Permission.find_or_create(local_context, p_on_lab)

    exp_status = Permission.find_all_for_context(local_context)
    data = {'context_id' :  context_id,
            'context_laboratories' :  exp_status,
            'consumer_key' : request.form.get('consumer_key')
            }

    return render_template('lti/experiments.html', info=data)


@lti.route("/", methods = ['POST'])
def start_ims():
    response = None

    consumer_key = request.form.get('oauth_consumer_key')
    auth = Credential.find_by_key(consumer_key)

    current_role = Set(request.form['roles'].split(','))
    req_course_data = request.form.get('lis_result_sourcedid')

    data = { 'user_agent' : request.user_agent,
             'origin_ip' : request.remote_addr,
             'lms' : auth.lms.name,
             'lms_id' : auth.lms.id,
             'context_label' : request.form.get('context_label'),
             'context_id' : request.form.get('context_id'),
             'access' : False,
             'consumer_key': consumer_key
             }

    local_context = Course.find_or_create(lms = auth.lms,
                                          context = data['context_id'],
                                          name = data['context_label'])

    context_laboratories = Permission.find_all_for_context(local_context)
    if context_laboratories:
        data['context_laboratories'] = context_laboratories

    if ('Instructor' in current_role):
        data['role'] = 'Instructor'
        data['rlms'] = {}
        data['rlms_ids'] = {}

        lms_laboratories = PermissionOnLaboratory.find_all_for_lms(auth.lms)

        for allowed_lab in lms_laboratories:
            laboratory = allowed_lab.laboratory
            owner_rlms = laboratory.rlms
            if( owner_rlms.kind in data['rlms'] ):
                data['rlms'][owner_rlms.kind].append(laboratory)
            else:
                data['rlms'][owner_rlms.kind] = [laboratory]
                data['rlms_ids'][owner_rlms.kind] = owner_rlms.id

        if lms_laboratories:
            response = render_template('lti/administrator_tool_setup.html', info=data)
        else:
            response = render_template('lti/instructions.html', info=data)

    elif ('Learner' in current_role):
        data['role'] = 'Learner'

        if context_laboratories:
            wo_denied = []
            for exp in context_laboratories:
                if exp.has_access:
                    wo_denied.append(exp)
            data['context_laboratories'] = wo_denied

            response = render_template('lti/administrator_tool_setup.html', info=data)
        else:
            response = render_template('lti/no_experiments_info.html', info=data)

    else:
        data['role'] = split_roles[0]
        response = render_template('lti/unknown_role.html', info=data)

    return response

@lti.route("/experiment/", methods = ['POST'])
def launch_experiment():
    response = ""
    consumer_key = request.form.get('consumer_key')
    lab_id = request.form.get('p_on_lab')
    context_id = request.form.get('context_id')

    auth = Credential.find_by_key(consumer_key)
    course = Course.find_by_lms_and_context(auth.lms, context_id)
    p_on_lab = PermissionOnLaboratory.find(lab_id)
    permission = Permission.get_for_lab_and_context(p_on_lab, course)

    if( permission and permission.has_access ):
        ## TODO:
        ## courses_configurations and request_payload
        ## author (from session?)
        ## referer
        db_lms = auth.lms
        courses_configurations = []
        request_payload = {}
        lms_configuration = p_on_lab.configuration
        db_laboratory   = p_on_lab.laboratory
        db_rlms         = db_laboratory.rlms
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
    else:
        response = "Not Allowed"

    return response
