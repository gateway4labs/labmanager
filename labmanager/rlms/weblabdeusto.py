# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""

import json

from flaskext.wtf import Form, TextField, PasswordField, Required, IntegerField, URL, ValidationError

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.data import Laboratory

from .weblabdeusto_client import WebLabDeustoClient
from .weblabdeusto_data import ExperimentId

class AddForm(AddForm):

    remote_login = TextField("Login",        validators = [Required()])
    password     = PasswordField("Password")

    base_url     = TextField("Base URL",    validators = [Required(), URL() ])

    mappings     = TextField("Mappings",     validators = [Required()], default = "{}")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        old_configuration_dict = json.loads(old_configuration)
        new_configuration_dict = json.loads(new_configuration)
        if new_configuration_dict.get('password', '') == '':
            new_configuration_dict['password'] = old_configuration_dict.get('password','')
        return json.dumps(new_configuration_dict)

    def validate_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

    def validate_mappings(form, field):
        try:
            content = json.loads(field.data)
        except:
            raise ValidationError("Invalid json content")
        
        if not isinstance(content, dict):
            raise ValidationError("Dictionary expected")
        
        for key in content:
            if not isinstance(key, basestring):
                raise ValidationError("Keys must be strings")
           
            if '@' not in key:
                raise ValidationError("Key format: experiment_name@experiment_category ")
                
            value = content[key]
            if not isinstance(value, basestring):
                raise ValidationError("Values must be strings")
           
            if '@' not in value:
                raise ValidationError("Value format: experiment_name@experiment_category ")

class PermissionForm(RetrospectiveForm):
    priority = TextField("Priority")
    time     = TextField("Time (in seconds)")

    def validate_number(form, field):
        if field.data != '' and field.data is not None:
            try:
                int(field.data)
            except:
                raise ValidationError("Invalid value. Must be an integer.")


    validate_priority = validate_number
    validate_time     = validate_number

class LmsPermissionForm(PermissionForm, GenericPermissionForm):
    pass

def connection_tester(configuration):
    config = json.loads(configuration)
    return None

class ManagerClass(object):
    def __init__(self, configuration):
        config = json.loads(configuration or '{}')
        self.login    = config.get('remote_login')
        self.password = config.get('password')
        self.base_url = config.get('base_url')
        
        if self.login is None or self.password is None or self.base_url is None:
            raise Exception("Laboratory misconfigured: fields missing" )

    def get_laboratories(self):
        client = WebLabDeustoClient(self.base_url)
        session_id = client.login(self.login, self.password)
        experiments = client.list_experiments(session_id)
        laboratories = []
        for experiment in experiments:
            id = '%s@%s' % (experiment['experiment']['name'], experiment['experiment']['category']['name'])
            laboratories.append(Laboratory(id, id))
        return laboratories

    def reserve(self, laboratory_id, username, general_configuration_str, particular_configurations, user_agent, origin_ip, referer):
        client = WebLabDeustoClient(self.base_url)
        session_id = client.login(self.login, self.password)

        consumer_data = {
            "user_agent"    : user_agent,
            "referer"       : referer,
            "from_ip"       : origin_ip,
            "external_user" : username,
            #     "priority"      : "...", # the lower, the better
            #     "time_allowed"  : 100,   # seconds
            #     "initialization_in_accounting" :  False,
        }

        best_config = self._retrieve_best_configuration(general_configuration_str, particular_configurations)

        consumer_data.update(best_config)

        consumer_data_str = json.dumps(consumer_data)

        reservation_status = client.reserve_experiment(session_id, ExperimentId.parse(laboratory_id), '{}', consumer_data_str)
        return "%sclient/federated.html#reservation_id=%s" % (self.base_url, reservation_status.reservation_id.id)

    def _retrieve_best_configuration(self, general_configuration_str, particular_configurations):
        max_time     = None
        min_priority = None

        for particular_configuration_str in particular_configurations:
            particular_configuration = json.loads(particular_configuration_str or '{}')
            if 'time' in particular_configuration:
                max_time = max(int(particular_configuration['time']), max_time)
            if 'priority' in particular_configuration:
                if min_priority is None:
                    min_priority = int(particular_configuration['priority'])
                else:
                    min_priority = min(int(particular_configuration['priority']), min_priority)

        MAX = 2 ** 30
        general_configuration = json.loads(general_configuration_str or '{}')
        if 'time' in general_configuration:
            global_max_time     = int(general_configuration['time'])
        else:
            global_max_time     = MAX
        if 'priority' in general_configuration:    
            global_min_priority = int(general_configuration['priority'])
        else:
            global_min_priority = None

        overall_max_time = min(global_max_time or MAX, max_time or MAX)
        if overall_max_time is MAX:
            overall_max_time = None

        overall_min_priority = max(global_min_priority, min_priority)

        consumer_data = {}
        if overall_min_priority is not None:
            consumer_data['priority'] = overall_min_priority
        if overall_max_time is not None:
            consumer_data['time_allowed'] = overall_max_time
        return consumer_data
