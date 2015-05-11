# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys
import json
import traceback

from flask.ext.wtf import TextField, Required, URL

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.rlms import register, Laboratory, BaseRLMS, BaseFormCreator, Capabilities, Versions

def get_module(version):
    return sys.modules[__name__]

class VirtualAddForm(AddForm):

    web      = TextField("Web",    validators = [Required(), URL() ])
    web_name = TextField("Web name",    validators = [Required() ])
    height   = TextField("Height")
    translation_url = TextField("Translations URL", description = "List of translations for this lab in a particular JSON format, if available")

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

    DEFAULT_AUTOLOAD = True

    def __init__(self, configuration):
        self.configuration = configuration

        config = json.loads(configuration or '{}')
        self.web  = config.get('web')
        self.name = config.get('web_name')
        self.height = config.get('height')
        self.translation_url = config.get('translation_url')

        if not self.web or not self.name:
            raise Exception("Laboratory misconfigured: fields missing: %s" % (configuration) )

    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self): 
        capabilities = [ Capabilities.WIDGET ] 
        if self.translation_url:
            capabilities.append(Capabilities.TRANSLATIONS)
        return capabilities

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

    def get_translations(self, laboratory_id, **kwargs):
        if not self.translation_url:
            return {}

        translations = VIRTUAL_LABS.rlms_cache.get('translations')
        if translations:
            return translations
        try:
            r = VIRTUAL_LABS.cached_session.get(self.translation_url)
            r.raise_for_status()
            translations_json = r.json()
        except Exception as e:
            traceback.print_exc()
            response = {
                'error' : unicode(e)
            }
            VIRTUAL_LABS.rlms_cache['translations'] = response
            return response
        else:
            VIRTUAL_LABS.rlms_cache['translations'] = translations_json
            return translations_json

    def list_widgets(self, laboratory_id, **kwargs):
        default_widget = dict( name = 'default', description = 'Default widget')
        if self.height is not None:
            default_widget['height'] = self.height
        return [ default_widget ]


def populate_cache(rlms):
    rlms.get_translations(None)

VIRTUAL_LABS = register("Virtual labs", ['0.1'], __name__)
VIRTUAL_LABS.add_local_periodic_task("Retrieve translations", populate_cache, minutes = 55)
