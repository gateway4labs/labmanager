# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys
import json

from flask.ext.wtf import TextField, Required, URL

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.rlms import register, Laboratory, BaseRLMS, BaseFormCreator, Capabilities, Versions

def get_module(version):
    return sys.modules[__name__]

class VirtualAddForm(AddForm):

    web  = TextField("Web",    validators = [Required(), URL() ])
    name = TextField("Name",    validators = [Required() ])

    def __init__(self, add_or_edit, *args, **kwargs):
        super(VirtualAddForm, self).__init__(*args, **kwargs)

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        return new_configuration

class VirtualPermissionForm(RetrospectiveForm):
    pass

class VirtualLmsPermissionForm(VirtualPermissionForm, GenericPermissionForm):
    pass

class VirtualFormCreator(BaseFormCreator):

    def get_add_form(self):
        return VirtualAddForm

    def get_permission_form(self):
        return VirtualPermissionForm

    def get_lms_permission_form(self):
        return VirtualLmsPermissionForm

FORM_CREATOR = VirtualFormCreator()

class RLMS(BaseRLMS):

    def __init__(self, configuration):
        self.configuration = configuration

        config = json.loads(configuration or '{}')
        self.web  = config.get('web')
        self.name = config.get('name')
        self.height = config.get('height')

        if not self.web or not self.name:
            raise Exception("Laboratory misconfigured: fields missing" )

    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self): 
        return [ Capabilities.WIDGET ] 

    def test(self):
        json.loads(self.configuration)
        # TODO
        return None

    def get_laboratories(self, **kwargs):
        return [ Laboratory(self.name, self.name, autoload = True) ]

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):
        return {
            'reservation_id' : 'not-required',
            'load_url' : self.web
        }

    def load_widget(self, reservation_id, widget_name, **kwargs):
        return {
            'url' : self.web
        }

    def list_widgets(self, laboratory_id, **kwargs):
        default_widget = dict( name = 'default', description = 'Default widget')
        if self.height is not None:
            default_widget['height'] = self.height
        return [ default_widget ]


register("Virtual labs", ['0.1'], __name__)
